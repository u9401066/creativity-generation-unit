# CGU 創意升級 × 哲學導入 × Harness Plugin：分階段執行計畫

> **狀態**：計畫 v1（預設決策已採用，可否決）｜**日期**：2026-10-02｜**基線**：`master` @ `f293e19`（v0.6.0）
>
> **前置文件**：
> - [嚴格審查：缺陷分析與改進方案](./critical-review-and-improvement-plan.md)（缺陷編號 A1–F4）
> - [哲學後設探究 × 創意](./philosophical-inquiry-and-creativity.md)（缺口 PH1–PH8、Frame 與框架算子）
>
> **本文件的角色**：把兩份討論稿與「導入整個 harness plugin」的目標，轉成可逐步執行、可驗收、可中斷續做的長任務。**本文件本身不修改產品程式碼。**

## 目錄

0. 使用方式與續做協議
1. 目標、非目標與成功標準
2. 事實查證：Copilot 與 Codex 能不能導入？
3. 目標架構：三層分工與 plugin 配置
4. 預設決策（可否決）
5. 階段總覽與關卡
6. 工作包明細
7. 長任務治理
8. 驗證策略
9. 風險、開放問題與未查證事項

---

## 0. 使用方式與續做協議

- **計畫與狀態分離**：本文件維持穩定（目標、工作包、驗收）；執行狀態記在 [`memory-bank/progress.md`](../memory-bank/progress.md)，以工作包編號（例如 `P0.3`）為鍵。這樣計畫不會因為每次進度更新而產生雜訊。
- **新 session 的開場動作**（每次都做）：
  1. 讀 [`activeContext.md`](../memory-bank/activeContext.md) 的「下一步」與 `progress.md` 的工作包狀態。
  2. 跑基線：`uv run --extra dev python -m pytest -q`、`uv run --extra dev ruff check src tests`。
  3. 跑探針：`tests/probes/probe_defects.py`（base／pt／ol），確認已修的缺陷維持翻轉。
  4. 從下一個狀態為「待辦」且依賴已完成的工作包繼續。
- **編號規則**：工作包 `P<階段>.<序號>`；對應的審查缺陷以 `A1`、`B5` 等引用；決策以 `D-xx` 引用；關卡以 `G<階段>` 引用。

---

## 1. 目標、非目標與成功標準

### 1.1 目標

| # | 目標 | 對應 |
|---|---|---|
| T1 | **誠實**：輸出的每個數字都有測量程序，降級與模擬都明示 | 審查 C1、C2、A6 |
| T2 | **創意升級**：以「變異 → 可信選擇 → 保留」取代模板加亂數 | 審查 A–B 類、§7 |
| T3 | **哲學導入**：把「框架」做成一等公民，以框架算子實作變革型創意，並控管提問品質 | 哲學文件 §6–§7 |
| T4 | **MCP 改進**：工具面收斂、事件迴圈不阻塞、狀態隔離與持久化、不受信任內容隔離 | 審查 C、D 類 |
| T5 | **整個 harness**：以 Agent Plugins 1.0 打包 skills、MCP，並加上 Copilot／Codex 各自的延伸 | §2、§3 |
| T6 | **可驗證**：每個宣稱都有 baseline 比較與實驗報告，負面結果也保留 | 審查 E1、E2、§7.5 |

### 1.2 非目標

- 不追求「讓 CGU 自己比強模型更有創意」：預設由呼叫端的強模型生成，CGU 負責資訊、計算、狀態與測量（D-02）。
- 不做雲端服務與多用戶託管；資料預設只在本機（D-09）。
- 不在 v1.0 前承諾「哲學方法提升創意」這類結論；只承諾「已用什麼實驗、得到什麼結果」。
- 不修改使用者其他 MCP server 的設定（例如 `.vscode/mcp.json` 中的 `asset-aware-mcp`）。

### 1.3 成功標準（v1.0 的完成定義）

1. 審查文件中 🔴／🟠 缺陷全數關閉，且各有不變式回歸測試。
2. 所有輸出的數值欄位都有 `method`、`reference`、`calibrated`；做不到的已移除。
3. 至少一份對照 BL0–BL3 的等預算評估報告，含信賴區間與負面結果。
4. 一個通過 Agent Plugins 1.0 結構驗證的 plugin，可在 Copilot CLI／VS Code 與 Codex 安裝，並附人工驗證紀錄。
5. 每個保留的哲學算子都有「來源、護欄、提問品質判準、至少一次實驗結果」；沒有證據的算子已下架或標為 experimental。

---

## 2. 事實查證：Copilot 與 Codex 能不能導入？

**結論：可以，而且兩邊共用同一個開放標準。** 但標準只涵蓋 skills 與 MCP；agents、hooks、commands、rules 與指示檔各家自成一套。

### 2.1 已回查官方來源的事實

