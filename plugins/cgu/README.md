# CGU plugin（Agent Plugins 1.0）

CGU v0.9.0 的可安裝套件：**5 個 skills ＋ 1 個 MCP server ＋（Copilot 專屬）4 個薄包裝 agents**。目標是讓中階模型在創意協作時先審查問題框架、再反典型發散、測量有明確參照的新穎度，並將自己的提問整理成可重用、可追溯的素材。MCP 不需另設 local LLM；思考由呼叫端 agent 的模型完成。

| Skill | 用途 | 觸發例 |
|---|---|---|
| `creative-ideation` | 主流程：框架 → 典型答案 → 算子 → 發散 → 測量 → 評審 → 點子卡 | 「幫我發想」「卡住了」 |
| `frame-audit` | 對問題框架做哲學式檢查（隱性假設、概念、準則系譜、提問品質閘門） | 「這問題問對了嗎？」 |
| `maieutic-session` | 產婆模式：人產出、AI 只提問 | 「不要直接給答案，引導我」 |
| `idea-triage` | 測量＋成對評審＋點子卡 | 「幫我比較這幾個點子」 |
| `inquiry-mining` | 提問主題、框架習慣、橋接與創意素材整理 | 「我最近都在問什麼」「從我的提問找靈感」 |

MCP server `cgu` 提供 11 個工具：`cgu_status`、`cgu_session`、`cgu_frame`、`cgu_material`、`cgu_diverge`、`cgu_ideas`、`cgu_judge`、`cgu_evolve`、`cgu_feedback`、`cgu_question_gate`、`cgu_inquiry`（見 repo 的 `docs/architecture.md`）。預設 `CGU_PROVIDER=passthrough`＋`CGU_EMBEDDING=ngram`：只回傳工單、保存狀態與量測，不探測模型。

## 安裝

需求：`uv`（提供 `uvx`）、`git`、可連到 GitHub 的網路（首次啟動會從 git 取得套件）。

**GitHub Copilot CLI**
```shell
copilot plugin marketplace add u9401066/creativity-generation-unit
copilot plugin install cgu@creativity-generation-unit
# 或從本機 clone 直接安裝：
copilot plugin install ./plugins/cgu
```
驗證：`copilot plugin list`；互動模式下 `/skills list`、`/agent`、`/mcp`。修改本機 plugin 後需重新 `copilot plugin install`（內容會被快取）。

**VS Code（GitHub Copilot）**：確認 `chat.plugins.enabled` 已啟用，從 plugin marketplace 加入 `u9401066/creativity-generation-unit`，或以 Command Palette 的 plugin 安裝指令從本機路徑 `plugins/cgu` 安裝。確切選單名稱隨 VS Code 版本而異。

**Codex**
```shell
codex plugin marketplace add u9401066/creativity-generation-unit
codex plugin add cgu@creativity-generation-unit
codex mcp list
```
已在 Codex CLI 0.160.0 實測：marketplace 可加入、plugin 為「installed, enabled」，`codex mcp list` 看得到 `cgu`（命令與環境變數正確，含 Codex 注入的 `PLUGIN_ROOT`／`PLUGIN_DATA`）。**未驗證**：實際的 Codex 對話中 skills 是否載入、工具是否被呼叫（該環境未登入）。若要在特定專案啟用，於該專案 `.codex/config.toml`：
```toml
[plugins."cgu@creativity-generation-unit"]
enabled = true
```

安裝後請 plugin 的 MCP server 先過一次 `cgu_status()`：能回傳版本與 `embedding.semantic`，代表伺服器可用。

## 可攜 vs. Copilot 專屬

| 元件 | 路徑 | Copilot CLI／VS Code | Codex／其他 Agent Plugins 客戶端 |
|---|---|---|---|
| 清單 | `plugin.json` | ✅ | ✅ |
| Skills | `skills/<name>/SKILL.md` | ✅ | ✅（方法論主載體） |
| MCP | `mcp.json`（`type: stdio`） | ✅ | ✅ |
| Agents（薄包裝） | `com.github.copilot/agents/*.agent.md` | ✅ | ❌（被忽略；同樣行為由 skills 提供） |
| 呈現資訊 | `plugin.json` 的 `extensions.com.openai.interface` | 忽略 | OpenAI 客戶端用於顯示 |
| Marketplace | `.github/plugin/marketplace.json`／`.agents/plugins/marketplace.json` | Copilot 讀前者 | Codex 讀後者 |

