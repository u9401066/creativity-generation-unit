# CGU v0.9 架構規格（SDK 2 與創意素材記憶）

> **版本**：v0.9.0（與 0.6 / 0.7 不相容；保留 0.8 工具並新增提問記憶）｜**日期**：2026-10-07｜**作者**：u9401066 ＜u9401066@gap.kmu.edu.tw＞
>
> **依據**：[嚴格審查](./critical-review-and-improvement-plan.md)、[哲學後設探究](./philosophical-inquiry-and-creativity.md)、[執行計畫](./program-plan.md)。使用者於 2026-10-02 明確指示：MCP 以 SDK 2.0+ 為準、不相容舊版、直接重寫並設計較佳架構、可整合其他工具。因此執行計畫 D-05（保留別名）作廢；D-06（隔離舊引擎）改為**直接刪除**。

## 1. 設計原則

1. **誠實**：任何浮點「分數、距離、相似度」只能出現在 `Measurement` 物件內，且必須有 `method`、`reference`、`calibrated`；沒有測量程序就輸出 `null`。計數、ID、預算可以是整數。
2. **Work order 模式**：MCP 本身不提供思考能力。預設（`CGU_PROVIDER=passthrough`、`CGU_EMBEDDING=ngram`）下，CGU 不呼叫或探測本地模型；凡需要生成、命名、整理或語意判斷的步驟，CGU 回傳 `WorkOrder`（指示、輸入、輸出 schema、回交方式），由呼叫它的 agent 背後的模型執行，再用工具回交。Agent 可以使用雲端或本地模型；CGU 負責**狀態、測量、去重、編排、隔離、持久化**。
3. **Session 與個人記憶分界**：除 `cgu_status`、`cgu_session(open/list)` 與跨 session 的 `cgu_inquiry` 外，所有工具都要 `session_id`；狀態存 SQLite，不使用模組全域狀態。
4. **框架是一等公民**：Frame（假設、概念、隱喻、準則、利害關係人、單位、鉸鏈）有譜系；框架算子把變革型創意變成可執行、可追溯的操作。
5. **不受信任內容隔離**：網頁、PubMed 等外部碎片一律 `trusted=false`，截斷、剝除指令句型、包進 `<untrusted_data>` 區塊。
6. **降級要明說**：沒有 embedding 時退回字元 n-gram，並標 `semantic=false`；網路關閉或失敗時 `provenance.degraded=true` 並附警告。**不得**用模板冒充結果。
7. **SDK 2 原生**：`MCPServer`＋`lifespan`、型別化回傳（structured output）、`ToolAnnotations`、`Context` 日誌與進度、`Elicit` 徵求同意；不用全域單例、不在 import 時讀環境變數。
8. **可整合其他工具**：CGU 不內建所有檢索。呼叫端（skills）可用其他 MCP（例如 PubMed Search、Zotero Keeper、asset-aware-mcp）取得資料，再用 `cgu_material(add)` 與 `cgu_ideas(add, kind=prior_art)` 餵入；CGU 以該參照集計算新穎度，並如實回報 `reference_size`。

## 2. 套件結構與依賴規則