| # | 事實 | 來源 |
|---|---|---|
| V1 | Agent Plugins 1.0 是把 skills 與 MCP server 打包成單一可安裝 plugin 的開放標準，由 AWS、Anysphere、Microsoft、OpenAI、Vercel 於 2026-08-06 發布，Google 同日加入核心維護者；不受單一廠商治理 | GitHub Changelog 2026-08-12 |
| V2 | 在 VS Code、Copilot CLI、GitHub Copilot SDK、GitHub Copilot app 皆已 GA，所有 Copilot 方案可用；既有的 Copilot plugin 不需遷移 | 同上 |
| V3 | **可攜部分**：根目錄 `plugin.json`（含 `$schema`）、`skills/<name>/SKILL.md`、根目錄 `mcp.json`。**Copilot 專屬**：放在 `com.github.copilot/`（`agents/`、`commands/`、`rules/`、`hooks/hooks.json`），其他客戶端忽略此目錄 | GitHub Docs；VS Code Docs |
| V4 | Copilot CLI：`copilot plugin install ./路徑`、`copilot plugin list`、互動式 `/plugin list`、`/skills list`、`/agent`；安裝後內容會被快取，修改後需重新安裝。Marketplace 是 repo 內 `.github/plugin/marketplace.json`（也會讀 `.claude-plugin/`），以 `copilot plugin marketplace add owner/repo` 加入 | GitHub Docs |
| V5 | `plugin.json` 頂層只允許 `$schema`、`name`、`version`、`description`、`author`、`homepage`、`repository`、`license`、`keywords`、`extensions`；未知欄位會被回報並忽略 | GitHub Docs |
| V6 | Codex 也支援可攜格式：根目錄 `plugin.json`＋`mcp.json`；OpenAI 專屬的呈現、MCP 對應與 hook 設定放在 `extensions.com.openai`；舊的 `.codex-plugin/plugin.json` 仍相容。**但官方 scaffold（`@plugin-creator`）目前產生的是相容佈局，不是可攜佈局** | OpenAI Developers |
| V7 | Codex marketplace：repo 範圍為 `$REPO_ROOT/.agents/plugins/marketplace.json`，個人範圍為 `~/.agents/plugins/marketplace.json`；`codex plugin marketplace add owner/repo` 可從 GitHub 加入 | OpenAI Developers |
| V8 | 可攜的 MCP 格式要求每個 server 宣告傳輸 `type`（例如 `stdio`、`streamable-http`），不能只把舊的 `.mcp.json` 改名；`stdio` 的 `args`、`env`、`cwd` 可使用 `${PLUGIN_ROOT}`、`${PLUGIN_DATA}` | OpenAI Developers；GitHub Docs |
| V9 | Hooks 都是「執行本機程式碼」：Codex 要求先審查並信任（以 hook 定義的雜湊記錄），變更後需重新審查；VS Code 文件也提醒安裝前審查 plugin 內容與發布者。**Codex 與 Copilot 的 hook 事件與檔案位置各自定義，不可攜** | OpenAI Developers；VS Code Docs |
| V10 | `AGENTS.md` 是跨 agent 的共用指示格式（不是 Codex 專屬）；Copilot 另有 `.github/copilot-instructions.md` 與 `.instructions.md`（可用 `applyTo` 限定範圍） | VS Code Docs |
| V11 | 組織可用 `managed-settings.json` 的 `enabledPlugins`、`extraKnownMarketplaces`、`strictKnownMarketplaces` 管控；也可再搭配 MCP allowlist | GitHub Changelog |

### 2.2 本機環境與 repo 現況

| 項目 | 結果 |
|---|---|
| `copilot`、`codex`、`claude` CLI | **這台機器都找不到**，因此無法在此實際執行 `plugin install`；只能做結構驗證，實際安裝須由你在有 CLI 的環境人工驗證（§8） |
| Agent Plugins JSON Schema | 可下載：`plugin.schema.json`（1.8 KB）、`mcp.schema.json`（3.4 KB），可直接放進 CI 做離線驗證 |
| CGU 在 PyPI | **尚未發布**（404），所以 plugin 的 `mcp.json` 暫時無法用 `uvx creativity-generation-unit`；過渡方案是 `uvx --from git+https://github.com/u9401066/creativity-generation-unit@<tag> cgu-server` |
| 既有 `AGENTS.md` | 內容是 **Asset-Aware MCP 擴充套件**安裝的指示（未追蹤檔），不是 CGU 的；不應覆寫（D-16） |
| 既有 `.claude/skills/` | 是本 repo 的**開發用** skills（git-precommit、memory-updater…），與要對外發布的 plugin skills 應分開（D-17） |

### 2.3 可攜性矩陣

| 元件 | 可攜（跨 Copilot／Codex／其他） | Copilot | Codex | 對 CGU 的意義 |
|---|---|---|---|---|
| Skills（`SKILL.md`） | ✅ | ✅ | ✅ | **方法論主載體**：哲學探究協議、反典型發散、成對評審流程 |
| MCP server | ✅（`mcp.json`） | ✅ | ✅ | **I／C／S／M 主載體**：素材檢索、獨立取樣、存檔、測量 |
| 自訂 agent（`.agent.md`） | ❌ | ✅ `com.github.copilot/agents/` | 未查證 | 薄包裝：facilitator、frame-auditor、critic；Codex 端改由 skill 提供同樣行為 |
| Hooks | ❌ | ✅ `com.github.copilot/hooks/` | ✅ `extensions.com.openai`／`hooks/hooks.json` | 預設**不附**（D-20）；僅在有明確價值時作為 opt-in |
| Commands、Rules | ❌ | ✅ | 未查證 | 選用 |
| 專案指示檔 | ◐ `AGENTS.md` 為跨 agent 格式 | ✅（另有 `copilot-instructions.md`） | ✅ | plugin 不能安裝指示檔；改提供「可複製的指示片段」 |
| Marketplace 檔案 | ❌ | `.github/plugin/marketplace.json` | `.agents/plugins/marketplace.json` | 兩個檔案各自維護，指向同一個 plugin 目錄 |

### 2.4 設計含意

1. **方法論放 skills，不放 agent 人格**：skills 是唯一在兩家都能運作的行為載體；agent 只是 Copilot 端的薄包裝。這也呼應審查 B6——人格標籤本來就不是機制。
2. **哲學層大部分可以零 MCP 先上線**：框架審查、溯源檢驗、提問品質判準本質上是協議，可以先以 skill 形式交付並評估；需要「狀態」（Frame 譜系）與「測量」（決策差異）時再接 MCP。
3. **標準才剛發布**（2026-08），要預期欄位與慣例還會調整：把 schema 版本寫死在 CI，並在升版時走相容性檢查（風險 R2）。
4. **安全面**：plugin 可帶 hooks 與會執行程式碼的 MCP；CGU plugin 預設不附 hooks，MCP 預設走 passthrough（不連網、不呼叫本機模型），並把網頁碎片視為不受信任資料（審查 C5）。

---

## 3. 目標架構：三層分工與 plugin 配置

### 3.1 三層分工

```text
┌─ 方法論層（skills，可攜）─────────────────────────────────────────────┐
│ frame-audit · maieutic-session · anti-typical-diverge · idea-triage   │
│ 在呼叫端 LLM 的 context 內執行；規定「何時問、問什麼、何時停」          │
├─ 能力層（MCP，可攜）──────────────────────────────────────────────────┤
│ cgu_frame [S]  cgu_material [I]  cgu_diverge [C]  cgu_collide [C]     │
│ cgu_measure [M]  cgu_evolve [C]  cgu_archive [S]  + prompts/resources │
├─ 驗證層（evals，不進 plugin）─────────────────────────────────────────┤
│ 資料集 · baseline BL0–BL3 · 指標 · 評審 · 人類校準 · 報告               │
└───────────────────────────────────────────────────────────────────────┘
        Copilot 延伸：com.github.copilot/agents（薄包裝）
        Codex 延伸：extensions.com.openai（呈現與 MCP 對應）
```