Plugin 不自動安裝 hooks。選用 Copilot 收集器請先安裝固定版本 CLI，查看內容後再自行啟用：

```shell
uv tool install git+https://github.com/u9401066/creativity-generation-unit@v0.9.0
cgu inquiry install-hook --print
cgu inquiry settings --enable --yes
cgu inquiry install-hook
```

重新開啟 Copilot CLI 後生效。Hook 主動累積使用者提問；agent 讀 `cgu_status.inquiry.maintenance`，待辦達門檻（預設 20 筆）時用 `cgu_inquiry(action=organize)` 取得一批提問，以自己的模型整理並用 `cgu_inquiry(action=distill)` 回交，再以 `cgu_inquiry(action=materials)` 取回。現有 hook 不含助理回覆，無 agent 時不自行整理；Codex／VS Code hook 尚未驗證。管理與移除方式見 [主 README](../../README.zh-TW.md#提問記憶與選用-hook)。

## 隱私

- 所有 session、框架、點子、判決、回饋與整理後的創意素材都存在**本機 SQLite**（`CGU_DATA_DIR`，預設 `~/.cgu`，不使用 `PLUGIN_DATA`）。CGU 預設不呼叫或探測本地模型，也沒有遙測。明確選用 embedding 時，送至設定的後端；呼叫端 agent 的模型與資料政策由客戶端決定。
- 但請注意兩件事：①你的對話與工單內容會被**你使用的客戶端模型**（Copilot、Codex 背後的服務）看到，這是客戶端本身的行為，不是 CGU 的；②`cgu_material(action=search)` 會把**查詢字串**送到 Wikipedia。設定 `CGU_NETWORK=off` 可關閉；關閉後該動作會回報 `degraded`。
- 刪除：`cgu_session(action=delete, session_id=…, confirm=true)` 清除該 session 全部資料；`cgu_session(action=export, session_id=…)` 可匯出。

## 選用同伴工具（不是必要）

若你的客戶端另外裝了 **PubMed Search MCP**（找 prior art）、**Zotero Keeper**（個人文獻庫）、**asset-aware-mcp**（PDF 證據段），skills 會建議使用；取回的文字**必須**先經 `cgu_material(action=add)` 才使用（才會被隔離、截斷、剝除指令句型），文獻摘要再登錄為 `cgu_ideas(action=add, kind=prior_art)`，CGU 才能以它計算新穎度並如實回報 `reference_size`。沒有這些工具時，skills 會明說「未做文獻比對」，不會編造。

## 誠實的限制

- 新穎度是**相對於明確參照集**的相似度測量；參照集為空時回傳 `null`（「未量測」）。沒有 Ollama 語意 embedding 時，只是**詞面（字元 n-gram）相似度**，換句話說的重複偵測不到。
- 所有啟發式數值（優先度、勝率、多樣性）都是**未校準**；LLM 評審依賴評審模型，勝率附 Wilson 區間，AB／BA 順序不一致會被回報。
- 「哲學式框架審查能提升創意」「產婆模式保住人的原創性」目前是**待驗證的假設**，不是已證實的結論。
- skills 的效果取決於客戶端模型是否照流程執行；中階模型可能漏步驟，請留意最終回覆的「限制聲明」是否完整。
- Agent Plugins 1.0 於 2026-08 才發布，各客戶端的載入細節可能變動；Copilot 的 agent 工具白名單使用 `cgu/*` 形式，若客戶端對 plugin MCP server 使用不同命名，名稱不符的工具會被忽略。
- Codex 的公開 plugin 目錄目前要求遠端 HTTPS MCP；本 plugin 的 MCP 是本機 stdio，因此以 repo marketplace 方式安裝，而不是公開上架。
- MCP 設定指向 `master` 分支（持續更新）；需要穩定版本時請改為固定 git tag。
- 發布使用固定 git tag：`uvx --from git+https://github.com/u9401066/creativity-generation-unit@v0.9.0 cgu-server`。PyPI／MCP Registry 是後續發布階段（D-19）。

## 授權

Apache-2.0。作者：u9401066 ＜u9401066@gap.kmu.edu.tw＞。