```text
src/cgu/
├── __init__.py                 # __version__
├── domain/                     # 純資料與規則；只依賴 stdlib、pydantic、numpy
│   ├── common.py               # Provenance, Measurement, WorkOrder, ToolResult, ErrorInfo
│   ├── frame.py                # Frame, Assumption, Concept, Metaphor, Criterion, Stakeholder, Constraint, Hinge, FrameDraft, Disclosure
│   ├── operators.py            # OperatorCard 與 11 個算子定義（來源、護欄、指示模板）
│   ├── idea.py                 # Idea(kind: typical|candidate|human|prior_art), Fragment
│   ├── measure.py              # shingles/MinHash、dedup、NoveltyVector、vendi_score（純函式）
│   ├── doubt.py                # 懷疑的經濟學：觸發、優先度、停止（純函式）
│   ├── fence.py                # 不受信任內容的截斷／剝除／包裝
│   └── judge.py                # 配對生成、Wilson 區間、Pareto 前緣（純函式）
├── application/                # 用例；只依賴 domain 與 application.ports
│   ├── ports.py                # EmbeddingPort, LLMPort, RetrievalPort, ArchivePort（typing.Protocol；同意流程見 §8.1）
│   └── services/               # session, frame, material, diverge, ideas, judge, evolve, feedback, question_gate
├── infrastructure/             # 實作 ports
│   ├── config.py               # Settings.from_env()（明確呼叫，不在 import 時執行）
│   ├── embedding.py            # NgramHashEmbedding（預設，無模型）、OllamaEmbedding（選用）
│   ├── llm.py                  # OllamaLLM（可選；僅 provider=ollama 的 execute 模式使用）
│   ├── retrieval.py            # WikipediaRetrieval（httpx）
│   └── sqlite.py               # SQLiteArchive（WAL、user_version migration、執行緒安全）
└── interfaces/
    ├── mcp/
    │   ├── server.py           # create_server(settings)、main()；lifespan 組裝依賴
    │   ├── tools/              # 每個工具一個模組（session, frame, material, diverge, ideas, judge, evolve, feedback, question_gate, status）
    │   ├── resources.py        # 方法庫、算子卡、rubric
    │   └── prompts.py          # MCP prompts
    └── cli.py                  # `cgu doctor`、`cgu serve`
```

**依賴規則（以測試強制）**：`domain` 不 import `application`／`infrastructure`／`interfaces`／`mcp`／`httpx`／`sqlite3`；`application` 不 import `infrastructure`／`interfaces`／`mcp`；`infrastructure` 不 import `interfaces`。

**刪除**（不保留）：`src/cgu/{agents,core,graph,llm,soup,thinking,tools}/`、`src/cgu/{brainstorm_protocol,cli,server}.py` 舊檔、舊測試與 `tests/probes/`。**依賴移除**：`langgraph`、`langchain*`、`openai`、`instructor`、`duckduckgo-search`、`rich`、`python-dotenv`。**保留／新增依賴**：`mcp>=2,<3`、`pydantic>=2.12,<3`、`httpx`、`numpy`；dev：`pytest`、`pytest-asyncio`、`pytest-cov`、`ruff`、`mypy`、`jsonschema`。

## 3. 共用型別（`domain/common.py`）

```python
class Measurement(BaseModel):          # 浮點量測的唯一載體
    value: float
    method: str                        # 例如 "cosine over char-ngram hashing"
    reference: str                     # 參照集描述，例如 "session typical set (n=8)"
    calibrated: bool = False           # 只有完成人類校準才可為 True
    n: int | None = None               # 參照集大小

class Provenance(BaseModel):
    engine: Literal["passthrough", "ollama", "heuristic", "retrieval", "archive"]
    degraded: bool = False
    warnings: list[str] = []
    seed: int | None = None
    model: str | None = None
    version: str                       # cgu.__version__
    sources: list[dict] = []           # 例如 {"type": "web", "url": "...", "trusted": False}

class WorkOrder(BaseModel):
    id: str
    kind: str                          # typical_set | anti_typical | fanout_task | collide | frame_operate | judge | question_gate | evolve
    instructions: str                  # 完整、可直接照做的指示（繁中；識別字用英文）
    inputs: dict                       # 呼叫端需要的資料（例如 avoid 清單、frame 摘要、碎片）
    output_schema: dict                # JSON Schema：呼叫端回交內容的形狀
    submit_with: dict                  # {"tool": "cgu_ideas", "action": "add", "args_template": {...}}
    independence: Literal["same_context_ok", "separate_context_recommended"] = "same_context_ok"

class ErrorInfo(BaseModel):
    code: str                          # not_found | invalid_input | consent_required | unavailable | conflict
    message: str
    hint: str | None = None

class ToolResult(BaseModel):           # 所有工具的回傳外殼
    ok: bool
    data: dict = {}
    work_order: WorkOrder | None = None
    work_orders: list[WorkOrder] = []  # fanout／judge 等多張
    provenance: Provenance
    error: ErrorInfo | None = None
```

