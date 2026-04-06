"""
Simple Supplier Data Sharing System
---------------------------------

This Flask application implements a minimal supplier data sharing backend
with the following features:

* User registration and login using JWT authentication.
* Role‑based access control (viewer, editor, admin).
* CRUD operations on suppliers.
* Contract and rating management for suppliers.

The goal of this example is to demonstrate how one might build the core of
an internal supplier data sharing system. In a production system you would
separate models, configuration and blueprints into distinct modules and
enforce stricter security and validation. See the accompanying design
document for more details on recommended architecture and enhancements.
"""

import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import generate_password_hash, check_password_hash


def create_app() -> Flask:
    """Factory to create and configure the Flask app."""
    app = Flask(__name__)

    # Configuration: use SQLite by default; can override via environment
    db_url = os.environ.get("DATABASE_URI", "sqlite:///supplier.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # JWT configuration
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-this-secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register routes
    register_routes(app)

    return app


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


class User(db.Model):
    """Application user.

    Roles:
    - admin: manage users and perform all operations.
    - editor: create and update suppliers, contracts and ratings.
    - viewer: read‑only access.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="viewer", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class Supplier(db.Model):
    """Supplier entity."""

    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    status = db.Column(db.String(50), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contracts = db.relationship("Contract", back_populates="supplier", cascade="all, delete-orphan")
    ratings = db.relationship("SupplierRating", back_populates="supplier", cascade="all, delete-orphan")

    def to_dict(self, include_details: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details:
            data["contracts"] = [contract.to_dict() for contract in self.contracts]
            data["ratings"] = [rating.to_dict() for rating in self.ratings]
        return data


class Contract(db.Model):
    """Contract between the company and a supplier."""

    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    contract_number = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    terms = db.Column(db.Text)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="contracts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "contract_number": self.contract_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "terms": self.terms,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupplierRating(db.Model):
    """Rating given to a supplier."""

    __tablename__ = "supplier_ratings"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    score = db.Column(db.Float)
    assessment_date = db.Column(db.Date, default=datetime.utcnow)
    assessor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    notes = db.Column(db.Text)

    supplier = db.relationship("Supplier", back_populates="ratings")
    assessor = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "score": self.score,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "assessor_id": self.assessor_id,
            "notes": self.notes,
        }


def role_required(roles):
    """Decorator to require user to have a role in `roles`.

    Usage:
        @role_required(["editor", "admin"])
        def my_view(...)
    """
    def decorator(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            if not identity or identity.get("role") not in roles:
                return jsonify({"message": "Insufficient permission"}), 403
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


def register_routes(app: Flask) -> None:
    """Register all API routes."""

    @app.route("/api/register", methods=["POST"])
    def register_user():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "viewer")
        if not username or not password:
            return jsonify({"message": "username and password required"}), 400
        if role not in ("admin", "editor", "viewer"):
            return jsonify({"message": "invalid role"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "username already exists"}), 409
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "user created", "user": user.to_dict()}), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"message": "username and password required"}), 400
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"message": "invalid credentials"}), 401
        token = create_access_token(identity={"id": user.id, "role": user.role})
        return jsonify({"access_token": token, "user": user.to_dict()})

    @app.route("/api/suppliers", methods=["GET"])
    @jwt_required()
    def list_suppliers():
        """List suppliers with optional filters."""
        name_query = request.args.get("name")
        category = request.args.get("category")
        status = request.args.get("status")

        query = Supplier.query
        if name_query:
            query = query.filter(Supplier.name.ilike(f"%{name_query}%"))
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        suppliers = query.order_by(Supplier.name).all()
        return jsonify({"data": [supplier.to_dict() for supplier in suppliers]})

    @app.route("/api/suppliers", methods=["POST"])
    @role_required(["editor", "admin"])
    def create_supplier():
        data = request.get_json() or {}
        name = data.get("name")
        if not name:
            return jsonify({"message": "name is required"}), 400
        if Supplier.query.filter_by(name=name).first():
            return jsonify({"message": "supplier already exists"}), 409
        supplier = Supplier(
            name=name,
            category=data.get("category"),
            contact_person=data.get("contact_person"),
            contact_phone=data.get("contact_phone"),
            contact_email=data.get("contact_email"),
            address=data.get("address"),
            status=data.get("status", "active"),
        )
        db.session.add(supplier)
        db.session.commit()
        return jsonify({"message": "supplier created", "data": supplier.to_dict()}), 201

    @app.route("/api/suppliers/<int:supplier_id>", methods=["GET"])
    @jwt_required()
    def get_supplier(supplier_id: int):
        supplier = Supplier.query.get_or_404(supplier_id)
        include_details = request.args.get("details", "false").lower() == "true"
        return jsonify({"data": supplier.to_dict(include_details=include_details)})

    @app.route("/api/suppliers/<int:supplier_id>", methods=["PUT", "PATCH"])
    @role_required(["editor", "admin"])
    def update_supplier(supplier_id: int):
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json() or {}
        # update fields if provided
        for field in ["name", "category", "contact_person", "contact_phone", "contact_email", "address", "status"]:
            if field in data and data[field] is not None:
                setattr(supplier, field, data[field])
        supplier.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "supplier updated", "data": supplier.to_dict()})

    @app.route("/api/suppliers/<int:supplier_id>", methods=["DELETE"])
    @role_required(["admin"])
    def delete_supplier(supplier_id: int):
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        return jsonify({"message": "supplier deleted"})

    @app.route("/api/suppliers/<int:supplier_id>/contracts", methods=["GET"])
    @jwt_required()
    def list_contracts(supplier_id: int):
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify({"data": [c.to_dict() for c in supplier.contracts]})

    @app.route("/api/suppliers/<int:supplier_id>/contracts", methods=["POST"])
    @role_required(["editor", "admin"])
    def create_contract(supplier_id: int):
        Supplier.query.get_or_404(supplier_id)
        data = request.get_json() or {}
        contract_number = data.get("contract_number")
        if not contract_number:
            return jsonify({"message": "contract_number is required"}), 400
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        def parse_date(d):
            if not d:
                return None
            try:
                return datetime.fromisoformat(d).date()
            except ValueError:
                return None
        contract = Contract(
            supplier_id=supplier_id,
            contract_number=contract_number,
            start_date=parse_date(start_date),
            end_date=parse_date(end_date),
            terms=data.get("terms"),
            remarks=data.get("remarks"),
        )
        db.session.add(contract)
        db.session.commit()
        return jsonify({"message": "contract created", "data": contract.to_dict()}), 201

    @app.route("/api/suppliers/<int:supplier_id>/ratings", methods=["GET"])
    @jwt_required()
    def list_ratings(supplier_id: int):
        Supplier.query.get_or_404(supplier_id)
        ratings = SupplierRating.query.filter_by(supplier_id=supplier_id).order_by(SupplierRating.assessment_date.desc()).all()
        return jsonify({"data": [r.to_dict() for r in ratings]})

    @app.route("/api/suppliers/<int:supplier_id>/ratings", methods=["POST"])
    @role_required(["editor", "admin"])
    def create_rating(supplier_id: int):
        Supplier.query.get_or_404(supplier_id)
        data = request.get_json() or {}
        score = data.get("score")
        if score is None:
            return jsonify({"message": "score is required"}), 400
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return jsonify({"message": "score must be a number"}), 400
        assessment_date = data.get("assessment_date")
        if assessment_date:
            try:
                assessment_date_parsed = datetime.fromisoformat(assessment_date).date()
            except ValueError:
                return jsonify({"message": "assessment_date must be ISO date"}), 400
        else:
            assessment_date_parsed = datetime.utcnow().date()
        identity = get_jwt_identity()
        assessor_id = identity.get("id") if identity else None
        rating = SupplierRating(
            supplier_id=supplier_id,
            score=score_val,
            assessment_date=assessment_date_parsed,
            assessor_id=assessor_id,
            notes=data.get("notes"),
        )
        db.session.add(rating)
        db.session.commit()
        return jsonify({"message": "rating created", "data": rating.to_dict()}), 201


# Entrypoint when running this script directly
if __name__ == "__main__":
    app = create_app()
    # For local development only; use a proper server in production
    app.run(host="0.0.0.0", port=5000, debug=True)