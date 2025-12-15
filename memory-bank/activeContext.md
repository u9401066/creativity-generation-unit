# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## Current Goals

<!-- 一句話描述正在做什麼 -->
- 測試 CGU vLLM 整合功能，確認 Agent 可以使用真實 LLM 生成創意

## 🎯 當前焦點

- **vLLM 整合已完成** - 所有 9 個思考節點已接入 LLM

## 📝 已完成的變更

| 檔案 | 變更內容 |
|------|----------|
| `src/cgu/llm/client.py` | vLLM + Instructor 客戶端 |
| `src/cgu/llm/schemas.py` | Pydantic 結構化輸出模型 |
| `src/cgu/llm/prompts.py` | 提示詞模板 |
| `src/cgu/graph/nodes.py` | 整合 LLM 呼叫（含 fallback） |
| `.env.example` | 環境變數配置範例 |

## ⚠️ 待解決

- 安裝依賴 (`uv sync`)
- 啟動 vLLM 服務器測試
- 更新 README.zh-TW.md

## 💡 重要決定

- LLM 採用延遲載入機制，避免無 LLM 時程式崩潰
- 支援模擬模式 (`CGU_USE_LLM=false`)，方便開發測試
- Structured Output 使用 Instructor + Pydantic

## 📁 相關檔案

```
src/cgu/
├── core/
│   ├── thinking.py    # 快思慢想 ✅
│   └── creativity.py  # 創意方法 ✅
├── graph/
│   ├── state.py       # LangGraph 狀態 ✅
│   ├── nodes.py       # 思考節點 (整合LLM) ✅
│   └── builder.py     # 圖建構器 ✅
├── llm/
│   ├── client.py      # vLLM 客戶端 ✅
│   ├── schemas.py     # 輸出模型 ✅
│   └── prompts.py     # 提示詞 ✅
├── server.py          # FastMCP Server ✅
└── cli.py             # CLI 介面 ✅
```

## 🔜 下一步

1. `uv sync --all-extras` 安裝依賴
2. 測試模擬模式運行
3. 更新 README.zh-TW.md
4. Git push

---
*Last updated: 2025-01-XX*