領域錯誤回傳 `ok=false` 的 `ToolResult`，**不丟例外**；真正的程式錯誤才讓 SDK 處理。

## 4. 工具規格（v0.8.0 為 10 個，v0.9.0 起 11 個；名稱與 action 為對外契約）

工具描述必須以成熟度標記開頭：`[stable]`、`[heuristic]` 或 `[experimental]`，並說明「量測了什麼、沒量測什麼」。多工具以 `action`（`Literal`）區分動作，使 JSON Schema 產生 enum。

### 4.1 `cgu_status()` `[stable]`
回傳 `data`：`version`、`provider`（`passthrough|ollama`）、`embedding{backend, semantic}`、`retrieval{enabled}`、`data_dir`、`maturity{tool: level}`。**用途**：呼叫端在開工前確認哪些能力可用；`semantic=false` 時須知道新穎度只是詞面相似。

### 4.2 `cgu_session(action, session_id?, topic?, domain?, language?, seed?, confirm?)` `[stable]`
| action | 說明 |
|---|---|
| `open` | 必填 `topic`；選填 `domain`（自由文字，例如「醫療商品開發」）、`language`（預設 `zh-TW`）、`seed`。回傳 `session_id`、實際 `seed` |
| `get` | session 概況與各類資料筆數 |
| `list` | 所有 session（最新在前） |
| `export` | 該 session 全部資料（JSON） |
| `delete` | 需 `confirm=true`；刪除該 session 全部資料，無殘留 |

### 4.3 `cgu_frame(action, session_id, …)` `[heuristic]`
Frame 元素種類：`goal`、`assumption`（`core`｜`belt`）、`concept`、`metaphor`、`criterion`、`stakeholder`、`constraint`（`hard`｜`soft`｜`self_imposed`）、`unit`、`hinge`。**受限元素**（改寫須同意）：`goal`、`stakeholder`、`criterion`。

| action | 參數 | 回傳 |
|---|---|---|
| `create` | `problem`（必填）、`goal`、`stakeholders[]`、`concepts[]`、`assumptions[]`、`constraints[]`、`metaphors[]`、`criteria[]`、`hinges[]`、`unit` | `frame_id`、各元素的 ID |
| `get` | `frame_id` | 完整 Frame 與譜系鏈 |
| `operators` | — | 11 張算子卡（名稱、來源、說明、可作用元素、是否受限、護欄） |
| `operate` | `frame_id`、`operator`、`target`（元素 ID 或種類）、`params` | `work_order`（要求呼叫端產生 `FrameDraft` 子框架）；受限元素時 `data.requires_consent=true` |
| `commit` | `frame_id`（父）、`operator`、`child`（`FrameDraft`）、`consent{granted, note}` | 驗證子框架、檢查同意、寫入譜系；回傳 `child_frame_id` 與 `disclosure{changed[], why, operator, source}`。受限元素缺同意時 `ok=false, code=consent_required` |
| `doubt` | `frame_id`、`signals{stalled_rounds, anomalies[], conflicts[], high_stakes, user_requested}`、`estimates{assumption_id: {load_bearing, uncertainty, decision_impact, irreversibility}}`（呼叫端以 0–1 估計）、`budget{max_questions}` | `escalate`、`triggers[]`、`ranked[{assumption_id, priority: Measurement}]`（priority＝四因子乘積，`method` 註明「呼叫端估計值的乘積；未校準啟發式」）、`stop_reasons[]`、`untested_load_bearing[]` |

同意流程（SDK 2 `Elicit`）：伺服器先嘗試向用戶端徵求同意；用戶端不支援或拒絕時，改以 `requires_consent` 讓呼叫端詢問使用者，再以 `consent.granted=true` 重送。**未同意不得寫入受限元素的改寫。**