判準沿用審查 §3.1：能力層的每個工具都必須提供 **I**（模型外資訊）、**C**（模型做不到的計算，含獨立 context 取樣）、**S**（跨 context 狀態）、**M**（可驗證測量）至少一項；否則降為 skill 或 prompt。

### 3.2 repo 目錄（目標狀態）

```text
creativity-generation-unit/
├── src/cgu/
│   ├── domain/            # Idea、Frame、Assumption、Evaluation、Session（無外部依賴）
│   ├── application/       # 用例：frame、diverge、collide、measure、evolve、archive
│   ├── infrastructure/    # LLM／embedding／retrieval adapters、SQLite repository
│   ├── interfaces/mcp/    # MCP tools／prompts／resources 註冊（依工具分檔）
│   └── experimental/      # v1／v2 舊引擎隔離區（D-06）
├── plugins/cgu/           # 對外發布的 plugin（D-17）
│   ├── plugin.json        # $schema = Agent Plugins 1.0；extensions.com.openai
│   ├── mcp.json           # 可攜 MCP 設定（type: stdio）
│   ├── skills/            # 可攜 skills
│   └── com.github.copilot/agents/   # Copilot 專屬
├── .github/plugin/marketplace.json  # Copilot CLI marketplace
├── .agents/plugins/marketplace.json # Codex repo marketplace
├── evals/                 # 評估（不進 plugin、不進 CI hard gate）
├── tests/                 # 契約與不變式測試（進 CI）；tests/probes/ 為現況探針
└── .claude/skills/        # 開發用 skills（維持原狀，不對外發布）
```

> 這是**目標**狀態；各階段只搬動該階段需要的部分。DDD 分層直接落實憲法第 1–3 條（審查 D6）。

---

## 4. 預設決策（可否決）

這些是我為了讓計畫可往前推進而採用的預設。**任何一項都可以否決**；「若否決」欄說明會重排哪些工作。凡是標「（Phase 0 不受影響）」的決策，不會阻礙止血階段開工。

| ID | 決策 | 對應提問 | 理由 | 若否決 |
|---|---|---|---|---|
| D-01 | 同時服務 agent 與人，分期：先建量測，再做人機回饋 | Q1 | 沒有量測就無法談對人的效果 | 改成只做其中一邊，P5 或 P1 縮減 |
| D-02 | 預設**不在 CGU 內生成**；生成交給呼叫端強模型。本地 Ollama 只作為可選 adapter，用於驗證 H3 | Q2 | passthrough 初衷；強模型不需要 3B 替它發想 | 保留本地生成：P1.2、P4.2 增加 provider 路徑與評估 |
| D-03 | 本機優先；embedding 走可選的本機 adapter（Ollama `nomic-embed-text`）；**沒有 embedding 時降級為字元 n-gram，並如實標示** | Q3 | 你的環境已有該模型；降級必須誠實 | 允許雲端 API：新增 adapter 與隱私說明 |
| D-04 | 第一個評估領域：通用（中英文）；第二個垂直領域：醫學研究發想 | Q4 | 你已有 PubMed／MedPaper 工具鏈可比對既有成果 | 換領域：只影響 P1.5 題庫與 P4.3 檢索 adapter |
| D-05 | 24 個工具在 v0.8.0 收斂；舊名稱保留**一個小版本**的別名並標示 deprecated | Q5 | 上層 med-paper-assistant 有 integration lock | 立即移除：加速 P1.1，但需通知上層 |
| D-06 | v1／v2／v3 舊引擎先隔離到 `experimental/` 並在描述中標示，之後逐步重寫或刪除 | Q6 | 降低一次性風險，保留可回溯 | 直接刪除：P0.10 改為刪除，工作量更小 |
| D-07 | 品質評估只在手動或 nightly 執行；契約與不變式測試進 CI | Q7 | 評估有成本與隨機性 | 小型 smoke eval 進 CI：P1.5 增加預算上限 |
| D-08 | agent 對問題框架的改寫：概念與隱喻可直接提案；改寫**目標、利害關係人、評估準則**必須取得同意 | Q8、Q14 | 防止越權與操縱（框架效應） | 全部需同意：P3.6 更嚴格；全部不需：不建議 |
| D-09 | 回饋與存檔：本機 SQLite；可匯出、可刪除；預設不上傳 | Q9 | 隱私與可控 | 雲端同步：新增威脅模型 |
| D-10 | 評估真值：小規模人類校準（2–3 位評分者、約 100 個點子）＋跨模型 LLM 評審擴量 | Q10 | 成本與可信度平衡 | 只用 LLM 評審：結論一律標為「未經人類校準」 |
| D-11 | **框架**成為一等公民（Frame 物件＋框架算子） | Q11 | 直接解決 A1，並提供 QD 搜尋有意義的座標 | 先做成 prompt 資產：P3.1 縮減，P4.4 改用操作類型 |
| D-12 | 算子庫採多傳統，但每個算子都要通過提問品質判準與至少一次實驗，否則下架 | Q12 | 避免偽深刻與傳統偏誤 | 只用分析哲學：減少算子，風險降低 |
| D-13 | 對話姿態依情境切換（低風險直接提案，高風險或使用者要求時先提問），之後依 H9 結果調整 | Q13 | 避免一律產婆式造成的煩人與分析癱瘓 | 固定產婆式：影響 P3.5、P5 |
| D-14 | 哲學提問以 §6.5 五項判準＋LLM 評審＋人類校準驗證 | Q15 | 與 P1 共用評估基礎 | 只靠人類評分：成本升高 |
| D-15 | **plugin 的 MCP 預設 `CGU_LLM_PROVIDER=passthrough`**（0.x 內的破壞性變更，於 v0.7.0 公告） | 新增 | plugin 面向的是 Copilot／Codex 這類強模型；不連本機模型最安全 | 維持 ollama：plugin 首次使用會因無 Ollama 而降級 |
| D-16 | 不覆寫根目錄既有的 `AGENTS.md`（屬於 Asset-Aware 擴充套件）；CGU 開發慣例維持在 `.github/copilot-instructions.md`；對 plugin 使用者另提供**可複製的指示片段** | 新增 | 避免與擴充套件互相覆蓋 | 合併成單一 AGENTS.md：需先與擴充套件的更新機制協調 |
| D-17 | 對外發布的 plugin 放在 `plugins/cgu/`，與開發用 `.claude/skills/` 分開 | 新增 | 開發用 skills 含 repo 專屬流程，不該被使用者安裝 | plugin 放根目錄：會與開發用目錄混雜 |
| D-18 | 先做 Agent Plugins 1.0 可攜格式；Claude 格式（`.claude-plugin/`）延後，視需求再加 | 新增 | 可攜格式已涵蓋 Copilot 與 Codex | 同步做 Claude：P2.4 增加一個 manifest |
| D-19 | 發布順序：先以 git tag 供 `uvx --from git+…` 使用，驗證穩定後再發 PyPI，再提交到公共 marketplace | 新增 | PyPI 尚未發布；過渡方案已知可行 | 先發 PyPI：需先完成 P0 才適合公開 |
| D-20 | plugin **預設不附 hooks**；若日後新增，一律 opt-in，並附審查說明 | 新增 | hooks 會執行本機程式碼，且兩家不可攜 | 附 hooks：需完成安全審查（P2.7） |

