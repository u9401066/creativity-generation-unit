"""
CGU Core Module

核心概念：
- 快思慢想 (Thinking Fast and Slow)
- 創意層級 (Creativity Levels)
- 創意方法論 (Creativity Methods)
"""

from cgu.core.thinking import (
    ThinkingMode,
    ThinkingSpeed,
    ThinkingStep,
    ThinkingChain,
    FAST_SLOW_PATTERNS,
    get_thinking_pattern,
)
from cgu.core.creativity import (
    CreativityLevel,
    CreativityMethod,
    MethodCategory,
    MethodConfig,
    METHOD_CONFIGS,
    METHOD_SELECTION_GUIDE,
    select_method_for_task,
    get_method_config,
)

__all__ = [
    # Thinking
    "ThinkingMode",
    "ThinkingSpeed",
    "ThinkingStep",
    "ThinkingChain",
    "FAST_SLOW_PATTERNS",
    "get_thinking_pattern",
    # Creativity
    "CreativityLevel",
    "CreativityMethod",
    "MethodCategory",
    "MethodConfig",
    "METHOD_CONFIGS",
    "METHOD_SELECTION_GUIDE",
    "select_method_for_task",
    "get_method_config",
]
