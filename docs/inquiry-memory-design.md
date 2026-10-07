# 提問記憶（Inquiry Memory）：從使用者自己的提問歷史找創意來源

> **狀態**：v0.9.0 實作契約（2026-10-07）｜**前置**：[architecture.md](./architecture.md)（v0.9.0 契約）、[philosophical-inquiry-and-creativity.md](./philosophical-inquiry-and-creativity.md)（Frame、算子、懷疑的經濟學）。H10–H13 是待驗證假設；測試通過不等於效果獲證實。
>
> **發想者的提案**：CGU 是本地 server，可以蒐集使用者給 agent 的問題，整理、分群，並從中提取可能的創意來源；互動越多，CGU 能幫助的範疇應該越大。
>
> **本文件的角色**：先嚴格檢驗這個提案的前提，再凍結實作契約。結論先寫在前面：**提案可行，但有兩個前提是錯的、一個推論要拆開**。

## 2026-10-07 接續設計：主動累積、agent 整理、創意素材記憶

Hook 主動收集它能取得的使用者提問，MCP 提供持久化與待整理佇列，呼叫端 agent 定期將提問整理成**問題、限制、假設、類比、觀察或點子**。現有 `userPromptSubmitted` payload 只含使用者提問，不宣稱已收集助理回覆或完整對話。Agent 也可直接用 `capture` 留下創意素材，然後整理入庫。資料固定使用 `CGU_DATA_DIR`，未指定時為 `~/.cgu`，供多個客戶端共用。

- `settings(organize_after=20)`：設定幾筆待整理提問後提示整理（1–200；屬操作預算，不是品質門檻）。`cgu_status.inquiry.maintenance` 與 `settings.maintenance` 回報 `pending`、`materials`、`organize_after`、`due`。停用記錄後不自動提示，但仍可手動整理既有內容。
- `organize(project?, limit=20)`：從最早未整理的提問取一批（最多 100），回傳 `inquiry_organize` 工單，附去識別且隔離的文字、原始提問 ID、儲存文字 UTF-8 SHA-256、日期與來源。**不呼叫 LLM**；任一使用 CGU 的 agent 可處理，不限定 Copilot。
- `distill(reviewed=[{inquiry_id, text_sha256}], materials=[{kind, text, inquiry_ids}], agent_model?)`：agent 回交創意素材與已審閱的提問。每個素材至少連結一筆本批提問；整批驗證存在性與雜湊，原子保存後才標記整理完成。沒有可用素材可回交空陣列，避免硬湊。素材標記 `created_by=caller` 與呼叫端自行聲明的模型；不冒充 MCP 推論。
- `materials(project?, query?, limit=20, offset=0)`：取回整理後的素材，query 是確定性詞面篩選；agent 再做語意挑選。輸出保留完整來源 ID、SHA-256、日期及來源管道；可作 `cgu_material(add)` 的跨 session 素材。
- `export` 包含整理素材；刪除原始提問（含 session CASCADE）會刪除任何依賴它的素材與整理紀錄，避免留下失去證據的摘要。

此處的「定期」是累積達門檻後，在 agent 下次呼叫 `cgu_status`／`settings` 時取得待辦，再執行 `organize`。Hook 保持快速且不阻擋提問；沒有 agent 執行時不會自行整理，也不啟動背景模型或改寫 `AGENTS.md`。未來本地 LLM 可擔任這個 agent，無須 MCP 再配置第二個推理模型。CGU 預設詞面後端零模型連線；明確選用語意 embedding 的網路與隱私邊界另行揭露。管理開關、排除專案、匯出與刪除保留；本功能以累積可用素材為中心。

## 1. 先檢驗三個前提

### 1.1 「本地 server 可以蒐集使用者的問題」——**不成立，除非另開管道**

MCP server 只看得到 agent **選擇送來的工具呼叫**，看不到使用者的訊息。所以「蒐集」必須有管道：