---

## 5. 階段總覽與關卡

### 5.1 階段與版本

| 階段 | 名稱 | 目標 | 版本 | 規模（估計，未經實測校準） |
|---|---|---|---|---|
| **P0** | 止血 | 誠實與安全：關閉 🔴 缺陷中可立即修的部分，消除假數字與洩漏 | v0.7.0 | 約 3–5 天 |
| **P1** | 地基 | 架構分層、provenance、存檔、量測、評估框架與第一份 baseline 報告 | v0.8.0 | 約 2 週 |
| **P2** | Harness 骨架 | 可攜 plugin（skills＋MCP）、Copilot／Codex 延伸、marketplace、驗證工具 | v0.8.0 | 約 1 週，可與 P1 平行 |
| **P3** | 哲學層 | Frame、框架算子、懷疑的經濟學、提問品質閘門、哲學 skills | v0.9.0 | 約 2–3 週 |
| **P4** | 創意機制 | 反典型、獨立取樣、素材檢索、QD 搜尋、類比管線、附證據的批判 | v0.10.0 | 約 3–4 週 |
| **P5** | 人機回饋 | 人先發想、點子卡、回饋回流、個人化與多樣性下限 | v0.11.0 | 約 2–3 週 |
| **P6** | 驗證與 1.0 | 宣稱對照證據的審計、文件、PyPI 與 marketplace 發布 | v1.0.0 | 約 1 週 |

> **規模欄是粗估**，沒有實測依據；每個階段開工前會用該階段的工作包重估一次，並把偏差寫進 `progress.md`，作為下一階段估計的校準。

### 5.2 依賴關係

```text
P0 ──┬─► P1 ──┬─► P3 ──► P4 ──► P5 ──► P6
     │        │
     └─► P2 ──┘      （P2 的 skills 內容會隨 P3–P5 持續更新，與 CGU 同版發布）
```

- P1 與 P2 在 P0 完成後可平行；兩者都完成才進 P3（P3 需要 archive／measure，也需要 plugin 作為交付管道）。
- P3 的 skills 與 Frame 協議不依賴 P4 機制，可先交付並評估。

### 5.3 關卡（每個階段結束時必須通過才進下一階段）

| 關卡 | 條件 | 失敗時 |
|---|---|---|
| **G0** | 審查 P0 範圍內的探針全數翻轉並已轉為不變式回歸測試；沒有任何數值欄位缺 `method`；passthrough 下本機 LLM 呼叫數為 0；ruff／pytest 全綠 | 留在 P0，不得發版 |
| **G1** | 架構規則測試通過（domain 不依賴 infrastructure）；archive 與 measure 可用；**第一份「現行 CGU vs BL0–BL3」等預算報告**已產出（負面結果也算） | 補齊評估基礎，不進 P3 |
| **G2** | plugin 通過 Agent Plugins 1.0 結構驗證（CI）；MCP stdio 煙霧測試透過 plugin 的 `mcp.json` 通過；人工安裝驗證至少在一個 Copilot 客戶端完成並留下紀錄；Codex 端若無環境則標記「未驗證」 | 修正結構或標示限制，不得對外宣稱支援 |
| **G3** | H7、H8 實驗完成；每個算子有保留／下架決定與理由 | 無證據的算子標為 experimental 或移除 |
| **G4（停損關卡）** | 依審查 §7.6：若等預算下最佳管線對 BL3 的盲評勝率 95% CI 下界 ≤ 50%，**且**多樣性提升 < 10%，停止「增強生成」路線，轉向「量測＋回饋」定位 | 轉向，P5 改以量測與回饋為主體 |
| **G5** | H5、H9 結果已記錄；回饋資料可匯出與刪除；隱私說明完成 | 不得宣稱「保護人的創意能力」 |
| **G6** | 每條對外宣稱都能指到證據（報告或測試）；沒有證據的已移除或標為實驗性 | 不發 v1.0.0 |

---

## 6. 工作包明細

**欄位說明**：「缺陷」對應審查編號；「依賴」是必須先完成的工作包；「大小」S（≤半天）／M（約 1–2 天）／L（3 天以上），為粗估。每個工作包的完成都必須符合 §7.1 的完成定義（DoD）。

### 6.1 P0 止血（v0.7.0）

