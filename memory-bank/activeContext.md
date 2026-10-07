# Active Context

## 當前焦點

- **2026-10-07 v0.9.0 已發布**：README（EN／zh-TW）、架構、CHANGELOG、ROADMAP、設定範例與 plugin 已同步；安裝及 hook fallback 固定 `v0.9.0`。Release commit `bb32a8f42123223a1cc54a41f7baed93b0c90d50` 已推送 `master`，annotated tag `v0.9.0` 指向同一提交；[GitHub Release](https://github.com/u9401066/creativity-generation-unit/releases/tag/v0.9.0) 含 wheel、sdist、SHA256SUMS。579 tests、ruff／mypy 通過；[GitHub CI](https://github.com/u9401066/creativity-generation-unit/actions/runs/37620612551) 的 Python 3.11／3.12 全綠。獨立 Python 3.11＋MCP 2.3.0 wheel stdio／doctor／素材生命週期，以及遠端 tag 的 `uvx ... cgu doctor --json` 通過。sdist 限定 CGU 檔案並排除本機快取、擴充套件資料與 evals/runs。依 D-19，PyPI／MCP Registry 留待後續。

- **2026-10-07 接續 Copilot，已完成**：MCP 被動提供工具，推理由呼叫端 agent 的模型負責。Hook 主動累積使用者提問，agent 整理成可追溯的創意素材；資料採 `~/.cgu`。本地或雲端模型皆可作為 agent，CGU 不另要求推理模型。預設 embedding 改 `ngram`，doctor 亦不探測模型；新增 `organize`／`distill`／`materials` 與 migration 3。門檻預設 20 筆，在 agent 下次使用時處理一批；無 agent 時只累積。管理機制保留；本輪未在使用者個人設定安裝或啟用 hook。

- **2026-10-03：v0.8.0（MCP SDK 2 不相容重寫）已完成並推送 `master`**；進行中的是效果實驗的產出與報告（`evals/reports/`），以及把實驗結論據實回寫 README「證據」。
- 專案作者與聯絡人：**u9401066 ＜u9401066@gap.kmu.edu.tw＞**（先前文件中的誤植已更正）。
- 使用者指示（本輪）：MCP 直接改 SDK 2.0+、不相容、設計較佳架構；完整修正後更新文件＋Memory Bank＋分段 git＋push；**實際安裝 plugin 測試效果**，預設用 Sonnet／luna 等級模型（SOTA 模型不需要這些輔助）；創意討論不需倫理審查（以研究創意、醫療商品開發、行政流程轉變為例）；可整合其他工具。

## 架構摘要（詳見 `docs/architecture.md`）

- `src/cgu/{domain,application,infrastructure,interfaces}`；依賴規則由測試強制。
- 11 個工具：`cgu_status`、`cgu_session`、`cgu_frame`、`cgu_material`、`cgu_diverge`、`cgu_ideas`、`cgu_judge`、`cgu_evolve`、`cgu_feedback`、`cgu_question_gate`、`cgu_inquiry`；另有 5 resources、4 prompts。
- 預設 passthrough：CGU 不呼叫 LLM，回傳工單；數值只存在 `Measurement`；未量測為 `null`；每個結果帶 `Provenance`。
- Plugin：`plugins/cgu`（Agent Plugins 1.0）——5 skills（含 inquiry-mining）、4 Copilot agents、`mcp.json`；marketplace 在 `.github/plugin/` 與 `.agents/plugins/`。

## 本輪實測得到的事實

- `mcp` 2.0.0：`Elicit` 是 `Annotated[ElicitationResult[Form], Resolve(fn)]`；`ctx.log` 已棄用；無 elicitation 能力時 resolver 丟 `MCPError`；客戶端固定 `"2026-07-28"` 模式時 `client.instructions` 為 `None`。
- Copilot CLI 1.0.91：直接讀 plugin 根目錄 `mcp.json`（不需 `.mcp.json`）；`copilot plugin install <本機路徑>` 可用但已標示將棄用（未來走 `plugin@marketplace`）；`--plugin-dir` 只在 session 層級；project 的 `.claude/skills/creative-ideation` 會**遮蔽**同名 plugin skill（已刪除該舊 skill）。
- Windows：執行中的 `cgu-server.exe`（VS Code 啟動）會鎖住 `.venv`；改用 `UV_PROJECT_ENVIRONMENT=$env:TEMP\cgu-venv` 與 `uv run --no-sync`。
- `uvx --from git+…@master` 冷啟動約 84 s（建置），之後有快取；MCP 客戶端首次啟動若有逾時，先在終端機預熱一次。
- Opus 每次呼叫 15 premium requests；實驗評審因此改用 `gpt-6-sol`＋`claude-sonnet-5.5`。

## 實驗現況（三輪完成；詳見 `evals/reports/SUMMARY.md`）

- exp1（v1，6 題、36 格）、exp2（v2，held-out 3 題）、exp3（v3，held-out 3 題）；評審 `gpt-6-sol`＋`claude-sonnet-5.5`、兩種順序。
- **沒有證明整體勝過直接提問**：格子層級勝率 27%／25%／50%，區間都跨 50%。
- plugin 穩定提升新穎度與問題框架重寫（75–96%）；v1、v2 在實用性與可決策性被扣分（17–38%）。評審理由指出兩個根因：工具內部用語混進答案、門檻寫「待估」。v3 修了這兩點，可決策性 36%→79%、實用性 19%→38%，與 baseline 持平；**v3 僅 6 格、評審順序不穩定**。
- 被證偽的假設：v2 的「限制清單＋可行性閘門」沒有補回實用性。
- 自動觸發不穩定：不改提示時 9/12 格實質使用 CGU（Sonnet 3/6、luna 6/6）。
- 工具呼叫錯誤率 8.0%／8.2%／1.6%；`target` 漏填與自編 id 在修正後歸零，但總錯誤率在 exp3 才明顯下降。
- 已驗證的安裝：Copilot CLI（marketplace＋對話）、Codex CLI 0.160.0（marketplace＋`plugin add`＋`mcp list`；未登入故未驗證對話）。**VS Code 未驗證。**

## 待解決問題

- [ ] 人類校準（2–3 位評分者、約 100 個點子，D-10）；在此之前所有 LLM 評審結論都標為「未經人類校準」，且 v2、v3 是依 LLM 評審理由調整的，可能迎合 LLM 評審。
- [ ] VS Code 的實際安裝驗證；Codex 的實際對話驗證（需登入）。
- [ ] 加 `agent` 條件與消融實驗；評估 skill 是否該在任務型題自動退讓。
- [ ] 重測 `cgu_judge` 自編 session 名稱的錯誤（提示已改為列出真實 id，尚未重測）。
- [ ] 評估後續 PyPI／MCP Registry 發布（D-19）；v0.9.0 tag／GitHub Release 已完成。
- [ ] 在 med-paper-assistant 的 integration lock 中固定正式發布版本（0.8.0 為不相容變更，須通知上層）。
- [ ] 語意 embedding 的選用評估；2026-10-07 使用者要求 agent 模型負責思考，因此保留 `ngram` 為無模型預設，語意 embedding 需明確設定。
- 未追蹤、**非 CGU 本體**的檔案：`.asset-aware-mcp/`、`.cline/`、`.clinerules/`、`.codex/`、`.github/agents/`、`AGENTS.md`、`.claude/skills/pdf-asset-extractor/` 與 `.vscode/mcp.json` 的修改，來自 Asset-Aware MCP 擴充套件安裝；不要提交、不要覆寫。

## 相關檔案

- `docs/architecture.md` - v0.9.0 契約與 as-built 備註
- `docs/program-plan.md` - 階段、工作包、決策（D-05／D-06 已被取代）
- `docs/critical-review-and-improvement-plan.md`、`docs/philosophical-inquiry-and-creativity.md` - 重寫的依據
- `plugins/cgu/` - 對外交付的 plugin
- `evals/` - 效果實驗（README 有協議與指令）
- `memory-bank/progress.md` - 工作包狀態表

## 已驗證（2026-10-03）

- `uv sync --locked --extra dev`、`ruff check`／`ruff format --check`（src、tests、evals）、`mypy src`、`pytest`：397 passed（`CGU_REQUIRE_LIVE_CONTRACT=1`）。
- `uvx --from git+…@master cgu doctor` 可執行；plugin 以 git 來源在隔離 Copilot CLI 中連線並成功呼叫 `cgu_status`。

## 更新時間

2026-10-07
