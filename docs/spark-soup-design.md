# Spark-Soup：Context Stuffing for Creativity

> **設計文件** | v0.5.0 新功能
> 
> **核心洞察**：模擬人類創意發生過程 - 用碎片化資訊填充 context，讓 LLM 產生意外連結

---

## 💡 設計理念

### 人類如何產生新想法？

```
新聞 + 新書 + 新體驗 + 新旅行 + 自我對話
                ↓
       碎片化資訊在腦中累積
                ↓
          意外連結 → 新想法！
```

### 問題：LLM 缺乏「生活經驗」

- 傳統方法：給 LLM 主題 → 直接要求產生想法
- 結果：容易產生「顯而易見」的想法，缺乏驚喜

### 解法：Context Stuffing

用**碎片化、多來源、看似無關**的資訊填滿 context window，讓 LLM 有「原料」可以連結：

```
┌─────────────────────────────────────────────────────────┐
│                   Context Window                         │
├─────────────────────────────────────────────────────────┤
│  🎯 主題: "遠距工作生產力"                              │
│  📰 碎片1: 咖啡因研究顯示清晨效率最高                   │
│  📖 碎片2: 日本 ikigai 概念：生活的意義                 │
│  🎯 主題: "遠距工作生產力"  ← 重複錨定                  │
│  ✈️ 碎片3: 峇里島數位游牧民在稻田旁工作                 │
│  💭 碎片4: 番茄工作法 25分鐘專注                        │
│  🎲 發想詞: 結合、顛覆、如果...會怎樣？                 │
│  🎯 主題: "遠距工作生產力"  ← 再次錨定                  │
│  🧩 碎片5: 蜂巢協作模式 - 蜜蜂如何分工                  │
│  🎭 碎片6: 即興劇 "Yes, and..." 原則                    │
│  ...                                                     │
└─────────────────────────────────────────────────────────┘
                       ↓
              LLM 自動產生意外連結！
```

---

## 🏗️ 架構設計

### 組件圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Spark-Soup Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Fragment     │   │ Fragment     │   │ Fragment     │    │
│  │ Collector    │   │ Processor    │   │ Injector     │    │
│  │              │   │              │   │              │    │
│  │ • DuckDuckGo │   │ • 微壓縮     │   │ • 主題錨定   │    │
│  │ • Wikipedia  │   │ • 多樣性     │   │ • 發想詞     │    │
│  │ • 使用者輸入 │   │ • 相關性     │   │ • 隨機排序   │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Soup Assembler                      │   │
│  │                                                       │   │
│  │   1. 收集碎片 → 2. 處理碎片 → 3. 組裝湯底            │   │
│  │                                                       │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 spark_soup() MCP Tool                 │   │
│  │                                                       │   │
│  │   輸出：組裝好的 Context Soup                         │   │
│  │   → 傳給 LLM 產生創意連結                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 API 設計

### MCP Tools

#### 1. `spark_soup` - 組裝創意湯

```python
@mcp.tool()
async def spark_soup(
    topic: str,
    fragment_count: int = 20,
    topic_repetition: int = 5,
    auto_search: bool = True,
    custom_fragments: list[str] | None = None,
    trigger_words: list[str] | None = None
) -> SparkSoupResult:
    """
    組裝「創意湯」- 用碎片化資訊填充 context
    
    Args:
        topic: 主題（會在 soup 中重複多次避免遺忘）
        fragment_count: 碎片數量（預設 20）
        topic_repetition: 主題重複次數（預設 5）
        auto_search: 是否自動搜尋外部資訊
        custom_fragments: 使用者自訂碎片
        trigger_words: 發想觸發詞
    
    Returns:
        SparkSoupResult:
            - soup: str  # 組裝好的 context soup
            - fragments_used: list[Fragment]  # 使用的碎片列表
            - diversity_score: float  # 多樣性評分
    """
```

#### 2. `collect_fragments` - 收集碎片