| ID | 工作 | 缺陷 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|---|
| P0.1 | **Provenance 與誠實降級**：所有工具輸出加入 `provenance`（`engine`、`degraded`、`warnings`、`seed`）；移除捏造欄位（寫死的 `thinking_steps`、依序號產生或常數的 `association_score`）；沒有 LLM 時回報 `degraded`，`method_used` 如實標示 | C1、C2、B10 | 探針 P9a 不再出現捏造欄位；每個工具有 provenance 契約測試 | — | L |
| P0.2 | **passthrough 隔離**：provider 顯式注入；passthrough 下不建立任何 LLM client；預設 provider 改為 passthrough（D-15） | C3 | 不變式測試：passthrough 下 LLM 呼叫數＝0（探針 P10 翻轉） | P0.1 | M |
| P0.3 | **LLM 呼叫不阻塞事件迴圈**：改用 `ainvoke` 或 `asyncio.to_thread`，加逾時與取消 | D1 | 探針 P9b：呼叫期間事件迴圈最長停頓 < 0.1 s | — | M |
| P0.4 | **session 隔離**：`session_id` 必填，狀態依 session 分離（暫以記憶體實作，P1.3 再接 repository） | D2 | 探針 P13：給 A 的想法寫入 A；測試涵蓋交錯 session | — | M |
| P0.5 | **新穎度與連結誠實化**：NoveltyChecker 加入重複偵測與字元 n-gram，不再輸出裸 `is_novel`；ConnectionFinder 對未知配對回傳 `unknown` 與 `null` 分數 | B1、B2 | 探針 P1、P2 翻轉；原句與去空白變體皆判為重複；既有的常數斷言測試已改寫 | P0.1 | M |
| P0.6 | **圖譜修正**：反向邊使用反向關係（或標記為 inverse）；移除「揭示更深層連結」這類模板洞察的誇大描述 | B3 | 探針 P3 不再出現「飲料 is_a 咖啡」；不變式測試：反向邊的關係語意正確 | — | S |
| P0.7 | **提示與設定缺陷**：修正層級提示 f-string；驗證回傳數量（不足則重試或標記 `degraded`）；**讓伺服器實際讀取 `OLLAMA_BASE_URL`／溫度／逾時**（見 §9.3 新發現 N1） | B10、D8、N1 | 探針 P8、P16；測試：環境變數確實進入 `LLMConfig` | P0.1 | M |
| P0.8 | **協議與方法清單誠實化**：SCAMPER 協議的「臨床」改為 `domain` 參數；`select_method` 與 `list_methods` 只回報已實作的方法；未實作的方法回傳明確的 `not_implemented` | B8、B9 | 探針 P7、P11 翻轉；不變式測試：推薦的方法一律可執行 | P0.1 | S |
| P0.9 | **Spark-Soup 安全與搜尋**：改用 `ddgs` 或移除搜尋；失敗時在 `provenance.warnings` 明示；網頁碎片放進隔離區塊（標示不受信任、截斷、剝除指令句型） | B7、D4、C5 | 探針 P12b、P12c；測試：注入文字出現在隔離區塊內並附標註 | P0.1 | M |
| P0.10 | **實驗性標示**：多 Agent、對抗、圖譜、類比相關工具的描述加上 `[experimental]`，並說明其分數為啟發式（D-06 的前置步驟） | B5、B6、E3 | 工具描述與 README 如實；契約測試檢查描述含 `experimental` | P0.1 | S |
| P0.11 | **文件與依賴誠實化**：README／README.zh-TW 授權、斷鏈、架構圖與「16 種方法」說法；`ARCHITECTURE.md`；`ROADMAP.md` 現況；移除未使用的 `instructor`、`openai`、`langchain-community` 並更新鎖檔 | D9、E3 | 文件連結檢查通過；`uv sync --locked` 與全測試通過 | — | M |
| P0.12 | **測試重整**：為 15 個無斷言的測試補上不變式斷言；常數斷言改為不變式；把 P0 範圍的探針轉成 `tests/` 回歸測試 | E1 | AST 稽核：無斷言的測試數＝0；對應探針翻轉 | P0.1–P0.9 | M |
| P0.13 | **`cgu*` 的 MCP 設定整理**：`.vscode/mcp.json`、`mcp-config/*` 中 CGU 條目改用 `passthrough`，修正 `OLLAMA_BASE_URL` 的 `/v1` 後綴；**不動其他 server 的條目** | N1、D9 | 設定檢查；不影響 `asset-aware-mcp` 等其他條目 | P0.2、P0.7 | S |

**G0 發版**：`CHANGELOG.md` 以「BREAKING（誠實化）」標示輸出契約變更並說明遷移方式；通知上層 med-paper-assistant 的 integration lock。

### 6.2 P1 地基（v0.8.0）

| ID | 工作 | 缺陷 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|---|
| P1.1 | **分層重構**：建立 `domain／application／infrastructure／interfaces/mcp／experimental`；`server.py` 縮減為註冊；舊引擎移入 `experimental/`（D-06）；舊工具名稱保留一個小版本的別名（D-05） | D5、D6 | 規則測試：domain 不 import infrastructure；`server.py` < 200 行；全部既有 smoke 測試通過 | G0 | L |
| P1.2 | **Provider 埠**：`LLMPort`、`EmbeddingPort`、`RetrievalPort`；passthrough 預設；Ollama 為可選 adapter（D-02：本地生成僅供驗證 H3）；設定物件依請求注入 | D8、C3 | 契約測試：各 adapter 可替換；無任何模組在 import 時讀環境變數 | P1.1 | M |
| P1.3 | **Archive**：SQLite repository 儲存 sessions、ideas、evaluations、feedback；含 migration、匯出與刪除；`session_id` 全面落實 | D2、D3 | 重啟後狀態保留；匯出／刪除測試；多 session 隔離測試 | P1.1 | L |
| P1.4 | **Measure（基礎版）**：重複偵測（MinHash 或 n-gram）、新穎度向量（各分量可為 `null`）、Vendi 多樣性、可選 embedding adapter（D-03）、成對評審的協議與資料結構（由呼叫端執行） | B1、A5、C1 | 新穎度回傳 `reference_set`、`method`、`calibrated`；缺參照集的分量為 `null`；探針 P1 的所有輸入皆行為正確 | P1.2 | L |
| P1.5 | **評估框架 `evals/`**：題庫（AUT、設計挑戰、研究發想；中英）、baseline BL0–BL3、等預算 token 記帳、多 seed、報告產生器；允許以手動貼入結果的方式接入強模型 | E2 | `uv run python -m evals.run --suite aut --seeds 3` 產出含信賴區間的報告；預算記帳正確；**評估只在手動或 nightly 執行，不進 CI hard gate（D-07）** | P1.2、P1.4 | L |
| P1.6 | **第一份 baseline 報告與人類校準協議**：現行 CGU 工具 vs. BL0–BL3；寫下評分者招募與評分流程 | E2 | 報告存入 `evals/reports/`，含負面結果；協議文件經你審閱 | P1.5 | M |

**G1**：見 §5.3。**注意**：評估若只有本機 3B 模型，不能代表強模型；報告必須註明模型與限制，並預留「手動貼入強模型結果」的路徑（風險 R1）。

### 6.3 P2 Harness 骨架（v0.8.0，與 P1 平行）

