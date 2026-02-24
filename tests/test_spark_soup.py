"""
Spark-Soup 模組測試

測試碎片收集、湯組裝、多樣性計算等功能。
"""

import pytest

from cgu.soup import (
    CREATIVITY_QUOTES,
    CROSS_DOMAIN_CONCEPTS,
    RANDOM_CONCEPTS,
    TRIGGER_WORDS,
    Fragment,
    FragmentSource,
    QuotesCollector,
    RandomConceptCollector,
    SoupAssembler,
    SparkSoupResult,
    collect_fragments,
    get_assembler,
    spark_soup,
)

# === 內建資料庫測試 ===


class TestBuiltinData:
    """測試內建資料庫"""

    def test_trigger_words_categories(self):
        """觸發詞應有 6 個類別"""
        expected_categories = {
            "combination",
            "inversion",
            "scale",
            "time",
            "perspective",
            "emotion",
        }
        assert set(TRIGGER_WORDS.keys()) == expected_categories

    def test_trigger_words_not_empty(self):
        """每個類別至少有 3 個觸發詞"""
        for category, words in TRIGGER_WORDS.items():
            assert len(words) >= 3, f"{category} 類別觸發詞不足"

    def test_creativity_quotes_count(self):
        """名言金句至少 15 條"""
        assert len(CREATIVITY_QUOTES) >= 15

    def test_random_concepts_count(self):
        """隨機概念至少 30 個"""
        assert len(RANDOM_CONCEPTS) >= 30

    def test_cross_domain_categories(self):
        """跨領域概念至少 5 個類別"""
        assert len(CROSS_DOMAIN_CONCEPTS) >= 5

    def test_cross_domain_concepts_not_empty(self):
        """每個跨領域類別至少 3 個概念"""
        for domain, concepts in CROSS_DOMAIN_CONCEPTS.items():
            assert len(concepts) >= 3, f"{domain} 領域概念不足"


# === Fragment 測試 ===


class TestFragment:
    """測試 Fragment 資料類別"""

    def test_fragment_creation(self):
        """基本建立"""
        f = Fragment(content="測試碎片", source=FragmentSource.USER)
        assert f.content == "測試碎片"
        assert f.source == FragmentSource.USER
        assert f.relevance == 0.5

    def test_fragment_with_relevance(self):
        """自訂相關性"""
        f = Fragment(content="高相關", source=FragmentSource.USER, relevance=0.9)
        assert f.relevance == 0.9

    def test_fragment_str(self):
        """字串輸出"""
        f = Fragment(content="測試內容", source=FragmentSource.QUOTES)
        assert "📌" in str(f)
        assert "測試內容" in str(f)


# === 收集器測試 ===


class TestCollectors:
    """測試碎片收集器"""

    @pytest.mark.asyncio
    async def test_quotes_collector(self):
        """名言收集器"""
        collector = QuotesCollector()
        fragments = await collector.collect("any topic", count=5)
        assert len(fragments) == 5
        assert all(f.source == FragmentSource.QUOTES for f in fragments)

    @pytest.mark.asyncio
    async def test_quotes_collector_count_limit(self):
        """名言收集器數量上限"""
        collector = QuotesCollector()
        fragments = await collector.collect("any", count=3)
        assert len(fragments) == 3

    @pytest.mark.asyncio
    async def test_random_concept_collector(self):
        """隨機概念收集器"""
        collector = RandomConceptCollector()
        fragments = await collector.collect("any topic", count=8)
        assert len(fragments) == 8
        assert all(f.source == FragmentSource.RANDOM for f in fragments)

    @pytest.mark.asyncio
    async def test_random_concept_diversity(self):
        """隨機概念應包含隨機和跨領域"""
        collector = RandomConceptCollector()
        fragments = await collector.collect("any", count=10)
        contents = [f.content for f in fragments]
        has_random = any("隨機概念" in c for c in contents)
        has_cross = any("領域" in c for c in contents)
        assert has_random or has_cross


# === SoupAssembler 測試 ===


