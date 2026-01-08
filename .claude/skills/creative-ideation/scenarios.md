# CGU 使用場景指南

> 根據你的情境，找到最適合的創意工具

---

## 🎯 場景一：新專案發想

**情境**：剛開始一個新專案，需要探索方向和可能性

**推薦流程**：
```
1. deep_think(topic="專案主題", depth="deep", mode="deep")
   → 多 Agent 探索各種可能性

2. generate_ideas(topic="最有潛力的方向", creativity_level=2, count=10)
   → 針對有潛力的方向深入發想

3. apply_method(method="six_hats", input_concept="最佳點子")
   → 全面評估可行性
```

**實際範例**：
```python
# 步驟 1：探索
→ deep_think(
    topic="開發一個幫助遠端團隊協作的工具",
    depth="deep",
    mode="deep"
)

# 步驟 2：聚焦
→ generate_ideas(
    topic="非同步溝通工具創新",
    creativity_level=2,
    count=10
)

# 步驟 3：評估
→ apply_method(
    method="six_hats",
    input_concept="AI 驅動的非同步視訊訊息系統"
)
```

---

## 🔧 場景二：改良現有產品

**情境**：有一個現有產品/功能，想要創新改良

**推薦流程**：
```
1. apply_method(method="scamper", input_concept="現有產品")
   → 7 種變形技巧探索改良方向

2. spark_collision(concept_a="產品核心", concept_b="其他領域概念")
   → 跨域創新靈感

3. apply_method(method="5w2h", input_concept="最佳改良方案")
   → 釐清實作細節
```

**實際範例**：
```python
# 步驟 1：變形
→ apply_method(
    method="scamper",
    input_concept="傳統待辦清單 App"
)
# 輸出：
# S: 用 AI 替代手動輸入
# C: 結合行事曆和專案管理
# A: 借鏡遊戲化機制
# M: 放大社交元素
# P: 用於團隊 OKR 追蹤
# E: 去掉複雜的標籤系統
# R: 從完成驅動改為動機驅動

# 步驟 2：跨域
→ spark_collision(
    concept_a="待辦清單",
    concept_b="社群媒體動態牆"
)

# 步驟 3：釐清
→ apply_method(
    method="5w2h",
    input_concept="社交化的任務完成分享系統"
)
```

---

## 😫 場景三：思考卡關

**情境**：想了很久沒有進展，需要突破

**推薦流程**：
```
1. apply_method(method="reverse", input_concept="你的問題")
   → 反向思考：如何讓情況更糟？

2. select_method(is_stuck=True, creativity_level=3)
   → 讓 AI 推薦適合的方法

3. spark_collision_deep(concept_a="問題", concept_b="完全無關的領域")
   → 強制跨域碰撞產生火花
```

**實際範例**：
```python
# 步驟 1：反向思考
→ apply_method(
    method="reverse",
    input_concept="如何提高用戶留存率"
)
# 輸出：
# 反向問題：如何讓用戶快速流失？
# 失敗方法：
# - 讓 onboarding 超級複雜
# - 發送大量無關推播
# - 隱藏核心功能
# 反轉解法：
# - 30 秒內體驗核心價值
# - 只推送個人化內容
# - 首頁直接展示最強功能

# 步驟 2：AI 推薦
→ select_method(is_stuck=True, creativity_level=3)
# 輸出：推薦 random_input（隨機詞刺激）

# 步驟 3：跨域碰撞
→ spark_collision_deep(
    concept_a="用戶留存",
    concept_b="健身教練"
)
```

---

## 🤔 場景四：決策評估

**情境**：有多個選項，需要全面評估做決定

**推薦流程**：
```
1. apply_method(method="six_hats", input_concept="選項 A")
   → 六個角度分析選項 A

2. apply_method(method="six_hats", input_concept="選項 B")
   → 六個角度分析選項 B

3. multi_agent_brainstorm(topic="A vs B 如何選擇")
   → 多 Agent 討論決策
```

**實際範例**：
```python
# 選項 A 分析
→ apply_method(
    method="six_hats",
    input_concept="使用 React 開發前端"
)

# 選項 B 分析
→ apply_method(
    method="six_hats",
    input_concept="使用 Vue 開發前端"
)

# 綜合討論
→ multi_agent_brainstorm(
    topic="React vs Vue：考量團隊經驗、專案需求、長期維護",
    agents=3
)
```

