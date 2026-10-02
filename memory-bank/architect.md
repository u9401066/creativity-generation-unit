# System Architect

> 📌 此檔案記錄重大架構決策，架構變更時更新。

## 🌐 系統架構圖

```
┌─────────────────────────────────────────────┐
│              專案模板結構                      │
├─────────────────────────────────────────────┤
│  🏔️ 規則層                                        │
│  ┌─────────────┐                                  │
│  │ CONSTITUTION │ ───┐                             │
│  └─────────────┘     │                             │
│        │            ▼                             │
│        │     ┌────────────┐                        │
│        ├────▶│  Bylaws   │                        │
│        │     └────────────┘                        │
│        │            │                             │
│        ▼            ▼                             │
│  ┌───────────────────────┐                      │
│  │    Claude Skills      │                      │
│  └───────────────────────┘                      │
├─────────────────────────────────────────────┤
│  🧠 記憶層                                        │
│  ┌───────────────────────┐                      │
│  │     Memory Bank       │                      │
│  │  (7 markdown files)   │                      │
│  └───────────────────────┘                      │
├─────────────────────────────────────────────┤
│  ⚙️ 工具層                                        │
│  ┌────────┐ ┌─────────┐ ┌─────────┐           │
│  │ CI/CD  │ │ Testing │ │ Linting │           │
│  └────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────┘
```

## 🏛️ 架構決策紀錄

### ADR-001: 採用憲法-子法層級架構

**日期**：2025-12-15

**背景**：需要一個清晰的規則層級系統

**決定**：採用憲法 → 子法 → Skills 三層結構

**理由**：
- 最高原則集中在 CONSTITUTION.md
- 細則可在 bylaws/ 擴展
- Skills 專注於操作程序

### ADR-002: DDD + DAL 獨立

**日期**：2025-12-15

**背景**：確保業務邏輯與資料存取分離

**決定**：Repository 介面在 Domain，實作在 Infrastructure

**理由**：
- 提高可測試性
- Domain 不依賴資料庫技術
- 可替換儲存實作

### ADR-003: uv 優先套件管理

**日期**：2025-12-15

**背景**：Python 套件管理工具選擇

**決定**：優先使用 uv，後備 pip

**理由**：
- 比 pip 快 10-100 倍
- 原生支援 lockfile
- 與 pip 完全相容

## 📦 元件圖

```
.claude/skills/          # 12 個 Skills
├── git-precommit/       # 編排器
├── ddd-architect/       # 架構
├── code-refactor/       # 重構
├── code-reviewer/       # 審查
├── test-generator/      # 測試
├── memory-updater/      # 記憶
├── memory-checkpoint/   # 檢查點
├── readme-updater/      # README
├── changelog-updater/   # CHANGELOG
├── roadmap-updater/     # ROADMAP
├── project-init/        # 初始化
└── git-doc-updater/     # 文檔更新

.github/bylaws/          # 4 個子法
├── ddd-architecture.md
├── git-workflow.md
├── memory-bank.md
└── python-environment.md
```

---

## 🧭 CGU 實際系統架構與成熟度盤點（2026-10-02）

> 上方圖表描述的是源自模板的「規則/記憶層」；本節描述 CGU 產品本體。

### 系統分層

```
呼叫端 Agent（Copilot / Claude / OpenClaw）
        │  MCP（SDK 2，stdio / http）
        ▼
src/cgu/server.py ── MCPServer：24 tools + 2 resources
        │
        ├─ v1 方法論/生成   core/creativity.py（方法設定）, thinking/engine.py → agents/（模板 Agent，不呼叫 LLM）
        ├─ v2 創意機制     core/analogy.py, core/graph.py, core/adversarial.py, core/creativity_core.py（⚠ MCP／CLI 不可達，只有測試使用）
        ├─ v3 Agent 工具   tools/creativity_tools.py（CreativityToolbox，server 端單例）
        ├─ Spark-Soup      soup/spark_soup.py（碎片收集 + 主題錨定 → context soup）
        └─ A2A 協作        brainstorm_protocol.py（雙 Agent 分階段腳本 + 評分 rubric）
        │
        ▼
LLM 後端（CGU_LLM_PROVIDER）
  ollama      → llm/client.py：LangChain ChatOllama + with_structured_output（預設 qwen2.5:3b）
  passthrough → 不呼叫 LLM，回傳思考框架讓呼叫端 LLM 填充（copilot 為已棄用別名）
  無 LLM 可用 → 回傳 "[模擬]" 佔位結果
```

