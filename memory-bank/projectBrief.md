# Project Brief

> 📌 此檔案描述專案的高層級目標和範圍，建立後很少更改。
> 🔄 2026-10-02：原內容為專案模板殘留，依實際程式碼改寫為 CGU 定位。

## 🎯 專案目的

CGU（Creativity Generation Unit）是以 MCP 提供的創意發想服務，讓 AI Agent（Copilot、Claude、OpenClaw 等）呼叫結構化創意方法、概念碰撞、碎片化原料（Spark-Soup）與雙 Agent 腦力激盪流程。

核心主張：
- **創意 = 連結**：不需完整世界模型，局部資訊加上足夠的連結能力即可產生創意（Koestler Bisociation）。
- **快思慢想**：System 1 快速聯想 × System 2 分析評估 × 發散 / 收斂。
- **模型民主化**：小模型（Ollama qwen2.5:3b）或呼叫端大模型（passthrough）皆可使用。
- **從 Prompt 到工具**（v3）：不規定流程，提供 Agent 可自主組合的創意工具。

## 👥 目標用戶

- 直接呼叫者：需要「創意副駕」的 AI Agent（Agent-to-Agent）
- 最終受益者：透過 VS Code Copilot / Claude Desktop / OpenClaw 使用這些 Agent 的開發者、研究者與創意工作者
- 上層整合：med-paper-assistant（以 integration lock 固定 CGU 版本）

## 🏆 成功指標

- [x] 24 個 MCP tools 以 SDK 2 structured output 穩定運作（103 tests 綠燈）
- [ ] 創意品質可被量測（NUS：Novelty × Usefulness × Surprise），而非啟發式假分數
- [ ] 以外部知識源（ConceptNet / Wikidata / embedding）取代硬編碼小型知識庫
- [ ] Agent 產出的創意能以人類可吸收、可回饋的形式呈現

## 🚫 範圍限制

- CGU 本身不保證創意品質；passthrough 模式下真正的生成者是呼叫端 LLM
- 只提供發散、碰撞、收斂的框架與素材，不做最終決策
- 不包含生產環境部署配置

## 📝 備註

- 規則層（CONSTITUTION / bylaws / skills / Memory Bank）源自專案模板，仍然適用
- 實作成熟度盤點見 `architect.md` 的「CGU 實際系統架構與成熟度盤點」

---
*Created: 2025-12-15 | Rewritten: 2026-10-02*