**11 個算子**（`domain/operators.py`，每個含 `source`、`guardrails`、`targets`、`restricted`、`instruction_template`）：`explicate`（從典型答案溯因出隱性框架）、`bracket`（暫時移除假設）、`negate`（反轉假設）、`tetralemma`（四句：是／非／亦是亦非／非是非非）、`re_explicate`（改寫概念定義，Carnap 闡明）、`swap_metaphor`、`recut_unit`（改分析單位）、`shift_stakeholder`（改利害關係人視角，含無知之幕檢查）、`invert_criterion`（反轉評估準則，無用之用）、`genealogize`（追溯準則來源，**必含籬笆檢查**）、`thought_experiment`（把參數推到極端並轉旋鈕）。

### 4.4 `cgu_material(action, session_id, …)` `[stable]`
| action | 參數 | 說明 |
|---|---|---|
| `search` | `query`、`source`（預設 `wikipedia`）、`lang`、`limit`（≤10） | 以 httpx 檢索；結果存為不受信任碎片。網路關閉或失敗 → `degraded=true` 與警告 |
| `add` | `fragments[{text, source_type, source_id?, url?, title?}]` | 接收其他工具（PubMed、Zotero…）取得的資料，同樣隔離與存檔 |
| `list` | `band?`（`near｜mid｜far`） | 列出碎片 |

碎片輸出含 `fenced_text`（`<untrusted_data source="…">…</untrusted_data>`）、`trusted=false`、`truncated`、`distance_band`（有語意 embedding 時為 `Measurement`，否則 `null`）。上限 1200 字元；剝除「ignore previous instructions」「system note」「run the … tool」等指令句型，並在 `provenance.warnings` 註明已剝除幾處。

### 4.5 `cgu_diverge(action, session_id, …)` `[heuristic]`
| action | 參數 | 回傳 |
|---|---|---|
| `typical_set` | `frame_id?`、`k`（預設 8） | `work_order`：要求呼叫端**先不看任何素材**，列出 k 個「最直覺的回答」；以 `cgu_ideas(add, kind=typical)` 回交 |
| `anti_typical` | `frame_id?`、`operators[]?`、`n`（預設 6） | `work_order`：附上 `avoid`（該 session 的 typical 想法）與要套用的算子，要求每個點子標明「改寫了哪個框架元素」；無 typical 時警告 |
| `fanout` | `n`（預設 4）、`vary`（`prompt｜material｜operator｜model` 子集）、`frame_id?` | `work_orders[]`：每張指定不同的 seed、素材 ID 或算子，`independence=separate_context_recommended`，並註明「不得參考其他任務的輸出」 |
| `collide` | `a`、`b`、`mode`（`analogy｜bridge`） | `work_order`：結構映射表（對應關係、候選推論），附檢核清單（一對一、關係而非屬性、系統性、可檢驗的推論） |

### 4.6 `cgu_ideas(action, session_id, …)` `[stable]`（`measure` 為 `[heuristic]`）
| action | 參數 | 回傳 |
|---|---|---|
| `add` | `ideas[{text, kind, frame_id?, operator?, parent_id?, material_ids?, meta?}]`，`kind∈{typical, candidate, human, prior_art}` | 每筆的 `idea_id`、`duplicate_of`（若與既有想法近重複，附 `Measurement`） |
| `list` | `kind?` | 想法清單 |
| `measure` | `idea_ids?`（預設全部 candidate）、`thresholds?` | 每個 candidate 的 `novelty`：`vs_typical`、`vs_human`、`vs_prior_art`、`vs_session`（皆為 `{max_similarity, mean_similarity: Measurement, nearest_id, reference_size}` 或 `null`——參照集為空即 `null`）；集合層級 `diversity`（Vendi，`Measurement`）；`embedding{backend, semantic}` |

重複偵測：字元 shingle Jaccard（預設 ≥0.8）或 embedding 餘弦（預設 ≥0.92）；門檻可由 `thresholds` 覆寫並寫入 `method`。

