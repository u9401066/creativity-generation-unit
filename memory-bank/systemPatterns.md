# System Patterns

> 📌 此檔案記錄專案中使用的模式和慣例，新模式出現時更新。

## 🏗️ 架構模式

### DDD 分層架構
```
Presentation → Application → Domain ← Infrastructure
```
- Domain 層不依賴任何外層
- Repository Pattern 為唯一資料存取方式

### 憲法-子法層級
```
CONSTITUTION.md (最高原則)
  └── .github/bylaws/ (子法)
        └── .claude/skills/ (實施細則)
```

## 🛠️ 設計模式

### Hook 累積與 agent 整理（2026-10-07）
- Hook 快速寫入提問，不載入 MCP 或呼叫模型；未整理佇列由缺少 review 的提問推導。
- MCP 暴露待辦與 `inquiry_organize` 工單；呼叫端模型完成語意整理，`distill` 回交可重用素材。
- 來源 ID 與儲存文字 SHA-256 在同一資料庫寫入交易驗證；素材 ID 依種類、去識別後文字與證據產生，重送不重複。
- 刪除任一來源即刪除依賴素材；預設 `ngram`，embedding 與 local generation 僅明確選用。

### Repository Pattern
- 介面在 Domain 層定義
- 實作在 Infrastructure 層

### Strategy Pattern
- 用於取代複雜條件判斷
- 實例：ShippingStrategy, PaymentStrategy

### Command Pattern (CQRS)
- Commands: 寫入操作
- Queries: 讀取操作

## 📝 命名慣例

| 類型 | 慣例 | 範例 |
|------|------|------|
| Entity | 名詞單數 | `User`, `Order` |
| Value Object | 描述性名詞 | `Email`, `Money` |
| Repository | `I{Entity}Repository` | `IUserRepository` |
| Use Case | 動詞 + 名詞 | `CreateOrder` |
| Domain Event | 過去式 | `OrderCreated` |

## 📚 程式碼慣例

### Python
- 使用 `snake_case` 命名
- 檔案名全小寫
- 類別使用 `PascalCase`
- 優先使用 type hints

### 測試
- 測試檔案以 `test_` 開頭
- 測試類別以 `Test` 開頭
- 使用 pytest markers 分類

---
*Last updated: 2025-12-15*
