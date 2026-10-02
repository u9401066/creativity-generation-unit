# Product Context

> 📌 產品定位與技術棧。v0.8.0（2026-10-03）起改寫；0.6 以前的描述（LangGraph、24 tools、Spark-Soup）已移除。

## 📋 專案概述

**專案名稱**：Creativity Generation Unit (CGU)

**一句話描述**：給 LLM agent 用的「誠實創意鷹架」——MCP server（SDK 2）加上可攜的 Agent Plugin（Agent Plugins 1.0）。

**目標用戶**：用 Copilot／Codex／其他 MCP 客戶端做創意協作的研究者、醫療商品開發者、行政流程改造者。

## 🧭 定位：CGU 補的是 LLM 做不到的部分

| LLM 弱項 | CGU 提供 |
|---|---|
| 看不見自己問題裡的隱性假設 | Frame 物件＋11 個哲學算子（受限元素須同意） |
| 難以離開典型答案 | 反典型發散（先寫典型答案集，再往外生成） |
| 「平行」點子其實不獨立 | fan-out 工單（獨立 context） |
| 不知道點子是否新 | 附參照集的測量；沒量就是 `null` |
| 評審有偏誤 | 盲評成對比較、AB／BA、Wilson 區間 |
| 長流程記不住 | SQLite 狀態與譜系 |
| 不誠實交代沒做到的事 | 每個結果帶 `Provenance` |

預設 `CGU_PROVIDER=passthrough`：**CGU 不呼叫 LLM**，只回傳工單；生成與判斷由呼叫端模型做。

## 🏗️ 架構

```
plugins/cgu          可攜 plugin：skills ＋ mcp.json ＋（Copilot）agents
src/cgu
├── domain           純規則（Measurement、Frame、算子、doubt、fence、judge）
├── application      ports ＋ services
├── infrastructure   SQLite、embedding、檢索、選用 LLM、Settings
└── interfaces       mcp（10 tools、5 resources、4 prompts）、cli
evals                隔離式 Copilot CLI 效果實驗
```

詳見 [`docs/architecture.md`](../docs/architecture.md)。

## ✨ 核心功能

- 10 個工具：`cgu_status`、`cgu_session`、`cgu_frame`、`cgu_material`、`cgu_diverge`、`cgu_ideas`、`cgu_judge`、`cgu_evolve`、`cgu_feedback`、`cgu_question_gate`
- 4 個 skills：`creative-ideation`、`frame-audit`、`maieutic-session`、`idea-triage`
- 4 個 Copilot agents：`creative-facilitator`、`frame-auditor`、`independent-ideator`、`adversarial-critic`
- 示範領域：研究創意、醫療商品開發、行政流程轉變

## 🔧 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.11+ |
| MCP SDK | 官方 MCP Python SDK 2（`mcp>=2,<3`，`MCPServer`） |
| 資料驗證 | Pydantic 2.12+ |
| 持久化 | SQLite（WAL） |
| Embedding | n-gram 雜湊後備（`semantic=false`）；可選 Ollama `nomic-embed-text` |
| 檢索 | httpx（Wikipedia；`CGU_NETWORK=off` 可關閉） |
| 數值 | numpy |
| 套件管理 | uv |
| 品質 | pytest、ruff、mypy、jsonschema（plugin schema 驗證） |

已移除：langgraph、langchain*、openai、instructor、duckduckgo-search、rich、python-dotenv。

## 🚢 發行

- 目前：`uvx --from git+https://github.com/u9401066/creativity-generation-unit@master cgu-server`（尚未上 PyPI）。
- Marketplace：Copilot `.github/plugin/marketplace.json`；Codex `.agents/plugins/marketplace.json`。
- 順序（D-19）：git tag → PyPI → MCP Registry。

---
*Last updated: 2026-10-03*