| 管道 | 怎麼運作 | 覆蓋 | 風險 | 狀態 |
|---|---|---|---|---|
| A. skill 轉送 | skill 要求 agent 在處理問題時呼叫 `cgu_inquiry(capture)` | 只有「skill 被觸發」的問題。實驗顯示自動觸發只有 9/12，且偏向創意類問題 | 取樣偏差：記到的是**創意型**提問，不是使用者的全貌 | 可攜（skills＋MCP） |
| B. hook | Copilot `userPromptSubmitted` hook 對**每個**提問執行本地命令 | 全部提問，包含與創意無關的 | 隱私面最大；hook 會執行本機程式碼；不可攜（D-20） | **已實測 payload**：`{sessionId, timestamp(ms), cwd, prompt}`；Codex、VS Code 未驗證 |
| C. 匯入 | 使用者匯入自己的提問清單（檔案） | 使用者決定 | 低 | 本地 CLI |

**決策 D-21**：A 為預設（可攜、使用者可見）；B 為**明確 opt-in** 的選用管道，由使用者自己執行 `cgu inquiry install-hook`，plugin **不自動安裝** hook；C 供批次與測試。三條管道共用同一個 `capture` 服務、同一個開關、同一套去識別。

### 1.2 「蒐集後放在 plugin 的資料目錄」——**不適合累積型記憶**

v0.8.0 的 plugin `mcp.json` 把資料放在 `${PLUGIN_DATA}/cgu`：解除安裝或換客戶端就斷了，而且 hook 命令（不在 plugin 內）拿不到同一個目錄。一份要累積的個人記憶需要**使用者層級、跨客戶端共用、重裝不丟**的位置。

**決策 D-22**：資料目錄優先序改為 `CGU_DATA_DIR` ＞ `~/.cgu`；**不再使用 `PLUGIN_DATA`**；plugin 的 `mcp.json` 移除 `CGU_DATA_DIR`。代價：多專案共用同一份庫（用 `project` 欄位與 `excluded_projects` 控制）；風險見 §3。

### 1.3 「互動越多，CGU 能幫助的範疇越大」——**要拆開，不能整包接受**

把「範疇」拆成五件事，各自有不同的命運：

| 會隨資料增加的 | 為什麼 | 會反過來惡化的 |
|---|---|---|
| **個人參照集**：新穎度可以相對於「這位使用者自己想過的」來量 | 參照集單調增加 | 舊資料過時（需時間篩選） |
| **框架習慣的偵測**：重複出現的問法／預設 | 樣本越多越穩 | 太少樣本時是雜訊（需最小樣本數） |
| **停滯偵測**：同一主題反覆出現卻沒有採用任何點子 | 需要時間跨度 | 只在有回饋紀錄時才準 |
| **跨主題橋接候選** | 主題對數 ∝ k² | **精確度下降**：候選暴增、多數是巧合（多重比較），必須限量排序 |
| **休眠點子復活** | 被放棄的點子累積 | 只有當它與現在的提問相近才有意義 |

**不會增大的**：底層模型的創造力；也不是「通用能力變強」，而是**個人化的脈絡變豐富**。因此我們**不宣稱「越用越有創意」**，只宣稱「越用，可供參照與組合的素材越多」，並用 §2 的指標檢驗這些素材是否真的被採用。

### 1.4 這個機制自己的失敗模式（先寫下來）

