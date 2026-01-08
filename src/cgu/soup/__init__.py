"""
CGU Soup Module - Spark-Soup: Context Stuffing for Creativity

用碎片化資訊填充 context，激發意外連結。
"""

from cgu.soup.spark_soup import (
    # 主要 API
    spark_soup,
    collect_fragments,
    get_assembler,
    
    # 資料類別
    Fragment,
    FragmentSource,
    SparkSoupResult,
    Idea,
    
    # 收集器
    FragmentCollector,
    QuotesCollector,
    RandomConceptCollector,
    DuckDuckGoCollector,
    
    # 組裝器
    SoupAssembler,
    
    # 內建資料
    TRIGGER_WORDS,
    CREATIVITY_QUOTES,
    RANDOM_CONCEPTS,
    CROSS_DOMAIN_CONCEPTS,
)

__all__ = [
    # 主要 API
    "spark_soup",
    "collect_fragments",
    "get_assembler",
    
    # 資料類別
    "Fragment",
    "FragmentSource",
    "SparkSoupResult",
    "Idea",
    
    # 收集器
    "FragmentCollector",
    "QuotesCollector",
    "RandomConceptCollector",
    "DuckDuckGoCollector",
    
    # 組裝器
    "SoupAssembler",
    
    # 內建資料
    "TRIGGER_WORDS",
    "CREATIVITY_QUOTES",
    "RANDOM_CONCEPTS",
    "CROSS_DOMAIN_CONCEPTS",
]
