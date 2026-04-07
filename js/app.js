const defaultSuppliers = [
  {
    id: 1,
    vendorName: "宏達工業股份有限公司",
    taxId: "24567891",
    contactPerson: "王志明",
    phone: "02-2345-6789",
    email: "service@hungda.com.tw",
    status: "合作中",
    address: "台北市內湖區瑞光路100號",
    remark: "主要提供機構零組件"
  },
  {
    id: 2,
    vendorName: "昇揚精密企業有限公司",
    taxId: "53426789",
    contactPerson: "陳怡君",
    phone: "04-2256-8899",
    email: "contact@shengyang.com.tw",
    status: "審核中",
    address: "台中市西屯區台灣大道三段99號",
    remark: "待完成品質稽核"
  },
  {
    id: 3,
    vendorName: "聯成材料科技股份有限公司",
    taxId: "82914567",
    contactPerson: "林柏翰",
    phone: "07-3388-1122",
    email: "sales@liancheng.com.tw",
    status: "停用",
    address: "高雄市前鎮區中山二路88號",
    remark: "暫停合作中"
  }
];

function initSuppliers() {
  if (!localStorage.getItem("suppliers")) {
    localStorage.setItem("suppliers", JSON.stringify(defaultSuppliers));
  }
}

function getSuppliers() {
  return JSON.parse(localStorage.getItem("suppliers")) || [];
}

function saveSuppliers(data) {
  localStorage.setItem("suppliers", JSON.stringify(data));
}

function getStatusClass(status) {
  if (status === "合作中") return "status-active";
  if (status === "審核中") return "status-review";
  return "status-stop";
}

function renderSuppliers() {
  const tableBody = document.getElementById("supplierTableBody");
  if (!tableBody) return;

  const searchInput = document.getElementById("searchInput");
  const statusFilter = document.getElementById("statusFilter");

  let suppliers = getSuppliers();
  const keyword = (searchInput?.value || "").trim().toLowerCase();
  const status = statusFilter?.value || "";

  suppliers = suppliers.filter(item => {
    const matchKeyword =
      item.vendorName.toLowerCase().includes(keyword) ||
      item.contactPerson.toLowerCase().includes(keyword) ||
      item.taxId.toLowerCase().includes(keyword);

    const matchStatus = !status || item.status === status;
    return matchKeyword && matchStatus;
  });

  tableBody.innerHTML = suppliers.map(item => `
    <tr>
      <td>${item.vendorName}</td>
      <td>${item.taxId}</td>
      <td>${item.contactPerson}</td>
      <td>${item.phone}</td>
      <td>${item.email}</td>
      <td><span class="status-badge ${getStatusClass(item.status)}">${item.status}</span></td>
      <td>
        <div class="action-links">
          <a href="#" onclick="editSupplier(${item.id})">編輯</a>
          <a href="#" onclick="deleteSupplier(${item.id})">刪除</a>
        </div>
      </td>
    </tr>
  `).join("");

  if (!suppliers.length) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color:#6b7280;">查無符合條件的供應商資料</td>
      </tr>
    `;
  }
}

function deleteSupplier(id) {
  const confirmed = confirm("確定要刪除此供應商資料嗎？");
  if (!confirmed) return;

  const suppliers = getSuppliers().filter(item => item.id !== id);
  saveSuppliers(suppliers);
  renderSuppliers();
}

function editSupplier(id) {
  localStorage.setItem("editSupplierId", String(id));
  window.location.href = "supplier-form.html";
}

function loadSupplierToForm() {
  const form = document.getElementById("supplierForm");
  if (!form) return;

  const editId = localStorage.getItem("editSupplierId");
  if (!editId) return;

  const supplier = getSuppliers().find(item => item.id === Number(editId));
  if (!supplier) return;

  document.getElementById("vendorName").value = supplier.vendorName;
  document.getElementById("taxId").value = supplier.taxId;
  document.getElementById("contactPerson").value = supplier.contactPerson;
  document.getElementById("phone").value = supplier.phone;
  document.getElementById("email").value = supplier.email;
  document.getElementById("status").value = supplier.status;
  document.getElementById("address").value = supplier.address || "";
  document.getElementById("remark").value = supplier.remark || "";
}

function handleFormSubmit() {
  const form = document.getElementById("supplierForm");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const suppliers = getSuppliers();
    const editId = localStorage.getItem("editSupplierId");

    const data = {
      vendorName: document.getElementById("vendorName").value.trim(),
      taxId: document.getElementById("taxId").value.trim(),
      contactPerson: document.getElementById("contactPerson").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      email: document.getElementById("email").value.trim(),
      status: document.getElementById("status").value,
      address: document.getElementById("address").value.trim(),
      remark: document.getElementById("remark").value.trim()
    };

    if (editId) {
      const index = suppliers.findIndex(item => item.id === Number(editId));
      if (index !== -1) {
        suppliers[index] = { ...suppliers[index], ...data };
      }
      localStorage.removeItem("editSupplierId");
    } else {
      suppliers.push({
        id: Date.now(),
        ...data
      });
    }

    saveSuppliers(suppliers);
    alert("資料已儲存");
    window.location.href = "suppliers.html";
  });
}

function bindFilters() {
  const searchInput = document.getElementById("searchInput");
  const statusFilter = document.getElementById("statusFilter");

  if (searchInput) {
    searchInput.addEventListener("input", renderSuppliers);
  }

  if (statusFilter) {
    statusFilter.addEventListener("change", renderSuppliers);
  }
}

function bindLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (!logoutBtn) return;

  logoutBtn.addEventListener("click", function (e) {
    e.preventDefault();
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("editSupplierId");
    window.location.href = "index.html";
  });
}

function checkLogin() {
  const path = window.location.pathname;
  const isLoginPage = path.includes("index.html") || path.endsWith("/") || path === "";
  const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";

  if (!isLoginPage && !isLoggedIn) {
    window.location.href = "index.html";
  }
}

initSuppliers();
checkLogin();
renderSuppliers();
bindFilters();
handleFormSubmit();
loadSupplierToForm();
bindLogout();
