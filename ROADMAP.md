# Roadmap

CGU (Creativity Generation Unit) 的路線圖。詳細的工作包、關卡與決策見[分階段執行計畫](docs/program-plan.md)；逐項狀態見 [`memory-bank/progress.md`](memory-bank/progress.md)。

## 現況：v0.9.0（2026-10-07）

以 v0.8.0 的 SDK 2 重寫為基礎，v0.9.0 加入提問與創意素材記憶：

- [x] MCP SDK 2 原生 server：11 個工具、5 個 resources、4 個 prompts（[契約](docs/architecture.md)）
- [x] 分層架構（domain / application / infrastructure / interfaces），依賴規則由測試強制
- [x] `passthrough`＋`ngram` 為預設：CGU 不呼叫或探測模型；整理與推理由 agent 背後的模型負責
- [x] 所有數值皆為附方法的 `Measurement`；未量測回報 `null`
- [x] 哲學框架層：Frame 物件、11 個算子、懷疑的經濟學、提問品質閘門、受限元素同意
- [x] Agent Plugin（Agent Plugins 1.0）：5 skills、4 個 Copilot agents、Copilot／Codex marketplace
- [x] 跨客戶端 `~/.cgu` 提問記憶；選用 Copilot hook、skill 轉送與檔案匯入
- [x] `organize`／`distill`／`materials`：agent 整理可用創意素材，保留來源 ID／SHA-256；預設 20 筆待辦，無 agent 時只累積
- [x] 安裝來源固定 `v0.9.0`；資料庫遷移、原子回交、來源刪除連動與套件打包範圍有回歸測試
- [x] 在隔離的 Copilot CLI 實際安裝（marketplace 流程）並以 Sonnet／GPT luna 等級模型測試；Codex CLI 驗證安裝與 MCP 註冊
- [x] 效果實驗框架 `evals/`（baseline vs plugin vs plugin_explicit，盲評成對比較）與三輪實驗（[摘要](evals/reports/SUMMARY.md)）：**未證明整體勝過直接提問**，但穩定提升新穎度與問題重構；v3 與 baseline 持平

## 下一步

| 優先 | 項目 | 說明 |
|---|---|---|
| 1 | 人類校準與更大樣本 | 目前只有 LLM 評審、n 很小（見 [效果實驗摘要](evals/reports/SUMMARY.md)）：2–3 位評分者、約 100 個點子（D-10）；加一次 Opus 評審抽樣驗證 |
| 2 | `agent` 條件與消融 | 自動觸發不穩定（9/12 格實質使用 CGU）：加 `--agent creative-facilitator` 條件；消融「白話輸出＋決策值」與 `frame-audit` 各自的貢獻 |
| 3 | 任務型題的退讓 | 行政流程題在 exp1 的 plugin_explicit 為 0/4；評估 skill 是否該在任務型題自動退讓 |
| 4 | VS Code 與 Codex 對話實測 | Copilot CLI 已實測安裝＋對話；Codex CLI 已驗證安裝與 MCP 註冊但未登入、未驗證對話；VS Code 未驗證 |
| 5 | 選用 embedding 與記憶效果驗證 | 保留無模型預設；補 held-out H13、真實 agent 整理與 H10 採用效果驗證，不用單元測試宣稱更有創意 |
| 6 | P5 人機回饋 | `cgu_feedback` 已有資料模型；補上對人類原創性與擁有感的量測（H5、H9） |
| 7 | 後續發布管道 | git tag／GitHub Release 後，再評估 PyPI 與 MCP Registry（D-19） |

## 刻意不做

- Plugin 不自動安裝 hooks；Copilot 收集器由使用者選用，Codex／VS Code hook 尚未驗證。
- 不在創意討論上加倫理閘門；下游法規以點子卡的風險欄位呈現。
- 不再提供舊版 24 個工具的別名。

## 歷史

v0.1–v0.6 的紀錄見 [CHANGELOG.md](CHANGELOG.md)。0.6 以前的「創意機制」多為模板、隨機數與固定常數，詳見[嚴格審查](docs/critical-review-and-improvement-plan.md)。
