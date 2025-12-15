# Product Context

> 📌 此檔案描述專案的技術架構和產品定位，專案初期建立後較少更新。

## 📋 專案概述

**專案名稱**：Creativity Generation Unit (CGU)

**一句話描述**：基於 MCP 的 Agent-to-Agent 創意發想服務，採用快思慢想架構。

**目標用戶**：需要 AI 輔助創意發想的開發者和創意工作者

## 🏗️ 架構

```
CGU MCP Server
├── 核心概念 (Core)
│   ├── 快思慢想 (Thinking Fast/Slow)
│   └── 創意層級 (Creativity Levels)
├── 創意方法 (Methods)
│   └── 15 種人類創意方法論
├── Agent 編排 (LangGraph)
│   └── 快步驟 → 快步驟 → 慢步驟 → ...
└── 推理引擎 (vLLM + Qwen 4B)
```

### 快思慢想策略

```
System 1 (Fast): REACT → ASSOCIATE → PATTERN_MATCH
System 2 (Slow): ANALYZE → SYNTHESIZE → EVALUATE
Creative:        DIVERGE → CONVERGE → TRANSFORM
```

## ✨ 核心功能

- 🎨 3 層創意層級（組合、探索、變革）
- 🧠 15 種結構化創意方法
- ⚡ 快思慢想 Agent 編排
- 🔧 MCP 工具介面
- 🔍 Web Search 整合

## 🔧 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.11+ |
| MCP SDK | FastMCP |
| Agent 編排 | LangGraph |
| 本地推理 | vLLM + Qwen 4B |
| 結構化輸出 | Pydantic + Instructor |
| Web 搜尋 | DuckDuckGo Search |
| 套件管理 | uv (優先) |

## 📦 依賴

### 核心依賴
- mcp[cli] - MCP SDK
- langgraph, langchain - Agent 編排
- vllm - 本地推理
- pydantic, instructor - 結構化輸出
- duckduckgo-search - Web 搜尋

### 開發依賴
- pytest, pytest-asyncio, pytest-cov
- ruff, mypy

---
*Last updated: 2025-12-15*