class TestSoupAssembler:
    """測試湯組裝器"""

    def test_assembler_singleton(self):
        """單例模式"""
        a1 = get_assembler()
        a2 = get_assembler()
        assert a1 is a2

    def test_assembler_has_collectors(self):
        """組裝器應有收集器"""
        assembler = SoupAssembler()
        assert "quotes" in assembler.collectors
        assert "random" in assembler.collectors

    def test_assemble_soup_basic(self):
        """基本湯組裝"""
        assembler = SoupAssembler()
        fragments = [
            Fragment(content="碎片 A", source=FragmentSource.QUOTES),
            Fragment(content="碎片 B", source=FragmentSource.RANDOM),
            Fragment(content="碎片 C", source=FragmentSource.USER),
        ]
        result = assembler.assemble_soup(
            topic="測試主題",
            fragments=fragments,
            topic_repetition=2,
        )

        assert isinstance(result, SparkSoupResult)
        assert result.topic == "測試主題"
        assert len(result.fragments_used) == 3

    def test_topic_anchoring(self):
        """主題錨定：soup 中應多次出現主題"""
        assembler = SoupAssembler()
        fragments = [Fragment(content=f"碎片 {i}", source=FragmentSource.RANDOM) for i in range(10)]
        result = assembler.assemble_soup(
            topic="遠距工作",
            fragments=fragments,
            topic_repetition=3,
        )

        # 計算主題出現次數（開頭 + 錨定 + 結尾）
        anchors = result.soup.count("遠距工作")
        assert anchors >= 3, f"主題錨定不足，只出現 {anchors} 次"

    def test_trigger_words_in_soup(self):
        """觸發詞應出現在 soup 中"""
        assembler = SoupAssembler()
        fragments = [Fragment(content=f"碎片 {i}", source=FragmentSource.RANDOM) for i in range(10)]
        result = assembler.assemble_soup(
            topic="測試",
            fragments=fragments,
            topic_repetition=3,
            trigger_categories=["combination"],
        )

        assert "發想提示" in result.soup

    def test_diversity_score(self):
        """多樣性評分應在 0-1 之間"""
        assembler = SoupAssembler()
        fragments = [
            Fragment(content="A", source=FragmentSource.QUOTES, relevance=0.3),
            Fragment(content="B", source=FragmentSource.RANDOM, relevance=0.5),
            Fragment(content="C", source=FragmentSource.USER, relevance=0.8),
        ]
        result = assembler.assemble_soup(topic="test", fragments=fragments)
        assert 0 <= result.diversity_score <= 1

    def test_ensure_diversity_interleaving(self):
        """多樣性確保：不同來源交錯排列"""
        assembler = SoupAssembler()
        fragments = [
            Fragment(content="Q1", source=FragmentSource.QUOTES),
            Fragment(content="Q2", source=FragmentSource.QUOTES),
            Fragment(content="R1", source=FragmentSource.RANDOM),
            Fragment(content="R2", source=FragmentSource.RANDOM),
        ]
        result = assembler._ensure_diversity(fragments)

        # 檢查交錯：前兩個應來自不同來源
        assert result[0].source != result[1].source


# === 主要 API 測試 ===


class TestSparkSoupAPI:
    """測試主要 API"""

    @pytest.mark.asyncio
    async def test_spark_soup_basic(self):
        """基本 spark_soup 呼叫"""
        result = await spark_soup(
            topic="遠距工作",
            fragment_count=10,
            topic_repetition=3,
            auto_search=False,
        )

        assert isinstance(result, SparkSoupResult)
        assert result.topic == "遠距工作"
        assert len(result.fragments_used) <= 10
        assert result.diversity_score > 0

    @pytest.mark.asyncio
    async def test_spark_soup_custom_fragments(self):
        """自訂碎片"""
        custom = ["我的想法 A", "我的想法 B"]
        result = await spark_soup(
            topic="測試",
            fragment_count=15,
            auto_search=False,
            custom_fragments=custom,
        )

        # 自訂碎片應在 soup 中
        assert "我的想法 A" in result.soup or "我的想法 B" in result.soup

    @pytest.mark.asyncio
    async def test_spark_soup_trigger_categories(self):
        """指定觸發詞類別"""
        result = await spark_soup(
            topic="測試",
            fragment_count=10,
            auto_search=False,
            trigger_categories=["inversion", "scale"],
        )
        assert isinstance(result.trigger_words_used, list)

    @pytest.mark.asyncio
    async def test_collect_fragments_basic(self):
        """基本碎片收集"""
        fragments = await collect_fragments(
            topic="AI 創意",
            sources=["quotes", "random"],
            count_per_source=5,
        )
        assert len(fragments) > 0
        assert all(isinstance(f, Fragment) for f in fragments)

    @pytest.mark.asyncio
    async def test_spark_soup_to_dict(self):
        """結果轉 dict"""
        result = await spark_soup(
            topic="測試",
            fragment_count=5,
            auto_search=False,
        )
        d = result.to_dict()
        assert "soup" in d
        assert "topic" in d
        assert "diversity_score" in d
        assert "fragments_count" in d
