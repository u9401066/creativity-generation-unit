# Changelog

所有重要變更都會記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [Unreleased]

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
