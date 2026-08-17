# Progress (Updated: 2026-08-17)

## Done

- 保留 v2 核心引擎與 v3 Agent-Driven Creativity Tools。
- 全面遷移至官方 MCP Python SDK 2：`mcp>=2,<3`、`MCPServer`、SDK 2 schema/result 欄位。
- 24 個 tools 全部啟用 structured output。
- 新增 direct client、stdio subprocess、wheel-install MCP smoke tests。
- 把需要 live Ollama 的腳本式測試改為明確 opt-in integration test。
- 修正 LangGraph 1.x Functional API：entrypoint 改用單一 serializable input object，並加回歸測試。
- 修正既有型別與 lint 問題；ruff、mypy、103 tests 全綠。
- CI 改為 `master` 上 Python 3.11/3.12 的真實 hard gates，不再吞掉錯誤。

## Doing

- 準備 0.6.0 segmented commit、push、tag 與 release。

## Next

- 發布 PyPI 0.6.0 並讓上層 integration lock 固定版本。
- 外部知識源、語義距離與 NUS 品質評估仍列為後續產品演進。