**Fallback 鏈**：LLM 結構化輸出 → passthrough 框架 → `[模擬]` 佔位。閱讀任何 tool 輸出前，先確認走的是哪一段（目前輸出中沒有可機讀的 degraded 旗標）。

**不在 MCP 路徑上**：`graph/`（LangGraph 管線，只有 README 範例的 `run_cgu` 函式庫 API 會用到）與 v2 引擎。

### 24 個 MCP Tools 分組

| 群組 | Tools |
|------|-------|
| v1 方法論/生成 (6) | generate_ideas, spark_collision, associative_expansion, apply_method, select_method, list_methods |
| 深度思考 (3) | deep_think, multi_agent_brainstorm, spark_collision_deep |
| Spark-Soup (4) | spark_soup_generate, spark_soup_quick, collect_creativity_fragments, get_trigger_words |
| A2A 協作 (2) | brainstorm_protocol, evaluate_brainstorm_ideas |
| v3 Agent 工具 (9) | explore_concept, find_connections, check_novelty, evolve_idea_tool, random_concept, suggest_bridges, creativity_session_start / record / progress |

Resources：`cgu://creativity-levels`、`cgu://thinking-modes`

### 實作成熟度（設計宣稱 vs 實際）

> 🔄 2026-10-02 第二輪審查修訂：第一輪對 Spark-Soup、BrainstormProtocol 評得太寬鬆，且漏列 Multi-Agent／ThinkingEngine。完整缺陷清單（40 項）見 [`docs/critical-review-and-improvement-plan.md`](../docs/critical-review-and-improvement-plan.md)。

| 模組 | 設計宣稱 | 實際實作 | 狀態 |
|------|----------|----------|------|
| Spark-Soup | 碎片化 context 激發意外連結 | 固定 107 條素材（名言 20、隨機詞 40、跨域詞 47），與主題無關；MCP 預設 `auto_search=False`，且 `duckduckgo-search` 已改名為 `ddgs`，實測回傳 0 筆；`diversity_score` 含常數 +0.3；效果從未驗證 | 🟡 主題錨定可用，素材與主題無關 |
| BrainstormProtocol | 雙 Agent 發散→碰撞→收斂 | 4 種腳本可用（free／six_hats／scamper／reverse），另 3 種未實作；SCAMPER 寫死「臨床」字樣；評分 rubric 偏好保守點子（大膽 5.20 vs 保守 6.05） | 🟡 框架可用但有偏誤 |
| v1 apply_method | 16 種方法 | 只有 8 種有框架或 LLM 實作；其餘 8 種在任何模式下都回 `[模擬] X 方法應用於 Y`；`select_method` 會推薦未實作的方法 | 🟡 半數為佔位 |
| Multi-Agent（deep_think／multi_agent_brainstorm／spark_collision_deep） | 多個獨立 Agent 並發深度思考 | Explorer／Critic／Wildcard 都不呼叫 LLM；點子是模板拼接，novelty 依人格區間抽亂數（Wildcard 0.7–1.0）；spark 分數＝基礎值＋亂數；`agents` 參數被忽略 | 🔴 模板＋亂數 |
| ThinkingEngine | 智能選擇思考模式 | 依關鍵字（如「結合」）選模式；passthrough 模式下仍會建立 Ollama client 並發出呼叫 | 🔴 模式洩漏 |
| v2 GraphTraversal | 知識空間的非顯而易見路徑 | 演算法為真；50 節點／66 條有向邊的手工資料；反向邊沿用正向關係（如「飲料 is_a 咖啡」）；招牌案例被回傳為最短路徑，創意路徑為 0 條；MCP 路徑不可達 | 🔴 語意錯誤、不可達 |
| v2 AnalogyEngine | 結構同構跨域類比 | 標籤交集比對；4 個真實問題中有 3 個找不到類比；LLM 路徑為 TODO；MCP 路徑不可達 | 🔴 表面比對、不可達 |
| v2 AdversarialEngine | 攻擊→防禦→進化 | 攻擊不讀想法內容；任何輸入都得到 novelty_improvement=1.00、robustness=1.00；MCP 路徑不可達 | 🔴 字串膨脹 |
| v3 ConceptExplorer | 搜尋概念空間 | 11 個硬編碼概念 | 🔴 玩具知識庫 |
| v3 ConnectionFinder | 發現意外連結 | 查不到 → `unexplored`、novelty=0.95；測試把它鎖成規格 | 🔴 把「未知」當「最新穎」 |
| v3 NoveltyChecker | 驗證新穎度 | 空白分詞後與 5 筆假想法比對；資料庫原句也判為新穎 1.00 | 🔴 不可信 |
| v3 Session 工具 | 追蹤探索過程 | 全域單例、無 `session_id`；實測給 A 的想法被寫進 B | 🔴 串線 |

