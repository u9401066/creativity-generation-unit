# CGU - Creativity Generation Unit

> 🧠 MCP-based Agent-to-Agent 創意發想服務，採用「快思慢想」架構

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/modelcontextprotocol)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 特色

- 🚀 **快思慢想架構** - 多個快速小步驟 + 慢速大步驟組合
- 🎨 **16 種創意方法** - SCAMPER、六頂思考帽、心智圖、九宮格等
- 🔌 **MCP 協議** - 標準化的 Agent-to-Agent 通訊
- 🤖 **LangGraph 編排** - 靈活的思考流程控制
- 🏠 **本地推理** - Ollama + Qwen 支援，隱私優先
- 🔄 **思考引擎切換** - Ollama 本地思考 / Copilot 框架模式

## 🏗️ 架構

```
┌─────────────────────────────────────────────────────────┐
│                    CGU Architecture                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │  MCP    │───▶│ LangGraph│───▶│  Ollama │             │
│  │ Server  │    │  Agent   │    │   LLM   │             │
│  └─────────┘    └─────────┘    └─────────┘             │
│       │              │                                   │
│       ▼              ▼                                   │
│  ┌─────────────────────────────────────┐               │
│  │         Creativity Methods          │               │
│  │  SCAMPER │ 六頂帽 │ 九宮格 │ ...    │               │
│  └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## 📦 安裝

```bash
# 使用 uv（推薦）
uv sync

# 或使用 pip
pip install -e .
```

## 🚀 快速開始

### CLI 使用

```bash
# 生成創意點子
cgu generate "如何提升團隊創造力"

# 概念碰撞
cgu spark "人工智慧" "傳統手工藝"

# 使用特定方法
cgu apply scamper "智慧手錶"

# 查看可用方法
cgu methods
```

### MCP Server

```bash
# 啟動 MCP Server
cgu-server
```

### 程式碼使用

```python
from cgu.graph import run_cgu
from cgu.core import CreativityLevel

# 運行創意生成
result = await run_cgu(
    topic="未來的教育方式",
    creativity_level=CreativityLevel.L2_EXPLORATORY,
    target_count=5,
)

for idea in result["final_ideas"]:
    print(f"💡 {idea.content}")
```

## 🎯 創意層級

| 層級 | 名稱 | 關聯性 | 說明 |
|------|------|--------|------|
| L1 | 組合創意 | 0.7-1.0 | 已知元素的新組合 |
| L2 | 探索創意 | 0.3-0.7 | 在既有規則內探索邊界 |
| L3 | 變革創意 | 0.0-0.3 | 打破規則，創造新範式 |

## 🧰 創意方法

### 發散類
- 🧠 心智圖 (Mind Map)
- 💡 腦力激盪 (Brainstorm)
- 🔄 SCAMPER 檢核表
- 🎲 隨機輸入法

### 結構類
- 📊 曼陀羅九宮格
- 🔬 形態分析法
- ❓ 5W2H
- 🐟 魚骨圖

### 觀點類
- 🎩 六頂思考帽
- 👥 角色扮演法
- 🔄 逆向思考法

## ⚙️ 配置

### 環境變數

```bash
# .env 配置
CGU_USE_LLM=true                          # 啟用 LLM
CGU_LLM_PROVIDER=ollama                   # 思考引擎：ollama / passthrough / copilot
OLLAMA_BASE_URL=http://localhost:11434/v1  # Ollama 地址
OLLAMA_MODEL=qwen2.5:3b                    # 模型名稱
```

### 思考引擎模式

| 模式 | 說明 |
|------|------|
| `ollama` | 使用本地 Ollama 模型思考（預設） |
| `passthrough` | **推薦用於 OpenClaw** — 只提供方法論框架，讓 Agent（Claude/GPT）自行思考填充 |
| `copilot` | *(已棄用，等同 passthrough)* |

### 🤖 OpenClaw 配置

在 OpenClaw 裡，你的 agent 本身就是 LLM，不需要再用一個弱的 Ollama 模型。
使用 `passthrough` 模式，CGU 會輸出完整的方法論框架（SCAMPER 7 維度、六頂帽 6 角度、逆向思考引導等），讓你的 agent 用自己的推理能力填充。

```yaml
# OpenClaw config.yaml
mcp:
  servers:
    cgu:
      url: "http://localhost:8818/mcp"
```

或 stdio 模式：

```yaml
mcp:
  servers:
    cgu:
      command: "uv"
      args: ["--directory", "/path/to/creativity-generation-unit", "run", "cgu-server"]
      env:
        CGU_LLM_PROVIDER: "passthrough"
```

### Agent-to-Agent 腦力激盪

使用 `brainstorm_protocol` 產生結構化的雙 Agent 討論腳本：

```
Agent A（領域專家）+ Agent B（架構師）
    │
    ▼
brainstorm_protocol(topic="...", method="six_hats")
    │
    ▼
Phase 1: Diverge 發散 → 各自從專業角度發想
Phase 2: Collide 碰撞 → 互相挑戰、交叉激盪
Phase 3: Converge 收斂 → 共同篩選最佳方案
    │
    ▼
evaluate_brainstorm_ideas(ideas=[...])
    │
    ▼
四維度評分：可行性 / 新穎度 / 影響力 / 成本
```

### VS Code MCP 配置

將 `.vscode/mcp.json` 放在專案根目錄：

```json
{
  "servers": {
    "cgu": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "cgu-server"],
      "env": {
        "CGU_USE_LLM": "true",
        "CGU_LLM_PROVIDER": "ollama"
      }
    },
    "cgu-copilot": {
      "type": "stdio", 
      "command": "uv",
      "args": ["--directory", "${workspaceFolder}", "run", "cgu-server"],
      "env": {
        "CGU_USE_LLM": "true",
        "CGU_LLM_PROVIDER": "passthrough"
      }
    }
  }
}
```

在 VS Code 中使用 `MCP: List Servers` 選擇啟動哪個模式。

## 🔧 開發

```bash
# 安裝開發依賴
uv sync --all-extras

# 運行測試
pytest

# 程式碼檢查
ruff check src/
```

## 📚 文檔

- [創意生成單元概念](docs/creativity-generation-unit.md)
- [API 參考](docs/api.md)
- [MCP 工具說明](docs/mcp-tools.md)

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE)

---

<p align="center">
  Made with 💡 by CGU Team
</p>
