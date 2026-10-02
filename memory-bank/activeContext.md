# Active Context

## 當前焦點

- 2026-10-02（第四輪）：使用者確立目標——**分階段有條理地完成創意升級與哲學導入，涵蓋 MCP 改進，並延伸為整個 harness plugin**。已完成 [`docs/program-plan.md`](../docs/program-plan.md)：
  - 事實查證（已回查官方來源）：**Copilot 與 Codex 都能導入**，因為兩者都實作 Agent Plugins 1.0 開放標準（2026-08-06 發布）。可攜的只有 skills＋MCP；agents、hooks、commands、rules 在各家命名空間（`com.github.copilot/`、`extensions.com.openai`）。
  - 本機沒有 `copilot`／`codex`／`claude` CLI → 實際安裝需人工驗證，沒驗證就不寫「支援」。CGU 尚未上 PyPI → plugin 過渡期用 `uvx --from git+…@<tag>`。
  - 方法論放可攜 skills、能力放 MCP（I／C／S／M）、驗證放 `evals/`；阻塞點是「評估」而非「生成」。
  - 預設決策 D-01～D-20 已採用（可否決）；P0 不依賴未確認的決策。
- **下一步**：見 `progress.md`「計畫狀態」與「Next」；等使用者確認開工與 §9.4 的四個開放問題後，從 P0.1 開始。依憲法第 6 條與使用者的節奏，本輪**未修改任何產品程式碼**。

## 先前輪次（摘要）

- 第三輪：[`docs/philosophical-inquiry-and-creativity.md`](../docs/philosophical-inquiry-and-creativity.md)。內容包括：
  - 評估使用者與 Gemini 的「哲學導入 agent」框架（缺口 PH1–PH8）。
  - 回答「高階創意討論是否屬於哲學」，提出 L0／L1／L2 三層框架模型。
  - 擴充哲學工具箱，並提出修訂版框架：五個動作 × 七個透鏡 × 懷疑的經濟學。
  - 導入 CGU 的設計：Frame 物件、框架算子、「有理由的新穎」。
  - 新增假設 H7–H9 與決策點 Q11–Q15。
- 第二輪：[`docs/critical-review-and-improvement-plan.md`](../docs/critical-review-and-improvement-plan.md)：
  - 40 項缺陷（🔴9／🟠18／🟡11／⚪2）。
  - 改進路線 P0–P4、可證偽假設 H1–H6、停損條件。
  - 對上一輪論點的自我修正。
- 舊的「下一步」（與使用者逐項討論 Q1–Q15）已由執行計畫的 D-01～D-20 預設決策取代；任何決策都可否決，流程見計畫 §7.4。
- 背景：CGU 0.6.0 已完成 MCP SDK 2 遷移並推送 `master`（24 tools、structured output）。

## 哲學討論核心結論（摘要）

1. 哲學與創意共享的核心操作是「在 L1 改變框架」：哲學擅長表徵與評估框架，創意擅長生成框架與內容。
2. 原始框架缺少「生成」動作，也缺少「何時停止懷疑」的節制原則；它預設的基礎論，應改為 Neurath 之船式的選擇性懷疑。
3. 往 L1 升級的觸發條件是僵局、異常、衝突與高風險，而不是每一輪都升級；停損採實用準則：不再改變決策就停。
4. 「有理由的新穎」：從典型答案溯因出隱性假設，再以框架算子改寫承重假設。
5. 哲學提問本身也要受品質控制（決策相關、可操作、承重、非口頭、非典型），以防偽深刻。

## 審查核心結論（摘要）

1. 多數「創意機制」是模板＋亂數＋常數；24 個工具中有 12 個輸出沒有測量程序的數字（C1）。
2. 根本缺陷是「選擇」缺位（A6）：沒有可信的評估，演化與對抗迴圈不可能收斂。
3. 從未與 baseline（直接請呼叫端模型發想）比較過（E2）；15/104 個測試函式沒有斷言（E1）。
4. 立即可修的 bug：事件迴圈阻塞（D1）、passthrough 洩漏到 Ollama（C3）、session 串線（D2）、DuckDuckGo 改名後回 0 筆（D4）、網頁碎片未隔離（C5）。
5. 判準：工具價值四準則 I／C／S／M（資訊／計算／狀態／測量）。

## 相關檔案

- `docs/critical-review-and-improvement-plan.md` - 審查討論稿（缺陷編號供討論引用）
- `docs/philosophical-inquiry-and-creativity.md` - 哲學討論稿（PH1–PH8、Frame 物件、框架算子、Q11–Q15）
- `tests/probes/probe_defects.py` - 可重現的缺陷探針（base／pt／ol 三組；不被 pytest 收集，不是 CI gate）
- `src/cgu/server.py` - MCP 入口，24 tools + 2 resources，LLM provider 切換與 fallback 鏈
- `src/cgu/thinking/engine.py`、`src/cgu/agents/` - 「Multi-Agent 深度思考」（模板 Agent，不呼叫 LLM）
- `src/cgu/tools/creativity_tools.py` - v3 Agent 工具（硬編碼小型知識庫、啟發式新穎度）
- `src/cgu/soup/spark_soup.py`、`src/cgu/brainstorm_protocol.py` - Spark-Soup 與 A2A 腦力激盪腳本

## 已驗證

- Python 3.11 與 3.12 相容；SDK 2 direct client、stdio、wheel-install smoke 通過（2026-08-17）。
- 2026-10-02：`uv run --extra dev python -m pytest -q` → 103 passed, 2 deselected；`ruff check src tests`、`ruff format --check src tests` 通過。
- 注意：`.venv` 若未安裝 dev extras，`uv run pytest` 會落到全域 Python 並報 `No module named 'cgu'`；請用 `uv sync --all-extras` 或 `--extra dev`。
- 探針需在 repo 根目錄執行，Windows 需設 `PYTHONUTF8=1`；`ol` 組需要本機 Ollama（qwen2.5:3b）。

## 待解決問題

- [ ] 討論並決定 Q1–Q15（審查文件第 9 節 Q1–Q10；哲學文件第 9 節 Q11–Q15）。
- [ ] 建立 `v0.6.0` tag / GitHub Release，確認 PyPI 發布流程（目前無任何 tag 或 release）。
- [ ] 在 med-paper-assistant 的 integration lock 中固定正式發布版本。
- [ ] 文件落差、死依賴、與 CGU 無關的檔案：已列入審查文件 D9／E3，待 P0-14 處理。
- [ ] 未追蹤變更：`.asset-aware-mcp/`、`.cline/`、`.clinerules/`、`.codex/`、`.github/agents/`、`AGENTS.md`、`.claude/skills/pdf-asset-extractor/` 與 `.vscode/mcp.json` 的修改，來自 Asset-Aware MCP 擴充套件安裝，非 CGU 本體。

## 更新時間

2026-10-02 23:10
