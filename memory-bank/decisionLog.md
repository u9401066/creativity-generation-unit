# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-15 | 採用憲法-子法層級架構 | 類似 speckit 的規則層級，可擴展且清晰 |
| 2025-12-15 | DDD + DAL 獨立架構 | 業務邏輯與資料存取分離，提高可測試性 |
| 2025-12-15 | Skills 模組化拆分 | 單一職責，可組合使用，易於維護 |
| 2025-12-15 | Memory Bank 與操作綁定 | 確保專案記憶即時更新，不遺漏 |
| 2025-12-15 | 升級 LangGraph 到 1.0+ 並採用 Functional API，同時更新 Python 目標版本到 3.12 | LangGraph 1.0 與 Python 3.12 讓程式碼更簡潔，同時保留 builder.py 作為兼容選項 |
| 2025-12-15 | 採用 Multi-Agent 並發架構進行創意發想，避免 Context 污染 | 各 Agent 保有獨立上下文，並以 Orchestrator 統籌整合結果 |
| 2025-12-15 | 建立統一 ThinkingEngine，支援 Simple / Deep / Spark 三種模式 | 保持快速發想能力，同時支援更深的思考結構 |
| 2025-12-15 | 採用 ThinkingEngine 統一架構整合 Simple / Deep / Spark / Hybrid 四種思考模式 | 讓系統能依主題複雜度自動選擇最適合的模式，並維持向後兼容 |
| 2025-12-16 | LLM Client 從 instructor + OpenAI 改為 LangChain + Ollama（with_structured_output） | 提升穩定性、減少初始化成本並簡化架構 |
| 2026-01-06 | CGU v2 重構：從「模擬創意」到「實現創意機制」 | 以 Analogy / Graph / Adversarial 三大引擎取代單純 Prompt 模擬 |
| 2026-01-06 | CGU v3 轉變：從「語言互動」到「Agent 工具互動」 | 讓 Agent 自主決定搜尋、連結、驗證、演化流程 |
| 2026-04-15 | 將 ROADMAP 升級為正式產品路線圖 | 對齊目前已落地能力與未來版本規劃，讓 PR 與版本溝通有一致基準 |

---

## [2025-12-15] 採用憲法-子法層級架構

### 背景
需要一個清晰的規則層級系統，類似 speckit 但可擴展。

### 選項
1. 單一 `copilot-instructions.md`
2. 憲法 + 子法層級
3. 全部放在 Skills 內

### 決定
採用選項 2：憲法-子法層級。

### 理由
- 最高原則集中在 `CONSTITUTION.md`
- 細則可在 `.github/bylaws/` 擴展
- Skills 可專注於操作程序

### 影響
- 新增 `CONSTITUTION.md`
- 新增 `.github/bylaws/` 目錄
- Skills 需引用相關法規

## [2026-01-06] CGU v2 重構：從「模擬創意」到「實現創意機制」

### 背景
早期版本本質上仍偏向 Prompt 模板加上隨機碰撞，缺乏真正可驗證、可迭代的創意機制。

### 選項
1. 繼續擴充提示詞模板
2. 建立可組合的核心創意引擎

### 決定
採用選項 2：以 AnalogyEngine、GraphTraversalEngine、AdversarialEngine 建立創意核心。

### 理由
- 可將創意過程拆為可理解、可測試、可組合的模組
- 更符合「創意是跨結構連結」的理論基礎
- 能支援後續 Agent 自主工具互動

### 影響
- 新增 v2 核心引擎與統一 `CreativityCore`
- 成為後續 v3 Agent 工具箱的能力底座

## [2026-01-06] CGU v3 轉變：從「語言互動」到「Agent 工具互動」

### 背景
單純依賴外層 prompt engineering 難以突破內部模型限制，無法讓 Agent 形成真正自主的探索流程。

### 選項
1. 持續優化提示詞方法論
2. 提供 Agent 可調用的創意工具，讓其自行決定流程

### 決定
採用選項 2：建立 Agent 自主創意工具箱。

### 理由
- 工具流程比純文字互動更可驗證
- Agent 可以根據任務動態選擇探索策略
- 為後續 Session、Spark-Soup、品質評估整合鋪路

### 影響
- 新增 ConceptExplorer、ConnectionFinder、NoveltyChecker、IdeaEvolver、CreativityLogger
- 專案核心敘事改為 Agent-Driven Creativity

## [2026-04-15] 將 ROADMAP 升級為正式產品路線圖

### 背景
現有 `ROADMAP.md` 仍以 v0.4 時期的規劃語氣為主，但倉庫實作已包含 Spark-Soup、互動式 Session、品質評估與演化相關能力，文件與產品現況之間出現落差。

### 選項
1. 只更新既有核取方塊與少量文句
2. 直接重寫 ROADMAP，整理成正式產品文件

### 決定
採用選項 2：將 `ROADMAP.md` 重寫為正式產品路線圖。

### 理由
- 讓版本敘事與現有實作對齊
- 讓後續 PR、README、CHANGELOG 有一致參照基準
- 讓 v0.5.x 的完成範圍與完成定義更清楚

### 影響
- `ROADMAP.md` 會以版本主軸、完成定義與目標時程為核心
- Memory Bank 需同步反映此次文檔治理任務
- 後續版本討論應以新版 ROADMAP 為優先依據
