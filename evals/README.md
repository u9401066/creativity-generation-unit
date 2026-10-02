# evals：CGU plugin 成對盲評框架

這個目錄量測一件事：**安裝 CGU plugin 之後，中階模型在「創意與哲學式探問」類任務上的答案，是否比沒有 plugin 時更好**。
它只回答「在這組題目與這批評審下，哪一種答案較常被偏好」，**不證明**更有創意（見〈限制〉與報告中的「這份結果不能說明什麼」）。

## 設計摘要

| 條件 | 內容 |
|---|---|
| `baseline` | 乾淨環境、不載入 plugin，直接給任務提示 |
| `plugin` | 載入 plugin（skills + `cgu` MCP），**提示與 baseline 完全相同**，看模型會不會自動使用 |
| `plugin_explicit` | 同上，但提示前多一句固定前綴：「請使用 `creative-ideation` skill 來處理以下需求。」 |
| `baseline_prompted`（選用，預設不跑） | 無 plugin，但前綴一句「多方探索、檢查隱性假設」的通用指示；用來檢驗 plugin 是否只是贏過「叫模型多想一點」 |

- **隔離**：每次呼叫都用全新的 `COPILOT_HOME` 與工作目錄，絕不碰你真正的 `~/.copilot`；`--no-custom-instructions`、`--disable-builtin-mcps`、`--no-auto-update`，並用 `--secret-env-vars` 讓 token 不進入模型可執行的 shell 與 MCP 環境。
- **工作目錄必須在 repo 外**：預設在系統暫存目錄。CLI 會從 cwd 往上找專案設定；實測在 repo 內執行時，repo 的 `.claude/skills/creative-ideation` 會以 `inherited` 來源被載入並**蓋掉** plugin 的同名 skill，baseline 也會被污染。`--work-root` 指在 repo 內會被拒絕。
- **盲評**：評審只看到「使用者需求」與兩份匿名答案（A/B）。每個 (題目, 模型) 兩種順序都評；兩個評審模型各評一次。答案裡出現的 `cgu*`、`creative-ideation` 字樣會先遮蔽並計數。
- **統計單位**：主要指標是「格子」層級（題目 × 生成模型 × 重複）。同一格的 4 次判斷（2 評審 × 2 順序）先合成一個勝／負／平，再算 Wilson 95% CI；位置偏誤因此會互相抵銷成平手。評審層級的 CI 只作輔助，因為同一格的判斷彼此相關，會高估精確度。
- **等預算**：保證同模型、同提示、同 reasoning effort、同逾時；**不**強制等 token（plugin 條件會多出 skill 載入與工具往返）。報告列出各條件的 token、秒數與 premium requests，請對照解讀。

## 前置條件

1. Copilot CLI（預設找 `%TEMP%\cgu-copilot\node_modules\.bin\copilot.cmd`，否則用 PATH 上的 `copilot`；可用 `COPILOT_BIN` 覆寫）。
2. 認證：設定 `COPILOT_GITHUB_TOKEN`，或已執行 `gh auth login`（會用 `gh auth token`）。
3. `uv`（plugin 條件預設以 `uv --directory <repo> run cgu-server` 啟動本機 MCP）。
4. `plugins/cgu` 存在。

> **重要（CLI 1.0.91 實測，2026-10-03 更正）**：plugin 根目錄的 **`mcp.json` 會被直接載入**（`session.mcp_servers_loaded` 顯示 `source=plugin`、`status=connected`），不需要 `.mcp.json`；先前「只有 `.mcp.json` 才會載入」的說法是錯的。`--mcp-dotfile-shim` 保留給舊版 CLI，預設關閉。每個儲存格都會記錄 MCP 連線狀態，plugin 條件若沒連上 `cgu` 會在 meta 留下警告。

```powershell
$env:PYTHONUTF8 = '1'
```

以下指令都在 repo 根目錄執行；使用 `uv run --no-project` 是因為 evals 只用標準庫，不需要同步專案環境（同步會與正在執行的 MCP 伺服器互搶 `cgu-server.exe`）。

## 三個階段

### 0. 離線自我檢查（不連網、不花錢）

```powershell
uv run --no-project python -m evals.runner --dry-run
uv run --no-project python -m evals.judge --run-dir evals/runs/<dry-...> --dry-run
uv run --no-project python -m evals.aggregate --run-dir evals/runs/<dry-...> --reports-dir evals/runs/<dry-...>/reports
```

### 1. 產生（runner）

```powershell
# 煙霧測試：只跑 2 格
uv run --no-project python -m evals.runner --run-id smoke --limit 2 --models claude-sonnet-5.5 --conditions baseline,plugin

# 完整實驗：6 題 × 2 模型 × 3 條件 = 36 格
uv run --no-project python -m evals.runner --run-id exp1 --jobs 3
```

常用參數：`--models`、`--conditions`、`--tasks id1,id2`、`--domains medical_research`、`--repeats N`、`--jobs N`、`--timeout 秒`、`--retries N`、`--reasoning-effort`、`--mcp-source local|git`、`--uv-no-sync`、`--resume evals/runs/<id>`（續跑，略過成功格）、`--keep-work`（保留暫存工作目錄除錯）。