| ID | 工作 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|
| P2.1 | **可攜核心**：`plugins/cgu/plugin.json`（含 `$schema`）、`mcp.json`（`type: stdio`；過渡期用 `uvx --from git+…@<tag>`，因 PyPI 尚未發布，順序見 D-19；`CGU_LLM_PROVIDER=passthrough`）、`skills/`（把現有 `creative-ideation` 改寫成誠實版；其餘先放協議骨架） | 通過 plugin 與 mcp 的 JSON Schema 驗證；每個 `SKILL.md` frontmatter 合法 | G0 | M |
| P2.2 | **Copilot 延伸**：`com.github.copilot/agents/`（`creative-facilitator`、`independent-ideator`、`adversarial-critic`、之後 P3 的 `frame-auditor`），皆為薄包裝並指向 skills；**plugin 與開發用 `.claude/skills/` 分離，見 D-17** | agent frontmatter 驗證；內容不得重複 skills 的協議 | P2.1 | M |
| P2.3 | **Codex 延伸**：`plugin.json` 的 `extensions.com.openai`；consumer 用的 `AGENTS.md` 指示片段（D-16）；文件列出 Codex 端與 Copilot 端的行為差異（agents 不可攜 → 以 skill 提供） | schema 驗證；差異表經你審閱 | P2.1 | S |
| P2.4 | **Marketplace**：`.github/plugin/marketplace.json`、`.agents/plugins/marketplace.json`，皆指向 `plugins/cgu`（D-18：暫不含 Claude 格式） | 兩個檔案格式正確、`source` 路徑可解析 | P2.1 | S |
| P2.5 | **本機驗證工具與 CI**：把 plugin／mcp schema 下載後放進 repo 並釘版本；SKILL.md 與 `.agent.md` frontmatter lint；路徑逃逸檢查（檔案必須落在 plugin 根目錄內）；以 plugin 的 `mcp.json` 啟動 stdio 並列出工具（沿用既有煙霧測試）；`uvx --from git+…` 解析測試 | CI 新增 `plugin-validate` 工作且為 hard gate | P2.1 | L |
| P2.6 | **人工安裝驗證清單與紀錄**：Copilot CLI（`copilot plugin install ./plugins/cgu`、`/plugin list`、`/skills list`、`/agent`）、VS Code（Chat: Open Customizations）、Codex（`codex plugin marketplace add`）；每項記錄日期、版本、結果 | 至少一個 Copilot 客戶端有成功紀錄；其餘標示「未驗證」而非「支援」 | P2.2–P2.4 | M |
| P2.7 | **plugin 安全審查**：確認不附 hooks（D-20）；MCP 預設不連網、不呼叫本機模型；環境變數與資料目錄（`${PLUGIN_DATA}`）處理；對使用者說明信任提示 | 審查記錄入 `docs/`；使用者文件含風險說明 | P2.1 | S |

**G2**：見 §5.3。

### 6.4 P3 哲學層（v0.9.0）

| ID | 工作 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|
| P3.1 | **Frame 領域模型與存檔**：Frame、Assumption（`core`／`belt`）、Concept、Metaphor、Criterion、Hinge、Stakeholder；父子譜系與所用算子；JSON Schema；archive 表。數值欄位（承重度、不確定度）必須標示估計者與方法，並標為未校準（C1 原則） | 不變式測試：每個子框架都能追溯到父框架與算子；數值欄位缺 `method` 時拒絕寫入 | G1 | M |
| P3.2 | **框架算子**（**多傳統，每個都須通過提問品質閘門與至少一次實驗，否則下架——D-12**）：`explicate`（從典型答案溯因）、`bracket`、`negate`、`tetralemma`、`re_explicate`、`swap_metaphor`、`recut_unit`、`shift_stakeholder`、`invert_criterion`、`genealogize`、`thought_experiment`。每個算子有「算子卡」（來源、護欄、輸入／輸出 schema）。passthrough 模式輸出工作單，provider 模式可直接執行 | 契約測試：輸出符合 schema；算子卡齊全（來源、護欄）；`genealogize` 必須附籬笆檢查欄位 | P3.1 | L |
| P3.3 | **懷疑的經濟學**：升級觸發條件（僵局、異常、衝突、高風險、使用者要求）、承重假設的優先度估計、停止條件（不再改變決策、預算用盡、滿意化）。以純函式實作，並明確標註優先度是**未校準的啟發式** | 單元測試涵蓋每種觸發與停止條件；預算用盡時回報「尚未檢驗的承重假設」清單 | P3.1 | M |
| P3.4 | **提問品質閘門**（哲學文件 §6.5；驗證方式依 D-14）：決策相關、可操作、承重、非口頭、非典型（加分項）五項判準；LLM 評審提示；人類校準集；以重排測試檢查「反事實依賴」 | 在人類校準集上，閘門與人類評分的一致性已量測並記錄；不達標時標為 experimental | P1.4、P3.1 | M |
| P3.5 | **哲學 skills 與 agent**（對話姿態依情境切換，D-13）：`frame-audit`、`maieutic-session`、`anti-typical-diverge` v1；Copilot 的 `frame-auditor` agent（唯讀、只提問與表徵）。skills 內必須寫明觸發條件與停止條件，避免無限追問 | skill lint 通過；以 3 個真實題目試跑並記錄「是否改變了決策」 | P2.1、P3.2、P3.3 | M |
| P3.6 | **同意與揭露政策**（D-08）：每次框架改寫都輸出「改了什麼、為什麼改、依據哪個算子」；改寫目標、利害關係人或評估準則時要求使用者同意 | 契約測試：未取得同意不得改寫受限元素；揭露欄位必填 | P3.1 | S |
| P3.7 | **實驗 H7、H8**：框架算子 vs. 反典型的 embedding 推離（H7）；通過閘門的哲學提問 vs. 未篩選的「深刻提問」（H8）。使用 P1 評估框架，等預算比較 | 兩份報告（含信賴區間與負面結果）；每個算子有保留／下架決定 | P3.2、P3.4、P1.5 | L |

**G3**：見 §5.3。

### 6.5 P4 創意機制（v0.10.0）

| ID | 工作 | 驗證假設 | 依賴 | 大小 |
|---|---|---|---|---|
| P4.1 | **反典型算子**：對負責生成的模型取典型答案集 M（依主題與模型快取）；門檻 τ 以實驗校準；可選語言化取樣 | H1 | G3、P1.4 | M |
| P4.2 | **獨立 context 扇出**：passthrough 模式產生「取樣計畫」（不同提示、素材或模型）由呼叫端以子 agent 執行；provider 模式可平行執行 | H3 | P4.1 | L |
| P4.3 | **素材檢索（距離帶）**：Wikipedia／Wikidata／PubMed 等 adapter；每個碎片附出處並套用隔離區塊；距離以 embedding 量測。ConceptNet 公開 API 自 2025-11 回報故障，**不作為預設** | H2 | P1.2、P0.9 | L |
| P4.4 | **品質多樣性搜尋**：MAP-Elites 骨架；格子維度依 D-11 為「被改寫的框架元素 × 距離帶」；以 SCAMPER、TRIZ、類比、假設反轉為突變算子；成對評審決定替換；譜系保存 | H4 | P4.2、P3.2 | L |
| P4.5 | **類比管線**：圖式抽取 → 抽象化 → 檢索 → 映射表＋候選推論 → 一對一與系統性檢核 → 評估 | 併入 H4／H7 的比較 | P4.3 | L |
| P4.6 | **附證據的批判者**：批判先檢索既有成果；可行時改用不同家族的模型（**「是否能指定 agent 使用的模型」尚未查證**，見 §9.2） | 併入 H6 | P4.3 | M |
| P4.7 | **成對評審錦標賽**：跨模型、交換位置、非補償式可行性門檻、輸出 Pareto 前緣（取代加權總分） | H6 | P1.4 | M |