```python
@mcp.tool()
async def collect_fragments(
    topic: str,
    sources: list[str] = ["duckduckgo", "wikipedia", "quotes"],
    count_per_source: int = 5,
    randomness: float = 0.7
) -> list[Fragment]:
    """
    從多個來源收集碎片化資訊
    
    Args:
        topic: 相關主題（用於引導搜尋）
        sources: 資料來源
            - "duckduckgo": 新聞搜尋
            - "wikipedia": 維基百科隨機相關頁面
            - "quotes": 名言金句
            - "concepts": ConceptNet 相關概念
        count_per_source: 每個來源收集數量
        randomness: 隨機性（0-1，越高越隨機）
    
    Returns:
        list[Fragment]: 碎片列表，每個包含：
            - content: str  # 碎片內容
            - source: str   # 來源
            - relevance: float  # 相關性
    """
```

#### 3. `generate_from_soup` - 從湯中生成想法

```python
@mcp.tool()
async def generate_from_soup(
    soup: str,
    idea_count: int = 5,
    creativity_level: float = 0.8
) -> list[Idea]:
    """
    從 Spark Soup 中生成創意想法
    
    Args:
        soup: spark_soup() 產生的 context soup
        idea_count: 想要生成的想法數量
        creativity_level: 創意程度（0-1）
    
    Returns:
        list[Idea]: 生成的想法，每個包含：
            - title: str  # 想法標題
            - description: str  # 描述
            - connected_fragments: list[str]  # 連結了哪些碎片
            - novelty_score: float  # 新穎度評分
    """
```

---

## 🎲 碎片來源設計

### 1. DuckDuckGo 搜尋

```python
class DuckDuckGoCollector:
    """從 DuckDuckGo 收集新聞碎片"""
    
    async def collect(self, topic: str, count: int) -> list[Fragment]:
        # 搜尋相關 + 隨機延伸主題
        queries = [
            topic,
            f"{topic} 新趨勢",
            f"{topic} 意外發現",
            self._random_extension(topic)  # 隨機延伸
        ]
        # ...
```

### 2. Wikipedia 隨機頁面

```python
class WikipediaCollector:
    """從 Wikipedia 收集知識碎片"""
    
    async def collect(self, topic: str, count: int) -> list[Fragment]:
        # 策略：相關頁面 + 完全隨機頁面
        related = await self._get_related_pages(topic)
        random = await self._get_random_pages()
        # 混合產生意外連結機會
        return self._mix(related, random, ratio=0.6)
```

### 3. 名言金句

```python
class QuotesCollector:
    """收集名言金句作為思考觸發"""
    
    QUOTES = [
        "創意就是連結事物。 — Steve Jobs",
        "限制激發創意。 — 不詳",
        "好的藝術家複製，偉大的藝術家偷竊。 — Picasso",
        # ...內建 100+ 創意相關名言
    ]
```

### 4. ConceptNet 概念

```python
class ConceptNetCollector:
    """從 ConceptNet 收集相關概念"""
    
    async def collect(self, topic: str, count: int) -> list[Fragment]:
        # 獲取概念關係
        relations = await self._get_relations(topic)
        # 返回意外關聯
        return [f for f in relations if f.relation in ["RelatedTo", "UsedFor", "SymbolOf"]]
```

---

## 🎯 發想詞庫

### 內建觸發詞

```python
TRIGGER_WORDS = {
    "combination": [
        "如果把 A 和 B 結合會怎樣？",
        "這兩個概念有什麼共通點？",
        "把這個放到另一個領域會變成什麼？",
    ],
    "inversion": [
        "如果完全相反會怎樣？",
        "把這個顛倒過來呢？",
        "如果缺點變成優點呢？",
    ],
    "scale": [
        "如果放大 10 倍呢？",
        "如果縮小到極致呢？",
        "如果給無限資源呢？",
    ],
    "time": [
        "100 年後會變成什麼樣子？",
        "如果在古代就有這個呢？",
        "如果必須在 1 小時內完成呢？",
    ],
    "perspective": [
        "如果是小孩來看這個問題呢？",
        "如果是外星人第一次看到呢？",
        "如果競爭對手這樣做呢？",
    ],
}
```

---

## 🔧 實作要點

### 1. 主題錨定策略

```python
def assemble_soup(topic: str, fragments: list[Fragment], repetition: int = 5) -> str:
    """組裝 soup，確保主題不被遺忘"""
    
    soup_parts = []
    interval = len(fragments) // (repetition + 1)
    
    for i, fragment in enumerate(fragments):
        # 每隔 N 個碎片插入主題錨定
        if i % interval == 0:
            soup_parts.append(f"\n🎯 **主題提醒**: {topic}\n")
        
        soup_parts.append(f"📌 {fragment.content}")
    
    return "\n".join(soup_parts)
```

