# Roadmap

CGU (Creativity Generation Unit) 專案發展路線圖。

## 已完成 ✅

### v0.1.0 (2025-12-15)
- [x] 專案初始化
- [x] Memory Bank 系統建立
- [x] Claude Skills 基礎架構
- [x] Git 文檔自動更新 Skill

### v0.2.0 (2025-12-16)
- [x] CGU 核心架構（快思慢想）
- [x] 16 種創意方法實作
- [x] LangGraph Agent 整合
- [x] vLLM → Ollama 遷移
- [x] MCP Server 完整實作
- [x] 真實 LLM 整合（qwen2.5:3b）
- [x] 思考引擎切換（Ollama/Copilot 模式）
- [x] VS Code MCP 配置

### v0.3.0 (2025-12-16) 
- [x] 🧠 **ThinkingEngine** - 統一思考引擎（Simple/Deep/Spark/Hybrid）
- [x] 🤖 **Multi-Agent 系統** - Explorer/Critic/Wildcard 三種人格
- [x] ⚡ **Spark Engine** - 概念碰撞火花引擎
- [x] 🔗 **Ollama + Copilot 整合** - 簡單/深度模式兼容
- [x] 📋 **LangGraph 1.0 Functional API** - @entrypoint/@task 裝飾器
- [x] 🔧 **新 MCP 工具** - deep_think, multi_agent_brainstorm, spark_collision_deep

### v0.4.0 (2026-01-06) ⭐ NEW - Agent-Driven Creativity
- [x] 🧠 **v2 核心引擎** - 從「模擬創意」到「實現創意機制」
  - AnalogyEngine - 跨域類比搜尋器
  - GraphTraversalEngine - 概念圖譜遍歷
  - AdversarialEngine - 對抗式進化
  - CreativityCore - 統一創意引擎
- [x] 🛠️ **v3 Agent-Driven Tools** - Agent 自主創意工具
  - ConceptExplorer - 概念搜尋器
  - ConnectionFinder - 連結發現器
  - NoveltyChecker - 新穎度驗證器
  - IdeaEvolver - 想法演化器
  - CreativityToolbox - 統一工具箱
- [x] 💡 **核心轉變** - 從「語言互動」到「Agent 工具互動」

## 進行中 🚧

### v0.5.0 - Agent 自主探索強化 (Agent Autonomy Enhancement)

> 💡 **設計理念**：擴充 Agent 工具，整合外部知識源，
> 讓 Agent 能更自主地探索創意空間。

#### Phase 1: 工具擴充
- [ ] 🔌 **MCP Tool 註冊** - 將 v3 Tools 註冊為 MCP Tools
- [ ] 🌐 **外部知識源整合** - ConceptNet, Wikidata API
- [ ] 📊 **Embedding 語義距離** - 真實的跨域相似度計算

#### Phase 2: Agent 智能
- [ ] 🤖 **探索策略學習** - Agent 學習哪些工具組合有效
- [ ] 📝 **探索歷史分析** - 從過去探索中學習
- [ ] 🎯 **目標導向探索** - 根據目標自動調整策略

#### Phase 3: 評估與回饋
- [ ] ✅ **品質評估系統** - NUS 模型（Novelty × Usefulness × Surprise）
- [ ] 🔄 **自動迭代** - 根據評估結果自動演化

## 計劃中 📋

### 短期目標 (v0.5.0) - 遊戲化與評估
- [ ] 🎮 **遊戲化介面** - 創意積分、成就系統
- [ ] 📊 **創意品質評估** - 自動評分與改進建議
- [ ] 🔄 **動態方法生成** - 根據主題自動組合方法
- [ ] 💾 **創意歷史記錄** - 保存與回顧過往發想

### 中期目標 (v0.6.0)
- [ ] 🌐 **知識圖譜整合** - 結構化聯想路徑
- [ ] 🎲 **隨機挑戰模式** - 強制跳出舒適圈
- [ ] 📈 **思維成長樹** - 視覺化創意擴展路徑
- [ ] 🔌 **多 LLM 支援** - OpenAI/Anthropic 切換

### 長期目標 (v1.0.0)
- [ ] 🚀 **GPU 加速** - 本地高效能推理
- [ ] 🛠️ **自訂方法編輯器** - 使用者自建創意方法
- [ ] 🤝 **協作模式** - 多人即時腦力激盪
- [ ] 📦 **發布至 MCP Registry** - 讓更多人使用

## 版本里程碑

```
v0.4.0 ──────────────────────────────► 現在位置 ⭐
   │   Agent-Driven Creativity
   │   - v2 核心引擎 (Analogy/Graph/Adversarial)
   │   - v3 Agent Tools (5 個創意工具)
   │   - 核心轉變: 語言 → 工具互動
   │
   ├── v0.5.0 Agent 自主探索強化 (2026-Q1)
   │       ├── MCP Tool 註冊
   │       ├── 外部知識源整合
   │       └── 品質評估系統
   │
   ├── v0.6.0 遊戲化 + 視覺化 (2026-Q2)
   │
   └── v1.0.0 完整版發布 (2026-Q3)
```