### 4.7 `cgu_judge(action, session_id, …)` `[experimental]`
| action | 參數 | 說明 |
|---|---|---|
| `plan` | `idea_ids`、`rounds?`、`criteria?`（預設 `novelty_vs_typical`、`usefulness`、`framing`）、`gate{feasibility_min?}` | 產生配對與**位置交換**的 `work_orders[]`（AB／BA）；指示建議使用至少兩個不同家族的評審模型 |
| `record` | `verdicts[{matchup_id, order, winner, criteria_winners?, judge_model?, reason?}]` | 存入判決 |
| `rank` | — | 每個想法的勝負和、`win_rate`（`Measurement`，`method` 註明 Wilson 95% 區間與「依賴評審」）、AB／BA 一致率、有分項判決時的 Pareto 前緣（可行性為非補償式門檻） |

### 4.8 `cgu_evolve(action, session_id, …)` `[experimental]`
品質多樣性存檔：格子＝（被改寫的框架元素種類）×（距離帶；無語意 embedding 時為 `unknown`）。
| action | 說明 |
|---|---|
| `map` | 格子→想法的對應與覆蓋計數 |
| `next` | 以 session seed 挑選親代與算子，回傳 `work_order` |
| `submit` | `{child_text, parent_id, operator, frame_element_kind, material_ids?}`：去重、分格；格子被佔用時回傳比較用的 `judge` work order |
| `resolve` | `{niche, verdicts}`：依判決決定替換或丟棄；記錄譜系 |

### 4.9 `cgu_feedback(action, session_id, …)` `[stable]`
`record{idea_id, decision∈{adopt, modify, abandon}, reasons[], note?}`、`summary`（依決定、算子、框架元素的**計數**；不做個人化或預測）、`export`、`delete{confirm}`。

### 4.10 `cgu_question_gate(action, session_id, …)` `[experimental]`
| action | 說明 |
|---|---|
| `check` | `{question, frame_id?, decision_context}` → `work_order`，內含五項判準與操作程序：①決策相關（答案不同，行動排序會變嗎）②可操作（能指出要蒐集什麼證據）③承重（反事實：假設被推翻，結論翻轉嗎）④非口頭（禁用關鍵詞後問題仍在嗎）⑤非典型（加分項） |
| `record` | `{question, verdicts{decision_relevant, operable, load_bearing, non_verbal, non_typical?}, judge_model?}`；前四項皆真才算通過，回傳 `passed` 與未通過原因 |

### 4.11 `cgu_inquiry(action, …)` `[heuristic]`（v0.9.0 新增）
使用者提問歷史的**本機、opt-in**記憶：`settings`、`capture`、`list`、`themes`、`label`、`mine`、`related`、`organize`、`distill`、`materials`、`export`、`delete`。完整契約、管理規則與演算法見 [inquiry-memory-design.md](./inquiry-memory-design.md)。預設關閉；與其他工具不同，**它跨 session**（資料在使用者層級的 `~/.cgu`）。Hook 累積原始提問；agent 依 `maintenance.due` 取得整理工單，用自己的模型回交創意素材；CGU 驗證来源 ID 與儲存文字 SHA-256 後保存。這是個人參照與素材變豐富，不宣稱模型創造力增加。

## 5. Resources 與 Prompts

- **Resources**：`cgu://methods/{name}`（SCAMPER、六頂思考帽、TRIZ 原理、5W2H、逆向、形態分析…的**方法說明**，取代舊 `apply_method`）、`cgu://operators`、`cgu://rubrics/question-gate`、`cgu://rubrics/pairwise`、`cgu://triggers`（觸發問句庫）。
- **Prompts**：`frame_audit`、`anti_typical_session`、`maieutic_session`、`pairwise_judge`，內容為 skills 的精簡版，供不支援 skills 的用戶端使用。

## 6. 持久化（SQLite）