**G4（停損關卡）**：見 §5.3。**這是整個計畫最重要的關卡**：若證據顯示「增強生成」不划算，P5 就以量測與回饋為主體，不再投入更多生成機制。

### 6.6 P5 人機回饋（v0.11.0）

| ID | 工作 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|
| P5.1 | **人先發想模式**（D-01：先建量測，再做對人的回饋）：收集使用者自己的點子與背景（取得同意）；分析覆蓋地圖；agent 只補空白，並以「距離」搭配有用性門檻衡量貢獻 | 測試：agent 的提案與使用者點子的重疊率可量測；沒有使用者點子時退回一般模式 | G4、P1.3 | M |
| P5.2 | **點子卡**：推導路徑、操作類型與被改寫的框架元素、素材出處、新穎度向量與其參照集、主要風險、最小驗證、決定欄位（採用／修改／放棄＋理由） | 快照測試；所有欄位都可回溯到 provenance | P3.1、P1.4 | M |
| P5.3 | **回饋收集與回流**：記錄採用、修改、放棄與理由標籤；可匯出與刪除（D-09）；回流成評審權重的訊號 | 隱私測試：預設不上傳；刪除後無殘留 | P1.3、P5.2 | M |
| P5.4 | **個人化與多樣性下限**：依回饋調整評審權重，但保留最低比例的「偏離你偏好」的候選，避免同溫層 | 測試：個人化後的候選集多樣性不低於下限 | P5.3 | M |
| P5.5 | **實驗 H5、H9**：人先發想 vs. agent 先給（H5）；產婆式 vs. 答案式對之後無輔助表現的影響（H9）。**H9 的先驗並不樂觀**（Kumar et al. 2025 的教練式組別未優於對照組），須準備好接受否定結果 | 實驗設計與倫理說明經你審閱；結果入報告 | P5.1–P5.4 | L |

**G5**：見 §5.3。

### 6.7 P6 驗證與 1.0（v1.0.0）

| ID | 工作 | 驗收 | 依賴 | 大小 |
|---|---|---|---|---|
| P6.1 | **宣稱對照證據的審計**：列出 README、工具描述、skills 中的每一條對外宣稱，逐條指到報告或測試；沒有證據的移除或標為實驗性 | 審計表入 `docs/`；G6 通過 | G5 | M |
| P6.2 | **文件與多語**：README（英／繁中）、使用者指南（plugin 安裝、Copilot／Codex 差異、隱私）、開發者指南 | 文件連結與範例可執行 | P6.1 | M |
| P6.3 | **發布**（順序依 D-19：git tag → PyPI → 公共 marketplace）：PyPI；plugin 的 `mcp.json` 改為 `uvx creativity-generation-unit`；提交至公共 marketplace（例如 Awesome Copilot）；v1.0.0 tag 與 GitHub Release | 乾淨環境安裝測試通過；上層 integration lock 已更新 | P6.2 | M |
| P6.4 | **回顧**：記錄估計偏差、被否決的方向、保留的算子與證據 | 回顧文件入 Memory Bank | P6.3 | S |

---

## 7. 長任務治理

### 7.1 完成定義（DoD）：每個工作包都必須滿足

審查 E2 指出：過去「完成」只等於「程式存在」。因此 DoD 要求**行為證據**：

1. **不變式測試**：對應的缺陷或需求有回歸測試，斷言行為而非常數（例如「重複的想法不得判為新穎」，而不是「某輸入回傳 0.95」）。
2. **探針翻轉**：若該工作包修正的是已知缺陷，對應探針的結果已翻轉；探針隨後轉成測試。
3. **誠實輸出**：新增或修改的輸出都含 `provenance`；沒有測量程序的數字不得出現。
4. **成熟度標示**：工具與 skill 的描述標明 `stable`／`heuristic`／`experimental`。
5. **品質閘門**：`ruff check src tests`、`ruff format --check src tests`、`pytest` 全綠；涉及 plugin 的工作包再加 `plugin-validate`。
6. **Memory Bank**（憲法第 4–5 條）：更新 `progress.md`（工作包狀態）與 `activeContext.md`（下一步）；有重大決策時寫入 `decisionLog.md`。
7. **文件**：直接相關的文件已同步（憲法第 6 條）。

### 7.2 分支、提交與發版

- **階段分支** `phase/<n>-<name>`；每個工作包至少一個提交，訊息採 Conventional Commits，並附 `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`。
- 階段結束且通過關卡後合併到 `master`，再打 tag（`v0.7.0` 等）。0.x 階段允許破壞性變更，但必須在 `CHANGELOG.md` 標示並說明遷移。
- **未經你同意，不會 push、不會建立 tag 或 Release。** 目前 `v0.6.0` 也還沒有 tag。
- 影響上層 med-paper-assistant 的變更（輸出契約、工具名稱）在發版前先通知，並在 integration lock 中固定版本。

### 7.3 追蹤

| 內容 | 位置 |
|---|---|
| 計畫（穩定） | 本文件 |
| 工作包狀態（待辦／進行中／審查中／完成）與估計偏差 | `memory-bank/progress.md` |
| 下一步與阻塞 | `memory-bank/activeContext.md` |
| 決策與否決理由 | `memory-bank/decisionLog.md` |
| 實驗報告 | `evals/reports/`（P1 起） |
| 單次 session 內的細項 | session 資料庫（只在該 session 有效，不作為跨 session 紀錄） |

### 7.4 變更控制

- **否決或修改預設決策**：更新 §4 的對應列，並在 `decisionLog.md` 記錄原因；依「若否決」欄重排受影響的工作包。
- **範圍增加**：新工作必須指出它提供 I／C／S／M 哪一項，或對應哪個缺陷；否則不進計畫。
- **停損**：G4 是預先登記的轉向條件，結果出來之前不得修改門檻。

