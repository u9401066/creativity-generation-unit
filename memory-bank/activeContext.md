# Active Context

## 當前焦點

- CGU 0.6.0 已完成官方 MCP Python SDK 2 遷移，等待提交、推送、標記與發布。
- 24 個 MCP tools 使用 `MCPServer` 與 structured output；SDK 1 `FastMCP` 已移除。

## 已驗證

- Python 3.11 與 3.12 相容。
- ruff、mypy、103 個非外部整合測試通過；2 個 live LLM tests 預設排除。
- SDK 2 direct client 與 subprocess stdio smoke 通過，protocol 為 `2026-07-28`。
- sdist/wheel 隔離安裝後可列出並呼叫全部 24 tools。

## 待辦

- [ ] 提交並推送 `master`。
- [ ] 建立 `v0.6.0` tag / GitHub Release，確認 PyPI 發布流程。
- [ ] 在 med-paper-assistant 的 integration lock 中固定正式發布版本。

## 更新時間

2026-08-17
