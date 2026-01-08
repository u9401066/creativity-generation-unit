# CGU 工具使用範例

> 實際呼叫範例與輸出說明

---

## 🚀 generate_ideas - 批次創意生成

### 基本用法

```python
→ generate_ideas(
    topic="如何讓閱讀習慣更容易養成",
    creativity_level=2,
    count=5
)
```

### 輸出範例

```json
{
  "topic": "如何讓閱讀習慣更容易養成",
  "creativity_level": "EXPLORATORY",
  "ideas": [
    {
      "id": 1,
      "content": "微型閱讀：每天只讀一頁，降低啟動門檻",
      "association_score": 0.70
    },
    {
      "id": 2,
      "content": "社交閱讀：與朋友組成讀書小組，互相督促",
      "association_score": 0.65
    },
    {
      "id": 3,
      "content": "場景觸發：將書放在固定位置，看到就讀",
      "association_score": 0.60
    },
    {
      "id": 4,
      "content": "獎勵機制：完成閱讀解鎖下一章節有聲版",
      "association_score": 0.55
    },
    {
      "id": 5,
      "content": "替代方案：通勤時用有聲書替代音樂",
      "association_score": 0.50
    }
  ],
  "method_used": "llm_brainstorm"
}
```

### 參數說明

| 參數 | 類型 | 說明 |
|------|------|------|
| `topic` | str | 發想主題（必填） |
| `creativity_level` | int | 1=組合, 2=探索, 3=變革 |
| `count` | int | 點子數量（預設 5） |
| `constraints` | list | 限制條件（選填） |

---

## 💥 spark_collision - 概念碰撞

### 基本用法

```python
→ spark_collision(
    concept_a="咖啡店",
    concept_b="健身房"
)
```

### 輸出範例

```json
{
  "concept_a": "咖啡店",
  "concept_b": "健身房",
  "sparks": [
    "運動咖啡館：邊騎飛輪邊喝咖啡",
    "蛋白質拿鐵：運動後的蛋白質咖啡飲品",
    "社交健身空間：健身完在咖啡區交流",
    "訂閱制健康生活：月費包含健身和咖啡",
    "能量補給站：運動前後的營養咖啡吧"
  ],
  "rationale": "咖啡店的社交舒適氛圍 + 健身房的健康運動元素，創造新型態的健康社交空間",
  "association_score": 0.3
}
```

### 使用技巧

- 兩個概念距離越遠，火花越有創意
- 嘗試不同領域：科技 × 傳統、藝術 × 工程
- 連續碰撞：將火花再與新概念碰撞

---

## 🎩 apply_method - 應用創意方法

### SCAMPER 範例

```python
→ apply_method(
    method="scamper",
    input_concept="傳統書店"
)
```

**輸出：**
```json
{
  "method": "scamper",
  "output": {
    "S_substitute": "用 AI 店員替代人工推薦",
    "C_combine": "結合咖啡廳和閱讀空間",
    "A_adapt": "借鏡圖書館的分類和查詢系統",
    "M_modify": "縮小成自動販賣機形式的迷你書店",
    "P_put_to_other_uses": "變成作家簽書會和讀書會場地",
    "E_eliminate": "去掉實體庫存，改為展示+線上訂購",
    "R_reverse": "讓讀者決定要進什麼書",
    "best_idea": "C: 書店 + 咖啡 + 共享工作空間的複合體驗"
  }
}
```

### 六頂思考帽範例

```python
→ apply_method(
    method="six_hats",
    input_concept="在公司推行遠端工作政策"
)
```

**輸出：**
```json
{
  "method": "six_hats",
  "output": {
    "white_facts": "目前 30% 員工已遠端，生產力數據持平，設備成本可降 20%",
    "red_feelings": "年輕員工期待彈性，資深主管擔心失控，團隊凝聚力受質疑",
    "black_risks": "溝通成本增加、新人融入困難、資安風險、績效難評估",
    "yellow_benefits": "人才招募範圍擴大、員工滿意度提升、辦公室成本降低",
    "green_ideas": "混合制（週三必到）、虛擬辦公室、異步溝通文化培訓",
    "blue_summary": "建議先試行 3 個月混合制，設立 KPI 追蹤，再決定全面政策"
  }
}
```

### 逆向思考範例

```python
→ apply_method(
    method="reverse",
    input_concept="如何提高客戶滿意度"
)
```

**輸出：**
```json
{
  "method": "reverse",
  "output": {
    "reverse_question": "如何讓客戶徹底失望？",
    "failure_methods": [
      "永遠不回覆客戶訊息",
      "把問題推給其他部門",
      "只用機器人回覆，沒有真人",
      "承諾做不到的事",
      "對客戶抱怨表現不耐煩"
    ],
    "solutions": [
      "30 分鐘內必回覆，即使只是告知處理中",
      "設立單一窗口，一人負責到底",
      "重要問題確保真人介入",
      "承諾前確認可行性",
      "建立客訴處理 SOP，保持同理心"
    ]
  }
}
```

---

## 🧠 deep_think - 深度思考

### 基本用法

```python
→ deep_think(
    topic="如何在 AI 時代保持競爭力",
    depth="deep",
    mode="deep"
)
```

### 輸出範例

