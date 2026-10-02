# Progress (Updated: 2026-10-02)

## Done

- 2026-10-02（第四輪）：完成**分階段執行計畫** `docs/program-plan.md`（含 Copilot／Codex 可攜性事實查證、三層分工、plugin 配置、D-01～D-20 預設決策、P0–P6 共 49 個工作包、關卡 G0–G6、DoD、風險 R1–R11）；新發現 N1（伺服器忽略 `OLLAMA_BASE_URL`）；解決命名衝突（baseline 改稱 `BL0–BL3`，避免與缺陷 `B1–B11` 混淆）；`ROADMAP.md` 加上現況橫幅。
- 2026-10-02（第三輪）：完成哲學討論稿 `docs/philosophical-inquiry-and-creativity.md`。
  - 內容：評估 Gemini 框架（PH1–PH8）、L0／L1／L2 三層模型、哲學工具箱、修訂版框架（五動作 × 七透鏡 × 懷疑的經濟學）、Frame 物件與框架算子、H7–H9、Q11–Q15。
  - 已與審查文件互相連結（§7.2、§7.4.3、§9）。
- 2026-10-02（第二輪）：完成嚴格審查討論稿 `docs/critical-review-and-improvement-plan.md`（40 項缺陷、P0–P4 路線、H1–H6 假設、停損條件、Q1–Q10 決策點）；新增可重現探針 `tests/probes/probe_defects.py`；修訂 `architect.md` 成熟度表（第一輪評等過寬）。
- 2026-10-02：完成 repo 全面理解與實作成熟度盤點（`architect.md`），改寫模板殘留的 `projectBrief.md`，修正 `productContext.md` 技術棧；重跑測試基線 103 passed。
- 0.6.0 SDK 2 遷移相關 commit 已推送 `master`（2026-08-17）。
- 保留 v2 核心引擎與 v3 Agent-Driven Creativity Tools。
- 全面遷移至官方 MCP Python SDK 2：`mcp>=2,<3`、`MCPServer`、SDK 2 schema/result 欄位。
- 24 個 tools 全部啟用 structured output。
- 新增 direct client、stdio subprocess、wheel-install MCP smoke tests。
- 把需要 live Ollama 的腳本式測試改為明確 opt-in integration test。
- 修正 LangGraph 1.x Functional API：entrypoint 改用單一 serializable input object，並加回歸測試。
- 修正既有型別與 lint 問題；ruff、mypy、103 tests 全綠。
- CI 改為 `master` 上 Python 3.11/3.12 的真實 hard gates，不再吞掉錯誤。

## Doing

- **計畫已就緒，等待開工**：[`docs/program-plan.md`](../docs/program-plan.md)（49 個工作包、7 個關卡 G0–G6、預設決策 D-01～D-20）。P0 不依賴尚未確認的決策，隨時可開工。
- 待建立 `v0.6.0` tag / GitHub Release（未經同意不會建立）。

## 計畫狀態（鍵：工作包編號；定義見 `docs/program-plan.md` §6）

狀態值：待辦／進行中／審查中／完成／阻塞。**每完成一個工作包就更新此表，並記錄估計偏差。**

| 階段 | 工作包 | 狀態 | 備註 |
|---|---|---|---|
| P0 止血（v0.7.0） | P0.1 provenance 與誠實降級 | 待辦 | 其餘 P0 多數依賴它，建議最先做 |
| | P0.2 passthrough 隔離＋預設改 passthrough | 待辦 | 依賴 P0.1；D-15 的破壞性變更需你確認 |
| | P0.3 LLM 不阻塞事件迴圈 | 待辦 | 獨立 |
| | P0.4 session 隔離 | 待辦 | 獨立 |
| | P0.5 新穎度與連結誠實化 | 待辦 | 依賴 P0.1 |
| | P0.6 圖譜反向邊修正 | 待辦 | 獨立 |
| | P0.7 提示與設定缺陷（含 N1） | 待辦 | 依賴 P0.1 |
| | P0.8 協議與方法清單誠實化 | 待辦 | 依賴 P0.1 |
| | P0.9 Spark-Soup 安全與搜尋 | 待辦 | 依賴 P0.1 |
| | P0.10 實驗性標示 | 待辦 | 依賴 P0.1 |
| | P0.11 文件與依賴誠實化 | 待辦 | 獨立 |
| | P0.12 測試重整與探針轉回歸測試 | 待辦 | 依賴 P0.1–P0.9 |
| | P0.13 `cgu*` MCP 設定整理 | 待辦 | 依賴 P0.2、P0.7；只動 cgu 條目 |
| P1 地基（v0.8.0） | P1.1–P1.6 | 待辦 | 需 G0 |
| P2 Harness 骨架（v0.8.0） | P2.1–P2.7 | 待辦 | 需 G0；可與 P1 平行 |
| P3 哲學層（v0.9.0） | P3.1–P3.7 | 待辦 | 需 G1、G2 |
| P4 創意機制（v0.10.0） | P4.1–P4.7 | 待辦 | 需 G3；**G4 為停損關卡** |
| P5 人機回饋（v0.11.0） | P5.1–P5.5 | 待辦 | 需 G4 |
| P6 驗證與 1.0 | P6.1–P6.4 | 待辦 | 需 G5 |

## Next

- **下一步動作**：等你確認開工與 `docs/program-plan.md` §9.4 的四個開放問題（尤其 D-15：plugin 預設 passthrough 的 0.x 破壞性變更）後，從 P0.1 開始；P0.3、P0.4、P0.6、P0.11 與 P0.1 無依賴，可平行。
- P1 評估基礎建設：資料集、等預算 baseline（BL0–BL3）、多樣性／新穎度向量／成對評審、人類校準。
- 發布 PyPI 0.6.0 並讓上層 integration lock 固定版本（順序依 D-19）。
