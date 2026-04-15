# Progress (Updated: 2026-04-15)

## Done

- [x] 完成 v2/v3 創意核心、Agent-Driven 工具與 MCP 基礎能力整理（2026-01-06）
- [x] 補上 Spark-Soup、互動式 Session 與 ExplorerAgent LLM 整合等 v0.5.x 相關能力（2026-04-11）
- [x] 將 `ROADMAP.md` 重寫為正式產品路線圖，對齊目前版本狀態與後續里程碑（2026-04-15）

## Doing

- [ ] 整理正式 roadmap PR 說明，確認文檔治理敘事一致

## Next

- [ ] 對齊 `CHANGELOG.md` 與 README 的版本敘事
- [ ] 將 v0.5.x 工作流閉環（Session × Evaluation × Logging）定義得更完整
- [ ] 規劃 v0.6 的外部知識源與語義排序能力

## Blocked

- [ ] 現有 `ruff check .` 與 `mypy src` 在未修改的既有程式碼上即失敗；`pytest` 亦因本機未啟動 Ollama 而於 LLM 測試收集階段中斷
