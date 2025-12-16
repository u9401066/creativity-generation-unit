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

### v0.3.0 (2025-12-16) ⭐ NEW
- [x] 🧠 **ThinkingEngine** - 統一思考引擎（Simple/Deep/Spark/Hybrid）
- [x] 🤖 **Multi-Agent 系統** - Explorer/Critic/Wildcard 三種人格
- [x] ⚡ **Spark Engine** - 概念碰撞火花引擎
- [x] 🔗 **Ollama + Copilot 整合** - 簡單/深度模式兼容
- [x] 📋 **LangGraph 1.0 Functional API** - @entrypoint/@task 裝飾器
- [x] 🔧 **新 MCP 工具** - deep_think, multi_agent_brainstorm, spark_collision_deep

## 進行中 🚧

### v0.4.0 - 完整創意流程 (Creativity Pipeline)

> 💡 **設計理念**：透過「多輪迭代 × 複合方法 × 智慧彙整」三階段，
> 實現從發散到收斂的完整創意工作流。

#### Phase 1: 發散階段 (Diverge)
- [ ] 🔁 **多輪迭代發想 (Iterative Ideation)**
  - `CreativitySession` 類別管理多輪狀態
  - 每輪結果作為下輪的「種子」輸入
  - 累積式 prompt：基於已有創意深化延伸
  - 支援 3-5 輪自動迭代或手動控制

- [ ] 🧩 **複合創意組合 (Compound Pipeline)**
  - `CreativityPipeline` 串接多個方法節點
  - 預設管線：SCAMPER → 六帽思考 → 概念碰撞 → 篩選
  - 支援自訂管線配置 (YAML/JSON)
  - 方法間自動傳遞上下文

#### Phase 2: 收斂階段 (Converge)
- [ ] 🎯 **創意篩選器 (Idea Filter)**
  - 多維度自動評分：新穎性 / 可行性 / 影響力
  - 去重合併相似創意（語意相似度）
  - Top-N 智慧排序輸出

#### Phase 3: 彙整階段 (Synthesize)
- [ ] 📝 **智慧彙整報告 (Smart Summary)**
  - LLM 生成結構化報告
  - 輸出格式：Markdown / JSON / Mermaid 圖
  - 包含：摘要、分類、關聯圖、行動建議

#### 技術實作
- [ ] 完整測試覆蓋率 (pytest)
- [ ] 錯誤處理強化 (graceful fallback)
- [ ] 新 MCP 工具：`run_pipeline`, `iterate_ideas`, `summarize_session`

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
v0.3.0 ──────────────────────────────────► 現在位置 ⭐
   │
   ├── v0.4.0 完整創意流程 (2025-12)
   │       ├── Phase 1: 發散 (多輪迭代 + 複合管線)
   │       ├── Phase 2: 收斂 (篩選 + 評分)
   │       └── Phase 3: 彙整 (報告 + 圖譜)
   │
   ├── v0.5.0 遊戲化 + 評估 (2025-Q1)
   │
   ├── v0.6.0 知識圖譜 + 視覺化 (2025-Q2)
   │
   └── v1.0.0 完整版發布 (2025-Q3)
```