- `--mcp-source local`（預設）：複製 `plugins/cgu` 到暫存目錄，把 `cgu` server 改寫成 `uv --directory <repo> run cgu-server`，env `CGU_PROVIDER=passthrough`（同時設 `CGU_LLM_PROVIDER`）與每格獨立的 `CGU_DATA_DIR`；其他 server 條目不動。
- `--mcp-source git`：不改寫，使用 plugin 出貨的 `mcp.json`（例如 `uvx --from git+…`）。
- 啟動前會預檢本機 `cgu-server` 能否啟動（`--skip-mcp-check` 可略過）。實測常見失敗：`uv run` 要重裝套件，但 VS Code 正在執行的 `cgu-server.exe` 鎖住檔案；請關閉那些 MCP、先自行 `uv sync`，並加 `--uv-no-sync`。
- plugin 條件若 `cgu` MCP 沒有 `connected`，該格標記失敗（`cgu_mcp_not_connected`）並重試，不會悄悄變成第二個 baseline。

輸出：`evals/runs/<run-id>/<condition>/<model>/<task>/`（重複 k>0 時為 `<task>__r<k>`）

| 檔案 | 內容 |
|---|---|
| `answer.md` | 最終答案（最後一則沒有工具請求的 assistant 訊息） |
| `prompt.txt` | 實際送出的提示 |
| `events.jsonl` | CLI 的 JSONL 事件原文 |
| `otel.jsonl` | OTel 檔案匯出（token 用量來源） |
| `meta.json` | 狀態、耗時、退出碼、重試歷史、`cgu_tool_calls` 與工具分布、已觸發 skill、MCP 連線狀態、token 與 premium requests、警告、plugin 副本資訊 |

`run.json`（整批資訊）含 repo commit、plugin 目錄雜湊、CLI 版本、預檢警告。`meta.json` 的 `base_prompt_sha256` 在各條件間必須相同，可用來稽核「提示完全一致」。

meta 的 `warnings` 值得留意：`unexpected_skills_loaded:*`／`unexpected_mcp_servers_connected:*`（baseline 被污染）、`short_answer_with_files_created`（模型把答案寫進檔案而非回覆）、`no_otel_token_usage`。

### 2. 評審（judge）

```powershell
uv run --no-project python -m evals.judge --run-dir evals/runs/exp1 --jobs 3
```

- 預設配對 `baseline:plugin,baseline:plugin_explicit`（`--pairs` 可改，例如 `baseline:baseline_prompted`），評審模型 `claude-opus-5.5,gpt-6-sol`（`--judge-models`），兩種順序（`--orders`）。
- 開始前對每個評審模型做一次極短呼叫確認可用；不可用時依序嘗試備援（`claude-opus-5`→`claude-opus-4.8`、`gpt-6.1-sol`→`gpt-5.6-sol`），並把警告寫進 `judge_models.json` 與報告（`--skip-model-check` 略過）。
- 輸出必須是嚴格 JSON；解析失敗會帶著錯誤原因重試（`--max-attempts`，預設 3 次）。結果寫入 `judgments.jsonl`（附加式；重跑會略過已成功的項目）。
- 每筆含：各準則勝者（新穎度、實用性、問題框架重寫、可決策性）、總體勝者、一句理由、評審對「確定語氣但無法驗證」程度的評等、遮蔽次數、是否截斷、評審端工具呼叫數（應為 0）。
- 每份答案最多送 9000 字元（命令列長度限制），超過會截斷並記錄。

### 3. 彙整（aggregate）

```powershell
uv run --no-project python -m evals.aggregate --run-dir evals/runs/exp1
```

產生 `evals/reports/<UTC時間戳>.md` 與 `.json`（`--name` 可改檔名）。內容：整體與依模型／領域／評審的勝率與 Wilson 95% CI、順序一致率、位置偏誤、評審間一致率與 kappa、答案長度比與「較長者勝」比例、長度相近子集、準則別結果、條件洩漏檢查、各條件的工具使用／觸發率／成本，以及「限制」與「這份結果不能說明什麼」。`evals/reports/` 納入版控；`evals/runs/` 不納入。

## 成本與時間預期（完整矩陣：6 題 × 2 模型 × 3 條件）

| 階段 | CLI 呼叫數 | 備註 |
|---|---|---|
| 產生 | 36（+重試） | 每次約 30–120 秒；`--jobs 3` 約 15–25 分鐘 |
| 評審模型檢查 | 2 | 實測：`claude-opus-5.5`、`gpt-6-sol` 皆可用 |
| 評審 | 96 = 2 配對 × 12 (題×模型) × 2 順序 × 2 評審（+JSON 重試） | 每次約 15–90 秒 |
| 合計 | 約 134 | |

- 實測 `claude-opus-5.5` 每次呼叫計 **15 premium requests**（`result.usage.premiumRequests`），`claude-sonnet-5.5`、`gpt-6-sol` 為 1。完整評審約 48 次 opus 呼叫 ≈ 720 premium requests，是主要成本；想省錢可 `--judge-models gpt-6-sol,claude-sonnet-5.5`，但評審較弱，要在報告中註明。
- 每次 CLI 呼叫的固定開銷約 2 萬 token（CLI 系統提示與工具定義），plugin 條件再加上 MCP 工具定義。

