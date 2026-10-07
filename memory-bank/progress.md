# Progress (Updated: 2026-10-07)

## Done

- 2026-10-07：**v0.9.0 正式發布**。[GitHub Release](https://github.com/u9401066/creativity-generation-unit/releases/tag/v0.9.0)、annotated tag 與 commit `bb32a8f` 已在遠端；wheel／sdist／SHA256SUMS 上傳完成。CI run `37620612551` 的 Python 3.11／3.12 均成功；遠端固定 tag 的 uvx 安裝與 doctor 通過。附件從乾淨 release commit 重建，sdist 306 個檔案均屬追蹤檔案或建置 metadata，沒有本機資料、快取與原始 runs。

- 2026-10-07：v0.9.0 發布準備完成。文件、MCP 範例、plugin 與 hook fallback 固定版本同步；sdist 明確選取 CGU 檔案並排除本機快取與原始 runs。**579 passed**；ruff／mypy（63 source files）、locked sync、build 通過；獨立 Python 3.11.9／MCP 2.3.0 的已安裝 wheel 測得 11 tools、doctor 零模型探測、素材跨程序持久化與來源刪除連動。

- 2026-10-07：接續 Copilot 的 inquiry memory，完成模型分工與創意素材整理。預設 `passthrough`＋`ngram`，MCP／doctor 不探測 Ollama；hook 累積、agent 用自己的模型執行 `organize`，`distill` 保存來源 ID／SHA-256 的 caller 素材，`materials` 跨 session 回用。Migration 3、門檻、分批／部分已讀、冪等重送、刪除連動、舊庫升級與競態回歸已驗證。功能階段 **577 passed**；加入發布檢查後 **579 passed**。未安裝或啟用使用者個人 hook。

- 2026-10-03（第五輪續）：三輪效果實驗與迭代。exp1（v1）→ 依評審理由改 v2（限制清單）→ exp2（held-out）證偽「限制違反是主因」→ 讀評審理由後改 v3（白話輸出、決策值不得寫「待估」）→ exp3（新 held-out）持平。伺服器小修：`default_target`、unknown session 提示列出真實 id。Codex CLI 0.160.0 驗證安裝與 MCP 註冊。
- 2026-10-03（第五輪，**v0.8.0 不相容重寫**）：依使用者指示「MCP 直接改 SDK 2.0+、不相容、設計較佳架構」完成並推送 `master`。
  - 規格：[`docs/architecture.md`](../docs/architecture.md)（10 個工具、`Measurement`／`Provenance`／`WorkOrder`／`ToolResult`、依賴規則、SDK 2 實作備註）。
  - Core：`src/cgu/{domain,application,infrastructure,interfaces}`；24 個舊工具與 LangGraph／template 引擎全部刪除，無別名；397 tests、ruff、mypy 全綠；非阻塞（事件迴圈停頓 1.2 s → < 40 ms）。
  - Plugin：`plugins/cgu`（Agent Plugins 1.0）含 4 skills、4 Copilot agents、Copilot／Codex marketplace；81 個結構與契約測試。
  - Evals：`evals/` 隔離式 Copilot CLI 效果實驗框架（baseline／plugin／plugin_explicit，盲評成對比較）。
  - **實際安裝驗證**：在隔離的 `COPILOT_HOME` 用 `copilot plugin install` 安裝；CLI 1.0.91 直接讀 plugin 根目錄 `mcp.json`（**不需要** `.mcp.json`，推翻 evals 子 agent 先前的說法）；`cgu` 以 `source=plugin`、`status=connected` 連線，`cgu-cgu_status` 實際呼叫成功；`uvx --from git+…@master` 冷啟動約 84 s（建置），之後有快取。
  - 一個真實試跑（plugin × Sonnet 5.5 × 居家照護產品題）：自動載入 `creative-ideation`，呼叫 CGU 15 次（frame 9、ideas 3、diverge 1、session 1、status 1），產出附推導路徑的 3 張點子卡。
  - 文件：README（EN／zh-TW）重寫、CHANGELOG 0.8.0、ROADMAP 重寫、program-plan 狀態與 D-05／D-06 取代。
- 2026-10-02（第四輪）：分階段執行計畫 `docs/program-plan.md`；新發現 N1；baseline 改稱 `BL0–BL3`。
- 2026-10-02（第三輪）：哲學討論稿 `docs/philosophical-inquiry-and-creativity.md`（PH1–PH8、L0／L1／L2、Frame 與算子、H7–H9）。
- 2026-10-02（第二輪）：嚴格審查 `docs/critical-review-and-improvement-plan.md`（40 項缺陷、H1–H6、停損條件）。
- 2026-10-02：repo 全面理解與成熟度盤點；作者資訊更正為 u9401066 ＜u9401066@gap.kmu.edu.tw＞。
- 2026-08-17：0.6.0 SDK 2 遷移（已被 0.8.0 取代）。

## Doing

- 無進行中的長任務。Hook 累積與 agent 整理流程已完成；真實使用的採用效果尚待累積資料驗證。

## 計畫狀態（鍵：工作包編號；定義見 `docs/program-plan.md` §6）

| 階段 | 工作包 | 狀態 | 備註 |
|---|---|---|---|
| P0 止血 | P0.1–P0.13 | **被取代** | 整個舊程式碼已刪除，缺陷隨之消失；不再需要逐項修補 |
| P1 地基 | P1.1 分層 | 完成 | D-05／D-06 已被取代：無別名、無 `experimental/` |
| | P1.2 Provider 埠 | 完成 | passthrough 為預設；Ollama 為選用 adapter |
| | P1.3 Archive | 完成 | SQLite WAL、migration、export、delete、多 session 隔離 |
| | P1.4 Measure 基礎版 | 完成 | `Measurement`；無參照集回 `null`；n-gram 後備誠實標示 `semantic=false` |
| | P1.5 評估框架 | 完成（形式不同） | 實作為 Copilot CLI 效果實驗，不是原計畫的 AUT 題庫 |
| | P1.6 baseline 報告與人類校準 | 部分 | 三輪效果報告完成（`evals/reports/SUMMARY.md`），含負面結果；**人類校準協議未做** |
| P2 Harness | P2.1 可攜核心 | 完成 | |
| | P2.2 Copilot agents | 完成 | 4 個薄包裝 agent |
| | P2.3 Codex 延伸 | 部分 | `extensions.com.openai` 已有；consumer 用 `AGENTS.md` 片段（D-16）未做 |
| | P2.4 Marketplace | 完成 | |
| | P2.5 驗證與 CI | 完成 | schema 釘版本、frontmatter lint、live contract 測試 |
| | P2.6 人工安裝驗證 | 部分 | **Copilot CLI**：marketplace 安裝＋對話皆實測；**Codex CLI 0.160.0**：安裝與 MCP 註冊實測，對話未驗證（未登入）；**VS Code 未驗證** |
| | P2.7 plugin 安全審查 | 部分 | 不附 hooks；隱私說明在 plugin README；正式審查紀錄未寫 |
| P3 哲學層 | P3.1 Frame 模型 | 完成 | |
| | P3.2 11 個算子 | 完成 | 每個算子的保留／下架決定待實驗（P3.7） |
| | P3.3 懷疑的經濟學 | 完成 | 優先度標為未校準 |
| | P3.4 提問品質閘門 | 部分 | `cgu_question_gate` 已實作；人類校準一致性未量測 |
| | P3.5 哲學 skills 與 agent | 完成 | `anti-typical-diverge` 併入 `creative-ideation` |
| | P3.6 同意與揭露 | 完成 | Elicit＋`consent_required` 後備 |
| | P3.7 實驗 H7、H8 | 待辦 | |
| P4 創意機制 | P4.1–P4.6 | 基礎版已含於重寫 | 反典型、fan-out、素材（Wikipedia）、niche map；**皆未經實驗驗證**；G4 停損關卡待過 |
| P5 人機回饋 | P5.1–P5.5 | 部分 | `cgu_feedback` 資料模型已有；對人類原創性的量測待辦 |
| P6 驗證與 1.0 | P6.1–P6.4 | 部分 | v0.9.0 tag／GitHub Release 完成；1.0 宣稱審計、PyPI／Registry 與其他工作包待辦 |

## Next

1. 看實驗報告，據實更新 README「證據」；若 skill 自動觸發率低，改 skill 描述並用**未見過的題目**重驗。
2. 人類校準協議（2–3 位評分者、約 100 個點子，D-10）。
3. VS Code 與 Codex 的實際安裝驗證。
4. 評估後續 PyPI 與 MCP Registry（D-19）；v0.9.0 git tag／GitHub Release 已完成。