`CGU_DATA_DIR`（預設 `~/.cgu`；v0.9.0 起**不再使用 `PLUGIN_DATA`**，見 inquiry-memory-design D-22）下的 `cgu.sqlite3`；WAL；以 `PRAGMA user_version` 做 migration；所有寫入經單一連線鎖或 `to_thread`，**不得阻塞事件迴圈**。
資料表：`sessions`、`frames`（含 `parent_id`、`operator`、`json`）、`ideas`、`fragments`、`verdicts`、`niches`、`questions`、`feedback`；v0.9.0 migration 2 新增 `inquiry_settings`、`inquiries`、`inquiry_vectors`、`inquiry_themes`、`inquiry_sources`。刪除 session 時以外鍵 `ON DELETE CASCADE` 清除；`export` 與 `delete` 皆有測試。

Migration 3 新增 `inquiry_reviews`、`inquiry_materials`、`inquiry_material_links`；整理批次的證據驗證、素材寫入與已讀標記在同一寫入交易完成。刪除任一來源提問時，trigger 移除所有依賴素材，包含從 session CASCADE 進來的刪除；不留下失去來源的摘要。

## 7. 設定（環境變數；`Settings.from_env()`）

| 變數 | 預設 | 說明 |
|---|---|---|
| `CGU_PROVIDER` | `passthrough` | `passthrough`（回傳 work order）｜`ollama`（可選 execute 模式） |
| `CGU_DATA_DIR` | 見上 | 資料目錄 |
| `CGU_EMBEDDING` | `ngram` | 確定性的詞面比對，不需模型；明確設定 `auto` 或 `ollama` 才連線至選用 embedding 後端。Embedding 不負責思考 |
| `CGU_OLLAMA_URL` | `http://localhost:11434` | **不帶 `/v1`** |
| `CGU_OLLAMA_MODEL` | `qwen2.5:3b` | 僅 execute 模式 |
| `CGU_EMBED_MODEL` | `nomic-embed-text` | |
| `CGU_NETWORK` | `on` | `off` 時 `cgu_material(search)` 回傳 `degraded` |
| `CGU_LOG_LEVEL` | `INFO` | **日誌只寫 stderr**，stdout 保留給 MCP stdio |

## 8. SDK 2 使用規範

- 以 `MCPServer(name, instructions, lifespan=…)` 建立；依賴（Settings、Archive、Embedding、Retrieval）在 `lifespan` 組裝並經 `Context` 取得；`create_server(settings)` 讓測試可注入假依賴。
- 工具回傳型別一律標註為 `ToolResult`，使用 structured output；每個工具設定 `ToolAnnotations`（`title`、`readOnlyHint`、`destructiveHint`、`idempotentHint`、`openWorldHint`；`cgu_material` 為 `openWorldHint=True`；含 `delete` 動作者 `destructiveHint=True`）。
- 長作業（檢索、embedding）以 `ctx` 回報進度與日誌。
- 受限框架改寫以 `Elicit` 徵求同意，失敗時退回 `consent_required`。
- **實作者必須先閱讀已安裝的 `mcp` 2.0.0 原始碼**（`.venv` 內 `mcp/server/mcpserver/`）確認 `Context`、`lifespan`、`Elicit`、`ToolAnnotations` 的實際 API，**不得憑舊版 FastMCP 記憶撰寫**。

### 8.1 as-built 與規格的差異（v0.8.0 實作時確認）

以下為實作讀過 `mcp` 2.0.0 原始碼後的修正，**以此為準**：