---

## 8. 驗證策略

### 8.1 本機可驗證（進 CI）

| 項目 | 方式 |
|---|---|
| plugin 結構 | 對釘版的 Agent Plugins 1.0 `plugin.schema.json` 與 `mcp.schema.json` 做 JSON Schema 驗證 |
| skills、agents | frontmatter lint（`name`、`description` 必填；`skills/` 只能是直接子目錄且含 `SKILL.md`） |
| 路徑邊界 | 所有檔案必須落在 plugin 根目錄內，且不得用 symlink 逃逸（標準的套件邊界規則） |
| MCP 啟動 | 以 plugin 的 `mcp.json` 啟動 stdio，列出工具並呼叫（沿用既有的 direct／stdio／wheel 煙霧測試） |
| 輸出契約 | 每個工具的 `provenance` 契約測試；數值欄位必須有 `method`；passthrough 下 LLM 呼叫數為 0 |
| 架構規則 | domain 不依賴 infrastructure 的 import 規則測試 |
| 缺陷回歸 | 探針轉成的不變式測試 |

### 8.2 需人工驗證（不進 CI）

| 項目 | 原因 | 紀錄方式 |
|---|---|---|
| Copilot CLI／VS Code 實際安裝與載入 | 本機沒有 `copilot` CLI；VS Code 內的載入需人工操作 | P2.6 的驗證清單，附日期、版本與結果 |
| Codex 安裝與 marketplace | 本機沒有 `codex` CLI | 同上；沒有環境就標「未驗證」 |
| 創意品質 | 需要評審與人類評分；依 D-07 只在手動或 nightly 執行 | `evals/reports/` |
| 對人的效果（H5、H9） | 需要人類受試者與倫理考量 | P5.5 的實驗設計文件 |

### 8.3 「未驗證」的處理原則

任何尚未驗證的相容性，在文件與 marketplace 描述中一律寫「未驗證」，不寫「支援」。這與計畫的核心原則一致：**沒有測量程序的宣稱不得輸出**。

---

## 9. 風險、開放問題與未查證事項

### 9.1 風險登記

| ID | 風險 | 影響 | 緩解 |
|---|---|---|---|
| R1 | 本機 3B 模型不代表強模型；評估結論可能不適用於 Copilot／Codex 背後的模型 | 高 | 評估框架支援手動貼入強模型結果；報告必須註明模型與限制 |
| R2 | Agent Plugins 1.0 才發布不久，欄位與慣例可能調整 | 中 | schema 釘版本；升版時走相容性檢查；只依賴標準中已定義的欄位 |
| R3 | plugin 內的 hooks 與 MCP 會執行本機程式碼 | 高 | 預設不附 hooks（D-20）；MCP 預設 passthrough；安全審查（P2.7） |
| R4 | 破壞性的輸出契約變更影響上層 med-paper-assistant | 中 | 發版前通知；別名保留一個小版本；integration lock 固定版本 |
| R5 | 哲學層流於裝飾：聽起來深刻，卻不改變決策 | 高 | 提問品質閘門（P3.4）；每個算子都要有實驗結果；G3、G4 的下架機制 |
| R6 | passthrough 的結果取決於呼叫端模型的品質與隨機性 | 中 | provenance 記錄模型與 seed；結論標明「依賴呼叫端」 |
| R7 | LLM 評審有自我偏好、位置與冗長偏誤 | 中 | 跨模型、交換位置、人類校準（D-10） |
| R8 | Copilot 與 Codex 對 agents、hooks 的支援持續分歧 | 中 | 方法論放在可攜的 skills；agents 只做薄包裝 |
| R9 | 根目錄 `AGENTS.md` 與 Asset-Aware 擴充套件互相覆蓋 | 低 | D-16：不覆寫；提供可複製片段 |
| R10 | 本機沒有 CLI，無法自動驗證安裝 | 中 | §8.2 的人工驗證；未驗證不宣稱支援 |
| R11 | 範圍蔓延：計畫涵蓋面廣，容易同時做太多 | 高 | 階段關卡；一次只做一個階段；範圍變更需過 §7.4 |

### 9.2 尚未查證的事項（會在對應工作包中查證）

| 事項 | 影響的工作包 |
|---|---|
| Codex 是否支援自訂 agent 或 subagent，以及格式 | P2.2、P2.3、P4.2 |
| Copilot 自訂 agent 是否能在 frontmatter 指定模型（影響「跨家族批判者」是否可行） | P4.6 |
| Copilot 與 Codex 的 hooks 檔案格式細節 | 若日後要附 hooks（D-20） |
| VS Code 是否會自動發現 repo 內的自訂 marketplace，或需要額外設定 | P2.4、P2.6 |
| 公共 marketplace（例如 Awesome Copilot）的收錄條件 | P6.3 |
| `${PLUGIN_DATA}` 在各客戶端的實際路徑與持久性（影響 archive 預設位置） | P1.3、P2.7 |

### 9.3 本輪新發現

**N1（伺服器忽略 `OLLAMA_BASE_URL`、溫度與逾時）【程式碼】**：[`server.py`](../src/cgu/server.py#L73) 以 `LLMConfig(model=OLLAMA_MODEL)` 建立設定，所以只有模型名稱會被採用；`get_llm_config()` 雖讀取 `OLLAMA_BASE_URL`、`OLLAMA_TEMPERATURE`、`OLLAMA_TIMEOUT`，但伺服器路徑從未呼叫它。另外 README 與 `.vscode/mcp.json` 都建議把 `OLLAMA_BASE_URL` 設成帶 `/v1` 後綴，這對 LangChain `ChatOllama` 的原生 API 並不正確。已納入 P0.7 與 P0.13。

### 9.4 開放問題（需要你的意見，但不阻擋 P0 開工）

1. **D-15**：plugin 預設改為 passthrough 是 0.x 內的破壞性變更；你是否同意在 v0.7.0 公告？
2. **P1.5** 的強模型 baseline：你願意在哪些模型上手動跑（例如 Copilot 背後的模型）？這決定報告的代表性。
3. **P1.6／P5.5**：人類評分者與受試者的來源與倫理流程（是否需要機構審查）。
4. **D-04**：醫學研究發想若作為第二個垂直領域，是否要與 PubMed Search／MedPaper 工具鏈整合？

---

*本計畫是活文件：決策變更與範圍調整依 §7.4 處理；執行狀態不寫在本文件，而是寫在 `memory-bank/progress.md`。*



