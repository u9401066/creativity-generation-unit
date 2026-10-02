# Creativity Generation Unit (CGU)

> 給 LLM agent 用的「誠實創意鷹架」：MCP server（SDK 2）加上可攜的 Agent Plugin。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MCP SDK](https://img.shields.io/badge/MCP_SDK-2.x-green.svg)](https://modelcontextprotocol.io/)

🌐 [English](README.md)

> **v0.8.0 是不相容的重寫。** 舊的 24 個工具（`generate_ideas`、`spark_collision`、`deep_think` …）已移除，沒有別名。請見 [從 0.6 遷移](#從-06-遷移)。

## 為什麼

LLM 本來就會腦力激盪。它單靠自己做不到的，是腦力激盪「周邊」的那些事：

| LLM 不擅長 | CGU 提供 |
|---|---|
| 察覺自己問題裡的隱性假設 | **框架物件**與 11 個哲學算子（括號、否定、闡明、系譜…），受限元素須經同意 |
| 跳出典型答案 | **反典型發散**：先寫出典型答案集，再往外生成 |
| 「平行」點子之間真正獨立 | **fan-out 工單**：每個點子在獨立 context 產生，而不是同一個 context 裡的角色扮演 |
| 知道點子是否真的新 | **附參照集的測量**：新穎度永遠是相對的，附方法與 `reference_size`；沒量就是 `null` |
| 不帶偏見地評審 | **盲評成對比較，AB／BA 兩種順序**，Wilson 區間，回報位置偏誤 |
| 長流程中記得狀態 | **狀態**：SQLite session、框架譜系、點子庫、判決、回饋 |
| 誠實說出沒做到的事 | **每個結果都帶 provenance**：引擎、降級旗標、警告、seed、版本 |

CGU **不假裝自己有創意**。預設（`CGU_PROVIDER=passthrough`）它**完全不呼叫 LLM**：只回傳「工單」給你正在使用的模型，再對回來的內容做驗證、保存、測量與隔離。數字只由程式產生，每個浮點數都放在會註明方法的 `Measurement` 裡。

## 安裝

需求：[`uv`](https://docs.astral.sh/uv/)（提供 `uvx`）、`git`、首次啟動可連到 GitHub。首次啟動要從 git 建置套件，約需一分鐘；之後有快取。

### GitHub Copilot CLI

```shell
copilot plugin marketplace add u9401066/creativity-generation-unit
copilot plugin install cgu@creativity-generation-unit
```

用 `copilot plugin list` 確認，進入對話後請它呼叫 `cgu_status`。也可從本機 clone 安裝：`copilot plugin install ./plugins/cgu`（Copilot CLI 已標示直接以本機路徑安裝將被棄用，未來以 marketplace 為主）。

### VS Code（GitHub Copilot）與 Codex

**Codex CLI**（已在 Codex CLI 0.160.0 驗證安裝與 MCP 註冊；**完整的模型對話未驗證**，因為需要登入）：

```shell
codex plugin marketplace add u9401066/creativity-generation-unit
codex plugin add cgu@creativity-generation-unit
codex mcp list    # 應看到 cgu server
```

**VS Code** 實作同一個 [Agent Plugins 1.0](https://agent-plugins.org) 標準（Copilot 讀 `.github/plugin/marketplace.json`）。把本 repo 加為 plugin marketplace 再安裝 `cgu`；選單名稱依客戶端版本而異。**VS Code 我們尚未實測。** 細節見 [plugins/cgu/README.md](plugins/cgu/README.md)。

### 任何 MCP 客戶端（只有 server，沒有 skills）

```json
{
  "mcpServers": {
    "cgu": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/u9401066/creativity-generation-unit@master", "cgu-server"],
      "env": { "CGU_PROVIDER": "passthrough" }
    }
  }
}
```

從 clone 執行：`uv sync` 後 `uv run cgu-server`；`uv run cgu doctor` 會列出目前可用的能力。

## Plugin 內容

| Skill | 何時用 |
|---|---|
| `creative-ideation` | 「幫我發想」「卡住了」：框架 → 典型答案 → 算子 → 發散 → 測量 → 評審 → 點子卡 |
| `frame-audit` | 「我們問對問題了嗎？」：隱性假設、概念邊界、準則系譜、提問品質閘門 |
| `maieutic-session` | 「不要直接給答案，引導我」：人產出，AI 只提問 |
| `idea-triage` | 「幫我比較這幾個點子」：測量＋盲評成對比較＋點子卡 |

Copilot 另有四個薄包裝 agent（`creative-facilitator`、`frame-auditor`、`independent-ideator`、`adversarial-critic`）。**刻意不附 hooks**（不可攜，且會執行本機程式碼）。

## 10 個工具

| 工具 | actions | 用途 |
|---|---|---|
| `cgu_status` | | 現在有什麼能力（provider、embedding 是否 `semantic`、各工具成熟度） |
| `cgu_session` | open, get, list, export, delete | session 生命週期；`delete` 需 `confirm=true`，不留殘餘 |
| `cgu_frame` | create, get, operators, operate, commit, doubt | 框架物件、11 個算子、譜系、懷疑的經濟學 |
| `cgu_material` | search, add, list | 前人研究與素材；不受信任文字會被隔離並剝除指令句型 |
| `cgu_diverge` | typical_set, anti_typical, fanout, collide | 發散工單；獨立性是被明說的，不是被假設的 |
| `cgu_ideas` | add, list, measure | 點子庫、重複偵測、附參照集的新穎度／多樣性 |
| `cgu_judge` | plan, record, rank | 兩種順序的成對評審、Wilson 區間、Pareto 前緣 |
| `cgu_evolve` | map, next, submit, resolve | 利基地圖與突變工單，含 A/B 順序控制 |
| `cgu_feedback` | record, summary, export, delete | 人類實際拿這些點子做了什麼 |
| `cgu_question_gate` | check, record | 花力氣之前先過問題品質閘門 |

每個工具都回傳 `ToolResult{ok, data, work_order, work_orders, provenance, error}`；領域錯誤是 `ok=false`，不丟例外。另提供 5 個 resources（`cgu://methods/*`、`cgu://operators`、評分準則、觸發問句）與 4 個 prompts，給不支援 skills 的客戶端。完整契約：[docs/architecture.md](docs/architecture.md)。

### 範例（醫療商品開發）

> 「我們是 8 人新創，想做居家照護產品降低出院後 30 天再入院。不要再給我血氧穿戴加 App。」

裝了 plugin，中階模型會先開 session，寫出 8 個典型答案，抽出共同的隱性假設（居家量測 → 警示 → 有人處置），再用算子改寫其中三個，例如把「警示就是產品」否定成「產品是『誰在 SLA 下承接警示』」。接著把每個改寫獨立展開成點子卡：付費者與使用者、法規等級（標明為推測，須向主管機關確認）、所需驗證、最便宜的 MVP，並附推導路徑（典型答案 → 假設 → 算子 → 框架 ID）。

## 設定

| 變數 | 預設 | 說明 |
|---|---|---|
| `CGU_PROVIDER` | `passthrough` | `passthrough` 回傳工單；`ollama` 啟用 `cgu_diverge` 的選用執行模式 |
| `CGU_DATA_DIR` | `$PLUGIN_DATA`，否則 `~/.cgu` | SQLite 位置（`cgu.sqlite3`，WAL） |
| `CGU_EMBEDDING` | `auto` | `auto`／`ollama`／`ngram`。沒有 Ollama 時新穎度只是**詞面**相似（`semantic=false`） |
| `CGU_OLLAMA_URL` | `http://localhost:11434` | 不要加 `/v1` |
| `CGU_OLLAMA_MODEL` | `qwen2.5:3b` | 僅執行模式 |
| `CGU_EMBED_MODEL` | `nomic-embed-text` | |
| `CGU_NETWORK` | `on` | `off` 會停用 `cgu_material(search)`（回報 `degraded`） |
| `CGU_LOG_LEVEL` | `INFO` | 日誌只寫 stderr；stdout 保留給 MCP stdio |

## 架構

```
src/cgu/
├── domain/          純規則：Measurement、框架、算子、懷疑、隔離、評審（無 I/O）
├── application/     ports（Protocol）＋每個工具的 service
├── infrastructure/  SQLite、embedding、檢索、選用 LLM、Settings
└── interfaces/      mcp/（SDK 2 server、tools、resources、prompts）與 cli
```

依賴方向由測試強制（domain 不得 import 其他層，也不得用 `httpx`／`sqlite3`）。

## 誠實的限制

- 新穎度是**相對於明確參照集**的測量；用 n-gram 後備時，換句話說的重複偵測不到。
- 啟發式數值（優先度、多樣性、勝率）**未校準**。LLM 評審帶有評審模型的偏誤；順序不一致會被回報。
- 「哲學式框架審查能提升創意」「產婆模式保住人的原創性」是**待驗證的假設**，不是結論。
- skills 的效果取決於客戶端模型是否照流程執行；中階模型可能漏步驟。
- 依設計，創意討論本身不設倫理閘門；下游法規（醫療器材、個資、院內規範）以「每張點子卡上的風險欄位」呈現，而不是過濾條件。

## 證據

<!-- EVIDENCE:START -->
我們做了一個隔離式的 Copilot CLI 實驗（真的安裝 plugin；中階模型 `claude-sonnet-5.5`、`gpt-6-luna`；研究創意、醫療商品、行政流程題；`gpt-6-sol` 與 `claude-sonnet-5.5` 兩種順序盲評）。完整整理：[evals/reports/SUMMARY.md](evals/reports/SUMMARY.md)。

**能說與不能說**

- plugin **沒有顯示出整體勝過直接提問。** 相對 baseline 的格子層級勝率：27%（exp1，v1）、25%（exp2，v2）、50%（exp3，v3：1 勝 1 負 4 平）。所有 95% 區間都跨過 50%，誠實的讀法是「無法區分」，v1、v2 的點估計偏不利。
- 它**穩定地改變答案的樣貌**：三輪中新穎度（75–96%）與問題框架重寫（75–96%）都被明顯偏好。
- v1、v2 在實用性與可決策性上被扣分（17–38%）。評審自己寫的理由是：工具內部用語混進答案，以及把繼續／放棄門檻留成「待估」。v3 修了這兩件事（白話輸出、具體可調整的門檻）後，可決策性由約 36% 升到 79%，實用性由約 19% 升到 38%，代價是新穎度優勢縮小。**v3 只有 6 格，且評審順序一致率不穩定。**
- 我們的一個假設被證偽：加上限制清單與可行性閘門（v2）並沒有補回實用性。
- 成本：時間約 2–5 倍、輸入 token 約 4–40 倍（多為快取）。
- 自動觸發不穩定：不改提示時，12 格中有 9 格實質使用了 CGU 工具（Sonnet 3/6、luna 6/6）。
- 只有 LLM 評審、沒有人類校準、樣本很小；v2、v3 是依評審理由調整的，可能部分迎合了 LLM 評審。這不是對 SOTA 模型的結論。
<!-- EVIDENCE:END -->

## 開發

```shell
uv sync --extra dev
uv run pytest
uv run ruff check src tests evals && uv run ruff format --check src tests evals
uv run mypy src
```

Windows 上若有編輯器啟動的 `cgu-server.exe` 在執行，會鎖住 `.venv`。請改用獨立環境：`$env:UV_PROJECT_ENVIRONMENT = "$env:TEMP\cgu-venv"`。

## 文件

| 文件 | 內容 |
|---|---|
| [docs/architecture.md](docs/architecture.md) | v0.8.0 契約：工具、型別、持久化、SDK 2 備註 |
| [docs/critical-review-and-improvement-plan.md](docs/critical-review-and-improvement-plan.md) | 0.6 的 40 個缺陷與改進計畫 |
| [docs/philosophical-inquiry-and-creativity.md](docs/philosophical-inquiry-and-creativity.md) | 哲學作為後設審查：框架、算子、懷疑的經濟學 |
| [docs/program-plan.md](docs/program-plan.md) | 階段、工作包、關卡、決策 |
| [evals/README.md](evals/README.md) | 效果實驗協定 |
| [plugins/cgu/README.md](plugins/cgu/README.md) | Plugin 安裝、可攜性、隱私 |
| [CHANGELOG.md](CHANGELOG.md) | 版本紀錄 |

## 從 0.6 遷移

| 0.6 | 0.8 |
|---|---|
| `generate_ideas`、`deep_think`、`multi_agent_brainstorm`、`spark_soup_quick` | `cgu_diverge` ＋ 你的模型生成 ＋ `cgu_ideas` |
| `spark_collision`、`spark_collision_deep`、`find_connections`、`suggest_bridges` | `cgu_diverge(action=collide)` |
| `spark_soup_*`、`collect_creativity_fragments`、`explore_concept`、`random_concept`、`associative_expansion` | `cgu_material` |
| `check_novelty`、`evaluate_brainstorm_ideas` | `cgu_ideas(action=measure)`、`cgu_judge` |
| `evolve_idea_tool` | `cgu_evolve` |
| `creativity_session_*` | `cgu_session`、`cgu_ideas` |
| `apply_method`、`select_method`、`list_methods`、`brainstorm_protocol`、`get_trigger_words` | `cgu://methods/*` resources、prompts、skills |
| `CGU_LLM_PROVIDER`、`CGU_USE_LLM`、`OLLAMA_BASE_URL` | 見[設定](#設定) |

## 授權

Apache-2.0。作者：u9401066 ＜u9401066@gap.kmu.edu.tw＞。