---

## 🧩 場景五：跨域創新

**情境**：想要結合不同領域產生創新

**推薦流程**：
```
1. spark_collision(concept_a="領域 A", concept_b="領域 B")
   → 快速碰撞產生初步火花

2. spark_collision_deep(concept_a="最佳火花", concept_b="第三領域")
   → 深度碰撞擴展

3. apply_method(method="mandala_9grid", input_concept="最有潛力的組合")
   → 九宮格深度展開
```

**實際範例**：
```python
# 步驟 1：初步碰撞
→ spark_collision(
    concept_a="區塊鏈",
    concept_b="音樂串流"
)
# 輸出火花：
# - 音樂版權自動分潤
# - 歌曲 NFT 收藏
# - 去中心化音樂平台

# 步驟 2：深度碰撞
→ spark_collision_deep(
    concept_a="音樂版權自動分潤",
    concept_b="AI 作曲"
)

# 步驟 3：展開
→ apply_method(
    method="mandala_9grid",
    input_concept="AI 作曲 + 自動版權分潤系統"
)
```

---

## 📊 場景六：問題分析

**情境**：遇到問題需要找出根本原因

**推薦流程**：
```
1. apply_method(method="5w2h", input_concept="問題現象")
   → 釐清問題的各個面向

2. apply_method(method="fishbone", input_concept="問題")
   → 6M 因果分析找根因

3. generate_ideas(topic="解決根因", creativity_level=1, count=5)
   → 針對根因發想解法
```

**實際範例**：
```python
# 步驟 1：釐清問題
→ apply_method(
    method="5w2h",
    input_concept="App 啟動速度變慢"
)

# 步驟 2：根因分析
→ apply_method(
    method="fishbone",
    input_concept="App 啟動速度變慢"
)
# 輸出 6M 分析：
# - Man (人員)：新人不熟悉效能優化
# - Method (方法)：缺乏效能測試流程
# - Material (材料)：第三方 SDK 過多
# - Machine (設備)：測試機規格太高
# - Measurement (測量)：沒有監控啟動時間
# - Environment (環境)：Debug 模式未關閉

# 步驟 3：解決根因
→ generate_ideas(
    topic="減少第三方 SDK 對啟動速度的影響",
    creativity_level=1,
    count=5
)
```

---

## 🎨 場景七：團隊共創

**情境**：需要收集團隊多元意見並整合

**推薦流程**：
```
1. multi_agent_brainstorm(topic="議題", agents=5)
   → 模擬多人不同角度思考

2. apply_method(method="kj_method", input_concept="所有點子")
   → 收集、分群、命名

3. apply_method(method="six_hats", input_concept="各群組主題")
   → 評估各方向
```

**實際範例**：
```python
# 步驟 1：多角度發想
→ multi_agent_brainstorm(
    topic="如何提升團隊的創新文化",
    agents=5,
    thinking_steps=3,
    collision_count=5
)

# 步驟 2：整理分類（手動或使用 AI）
# 將點子分成：
# - 環境面：開放空間、創意牆、休息區
# - 制度面：創新時間、失敗獎勵、輪調
# - 活動面：黑客松、讀書會、跨部門交流

# 步驟 3：評估各方向
→ apply_method(
    method="six_hats",
    input_concept="導入每週五下午創新時間制度"
)
```

---

## 💡 場景八：快速原型發想

**情境**：需要快速產生可測試的概念

**推薦流程**：
```
1. generate_ideas(topic="目標", creativity_level=2, count=10)
   → 快速產生多個概念

2. apply_method(method="scamper", input_concept="最佳概念")
   → 快速變形產生變體

3. apply_method(method="5w2h", input_concept="選定概念")
   → 快速釐清原型範圍
```

---

## 🔄 通用技巧

### 方法串接

```
發散 → 收斂 → 發散 → 收斂
brainstorm → six_hats → scamper → 5w2h
```

### 創意層級遞進

```
Level 1 (安全) → Level 2 (探索) → Level 3 (突破)
組合既有 → 跨域連結 → 顛覆常規
```

### 卡關急救

```
reverse → random_input → spark_collision_deep
反向思考 → 隨機刺激 → 強制碰撞
```

---

*CGU v0.3.0 - Scenario Guide*