### 2. 多樣性確保

```python
def ensure_diversity(fragments: list[Fragment]) -> list[Fragment]:
    """確保碎片多樣性"""
    
    # 按來源分組
    by_source = defaultdict(list)
    for f in fragments:
        by_source[f.source].append(f)
    
    # 交錯排列
    result = []
    while any(by_source.values()):
        for source in list(by_source.keys()):
            if by_source[source]:
                result.append(by_source[source].pop(0))
    
    return result
```

### 3. 隨機性控制

```python
def add_randomness(fragments: list[Fragment], level: float = 0.3) -> list[Fragment]:
    """加入隨機性"""
    
    n_random = int(len(fragments) * level)
    random_indices = random.sample(range(len(fragments)), n_random)
    
    for i in random_indices:
        fragments[i] = get_completely_random_fragment()
    
    return fragments
```

---

## 📊 評估指標

### 1. 多樣性評分 (Diversity Score)

```python
def calculate_diversity(fragments: list[Fragment]) -> float:
    """計算碎片多樣性"""
    
    # 來源多樣性
    source_entropy = entropy([f.source for f in fragments])
    
    # 語義多樣性（使用 embedding 距離）
    embeddings = [get_embedding(f.content) for f in fragments]
    semantic_diversity = mean_pairwise_distance(embeddings)
    
    return (source_entropy + semantic_diversity) / 2
```

### 2. 連結品質評分 (Connection Quality)

```python
def evaluate_connection(idea: Idea, fragments: list[Fragment]) -> float:
    """評估想法與碎片的連結品質"""
    
    # 連結數量
    connection_count = len(idea.connected_fragments)
    
    # 連結距離（越遠越有創意）
    distances = [
        semantic_distance(idea.embedding, f.embedding)
        for f in idea.connected_fragments
    ]
    
    return mean(distances) * log(connection_count + 1)
```

---

## 🚀 使用範例

### 基本使用

```python
# 1. 組裝創意湯
soup = await spark_soup(
    topic="遠距工作生產力",
    fragment_count=20,
    auto_search=True
)

# 2. 從湯中生成想法
ideas = await generate_from_soup(
    soup=soup.soup,
    idea_count=5
)

for idea in ideas:
    print(f"💡 {idea.title}")
    print(f"   連結: {idea.connected_fragments}")
    print(f"   新穎度: {idea.novelty_score}")
```

### 進階使用

```python
# 先收集碎片
fragments = await collect_fragments(
    topic="遠距工作",
    sources=["duckduckgo", "wikipedia", "quotes"],
    randomness=0.8  # 高隨機性
)

# 加入自訂碎片
custom = [
    "我昨天在咖啡廳看到一個人用 iPad 開會",
    "日本有個概念叫 kaizen - 持續改善",
    "蜜蜂的協作模式非常高效"
]

# 組裝
soup = await spark_soup(
    topic="遠距工作生產力",
    custom_fragments=custom,
    trigger_words=["如果顛倒呢？", "100年後會變成？"]
)
```

---

## 📅 實作計畫

### Phase 1: 核心工具 (v0.5.0)

- [ ] 實作 `spark_soup()` MCP Tool
- [ ] 實作基本碎片組裝邏輯
- [ ] 內建發想詞庫

### Phase 2: 自動收集 (v0.5.1)

- [ ] 整合 DuckDuckGo 搜尋
- [ ] 整合 Wikipedia API
- [ ] 內建名言金句庫

### Phase 3: 進階功能 (v0.6.0)

- [ ] 整合 ConceptNet
- [ ] Embedding 語義距離計算
- [ ] 多樣性/連結品質評分

---

## 🔗 相關資源

- [CGU ROADMAP](../ROADMAP.md)
- [Creative Ideation Skill](../.claude/skills/creative-ideation/SKILL.md)
- [Competitor Analysis](./competitor-analysis-brainstorming.md)

---

*創建日期: 2026-01-08*
*作者: u9401066 <u9401066@gap.kmu.edu.tw>*
*狀態: 設計中*
