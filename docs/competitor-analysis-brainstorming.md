# 競品深度分析：obra/brainstorming

> **「核心競品」** - 與 CGU 同樣聚焦於創意發想，但採用完全不同的設計哲學

---

## 📊 基本資訊

| 屬性 | 值 |
|------|-----|
| **作者** | obra |
| **Stars** | 8,536 ⭐ |
| **Forks** | 709 |
| **來源** | [obra/superpowers](https://github.com/obra/superpowers) |
| **最後更新** | 2 個月前（v3.4.0 簡化版） |
| **月活躍度** | 5,757 次使用（過去 30 天） |

---

## 🎯 設計哲學對比

### brainstorming 的核心理念

```
Use when creating or developing, before writing code or implementation plans - 
refines rough ideas into fully-formed designs through collaborative questioning, 
alternative exploration, and incremental validation. 
Don't use during clear 'mechanical' processes
```

**關鍵特徵：**
1. **蘇格拉底式對話** - 透過提問引導設計
2. **協作式探索** - 人類與 AI 共同發展想法
3. **漸進式驗證** - 每個段落都確認後才繼續
4. **輕量化** - v3.4.0 刻意移除了重量級流程

### CGU 的核心理念

```
Multi-Agent 並行腦力激盪 + 概念碰撞產生火花
```

**關鍵特徵：**
1. **Multi-Agent 架構** - Explorer/Critic/Wildcard 並行思考
2. **概念碰撞** - 讓低關聯概念產生意外火花
3. **深度思考** - shallow/medium/deep 三種深度
4. **工具導向** - 提供 10+ 種創意方法

---

## 🔄 工作流程對比

### brainstorming 流程（v3.4.0 簡化版）

```mermaid
flowchart TD
    A[理解想法] --> B[探索方法]
    B --> C[呈現設計]
    C --> D{確認 OK?}
    D -->|是| E[文件化]
    D -->|否| A
    E --> F[實作計畫]
```

**詳細步驟：**

#### Phase 1: Understanding the Idea
- 先查看專案狀態（files, docs, commits）
- **一次只問一個問題** ← 這是核心原則
- 偏好選擇題，但開放式也可以
- 聚焦：目的、限制、成功標準

#### Phase 2: Exploring Approaches  
- 提出 2-3 個不同方案與權衡
- **以對話方式呈現，帶有推薦與理由**
- 領先展示推薦選項並解釋原因

#### Phase 3: Presenting the Design
- 將設計拆成 **200-300 字小節**
- 每節後詢問是否正確
- 涵蓋：架構、組件、資料流、錯誤處理、測試

#### Phase 4: After the Design
- 寫入 `docs/plans/YYYY-MM-DD-<topic>-design.md`
- 使用 `writing-clearly-and-concisely` skill
- 使用 `using-git-worktrees` 建立獨立工作區
- 使用 `writing-plans` 建立實作計畫

### CGU 流程

```mermaid
flowchart TD
    A[主題輸入] --> B{選擇模式}
    B -->|Simple| C[單次生成]
    B -->|Deep| D[Multi-Agent 並行]
    B -->|Spark| E[概念碰撞]
    C --> F[點子輸出]
    D --> G[Agent 貢獻整合]
    E --> H[火花產生]
    G --> H
    F --> I[最終結果]
    H --> I
```

---

## 💡 關鍵原則對比

| 原則 | brainstorming | CGU |
|------|---------------|-----|
| **互動模式** | 一次一問（Socratic） | 批次生成（Batch） |
| **探索方式** | 提案 2-3 選項 | Multi-Agent 平行 |
| **驗證機制** | 每段落確認 | 驚喜度評分 |
| **輸出格式** | 設計文件 | 點子列表 + 火花 |
| **YAGNI** | 嚴格執行 | 鼓勵探索 |
| **彈性** | 可回溯釐清 | 深度可調 |

---

## 🏗️ 架構對比

### brainstorming 架構（單一 SKILL.md）

```
skills/brainstorming/
└── SKILL.md (54 lines, ~500 words)
```

**特點：**
- 極度簡化（v3.4.0 移除 6-phase 流程）
- 純對話指引，無程式碼
- 依賴其他 skills（writing-plans, using-git-worktrees）

### CGU 架構（完整 MCP Server）

```
cgu/
├── server.py          # MCP 伺服器
├── engine/
│   ├── llm_interface.py
│   ├── thinking_engine.py
│   └── ollama_engine.py
├── creativity/
│   ├── idea_generator.py
│   └── collision_engine.py
└── methods/
    └── 10+ 創意方法
```

**特點：**
- 完整的 Python 套件
- MCP Server 可獨立運行
- 多種 LLM 後端支援
- 可程式化 API

---

## 📈 演進歷史（brainstorming）

| 版本 | 日期 | 變更 |
|------|------|------|
| v3.4.0 | 2025-10-30 | **大幅簡化**：移除 6-phase 流程，回歸對話本質 |
| v3.3.1 | 2025-10-28 | 自主偵察、推薦驅動決策、防止委託回人類 |
| v3.1.0 | 2025-10-17 | 新增 Quick Reference、checklist、flowchart |

**重要洞察：**
> v3.4.0 刻意「去流程化」，說明作者認為過度結構化反而阻礙創意

---

## ⚔️ 競爭力分析

### brainstorming 的優勢

1. **簡單** - 54 行就能運作
2. **整合** - 與 superpowers 生態系無縫協作
3. **人性化** - 蘇格拉底式對話更自然
4. **社群** - 8,500+ stars，活躍維護
5. **實戰驗證** - 來自真實工作流程

### brainstorming 的劣勢

1. **依賴人類** - 需要人類持續回答問題
2. **單一視角** - 沒有 Multi-Agent 多元觀點
3. **缺乏驚喜** - 沒有概念碰撞機制
4. **無法量化** - 沒有創意度評分

### CGU 的優勢

1. **自主性** - 可獨立運行產生多個點子
2. **多元性** - Multi-Agent 平行思考
3. **驚喜性** - 概念碰撞產生意外連結
4. **可量化** - 創意層級、驚喜度評分
5. **方法論** - 10+ 種結構化創意技法

### CGU 的劣勢

1. **複雜** - 需要更多設定
2. **獨立** - 不在 superpowers 生態系內
3. **較新** - 社群基礎尚小
4. **批次** - 不如對話式自然

---

## 🎯 差異化定位

```
               低互動                              高互動
                 │                                  │
                 ▼                                  ▼
    ┌────────────────────────────────────────────────────┐
    │                                                    │
    │   CGU                           brainstorming     │
    │   ████████                              ████████  │
    │   批次生成                              對話探索   │
    │   多Agent                               單一指引   │
    │   概念碰撞                              漸進驗證   │
    │                                                    │
    └────────────────────────────────────────────────────┘
                 ▲                                  ▲
                 │                                  │
            自主發散                            協作收斂
```

---

## 💡 可借鏡之處

### 1. 簡化是進化

> v3.4.0 的教訓：**過度結構化反而阻礙創意**

**CGU 可考慮：**
- 提供「極簡模式」只輸出核心點子
- 減少必填參數，增加智能預設

### 2. 一次一問的魔力

> **One question at a time** - Don't overwhelm with multiple questions

**CGU 可考慮：**
- 新增「互動模式」逐步引導
- `generate_ideas` 可加 `interactive=True` 選項

### 3. YAGNI 精神

> **YAGNI ruthlessly** - Remove unnecessary features from all designs

**CGU 可考慮：**
- 方法選擇加入「最小可用」原則
- 預設推薦最簡單的有效方法

### 4. 推薦驅動

> **Lead with your recommended option** and explain why

**CGU 可考慮：**
- 結果輸出加入「推薦」標記
- 自動排序並解釋為何推薦

---

## 🔮 策略建議

### 短期（v0.4.0）

1. **互補定位** - CGU 專注「批次發散」，不與 brainstorming 直接競爭
2. **極簡模式** - 新增 `quick=True` 快速出點子
3. **推薦機制** - 結果加入 AI 推薦與理由

### 中期（v0.5.0）

1. **對話模式** - 新增 `interactive_brainstorm()` 蘇格拉底式
2. **生態整合** - 考慮成為 superpowers 的擴展 skill
3. **設計輸出** - 新增 `export_design_doc()` 產生設計文件

### 長期

1. **混合模式** - 結合 CGU 發散 + brainstorming 收斂
2. **Workflow** - 提供完整的「想法→設計→計畫」流程
3. **社群** - 投入 superpowers 社群建立關係

---

## 📚 完整 SKILL.md 內容

<details>
<summary>點擊展開完整內容</summary>

```markdown
---
name: brainstorming
description: Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. Don't use during clear 'mechanical' processes
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

## The Process

**Understanding the idea:**
- Check out the current project state first (files, docs, recent commits)
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Presenting the design:**
- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git

**Implementation (if continuing):**
- Ask: "Ready to set up for implementation?"
- Use superpowers:using-git-worktrees to create isolated workspace
- Use superpowers:writing-plans to create detailed implementation plan

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
```

</details>

---

## 🏆 結論

**brainstorming 和 CGU 是互補而非競爭關係：**

| 場景 | 推薦工具 |
|------|----------|
| 需要快速發散多個點子 | **CGU** |
| 需要深入探索單一想法 | **brainstorming** |
| 需要多元視角碰撞 | **CGU** (Multi-Agent) |
| 需要與人類協作驗證 | **brainstorming** |
| 需要結構化創意方法 | **CGU** (SCAMPER, 六頂帽等) |
| 需要產出設計文件 | **brainstorming** + writing-plans |

**最佳實踐：CGU 發散 → brainstorming 收斂 → writing-plans 實作**

---

*最後更新：2025-01-XX*
*分析版本：brainstorming v3.4.0 vs CGU v0.3.0*