1. **回音室**：從使用者自己的提問找來源，只會強化他已有的框架。對策：把提問歷史當成**典型答案集**——它揭露的是「你慣用的框架」，用途是**離開**它（接框架算子），不是深化它；橋接候選偏重**跨主題**；每次輸出固定提醒「這只反映你已在想的事，外部視角請搭配 `cgu_material` 或文獻工具」。
2. **取樣偏差**：管道 A 只記到被 skill 觸發的提問。每份報告必須揭露各管道占比（`source` 計數）。
3. **隱私**：醫療情境的提問可能含病人資訊。對策見 §3。
4. **虛假精確**：沒有語意 embedding 時，「主題」只是詞面群聚。所有輸出帶 `embedding.semantic`；數值一律是 `Measurement`（未校準）；排序規則用文字說明，不合成「創意分數」。
5. **自我實現**：只有被呈現的來源才可能被採用，採用率因而偏高。對策：記錄漏斗（呈現→變成點子→被採用），並以「呈現但未使用」為基線，而不是只看採用數。

## 2. 假設與驗證（延續 H1–H9）

| 編號 | 假設 | 可證偽條件 | 現在能驗嗎 |
|---|---|---|---|
| **H10** | 從自己的提問歷史產出的來源，使點子卡的**採用率**高於不使用它 | 累積 ≥ 30 張卡後，採用率不高於對照 → 降為 experimental | **不能**（需要真實使用數週）；只儲備漏斗儀表 |
| **H11** | 以個人歷史當 `human` 參照集，可降低模型重提使用者自己已想過／已放棄的點子 | 啟用記憶與否，`duplicate_of`（對 human 集）比例無差 | 能（描述性） |
| **H12** | 偵測到的框架習慣（問法／預設）能產生與「單 session 的 explicate」不同的框架 | 評審認為兩者無差 | 部分（小型 LLM 評審） |
| **H13** | 資料量增加時，主題群聚與橋接候選的**精確度不崩**（在有種入結構的語料上） | 召回／精確度隨 n 增加而崩 | 能（種入結構的合成語料，**用另一份 held-out 語料評估，避免對調參語料過擬合**） |

停損：若 H13 在 held-out 語料上主題純度（ARI）< 0.5，或橋接精確度 < 0.3，則「橋接」降為 experimental 並在輸出中標示。

## 3. 資料與隱私（硬性規則，由測試強制）

1. **預設關閉（opt-in）**。`settings.enabled` 為 `null`（從未詢問）｜`false`（已拒絕，不再詢問）｜`true`。啟用需要**同意**：用戶端支援 elicitation 時由 SDK `Elicit` 直接問使用者（agent 無法偽造）；否則需要 `consent.granted=true` 且 `consent.note` 非空（使用者原話）——與 `cgu_frame` 受限元素同一套機制。停用不需同意。
2. **資料最小化**：只存提問文字（≤ 2000 字，超過截斷並標記）、時間、來源管道、`project`（`cwd` 的最後一段目錄名，不存完整路徑）、選填的 `gist`。**不存**助理回覆、工具輸出、檔案內容。
3. **去識別（盡力而為，不保證）**，確定性規則，命中即取代並計數：電子郵件→`[email]`；電話（台灣手機／市話／`+` 國際碼）→`[phone]`；台灣身分證字號 `[A-Z][12]\d{8}`→`[id]`；連續 ≥ 7 位數字（病歷號、檢體號）→`[number]`；URL 去掉 query 與 fragment。**不偵測**姓名、診斷、自由文字中的識別資訊——輸出一律回報 `redactions` 計數與一句「姓名與臨床細節未被偵測」。skill 另要求 agent 在提問含病人資訊時改寫為不含個資的版本再送出。
4. **預設本地、零模型連線**：`CGU_EMBEDDING=ngram` 時 `cgu_inquiry` 不發出網路請求（測試以假 httpx 斷言）。Hook 與 organize／distill／materials 不呼叫網路或模型，整理依賴呼叫端 agent。若明確選用 `auto`／`ollama`，相似度與群聚會把提問送至設定的 embedding URL；URL 未必是本機，不能宣稱零網路。Agent 的模型資料政策由客戶端決定。
5. **可看、可匯出、可刪**：`list`、`export`、`delete`（依 id／project／older_than_days／all；需 `confirm=true`）。刪除連同向量、主題成員、來源紀錄，**無殘留**（有測試）。刪除 session 會連帶刪除其 `session_id` 連結的提問（外鍵 CASCADE）。
6. **排除專案**：`settings.excluded_projects` 命中的 `project` 一律不記錄（保密專案）。
7. **hook 永不阻擋使用者**：任何錯誤只寫 stderr、結束碼 0、stdout 不輸出任何東西。