```json
{
  "mode_used": "deep",
  "topic": "如何在 AI 時代保持競爭力",
  "ideas": [
    {
      "content": "發展 AI 無法取代的人際能力：同理心、說服力、領導力",
      "source": "explorer",
      "novelty": 0.65
    },
    {
      "content": "成為 AI 的指揮者而非被取代者：學習 prompt engineering",
      "source": "explorer",
      "novelty": 0.70
    },
    {
      "content": "風險：過度依賴 AI 導致基礎能力退化",
      "source": "critic",
      "novelty": 0.45
    },
    {
      "content": "瘋狂想法：與 AI 共生，植入腦機介面",
      "source": "wildcard",
      "novelty": 0.95
    }
  ],
  "sparks": [
    {
      "content": "AI 增強的人際溝通：用 AI 分析對方情緒，優化溝通策略",
      "source_ideas": ["人際能力", "AI 指揮者"],
      "spark_value": 0.48
    }
  ],
  "best_ideas": [...],
  "agent_contributions": [
    {"agent_id": "explorer_xxx", "personality": "explorer", "idea_count": 3},
    {"agent_id": "critic_xxx", "personality": "critic", "idea_count": 2},
    {"agent_id": "wildcard_xxx", "personality": "wildcard", "idea_count": 2}
  ]
}
```

### 模式說明

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| `simple` | 單次快速生成 | 簡單主題、時間緊迫 |
| `deep` | Multi-Agent 並行 | 複雜問題、需要多角度 |
| `spark` | 概念碰撞 | 需要創意火花 |

---

## 👥 multi_agent_brainstorm - 多 Agent 腦力激盪

### 基本用法

```python
→ multi_agent_brainstorm(
    topic="設計一個創新的線上教育平台",
    agents=3,
    thinking_steps=3,
    collision_count=5
)
```

### 輸出範例

```json
{
  "topic": "設計一個創新的線上教育平台",
  "mode": "multi_agent",
  "agent_contributions": [
    {
      "agent_id": "explorer_abc",
      "personality": "explorer",
      "ideas": [
        "遊戲化學習路徑，像玩 RPG 一樣升級",
        "AI 助教 24/7 即時答疑",
        "學習夥伴配對系統"
      ]
    },
    {
      "agent_id": "critic_def",
      "personality": "critic",
      "ideas": [
        "遊戲化可能讓學習變得膚淺",
        "AI 答疑準確度需要驗證",
        "配對可能造成隱私問題"
      ]
    },
    {
      "agent_id": "wildcard_ghi",
      "personality": "wildcard",
      "ideas": [
        "VR 實境教室，感覺真的在上課",
        "學習幣可以換真實商品",
        "讓學生教 AI，AI 再教其他學生"
      ]
    }
  ],
  "sparks": [
    {
      "content": "AI 學習夥伴：結合 AI 助教和配對系統，創造個人化的 AI 學習夥伴",
      "spark_value": 0.52
    }
  ],
  "best_ideas": [...]
}
```

---

## 🔍 select_method - 方法選擇器

### 基本用法

```python
→ select_method(
    creativity_level=2,
    prefer_fast=True,
    is_stuck=True,
    purpose="強制創新"
)
```

### 輸出範例

```json
{
  "recommended_method": "random_input",
  "description": "隨機詞強制聯想",
  "category": "divergent",
  "thinking_speed": "fast",
  "agent_strategy": "隨機選詞，強制與主題建立連結",
  "selection_reason": {
    "creativity_level": "EXPLORATORY",
    "prefer_fast": true,
    "is_stuck": true,
    "purpose": "強制創新"
  }
}
```

---

## 🌳 associative_expansion - 聯想擴展

### 基本用法

```python
→ associative_expansion(
    seed="永續發展",
    direction="cross-domain",
    depth=2
)
```

### 輸出範例

```json
{
  "seed": "永續發展",
  "direction": "cross-domain",
  "depth": 2,
  "associations": [
    {
      "level": 1,
      "concepts": ["循環經濟", "綠色科技", "社會企業", "ESG 投資", "碳中和"]
    },
    {
      "level": 2,
      "concepts": ["二手經濟平台", "太陽能區塊鏈", "影響力投資", "碳權交易", "零廢棄生活"]
    }
  ]
}
```

### 方向說明

| 方向 | 說明 | 範例 |
|------|------|------|
| `similar` | 相似概念 | 蘋果 → 梨子、橘子 |
| `opposite` | 相反概念 | 熱 → 冷、溫度 |
| `random` | 隨機連結 | 咖啡 → 太空、音樂 |
| `cross-domain` | 跨領域 | 教育 → 遊戲、區塊鏈 |

---

## 📋 list_methods - 方法清單

### 用法

```python
→ list_methods()
```

### 輸出

```json
{
  "total_methods": 16,
  "categories": ["divergent", "structural", "perspective", "process", "systematic"],
  "methods_by_category": {
    "divergent": [
      {"name": "mind_map", "description": "從中心概念向外放射擴展", "thinking_speed": "fast"},
      {"name": "brainstorm", "description": "不批判的快速點子生成", "thinking_speed": "fast"},
      {"name": "scamper", "description": "7種變形技巧", "thinking_speed": "fast"},
      {"name": "random_input", "description": "隨機詞強制聯想", "thinking_speed": "fast"}
    ],
    ...
  }
}
```

---

## 🔗 組合技範例

### 產品創新全流程

```python
# 1. 發散：大量點子
→ generate_ideas(topic="智慧家居創新", creativity_level=2, count=15)

# 2. 碰撞：跨域靈感
→ spark_collision(concept_a="智慧家居", concept_b="寵物照護")

# 3. 變形：深化最佳點子
→ apply_method(method="scamper", input_concept="智慧寵物餵食器")

# 4. 評估：多角度分析
→ apply_method(method="six_hats", input_concept="AI 驅動的寵物健康管理系統")

# 5. 細化：釐清實作
→ apply_method(method="5w2h", input_concept="寵物健康管理 MVP")
```

---

*CGU v0.3.0 - Tool Examples*
