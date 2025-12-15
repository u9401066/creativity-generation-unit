# Creativity Generation Unit (CGU)

> 🎨 **MCP-based Agent-to-Agent Creative Idea Generator**
> 
> 基於快思慢想 (Thinking, Fast and Slow) 的創意發想服務

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

🌐 [繁體中文](README.zh-TW.md)

## 💡 Core Insight

> **"All models are wrong, but some are useful!"** — George Box

**Key Discovery: Creativity can emerge from partial information!**

- Humans don't need complete world knowledge to generate creative ideas
- Creativity requires **connection ability**, not information volume
- Even the simplest models can provide unique creative perspectives

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               Creativity Generation Unit (CGU)                │
│                        MCP Server                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              🧠 Thinking Engine (v0.3.0)              │   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│   │  │ Simple  │  │  Deep   │  │  Spark  │  │ Hybrid │ │   │
│   │  │(Copilot)│  │(Multi-  │  │(Concept │  │(Fast+  │ │   │
│   │  │         │  │ Agent)  │  │Collision│  │ Slow)  │ │   │
│   │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│   └──────────────────────┬──────────────────────────────┘   │
│                          │                                   │
│   ┌──────────────────────┴──────────────────────────────┐   │
│   │              Multi-Agent Orchestrator                │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│   │   │ Explorer │  │  Critic  │  │ Wildcard │         │   │
│   │   │  Agent   │  │  Agent   │  │  Agent   │         │   │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘         │   │
│   │        │             │             │                │   │
│   │        └─────────────┼─────────────┘                │   │
│   │                      ▼                              │   │
│   │              ⚡ Spark Engine                        │   │
│   │           (Concept Collision)                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   Backend: Ollama (Local) / Copilot (Framework Mode)         │
└──────────────────────────────────────────────────────────────┘
```

## 🧠 Thinking, Fast and Slow

Based on Daniel Kahneman's theory:

| System | Speed | Characteristics | CGU Implementation |
|--------|-------|-----------------|-------------------|
| **System 1** | Fast ⚡ | Intuitive, automatic | `REACT`, `ASSOCIATE`, `PATTERN_MATCH` |
| **System 2** | Slow 🐢 | Deliberate, analytical | `ANALYZE`, `SYNTHESIZE`, `EVALUATE` |
| **Creative** | Mixed 🎨 | Breaking boundaries | `DIVERGE`, `CONVERGE`, `TRANSFORM` |

**Core Strategy**: Multiple fast steps + occasional slow steps = Efficient creativity

## 🎯 Creativity Levels

```
Level 1: Combinational (0.7-1.0 association)
└─ New combinations of known elements

Level 2: Exploratory (0.3-0.7 association)
└─ Exploring boundaries within existing rules

Level 3: Transformational (0.0-0.3 association)
└─ Breaking rules, creating new paradigms
```

## 📚 15 Human Creativity Methods

CGU implements structured creativity methods:

| Category | Methods |
|----------|---------|
| **Divergent** | Mind Map, Brainstorm, SCAMPER, Random Input |
| **Structural** | 9-Grid Mandala, Morphological Analysis, 5W2H, Fishbone |
| **Perspective** | Six Thinking Hats, Reverse Thinking, Analogy |
| **Process** | Double Diamond, Design Sprint, KJ Method, World Café |
| **Systematic** | TRIZ 40 Principles |

## 🛠️ Tech Stack

- **MCP SDK**: FastMCP for tool serving
- **Agent Orchestration**: LangGraph
- **Local Inference**: vLLM + Qwen 4B
- **Structured Output**: Pydantic + Instructor
- **Web Search**: DuckDuckGo Search

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/creativity-generation-unit.git
cd creativity-generation-unit

# Setup environment (uv recommended)
uv venv
uv sync --all-extras

# Run MCP server
cgu-server

# Or use CLI
cgu generate "How to improve remote work productivity?"
```

## 📁 Project Structure

```
creativity-generation-unit/
├── src/cgu/
│   ├── core/           # Core concepts
│   │   ├── thinking.py # Fast/Slow thinking
│   │   └── creativity.py # Methods & levels
│   ├── methods/        # Method implementations
│   ├── agents/         # Multi-Agent system (v0.3.0)
│   │   ├── base.py     # Agent base classes
│   │   ├── explorer.py # Explorer Agent
│   │   ├── critic.py   # Critic Agent
│   │   ├── wildcard.py # Wildcard Agent
│   │   ├── orchestrator.py # Agent Orchestrator
│   │   └── spark.py    # Spark Engine
│   ├── thinking/       # Unified Thinking Engine (v0.3.0)
│   │   ├── engine.py   # ThinkingEngine
│   │   └── facade.py   # Simple API
│   ├── graph/          # LangGraph definitions
│   ├── llm/            # LLM backends (Ollama/Copilot)
│   └── server.py       # MCP Server
├── docs/               # Documentation
├── tests/              # Test suite
├── memory-bank/        # Project memory
└── pyproject.toml      # Dependencies
```

## 🔧 MCP Tools

```typescript
// Core Tools
generateIdeas(topic, creativityLevel, count)
sparkCollision(conceptA, conceptB)
associativeExpansion(seed, direction, depth)
applyMethod(method, input)

// Deep Thinking Tools (v0.3.0 新增)
deepThink(topic, depth, mode)          // 統一思考入口
multiAgentBrainstorm(topic, agents)    // Multi-Agent 並發
sparkCollisionDeep(conceptA, conceptB) // 深度概念碰撞
```

## 🎮 Thinking Modes (v0.3.0)

| Mode | Description | Use Case |
|------|-------------|----------|
| **Simple** | Single LLM call | Quick ideas, simple topics |
| **Deep** | Multi-Agent parallel | Complex problems, multi-perspective |
| **Spark** | Concept collision | Cross-domain innovation |
| **Hybrid** | Fast + Slow combined | Comprehensive exploration |

```python
# Example: Deep thinking with Multi-Agent
from cgu.thinking import deep_think

result = await deep_think("未來教育模式", agents=3, steps=5)
print(result["best_spark"])  # Best inspiration spark
```

## 🌟 Design Principles

1. **Model Democracy** - Even simple models have unique perspectives
2. **Partial is Enough** - No need for complete world model
3. **Connection > Knowledge** - Creativity is about linking
4. **Errors are Useful** - Wrong connections may be innovations

## 📋 Documentation

- [CGU Concept](docs/creativity-generation-unit.md) - Core concepts & methods
- [Constitution](CONSTITUTION.md) - Project principles
- [Architecture](ARCHITECTURE.md) - System design
- [Changelog](CHANGELOG.md) - Version history

## 📄 License

[Apache License 2.0](LICENSE)

---

*"Creativity is just connecting things."* — Steve Jobs