## 4. 契約

### 4.1 `cgu_inquiry(action, …)` `[heuristic]`（第 11 個工具；`cgu_status` 新增 `inquiry{enabled, count}`）

| action | 參數 | 回傳要點 |
|---|---|---|
| `settings` | `enable?`、`consent?{granted, note}`、`excluded_projects?` | `enabled`、`consent`（誰／何時／原話）、`excluded_projects`、`counts`、`coverage`、`funnel`（§4.3）、各管道 `source` 計數 |
| `capture` | `text`（必填）、`gist?`、`project?`、`session_id?`、`source?`（`agent｜hook｜import｜manual`，預設 `agent`）、`occurred_at?`、`items?`（批次，≤ 200） | `recorded`、`id`、`family_id`、`recurrence{of, count, similarity: Measurement}`、`redactions`、`truncated`。未啟用或專案被排除：`recorded=false` 並附 `reason`（**不是錯誤**）；未詢問過（`enabled=null`）時 `reason="consent_not_asked"` |
| `list` | `project?`、`since_days?`、`theme_id?`、`limit?`（50）、`offset?` | 提問清單（含 `redactions`、`source`） |
| `themes` | `min_size?`（3）、`threshold?`、`project?`、`since_days?` | `themes[]`：`theme_id`、`label｜null`、`size`、`families`、`distinct_days`、`first_seen`、`last_seen`、`exemplars[≤5]`、`projects`、`top_stems[{stem, share: Measurement}]`；`uncategorized`；`work_orders`：未命名主題的 `inquiry_label`（≤ 5 張）；`embedding{backend, semantic}`；`semantic=false` 時警告「這是詞面群聚」 |
| `label` | `labels[{theme_id, label}]`（label ≤ 60 字） | 寫入，`labeled_by="caller"` |
| `mine` | `kinds?`（預設全部：`frame｜bridge｜stalled｜dormant`）、`limit?`（每類 3）、`project?` | `sources[]`（§4.2）＋`work_orders`（`frame` 類）。每次必帶回音室警告。呈現過的來源寫入 `inquiry_sources` |
| `related` | `query`（必填）、`k?`（5） | `similar_inquiries[{id, text, occurred_at, days_ago, similarity: Measurement, recurrence}]`、`adopted_ideas[]`、`abandoned_ideas[]`（跨 session，來自 `cgu_feedback`）、`ideas_payload[]`（可直接丟給 `cgu_ideas(add, kind=human)`，`meta.from_inquiry`）。無資料時回空並寫明 `reference_size=0` |
| `export` | `project?` | 全部欄位 |
| `delete` | `ids?｜project?｜older_than_days?｜all?`、`confirm`（必填 true） | 刪除筆數；主題成員同步更新、過小的主題移除 |

錯誤與輸出規則同 v0.8.0：`ToolResult`、`ok=false` 不丟例外、浮點只在 `Measurement` 內、每個結果帶 `Provenance`（`engine="heuristic"`，semantic=false 時 `degraded=false` 但 `warnings` 說明）。

### 4.2 來源候選（`mine` 的 `sources[]`）

每筆：`source_id`（`src-`＋穩定雜湊，同證據同 ID）、`kind`、`title`（由事實**確定性**產生的一句話）、`evidence[{inquiry_id, text, occurred_at}]`、`measures{name: Measurement}`、`facts`（整數與字串）、`next`（建議的下一個工具呼叫與參數）。**不得有合成的「創意分數」**；排序規則以 `rank_rule` 文字揭露。

