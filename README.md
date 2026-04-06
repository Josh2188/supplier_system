# 供應商資料共用系統樣板

本專案提供一個簡易的 Flask 應用，用於內部管理供應商資料、合約與評分。它實作了前一份設計文檔中的關鍵概念，包含使用者註冊與登入、角色權限控管，以及供應商資料的 CRUD 操作。

## 環境安裝

1. 建議先建立 Python 虛擬環境：

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. 安裝依賴：

   ```bash
   pip install -r requirements.txt
   ```

3. 建立資料庫（預設使用 SQLite）：

   ```bash
   flask db init      # 首次初始化資料庫遷移檔
   flask db migrate   # 產生遷移腳本
   flask db upgrade   # 執行遷移建立資料表
   ```

   如果要使用 PostgreSQL 或其他資料庫，可在 `app.py` 使用環境變數 `DATABASE_URI` 重新指定，例如：

   ```bash
   export DATABASE_URI=postgresql://user:password@localhost/supplier_db
   ```

4. 設定 JWT 密鑰（可選）：

   預設情況下 `JWT_SECRET_KEY` 會使用程式碼內建的字串，建議自行設定環境變數：

   ```bash
   export JWT_SECRET_KEY=your-secret-key
   ```

5. 啟動應用：

   ```bash
   python app.py
   ```

   服務將在 `http://localhost:5000` 監聽，您可以使用 Postman 等工具進行 API 測試。

## API 範例

以下為部分 API 呼叫範例（使用 `curl`）：

### 註冊使用者

```bash
curl -X POST http://localhost:5000/api/register \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "password": "password123", "role": "admin"}'
```

### 登入取得 JWT

```bash
curl -X POST http://localhost:5000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "password": "password123"}'
```

將回傳的 `access_token` 用於後續請求，例：

```bash
export TOKEN=your_access_token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/suppliers
```

### 建立供應商

```bash
curl -X POST http://localhost:5000/api/suppliers \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "供應商A", "category": "電子零件", "contact_person": "王小明"}'
```

### 查詢供應商列表

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/suppliers
```

更多端點請參考 `app.py` 中的路由實作。

## 注意事項

* 此專案僅為示範用，並未實作前端介面。若要部署至生產環境，建議採用更完善的驗證、錯誤處理與輸入驗證機制。
* 若與公司其他系統整合，請依需求擴充資料模型與 API。
