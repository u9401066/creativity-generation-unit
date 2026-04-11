# Changelog

所有重要變更都會記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [Unreleased]

### Added
- 🔌 **v3 Agent-Driven Creativity Tools → MCP Tools 註冊**
  - `explore_concept` - 概念探索 MCP 工具
  - `find_connections` - 連結發現 MCP 工具
  - `check_novelty` - 新穎度驗證 MCP 工具
  - `evolve_idea_tool` - 想法演化 MCP 工具（5 種突變方式）
  - `random_concept` - 隨機概念 MCP 工具
  - `suggest_bridges` - 橋接建議 MCP 工具
  - `creativity_session_start` - 開始創意會話 MCP 工具
  - `creativity_session_record` - 記錄並驗證想法 MCP 工具
  - `creativity_session_progress` - 查看探索進度 MCP 工具

- 🧪 **v3 Tools 完整測試**
  - `tests/test_creativity_tools.py` - 52 個測試案例
  - 涵蓋：ConceptExplorer, ConnectionFinder, NoveltyChecker, IdeaEvolver, CreativityLogger, CreativityToolbox, MCP 整合

## [0.4.0] - 2026-01-06

### Added
- 🧠 **v2 核心引擎 - 從「模擬創意」到「實現創意機制」**
  - `src/cgu/core/analogy.py` - AnalogyEngine 跨域類比搜尋器
  - `src/cgu/core/graph.py` - ConceptGraph + GraphTraversalEngine
  - `src/cgu/core/adversarial.py` - AdversarialEngine 對抗式進化
  - `src/cgu/core/creativity_core.py` - CreativityCore 統一引擎
  - 基於 Koestler Bisociation 理論：創意 = 結構同構的意外連結

- 🛠️ **v3 Agent-Driven Creativity Tools**
  - `src/cgu/tools/creativity_tools.py` - Agent 自主創意工具集
  - `ConceptExplorer` - 概念搜尋器，探索概念空間
  - `ConnectionFinder` - 連結發現器，尋找跨域連結
  - `NoveltyChecker` - 新穎度驗證器，檢查想法是否新穎
  - `IdeaEvolver` - 想法演化器，突變和進化想法
  - `CreativityLogger` - 創意記錄器，追蹤探索過程
  - `CreativityToolbox` - 統一工具箱，供 Agent 自由組合

### Changed
- 核心架構轉變：從「人與 Agent 的語言互動」到「Agent 的自主工具互動」
- Agent 自己決定流程，而不是我們規定固定方法論

### Philosophy
> **「Copilot 內部觸碰不到，無論外層做什麼最終都是 Prompt 進去」**
>
> 解決方案：給 Agent 工具，讓它自己探索出創意

| 傳統 | Agent 驅動 |
|------|------------|
| 我們設計流程 | Agent 自己設計流程 |
| 固定的方法論 | 動態的探索策略 |
| 輸出無法驗證 | 工具可以驗證 |
| 一次性生成 | 迭代式探索 |

## [0.3.0] - 2025-12-16

### Added
- 🧠 **ThinkingEngine - 統一思考引擎**
  - `src/cgu/thinking/engine.py` - 核心思考引擎，支援 4 種模式
  - `src/cgu/thinking/facade.py` - 簡化 API（`think`, `quick_think`, `deep_think`, `spark_think`）
  - 自動模式選擇：根據主題複雜度智能選擇 Simple/Deep/Spark/Hybrid

- 🤖 **Multi-Agent 系統**
  - `src/cgu/agents/base.py` - Agent 基類與人格系統（Explorer/Critic/Wildcard）
  - `src/cgu/agents/explorer.py` - 探索者 Agent（廣度優先）
  - `src/cgu/agents/critic.py` - 批判者 Agent（深度分析）
  - `src/cgu/agents/wildcard.py` - 狂想者 Agent（跨界創新）
  - `src/cgu/agents/orchestrator.py` - Agent 協調者（並發管理）
  - `src/cgu/agents/spark.py` - 火花引擎（概念碰撞）

