# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-15 | 採用憲法-子法層級架構 | 類似 speckit 的規則層級，可擴展且清晰 |
| 2026-08-17 | MCP SDK 2-only 並建立 protocol/wheel smoke hard gate | 避免只改依賴宣告；每次發布都驗證 direct、stdio 與已安裝 wheel 的實際協定行為 |
| 2026-08-17 | live LLM 測試改為 opt-in integration marker | 預設 CI 必須可重現且不依賴本機 Ollama；真實後端仍可透過明確環境變數執行 |
| 2026-10-02 | 缺陷先以審查文件凍結，再討論、再實作（`docs/critical-review-and-improvement-plan.md`） | 憲法第 6 條「文檔優先」；40 項缺陷之間有相依關係（評估缺位是多數機制缺陷的前提），需先決定 Q1–Q10 再排 P0 範圍 |
| 2026-10-02 | 缺陷探針放在 `tests/probes/`（檔名非 `test_*`，不被 pytest 收集、不作 CI gate），修正後再轉為不變式回歸測試 | 憲法第 7.1 條要求零散測試寫進 `tests/`；但探針記錄的是「現況缺陷行為」，不能寫成斷言規格，否則會重蹈 E1「把缺陷鎖成規格」的覆轍 |
| 2026-10-02 | **採用 Agent Plugins 1.0 作為 harness 的對外交付格式**：可攜核心（`plugin.json`＋`skills/`＋`mcp.json`）放在 `plugins/cgu/`，Copilot 專屬放 `com.github.copilot/`，Codex 專屬放 `extensions.com.openai` | 已回查官方來源：Copilot（VS Code／CLI／SDK／app GA）與 Codex 都實作此開放標準（2026-08-06 發布）；可攜的只有 skills 與 MCP，因此方法論放 skills，agents 只做 Copilot 端薄包裝，hooks 預設不附（D-20）。本機無 CLI，安裝需人工驗證，未驗證不宣稱支援 |
| 2026-10-02 | 以分階段執行計畫（`docs/program-plan.md`）推進：P0 止血 → P1 地基／P2 Harness 骨架 → P3 哲學層 → P4 創意機制 → P5 人機回饋 → P6 v1.0；預設決策 D-01～D-20 先採用、可否決；G4 為預先登記的停損關卡 | 缺陷之間有相依（評估缺位是多數機制缺陷的前提），需有序處理；預先登記停損條件，避免在證據不利時持續投入生成機制 |
| 2026-10-02 | 評估 baseline 命名為 `BL0–BL3`，缺陷維持 `A1–F4` | 原 `B0–B3` 與缺陷 `B1–B11` 撞名（「B3」同時指圖譜缺陷與等預算 baseline），會讓討論與驗收混淆 |
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
| 2025-12-16 | LLM Client 從 instructor + OpenAI 改為 LangChain + Ollama (with_structured_output) | 1. LangChain 的 with_structured_output 更穩定且與 Ollama 整合更好 2. Ollama 服務持續運行，無需每次初始化延遲 3. 移除 instructor 依賴，簡化架構 |
| 2026-01-06 | CGU v2 重構：從「模擬創意」到「實現創意機制」| **問題**：v1 本質是 Prompt 模板 + 隨機碰撞 = 假創意。**解決**：採用三大核心引擎：1. AnalogyEngine（結構化類比搜尋）2. GraphTraversalEngine（概念圖譜非顯而易見路徑）3. AdversarialEngine（對抗式進化）。**原理**：基於 Koestler Bisociation 理論，創意 = 結構同構的意外連結。 |
| 2026-01-06 | CGU v3 轉變：從「語言互動」到「Agent 工具互動」| **核心洞察**：Copilot 內部觸碰不到，無論外層做什麼最終都是 Prompt 進去。**解決**：給 Agent 工具，讓它自己探索出創意。5 個核心工具：ConceptExplorer（搜尋）、ConnectionFinder（連結）、NoveltyChecker（驗證）、IdeaEvolver（演化）、CreativityLogger（記錄）。Agent 自己決定流程，而不是我們規定。 |
