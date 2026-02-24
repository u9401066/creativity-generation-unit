# CGU 專案 Gemini 指引

## 開發哲學 💡
> **「想要寫文件的時候，就更新 Memory Bank 吧！」**
> 
> **「想要零散測試的時候，就寫測試檔案進 tests/ 資料夾吧！」**

## 法規遵循
你必須遵守以下法規層級：
1. **憲法**：`CONSTITUTION.md` - 最高原則
2. **子法**：`.github/bylaws/*.md` - 細則規範
3. **技能**：`.claude/skills/*/SKILL.md` - 操作參考

## 架構原則
- 採用 DDD (Domain-Driven Design)
- DAL (Data Access Layer) 必須獨立
- 參見子法：`.github/bylaws/ddd-architecture.md`

## Python 環境（uv 優先）
- 使用 uv 管理套件與虛擬環境
- 禁止全域安裝套件
- 虛擬環境位於 `.venv/`
- 參見子法：`.github/bylaws/python-environment.md`

## Memory Bank 同步
每次重要操作必須更新 Memory Bank：
- 參見子法：`.github/bylaws/memory-bank.md`
- 目錄：`memory-bank/`

## Git 工作流
提交前必須確認：
1. `ruff check` 通過
2. `ruff format --check` 通過
3. 相關測試通過
- 參見子法：`.github/bylaws/git-workflow.md`

## 專案結構
```
src/cgu/
├── core/       # 核心引擎
├── tools/      # Agent 工具 (v0.4)
├── soup/       # Spark-Soup 創意湯 (v0.5)
├── agents/     # Multi-Agent 系統
├── thinking/   # 思考引擎
├── graph/      # LangGraph
├── llm/        # LLM 後端
└── server.py   # MCP Server
```

## 回應風格
- 使用繁體中文
- 提供清晰的步驟說明
- 引用相關法規條文
