"""
CGU MCP Server

使用 FastMCP 提供創意生成工具
"""

from mcp.server.fastmcp import FastMCP

from cgu.core import (
    CreativityLevel,
    CreativityMethod,
    ThinkingMode,
    ThinkingSpeed,
    METHOD_CONFIGS,
    select_method_for_task,
)

# 初始化 FastMCP Server
mcp = FastMCP(
    name="creativity-generation-unit",
    version="0.1.0",
)


# === MCP Tools ===


@mcp.tool()
async def generate_ideas(
    topic: str,
    creativity_level: int = 1,
    count: int = 5,
    constraints: list[str] | None = None,
) -> dict:
    """
    生成創意點子
    
    Args:
        topic: 要發想的主題
        creativity_level: 創意層級 (1=組合, 2=探索, 3=變革)
        count: 要產生的點子數量
        constraints: 限制條件列表
    
    Returns:
        包含點子和連結的字典
    """
    level = CreativityLevel(creativity_level)
    assoc_range = level.association_range
    
    # TODO: 實際呼叫 LLM 生成
    # 這裡先回傳結構示意
    return {
        "topic": topic,
        "creativity_level": level.name,
        "association_range": f"{assoc_range[0]:.1f} - {assoc_range[1]:.1f}",
        "constraints": constraints or [],
        "ideas": [
            {
                "id": i + 1,
                "content": f"[待實作] 點子 {i + 1} for '{topic}'",
                "association_score": 0.5,
            }
            for i in range(count)
        ],
        "method_used": "brainstorm",
        "thinking_steps": [
            {"mode": "REACT", "speed": "fast"},
            {"mode": "ASSOCIATE", "speed": "fast"},
            {"mode": "DIVERGE", "speed": "fast"},
        ],
    }


@mcp.tool()
async def spark_collision(
    concept_a: str,
    concept_b: str,
) -> dict:
    """
    概念碰撞 - 讓兩個概念產生火花
    
    低關聯但有潛力的連結往往能產生最有創意的點子
    
    Args:
        concept_a: 第一個概念
        concept_b: 第二個概念
    
    Returns:
        碰撞產生的火花和理由
    """
    # TODO: 實際計算概念相似度和碰撞
    return {
        "concept_a": concept_a,
        "concept_b": concept_b,
        "sparks": [
            f"[待實作] {concept_a} + {concept_b} 的創意組合 1",
            f"[待實作] {concept_a} + {concept_b} 的創意組合 2",
            f"[待實作] {concept_a} + {concept_b} 的創意組合 3",
        ],
        "rationale": f"從 {concept_a} 的特性與 {concept_b} 的特性中找到意想不到的連結",
        "association_score": 0.3,  # 低關聯 = 高創意潛力
    }


@mcp.tool()
async def associative_expansion(
    seed: str,
    direction: str = "similar",
    depth: int = 2,
) -> dict:
    """
    聯想擴展 - 從種子概念向外擴展
    
    Args:
        seed: 種子概念
        direction: 擴展方向 (similar/opposite/random/cross-domain)
        depth: 擴展深度
    
    Returns:
        擴展後的聯想樹
    """
    valid_directions = ["similar", "opposite", "random", "cross-domain"]
    if direction not in valid_directions:
        direction = "similar"
    
    # TODO: 實際實作聯想擴展
    return {
        "seed": seed,
        "direction": direction,
        "depth": depth,
        "associations": [
            {
                "level": 1,
                "concepts": [
                    f"[待實作] {seed} 的 {direction} 聯想 1",
                    f"[待實作] {seed} 的 {direction} 聯想 2",
                ],
            },
            {
                "level": 2,
                "concepts": [
                    f"[待實作] 深層 {direction} 聯想 1",
                    f"[待實作] 深層 {direction} 聯想 2",
                ],
            },
        ],
        "thinking_mode": ThinkingMode.ASSOCIATE.value,
        "thinking_speed": ThinkingSpeed.FAST.value,
    }


