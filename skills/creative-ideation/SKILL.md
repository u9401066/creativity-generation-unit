---
name: creative-ideation
description: Use when brainstorming ideas, stuck on a problem, exploring alternatives, or needing creative input - provides structured creativity methods (SCAMPER, Six Hats, Mind Map), Multi-Agent parallel thinking, and concept collision for unexpected sparks. Don't use for mechanical execution tasks
---

# Creative Ideation with CGU

## Overview

Turn vague ideas into concrete possibilities through structured creativity techniques and AI-powered ideation.

CGU (Creativity Generation Unit) offers three thinking modes:
- **Simple**: Quick single-pass ideation with Ollama/Copilot
- **Deep**: Multi-Agent parallel exploration (Explorer + Critic + Wildcard)
- **Spark**: Concept collision for unexpected creative connections

## When to Use

```
┌─────────────────────────────────────────────────┐
│  "I need ideas for..."     → generate_ideas    │
│  "What if we combine..."   → spark_collision   │
│  "I'm stuck on..."         → deep_think        │
│  "Analyze this from..."    → apply_method      │
│  "Which approach..."       → select_method     │
└─────────────────────────────────────────────────┘
```

**Use this skill when:**
- Starting a new project and need direction
- Feeling stuck or out of ideas
- Want multiple perspectives on a problem
- Need to break out of conventional thinking
- Exploring combinations of unrelated concepts

**Don't use when:**
- Task is clearly defined and mechanical
- Following established implementation plans
- Debugging specific technical issues

## Quick Start

**1. Need quick ideas?**
```
→ generate_ideas(topic="your topic", count=5)
```

**2. Stuck on a problem?**
```
→ deep_think(topic="your challenge", depth="deep", mode="deep")
```

**3. Want creative sparks?**
```
→ spark_collision(concept_a="idea A", concept_b="unrelated B")
```

**4. Need structured analysis?**
```
→ apply_method(method="six_hats", input_concept="your topic")
```

## The Process

**Understanding the challenge:**
- What are you trying to create or solve?
- What constraints exist? (time, resources, tech)
- What would success look like?

**Choosing your approach:**

| Situation | Recommended Tool | Why |
|-----------|------------------|-----|
| Need many ideas fast | `generate_ideas` | Divergent batch generation |
| Stuck, need breakthrough | `deep_think(mode="deep")` | Multi-Agent perspectives |
| Have two concepts to merge | `spark_collision` | Unexpected connections |
| Need structured analysis | `apply_method("six_hats")` | Multi-perspective evaluation |
| Don't know which method | `select_method` | AI recommends based on context |

**Refining results:**
- Use `spark_collision_deep` on best ideas for deeper exploration
- Apply `multi_agent_brainstorm` for complex topics
- Chain methods: SCAMPER → Six Hats → Mind Map

## Available Methods

**16 creativity methods across 5 categories:**

| Category | Methods | Best For |
|----------|---------|----------|
| Divergent | mind_map, brainstorm, scamper, random_input | Generating many options |
| Structural | mandala_9grid, morphological, 5w2h, fishbone | Systematic exploration |
| Perspective | six_hats, reverse, analogy | Multi-viewpoint analysis |
| Process | double_diamond, design_sprint, kj_method, world_cafe | End-to-end workflows |
| Systematic | triz | Inventive problem solving |

**Quick method selection:**
```
→ list_methods()  # See all available methods
→ select_method(is_stuck=True)  # AI recommends based on your situation
```

## Key Principles

- **Quantity before quality** - Generate many ideas first, filter later
- **Defer judgment** - Don't criticize during ideation phase
- **Build on ideas** - Use sparks to combine and extend
- **Change perspective** - Try different methods when stuck
- **Embrace randomness** - `random_input` and `spark_collision` create surprises

## Multi-Agent Deep Thinking

For complex challenges, use Multi-Agent mode:

```
→ multi_agent_brainstorm(
    topic="your challenge",
    agents=3,  # Explorer, Critic, Wildcard
    collision_count=5
)
```

**Agent personalities:**
- **Explorer** 🔍: Explores possibilities, finds connections
- **Critic** 🎯: Identifies risks, challenges assumptions  
- **Wildcard** 🎲: Injects randomness, breaks patterns

## Example Workflows

**Workflow 1: New Feature Ideation**
```
1. generate_ideas(topic="feature X", creativity_level=2, count=10)
2. spark_collision(concept_a="best idea", concept_b="user pain point")
3. apply_method(method="six_hats", input_concept="refined concept")
```

**Workflow 2: Problem Solving**
```
1. apply_method(method="reverse", input_concept="the problem")
2. deep_think(topic="how to achieve opposite", depth="deep")
3. apply_method(method="5w2h", input_concept="solution approach")
```

**Workflow 3: Breakthrough Thinking**
```
1. multi_agent_brainstorm(topic="stuck problem", agents=3)
2. spark_collision_deep(concept_a="best spark", concept_b="random domain")
3. apply_method(method="scamper", input_concept="promising direction")
```

## Integration with Other Skills

**Before coding:**
- Use this skill → Then `brainstorming` skill → Then `writing-plans`

**When stuck debugging:**
- `apply_method("reverse")` → "How could we make this bug worse?" → Insights

**For architecture decisions:**
- `apply_method("six_hats")` → Multi-perspective analysis

## Tool Reference

| Tool | Purpose | Key Args |
|------|---------|----------|
| `generate_ideas` | Batch ideation | topic, creativity_level(1-3), count |
| `spark_collision` | Concept merge | concept_a, concept_b |
| `deep_think` | Unified thinking | topic, depth, mode |
| `apply_method` | Specific technique | method, input_concept |
| `select_method` | Method recommendation | creativity_level, is_stuck, purpose |
| `multi_agent_brainstorm` | Parallel thinking | topic, agents(1-5) |
| `spark_collision_deep` | Deep collision | concept_a, concept_b |
| `associative_expansion` | Concept expansion | seed, direction, depth |
| `list_methods` | Show all methods | (none) |

## Tips

1. **Start broad, then narrow** - Use Level 3 creativity first, refine with Level 1
2. **Combine unrelated domains** - Best sparks come from distant concepts
3. **Use constraints creatively** - "How might we X without Y?"
4. **Iterate quickly** - Don't over-analyze early ideas
5. **Document sparks** - Good ideas disappear fast; capture them

---

*CGU v0.3.0 - Creativity Generation Unit*
*MCP Server with 16 methods, Multi-Agent thinking, and concept collision*
