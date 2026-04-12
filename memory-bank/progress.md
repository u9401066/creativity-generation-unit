# Progress (Updated: 2026-04-12)

## Done

### v2 核心引擎
- CGU v2 核心引擎設計與實作
- AnalogyEngine - 跨領域類比搜尋器
- ConceptGraph/GraphTraversalEngine - 概念圖譜遍歷
- AdversarialEngine - 對抗式創意進化
- CreativityCore - 統一創意引擎
- 測試檔案 test_creativity_core_v2.py

### v3 Agent-Driven Tools
- ConceptExplorer - 概念搜尋器
- ConnectionFinder - 連結發現器
- NoveltyChecker - 新穎度驗證器
- IdeaEvolver - 想法演化器
- CreativityLogger - 創意記錄器
- CreativityToolbox - 統一工具箱
- 核心轉變：從「Prompt 描述」到「Agent 自主工具互動」

### v3 MCP Tool 註冊 🆕
- explore_concept - 概念探索 MCP 工具
- find_connections - 連結發現 MCP 工具
- check_novelty - 新穎度驗證 MCP 工具
- evolve_idea_tool - 想法演化 MCP 工具
- random_concept - 隨機概念 MCP 工具
- suggest_bridges - 橋接建議 MCP 工具
- creativity_session_start - 開始創意會話 MCP 工具
- creativity_session_record - 記錄想法 MCP 工具
- creativity_session_progress - 查看進度 MCP 工具
- 測試檔案 test_creativity_tools.py (52 tests)

### v3 可靠性強化 🆕
- record_idea/log_idea 加入會話存在驗證，避免靜默失敗
- MCP creativity_session_record 返回結構化錯誤與 success 標記
- 測試補齊：未啟動會話的錯誤情境與 MCP 回傳路徑

## Doing

- 追蹤 LLM 相關測試所需的本地 Ollama 服務（tests/test_llm_basic.py、tests/test_scamper_llm.py）

## Next

- 外部知識源整合（ConceptNet, Wikidata）
- Embedding 語義距離計算
- 擴充 ConceptExplorer 知識庫
- Agent 自主探索流程優化
- 品質評估系統（NUS 模型）