| kind | 確定性的觸發條件（皆為未校準啟發式，數值標明） | `next` |
|---|---|---|
| `frame` | 主題大小 ≥ `min_size`。事實：該主題最常見的問句開頭（前 2 個字元／前 2 個英文詞）與占比 `Measurement`（`n`＝主題大小）。**工單**（`inquiry_explicate`）：以該主題的提問當「典型答案」，要求溯因出「這些提問默默依賴的假設」 | `cgu_session(open)` → `cgu_frame(create, assumptions=[…], …source="abduced_from_user_questions")` → 接 `operate` |
| `bridge` | 兩個主題大小皆 ≥ `min_size`，質心距離落在 `mid` 或 `far` 帶（沿用 `band_from_distance` 的未校準門檻）。事實：距離 `Measurement`；`co_occurrence`＝兩主題的提問出現在同一個 session 或相隔 ≤ 7 天的次數（整數）。排序：`co_occurrence` 遞減，再 `mid` 先於 `far`，再兩主題大小和遞減 | `cgu_diverge(collide, …)`，並把兩主題的代表提問當素材 |
| `stalled` | 主題 `distinct_days` ≥ 3 且 `families` ≥ 3，且其提問所連結的 session 沒有任何 `adopt`。必附 `evidence_quality`：有 session 連結的提問占比。**占比低時要明說「證據弱」** | `cgu_frame(doubt, signals.stalled_rounds=…)` 或 `frame-audit` skill |
| `dormant` | 某筆被 `abandon`／`modify` 的點子，與**近 14 天**內的某提問相似度 ≥ 門檻（`Measurement`） | 以該點子為 `human` 參照重啟 `creative-ideation` |

### 4.3 「範疇」的度量（`settings.coverage` 與 `settings.funnel`）

- `coverage`：`inquiries`、`families`、`themes_min_size`、`distinct_days`、`projects`、`sources_by_channel`、`bridge_candidates{near, mid, far}`。**這些數字增加代表素材變多，不代表更有創意。**
- `funnel`（H10 的儀表）：`surfaced`（`mine` 呈現過的來源數）→ `turned_into_ideas`（`cgu_ideas(add)` 的 `meta.from_source` 命中）→ `adopted`／`modified`／`abandoned`（`cgu_feedback`）。依 `kind` 分列。**「呈現但未使用」也計入，作為基線。**

### 4.4 演算法（確定性，純函式放 `domain/inquiry.py`）

- 向量：既有 `EmbeddingPort`，預設確定性的 n-gram，Ollama embedding 需明確選用，僅供比對。向量以 float32 快取於 `inquiry_vectors`（依 `backend`；換後端時重算，不混用）；命名、語意整理與創意判斷由 agent 的模型完成。
- 重複與復現：新提問與既有提問的詞面 Jaccard ≥ 0.8 或（語意）餘弦 ≥ 0.92 → 歸入同一 `family_id`。**復現是訊號，不是垃圾**：全部保存、`recurrence.count` 回報。
- 主題：向量的**平均連結**階層分群（餘弦距離，門檻 `threshold`），主題以 `family` 為單位計大小。上限：最近 2000 筆，超過時警告。**預設門檻必須在調參語料上校準並註明「未校準、只在合成語料上調過」。**
- 主題身分穩定：重算時以成員集合 Jaccard ≥ 0.5 對應舊主題，沿用 `theme_id` 與 `label`；對不到的是新主題。
- 所有計算在 `asyncio.to_thread` 內執行，不阻塞事件迴圈（沿用 v0.8.0 的非阻塞測試方法）。

### 4.5 資料表（migration 2）