@mcp.tool()
async def apply_method(
    method: str,
    input_concept: str,
    options: dict | None = None,
) -> dict:
    """
    應用特定創意方法
    
    Args:
        method: 方法名稱 (mind_map/scamper/six_hats/mandala_9grid/...)
        input_concept: 輸入概念
        options: 方法特定選項
    
    Returns:
        方法應用結果
    """
    # 驗證方法
    try:
        creativity_method = CreativityMethod(method)
    except ValueError:
        available = [m.value for m in CreativityMethod]
        return {
            "error": f"Unknown method: {method}",
            "available_methods": available,
        }
    
    config = METHOD_CONFIGS.get(creativity_method)
    if not config:
        return {"error": f"Method config not found: {method}"}
    
    # 根據方法類型回傳不同結構
    result = {
        "method": method,
        "method_description": config.description,
        "category": config.category.value,
        "thinking_speed": config.thinking_speed,
        "agent_strategy": config.agent_strategy,
        "input": input_concept,
        "options": options or {},
    }
    
    # 方法特定結構（示意）
    if method == "scamper":
        result["output"] = {
            "S_substitute": f"[待實作] 替代 {input_concept}",
            "C_combine": f"[待實作] 結合 {input_concept}",
            "A_adapt": f"[待實作] 調適 {input_concept}",
            "M_modify": f"[待實作] 修改 {input_concept}",
            "P_put_to_other_uses": f"[待實作] 他用 {input_concept}",
            "E_eliminate": f"[待實作] 消除 {input_concept}",
            "R_reverse": f"[待實作] 重排 {input_concept}",
        }
    elif method == "six_hats":
        result["output"] = {
            "white_facts": f"[待實作] 關於 {input_concept} 的事實",
            "red_feelings": f"[待實作] 對 {input_concept} 的感覺",
            "black_risks": f"[待實作] {input_concept} 的風險",
            "yellow_benefits": f"[待實作] {input_concept} 的好處",
            "green_ideas": f"[待實作] {input_concept} 的新點子",
            "blue_summary": f"[待實作] {input_concept} 的總結",
        }
    elif method == "mandala_9grid":
        result["output"] = {
            "center": input_concept,
            "extensions": [
                f"[待實作] {input_concept} 延伸 {i}" for i in range(1, 9)
            ],
        }
    else:
        result["output"] = f"[待實作] {method} 方法應用於 {input_concept}"
    
    return result


@mcp.tool()
async def select_method(
    creativity_level: int = 1,
    prefer_fast: bool = True,
    is_stuck: bool = False,
    purpose: str | None = None,
) -> dict:
    """
    根據情況選擇合適的創意方法
    
    Args:
        creativity_level: 創意層級 (1/2/3)
        prefer_fast: 是否偏好快速方法
        is_stuck: 是否卡關中
        purpose: 目的 (廣泛探索/結構化分析/強制創新/系統性組合/多元觀點/問題反轉/完整流程)
    
    Returns:
        推薦的方法和配置
    """
    level = CreativityLevel(creativity_level)
    method = select_method_for_task(
        creativity_level=level,
        prefer_fast=prefer_fast,
        is_stuck=is_stuck,
        purpose=purpose,
    )
    
    config = METHOD_CONFIGS.get(method)
    
    return {
        "recommended_method": method.value,
        "description": config.description if config else "",
        "category": config.category.value if config else "",
        "thinking_speed": config.thinking_speed if config else "fast",
        "agent_strategy": config.agent_strategy if config else "",
        "selection_reason": {
            "creativity_level": level.name,
            "prefer_fast": prefer_fast,
            "is_stuck": is_stuck,
            "purpose": purpose,
        },
    }


@mcp.tool()
async def list_methods() -> dict:
    """
    列出所有可用的創意方法
    
    Returns:
        所有方法的清單和說明
    """
    methods_by_category: dict[str, list[dict]] = {}
    
    for method, config in METHOD_CONFIGS.items():
        category = config.category.value
        if category not in methods_by_category:
            methods_by_category[category] = []
        
        methods_by_category[category].append({
            "name": method.value,
            "description": config.description,
            "thinking_speed": config.thinking_speed,
            "suitable_levels": config.suitable_levels,
        })
    
    return {
        "total_methods": len(METHOD_CONFIGS),
        "categories": list(methods_by_category.keys()),
        "methods_by_category": methods_by_category,
    }


# === MCP Resources ===


@mcp.resource("cgu://creativity-levels")
async def get_creativity_levels() -> str:
    """取得創意層級說明"""
    return """
# CGU Creativity Levels

## Level 1: Combinational (組合創意)
- Association Range: 0.7 - 1.0
- Description: 已知元素的新組合
- Example: 將現有功能重新組合

## Level 2: Exploratory (探索創意)  
- Association Range: 0.3 - 0.7
- Description: 在既有規則內探索邊界
- Example: 延伸現有概念到新領域

## Level 3: Transformational (變革創意)
- Association Range: 0.0 - 0.3
- Description: 打破規則，創造新範式
- Example: 顛覆性的全新概念
"""


@mcp.resource("cgu://thinking-modes")
async def get_thinking_modes() -> str:
    """取得思考模式說明"""
    return """
# CGU Thinking Modes (Fast/Slow)

## System 1 - Fast Thinking ⚡
- REACT: 基本反應，輸入 → 輸出
- ASSOCIATE: 快速聯想，概念 → 相關概念
- PATTERN_MATCH: 模式匹配，識別已知模式

## System 2 - Slow Thinking 🐢
- ANALYZE: 分析，拆解問題結構
- SYNTHESIZE: 綜合，組合多個概念
- EVALUATE: 評估，判斷品質與可行性

## Creative Thinking 🎨
- DIVERGE: 發散，產生多種可能
- CONVERGE: 收斂，選擇最佳方案
- TRANSFORM: 變革，打破規則創新

## Fast/Slow Patterns
- sprint: 5 fast + 1 slow (快速嘗試 + 評估)
- explore: 3 fast + 1 slow (快速聯想 + 分析)
- refine: 2 fast + 2 slow (生成 + 精煉)
- deep: 1 fast + 3 slow (直覺 + 深思)
"""


# === Entry Point ===


def main():
    """啟動 MCP Server"""
    mcp.run()


if __name__ == "__main__":
    main()