- **同意（Elicit）**：SDK 2 的 `Elicit` 不是可直接呼叫的函式，而是 `Annotated[ElicitationResult[Form], Resolve(fn)]` 參數解析。因此 `ConsentPort` **未實作**，同意邏輯放在 interface 層；用戶端無 elicitation 能力時先檢查 `ctx.client_capabilities.elicitation` 並退回 `consent_required`，否則 resolver 會丟 `MCPError`。2026-07-28 協定下 resolver 本體每輪重跑，必須是唯讀的。
- **日誌**：`ctx.log` 在 SDK 2 已棄用，改用 stdlib logging 寫 stderr，進度用 `ctx.report_progress`。
- **Context 取用**：`ctx.request_context.lifespan_context`；型別別名 `Ctx: TypeAlias = Context[Deps, Any]`。
- **參數為扁平結構**；schema 驗證錯誤（例如 `Literal` 不符）由 SDK 以 `is_error` 回傳，不經 `ToolResult`。
- **`Verdict.winner`** 為 `idea_id` 或 `"tie"`；`cgu_evolve(resolve)` 接受單一順序的提交，AB 與 BA 兩者齊備前維持 `pending`（位置偏差控制）。
- **額外資料表** `matchups`；gate 門檻以文字儲存。
- **Ollama execute 模式**只作用於 `cgu_diverge` 的 `typical_set`／`anti_typical`／`fanout`。
- **非阻塞**：重複偵測與量測以 `asyncio.to_thread` 執行，shingle 快取、n-gram 雜湊向量化；實測事件迴圈停頓由 1.2 s 降至 < 40 ms（100 個點子）。
- 用戶端若固定為 `"2026-07-28"` 模式，`client.instructions` 為 `None`；以 `auto`／`legacy` 讀取。
- mypy 對 numpy 使用 `follow_imports="skip"`。

## 9. 測試與驗收

1. **依賴規則測試**（§2）。
2. **domain 單元測試**：重複偵測（原句、去空白、近重複都被抓到）、新穎度參照集為空→`null`、Vendi 對相同／相異集合的行為、doubt 的觸發與停止、frame 譜系與同意規則、fence 剝除與截斷、Wilson 區間、Pareto 前緣。
3. **repository 測試**（tmp sqlite）：migration、cascade 刪除、export／delete 無殘留、多 session 隔離。
4. **工具契約測試**（SDK 2 in-process client）：每個工具回傳 `ToolResult`；`provenance` 必填；掃描輸出，**任何浮點必須位於 `Measurement` 之內**（計數與 ID 除外）；`passthrough` 下以假 httpx 斷言**零網路、零 LLM 呼叫**（`material.search` 除外且需 `CGU_NETWORK=on`）；注入文字經 `cgu_material(add)` 後被隔離並剝除。
5. **非阻塞測試**：以心跳量測，LLM／embedding／檢索期間事件迴圈停頓 < 0.1 s（可用假的慢 adapter）。
6. **stdio 子行程煙霧測試**：以 `uv run cgu-server` 啟動並列出 11 個工具、呼叫 `cgu_status`。
7. `ruff check`、`ruff format --check`、`mypy src` 全綠。

## 10. 舊→新對照（皆不相容）

| 舊（0.6） | 新（0.8） |
|---|---|
| `generate_ideas`、`deep_think`、`multi_agent_brainstorm`、`spark_soup_quick` | `cgu_diverge`＋呼叫端生成＋`cgu_ideas` |
| `spark_collision`、`spark_collision_deep`、`find_connections`、`suggest_bridges` | `cgu_diverge(collide)` |
| `spark_soup_*`、`collect_creativity_fragments`、`explore_concept`、`random_concept`、`associative_expansion` | `cgu_material` |
| `check_novelty`、`evaluate_brainstorm_ideas` | `cgu_ideas(measure)`、`cgu_judge` |
| `evolve_idea_tool`、對抗引擎 | `cgu_evolve` |
| `creativity_session_*` | `cgu_session`、`cgu_ideas` |
| `apply_method`、`select_method`、`list_methods`、`brainstorm_protocol`、`get_trigger_words` | resources／prompts＋skills |
| 環境變數 `CGU_LLM_PROVIDER`、`CGU_USE_LLM`、`OLLAMA_BASE_URL` 等 | 見 §7 |

## 11. Plugin 介面契約（供 skills 引用）

skills 只能引用本文件第 4 節的**工具名稱與 action**；測試會解析 `plugins/cgu/skills/*/SKILL.md`，驗證其中出現的 `cgu_*` 工具存在、被提及的 action 屬於該工具的 enum。其他工具（PubMed Search、Zotero Keeper 等）只能以「若可用則…」的**選用**方式提及，不得成為必要步驟。

