# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-15 | 採用憲法-子法層級架構 | 類似 speckit 的規則層級，可擴展且清晰 |
| 2025-12-15 | DDD + DAL 獨立架構 | 業務邏輯與資料存取分離，提高可測試性 |
| 2025-12-15 | Skills 模組化拆分 | 單一職責，可組合使用，易於維護 |
| 2025-12-15 | Memory Bank 與操作綁定 | 確保專案記憶即時更新，不遺漏 |

---

## [2025-12-15] 採用憲法-子法層級架構

### 背景
需要一個清晰的規則層級系統，類似 speckit 但可擴展。

### 選項
1. 單一 copilot-instructions.md - 簡單但不夠靈活
2. 憲法 + 子法層級 - 清晰層級，可擴展
3. 全部放在 Skills 內 - 分散，難以管理

### 決定
採用選項 2：憲法-子法層級

### 理由
- 最高原則集中在 CONSTITUTION.md
- 細則可在 bylaws/ 擴展
- Skills 專注於操作程序
- 符合現實法律體系，易理解

### 影響
- 新增 CONSTITUTION.md
- 新增 .github/bylaws/ 目錄
- Skills 需引用相關法規
| 2025-12-15 | 升級 LangGraph 到 1.0+ 並採用 Functional API，同時更新 Python 目標版本到 3.12 | 1. LangGraph 1.0 提供 @entrypoint/@task 裝飾器，代碼更簡潔
2. Python 3.12 的 Type Parameter Syntax (PEP 695) 讓泛型定義更清晰
3. Python 3.12 f-string 改進 (PEP 701) 允許多行和嵌套，提高可讀性
4. 保留原有 StateGraph 版本 (builder.py) 作為兼容選項 |
| 2025-12-15 | 採用 Multi-Agent 並發架構進行創意發想，避免 Context 污染 | 1. 每個 Agent 有獨立 Context，不會互相污染思考空間
2. 三種人格 Agent：Explorer（廣度探索）、Critic（深度批判）、Wildcard（狂想打破規則）
3. Spark Engine 火花引擎模擬「靈感一閃」：低關聯度 + 跨人格碰撞 = 意外連結
4. Orchestrator 統籌並發執行，整合最終結果
5. 支援 asyncio.gather 真正並發，效率更高 |
| 2025-12-15 | 建立統一 ThinkingEngine，支援三種模式：Simple（Ollama/Copilot快思）、Deep（Multi-Agent慢想）、Spark（碰撞創意） | 1. 保持與現有 Ollama/Copilot 模式兼容 2. 透過 mode 參數讓用戶選擇深度 3. 新增 MCP Tool: deep_think, multi_agent_brainstorm, spark_collision_deep |
| 2025-12-15 | 採用 ThinkingEngine 統一架構整合 Simple/Deep/Spark/Hybrid 四種思考模式 | 用戶需要保持 Ollama/Copilot 簡單模式的快速發想能力，同時希望能加深思考架構。ThinkingEngine 作為統一入口，根據主題複雜度自動選擇最適合的模式，同時保持向後兼容性。 |