`inquiry_settings(key, value, updated_at)`、`inquiries(id, session_id → sessions ON DELETE CASCADE, text, gist, source, project, occurred_at, captured_at, redactions, truncated, family_id, meta)`、`inquiry_vectors(inquiry_id → ON DELETE CASCADE, backend, dim, vec BLOB)`、`inquiry_themes(id, label, labeled_by, member_ids, backend, updated_at)`、`inquiry_sources(id, kind, json, first_surfaced_at, last_surfaced_at, times_surfaced)`。

### 4.6 CLI（`cgu inquiry …`，**延遲載入**，不匯入 MCP SDK，以免拖慢 hook）

`settings [--enable --yes | --disable]`、`hook`（stdin JSON `{sessionId, timestamp(ms), cwd, prompt}`；永遠結束碼 0、stdout 不輸出）、`import FILE`（每行純文字或 JSON `{text, occurred_at?, project?}`）、`themes`、`mine`、`export`、`delete`（需 `--yes`）、`install-hook [--print | --remove]`（寫入 `<COPILOT_HOME 或 ~/.copilot>/hooks/cgu-inquiry.json`；先印出將執行的內容與隱私說明；需使用者明確執行）。`--yes` 在 CLI 即為同意。

## 5. skills

- **新增 `inquiry-mining`**：「我最近都在問什麼？有哪些可以當創意來源？」。流程：`settings` → （未啟用則說明用途並詢問一次）→ `themes`（照工單為主題命名）→ `mine` → 用白話呈現（**不得出現 ID、Wilson、n-gram**）→ 使用者挑一個 → 交給 `creative-ideation`／`frame-audit`，並在 `cgu_ideas(add)` 的 `meta.from_source` 帶上 `source_id`。必須揭露：只反映你已在想的事、管道占比、`semantic=false` 時主題是詞面群聚。
- **修改 `creative-ideation`**：開頭若已啟用，`cgu_inquiry(related)` 取得「你問過類似的（日期）」與已採用／放棄的點子，加入 `human` 參照集；對使用者的提問呼叫 `capture`（提問含病人資訊時先改寫）。未詢問過時**只問一次**，拒絕就記為 `false`，不再問。
- 兩個 skill 都不得假裝有記憶：未啟用或資料不足時明說。

## 6. 驗收

1. **契約與隱私測試**：預設不記錄；同意流程（Elicit 與 caller-consent 兩條）；去識別規則逐條；截斷；排除專案；`delete` 無殘留（含向量、主題、來源）；零網路；`session` 刪除連帶；每個輸出的浮點都在 `Measurement`。
2. **演算法測試**：復現歸族；主題穩定身分；`mine` 四種來源各有觸發與不觸發案例；`stalled` 的 `evidence_quality`；`dormant` 的 14 天窗；漏斗計數（`meta.from_source`）。
3. **非阻塞**：2000 筆分群時事件迴圈停頓 < 0.1 s。
4. **hook**：以 stdin payload 呼叫 `cgu inquiry hook`；未啟用時不寫入；錯誤時結束碼 0。冷啟動耗時要**量測並記錄**（hook 會拖慢每個提問）。
5. **種入結構的評估**（H13）：調參語料（單元測試用）與**另一份 held-out 語料**（評估用，實作者看不到）分開；報告主題純度（ARI）、橋接與停滯的召回／精確度，以及 n=20/40/80/120 的趨勢。
6. **真實 agent 測試**：隔離的 Copilot CLI 安裝 plugin；匯入 held-out 語料；以 `inquiry-mining` 跑一次；檢查是否呼叫工具、是否找到種入的結構、是否有編造；另測 hook 路徑（同意前不寫入、同意後寫入且已去識別）。
7. `ruff`、`mypy src`、全部測試綠；plugin 的 skill↔tool 契約測試納入新工具與 action。

## 7. 非目標

- 不做偏好模型或預測（沿用 `cgu_feedback` 的原則：只計數）。
- 不上傳、不同步、不做跨使用者彙整。
- 不從助理回覆或檔案內容學習。
- 不宣稱「越用越有創意」；只量測素材與採用漏斗。