## 新增題目

編輯 `evals/suites/domains.json`（或另建檔，用 `--suite` 指定）：

```json
{ "id": "ap-new-task", "domain": "admin_process", "prompt": "…使用者原話…", "context": "…選用背景資料…" }
```

- `id` 不可重複；`domain` 是自由字串（報告會依它分組）；`context` 會以「【背景資料】」區塊接在 `prompt` 後面。
- 提示請寫成真實使用者會說的話，要求具體、可決策的產出；**所有條件共用同一份提示**，不要為特定條件客製。
- 新增題目後先 `--dry-run` 驗證，再用 `--tasks 新題目id --limit 2` 做煙霧測試。

## 限制（請誠實面對）

- **樣本很小**：預設 6 題、每格只跑一次；CI 很寬。`--repeats` 只增加對「同題隨機性」的估計，不增加題目多樣性，且格子層級 CI 仍把重複當獨立樣本，偏樂觀。
- **LLM 評審**：與人類創意判斷的相關性未校準；可能偏好長答案、條列、自信語氣與同家族模型文風。已用雙順序、雙評審（Claude／GPT 各一）、長度比、長度相近子集與遮蔽檢查降低（非消除）。
- **匿名並不完美**：只遮蔽明顯的工具／skill 名稱；plugin 答案特有的行文痕跡仍可能洩漏條件。
- **刻意聚焦中階模型**：不能外推到旗艦模型或未測試的模型家族。
- **plugin 是否有被用到取決於模型**：`plugin`（自動）條件可能根本沒觸發 skill；請看報告的觸發率與 cgu 工具呼叫率。觸發率低時，`plugin` 與 baseline 的差異大多是雜訊。
- **事實未逐項查證**：評審只被要求懲罰「確定語氣但無法驗證」的主張。
- **非確定性**：模型輸出、MCP 啟動時間與 CLI 版本都會影響結果；`run.json` 記錄 commit、plugin 雜湊與 CLI 版本以便重現。
- 結論必須配合 CI 解讀：CI 跨越 50% 是「無法區分」，不是「沒有效果」；負面結果同樣寫入報告。

## Copilot CLI 1.0.91 事件結構備忘

`--output-format json` 輸出 JSONL，每行 `{type, data, id, timestamp, parentId, ephemeral?}`；結尾的 `result` 行為 `{type, sessionId, exitCode, usage:{premiumRequests, totalApiDurationMs, sessionDurationMs, codeChanges}}`。

- 最終答案：最後一則 `assistant.message` 且 `data.toolRequests` 為空的 `data.content`（子代理訊息帶 `parentToolCallId`，略過）。
- 工具呼叫：`tool.execution_start`（`toolName`、`arguments`；MCP 工具另有 `mcpServerName`、`mcpToolName`、`mcpConfigSource`）配 `tool.execution_complete`（`success`）。MCP 工具對模型的名稱是 `<server>-<tool>`，例如 `cgu-list_methods`。
- skill 呼叫：`toolName == "skill"`，`arguments.skill` 為名稱，`toolTelemetry` 帶 `skillSource`。`session.skills_loaded` 並不總是列出 plugin 的 skill（`--plugin-dir` 時實測缺席），不要靠它判斷 skill 是否可用。
- MCP 狀態：`session.mcp_server_status_changed`（`serverName`、`status`: pending/connected/failed…）與 `session.mcp_servers_loaded`（含 `source`: plugin/user/builtin）。
- 可用工具清單：`session.usage_checkpoint.data.promptCacheBreakState[].models.*.tools[].name`。
- token 用量：**事件流本身沒有**逐呼叫 token；以環境變數 `COPILOT_OTEL_FILE_EXPORTER_PATH` 啟用 OTel 檔案匯出，加總 `gen_ai.operation.name == "chat"` 的 span：`gen_ai.usage.input_tokens`、`output_tokens`、`cache_read.input_tokens`、`cache_write.input_tokens`、`github.copilot.cost`。
- 完整 schema：CLI 安裝目錄的 `pkg/win32-x64/<版本>/schemas/session-events.schema.json`。
- Windows 的 npm `.cmd` 殼層會破壞含換行與特殊字元的提示；runner 改以 `node …\@github\copilot\npm-loader.js` 直接啟動（已實測多行、`%`、引號、`&^|<>` 原樣傳遞）。

## 測試

```powershell
$files = (Get-ChildItem tests\test_evals*.py).Name | ForEach-Object { "tests/$_" }
uv run --extra dev python -m pytest @files -q
```

（PowerShell 不會替原生指令展開萬用字元，所以先列出檔案。若 `uv run` 因 `cgu-server.exe` 被佔用而同步失敗，改用 `uv run --no-sync python -m pytest @files -q`。）測試只用假後端與 `tests/fixtures/` 內錄製的真實事件，不連網。