- ⚡ **新 MCP 工具**
  - `deep_think` - 統一思考入口，支援 depth 參數
  - `multi_agent_brainstorm` - Multi-Agent 並發腦力激盪
  - `spark_collision_deep` - 深度概念碰撞

- 📋 **LangGraph 1.0 Functional API**
  - `src/cgu/graph/builder_functional.py` - 使用 `@entrypoint` 和 `@task` 裝飾器
  - 支援 Python 3.12 PEP 695 Type Alias 語法

### Changed
- `src/cgu/server.py` - 整合 ThinkingEngine，新增 `CGU_THINKING_DEPTH` 環境變數
- `src/cgu/llm/__init__.py` - 新增 `get_llm_client()` 便捷函數

### Fixed
- **SparkEngine**: `collect_and_collide()` 改為同步方法（解決 async/sync 錯配）
- **AgentIdea**: Pydantic model 使用 `model_config` 替代 `class Config`
- **Personality 處理**: 新增 `_get_personality()` 輔助函數處理 string/enum 轉換
- **CreativeSession**: 修正 `to_dict()` 使用正確的屬性名稱

## [0.2.1] - 2025-12-16

### Added
- 🔄 **思考引擎切換**
  - 新增 `CGU_LLM_PROVIDER` 環境變數
  - 支援 `ollama` 模式（本地 LLM 思考）
  - 支援 `copilot` 模式（框架模式，讓 Copilot 填充）
- 📋 **VS Code MCP 配置**
  - `.vscode/mcp.json` - 雙 Server 配置（cgu / cgu-copilot）
  - `mcp-config/` - Claude Desktop 與 VS Code 配置範例
- 🧪 **測試檔案**
  - `tests/test_quick.py` - LangGraph Agent 快速測試

### Changed
- `src/cgu/server.py` - 所有 MCP 工具整合真實 LLM
- `src/cgu/llm/prompts.py` - 修正 PROMPT_EVALUATE 參數名稱
- `.env.example` - 新增 `CGU_LLM_PROVIDER` 選項說明

### Fixed
- FastMCP 初始化移除不支援的 `version` 參數

## [0.2.0] - 2025-12-15

### Added
- 🧠 **CGU 核心功能**
  - `src/cgu/core/thinking.py` - 快思慢想架構（9 種思考模式）
  - `src/cgu/core/creativity.py` - 創意層級與 15 種創意方法
- 🔌 **MCP Server**
  - `src/cgu/server.py` - FastMCP Server（6 個工具 + 2 個資源）
- 🤖 **LangGraph Agent**
  - `src/cgu/graph/state.py` - Agent 狀態定義
  - `src/cgu/graph/nodes.py` - 9 個思考節點
  - `src/cgu/graph/builder.py` - 圖建構器
- 🏠 **Ollama LLM 整合**
  - `src/cgu/llm/client.py` - Ollama + Instructor 客戶端
  - `src/cgu/llm/schemas.py` - Pydantic 結構化輸出
  - `src/cgu/llm/prompts.py` - 提示詞模板
- 💻 **CLI 介面**
  - `src/cgu/cli.py` - 6 個命令（generate, spark, expand, apply, methods, recommend）

### Changed
- 專案從模板轉型為 CGU 專案
- `pyproject.toml` 更新依賴：langgraph, mcp, instructor, ollama

## [0.1.0] - 2025-12-15

### Added
- 初始化專案結構
- 新增 Claude Skills 支援
  - `git-doc-updater` - Git 提交前自動更新文檔技能
- 新增 Memory Bank 系統
  - `activeContext.md` - 當前工作焦點
  - `productContext.md` - 專案上下文
  - `progress.md` - 進度追蹤
  - `decisionLog.md` - 決策記錄
  - `projectBrief.md` - 專案簡介
  - `systemPatterns.md` - 系統模式
  - `architect.md` - 架構文檔
- 新增 VS Code 設定
  - 啟用 Claude Skills
  - 啟用 Agent 模式
  - 啟用自定義指令檔案