**實測（2026-10-02）**：重現腳本為 [`tests/probes/probe_defects.py`](../tests/probes/probe_defects.py)（不被 pytest 收集），探針與缺陷的對照見審查文件附錄 A。

### 架構洞察

1. **CGU 目前的真實價值在「結構化呼叫端的思考」**（passthrough 框架、方法提示詞、Brainstorm 腳本），而非內部「產生」創意；真正的生成引擎是呼叫端 LLM。
2. **評估是根本缺口**：所有 novelty／surprise／spark 分數都是常數、亂數或字串統計，24 個工具中有 12 個會輸出這類沒有測量程序的數字，無法形成選擇壓力。在有可信評估之前，「演化」「對抗」迴圈都不可能收斂。
3. **工具價值四準則（I／C／S／M）**：工具只有在提供模型外資訊、模型做不到的計算（含獨立 context 取樣）、跨 context 狀態或可驗證測量時才值得存在；目前四項都沒有被實現。
4. **v2 引擎與 LangGraph 管線不在 MCP 路徑上**：server 與 CLI 都沒有呼叫；README 架構圖與實際不符。
5. **工程缺陷**：async 工具內同步呼叫 LLM（事件迴圈停頓與呼叫等長）；passthrough 洩漏；session 串線；狀態不持久；網頁碎片未隔離（prompt injection 面）。
6. **死依賴**：`instructor`、`openai`、`langchain-community` 有宣告，但 `src/` 從未 import。
7. **提案（Q11 以 D-11 預設採用，可否決）**：把「框架」做成 L1 一等公民——Frame 物件記錄目標、假設（硬核／保護帶）、概念、隱喻、評估準則與鉸鏈命題，並以框架算子（negate、swap_metaphor、recut_unit、invert_criterion、tetralemma 等）實作變革型創意。詳見 [`docs/philosophical-inquiry-and-creativity.md`](../docs/philosophical-inquiry-and-creativity.md) §7；落地排程見 P3。
8. **Harness 目標架構（2026-10-02 第四輪）**：方法論（可攜 skills）／能力（MCP，I-C-S-M）／驗證（`evals/`）三層；對外以 Agent Plugins 1.0 打包（`plugins/cgu/`），目標 repo 分層為 `domain／application／infrastructure／interfaces/mcp／experimental`（落實憲法第 1–3 條）。完整配置與事實查證見 [`docs/program-plan.md`](../docs/program-plan.md) §2–§3。

---
*Last updated: 2026-10-02（第二輪審查）*

