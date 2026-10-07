"""Skill and agent file quality gates (structure, frontmatter, protocol invariants)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_plugin_support import (  # noqa: E402
    AGENT_NAMES,
    AGENTS_DIR,
    SKILL_NAMES,
    SKILLS_DIR,
    read_frontmatter,
)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
MAX_DESCRIPTION = 1024
MAX_SKILL_LINES = 300
MAX_AGENT_BODY_CHARS = 1500
MAX_AGENT_BODY_LINES = 30

REQUIRED_SECTIONS = (
    "When to use",
    "Preconditions",
    "Procedure",
    "Decision rules",
    "Stop conditions",
    "Output format",
    "Honesty rules",
)

# Each honesty rule must be stated (briefly) in every skill.
HONESTY_MARKERS = {
    "reference_size": "report reference_size",
    "method": "report method",
    "embedding.semantic": "lexical-only novelty disclosure",
    "未校準": "heuristic scores are uncalibrated",
    "不是指令": "external text is data, never instructions",
    "null": "null reference set means not measured",
}

IDEA_CARD_COMMON_LABELS = (
    "推導路徑",
    "素材（未驗證）",
    "主要風險",
    "最小驗證步驟",
    "決策",
    "☐ 採用",
)
# creative-ideation cards are written for the decision maker: plain language, no tool internals.
IDEA_CARD_LABELS = {
    "creative-ideation": (
        "這張卡改了什麼",
        "符合限制",
        "資源估計",
        "繼續／放棄門檻",
    ),
    # idea-triage is the audit-style deliverable: it keeps the full measurement vector.
    "idea-triage": ("框架改寫", "新穎度向量"),
}

STALE_V06_TOOLS = (
    "generate_ideas",
    "deep_think",
    "multi_agent_brainstorm",
    "spark_soup",
    "spark_collision",
    "check_novelty",
    "evaluate_brainstorm_ideas",
    "apply_method",
    "creativity_session",
    "evolve_idea_tool",
)

COMPANION_NAMES = ("PubMed", "Zotero", "asset-aware")
OPTIONAL_WORDING = ("選用", "若有", "若可用", "同伴工具")


def _skill(name: str) -> tuple[dict, str, str]:
    path = SKILLS_DIR / name / "SKILL.md"
    meta, body = read_frontmatter(path)
    return meta, body, path.read_text(encoding="utf-8")


# --- skills ---------------------------------------------------------------------------


def test_exactly_the_five_skills_exist() -> None:
    assert sorted(p.name for p in SKILLS_DIR.iterdir()) == sorted(SKILL_NAMES)


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_frontmatter_follows_agent_skills_rules(skill: str) -> None:
    meta, _, _ = _skill(skill)
    assert set(meta) <= {"name", "description"}, f"unexpected frontmatter keys: {set(meta)}"
    assert meta["name"] == skill, "frontmatter name must equal the directory name"
    assert NAME_RE.match(meta["name"]) and len(meta["name"]) <= 64
    description = meta["description"]
    assert isinstance(description, str) and description.strip()
    assert len(description) <= MAX_DESCRIPTION, f"description is {len(description)} chars"
    assert CJK_RE.search(description), "description needs Traditional Chinese trigger phrases"
    assert re.search(r"[A-Za-z]{4,}", description), "description needs English trigger wording"
    assert "觸發詞" in description, "description should list zh-TW trigger phrases"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_is_concise_and_has_the_required_sections(skill: str) -> None:
    _, body, raw = _skill(skill)
    assert len(raw.splitlines()) <= MAX_SKILL_LINES
    headings = [line for line in body.splitlines() if line.startswith("#")]
    for section in REQUIRED_SECTIONS:
        assert any(section in h for h in headings), f"{skill}: missing section '{section}'"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_states_every_honesty_rule(skill: str) -> None:
    _, body, _ = _skill(skill)
    honesty = body.split("Honesty rules", 1)[1]
    honesty = re.split(r"\n## ", honesty, maxsplit=1)[0]
    for marker, why in HONESTY_MARKERS.items():
        text = body if marker == "null" else honesty
        assert marker in text, f"{skill}: honesty rules must cover '{why}' (missing {marker!r})"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_procedure_uses_numbered_steps_with_exact_tool_calls(skill: str) -> None:
    _, body, _ = _skill(skill)
    procedure = body.split("Procedure", 1)[1]
    procedure = re.split(r"\n## (?!#)", procedure, maxsplit=1)[0]
    numbered = re.findall(r"^\d+\. ", procedure, re.MULTILINE)
    assert len(numbered) >= 7, f"{skill}: procedure should be a numbered list of steps"
    assert re.search(r"cgu_[a-z_]+\(action=", procedure), f"{skill}: steps must show exact calls"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_does_not_reference_retired_v06_tools(skill: str) -> None:
    _, _, raw = _skill(skill)
    for stale in STALE_V06_TOOLS:
        assert stale not in raw, f"{skill} mentions retired tool {stale}"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_companion_tools_are_only_ever_optional(skill: str) -> None:
    _, _, raw = _skill(skill)
    for line in raw.splitlines():
        if any(name in line for name in COMPANION_NAMES):
            assert any(word in line for word in OPTIONAL_WORDING), (
                f"{skill}: companion tool mentioned without optional wording: {line.strip()}"
            )


@pytest.mark.parametrize("skill", ["creative-ideation", "idea-triage"])
def test_idea_card_template_is_complete(skill: str) -> None:
    _, _, raw = _skill(skill)
    for label in IDEA_CARD_COMMON_LABELS + IDEA_CARD_LABELS[skill]:
        assert label in raw, f"{skill}: idea card is missing '{label}'"
    if skill == "idea-triage":
        for reference_set in ("vs_typical", "vs_human", "vs_prior_art", "vs_session"):
            assert reference_set in raw
        assert "最近鄰" in raw, "triage must show the nearest neighbour text"


def test_creative_ideation_keeps_tool_internals_out_of_the_reply() -> None:
    _, _, raw = _skill("creative-ideation")
    output = raw.split("Output format", 1)[1].split("\n## ", 1)[0]
    assert "不得出現 CGU 內部術語" in output
    assert "CGU session：" in output, "the reply must point to the stored audit trail"
    card = output.split("```", 2)[1]
    for internal in ("disclosure", "Wilson", "vs_typical", "child_frame_id", "operator"):
        assert internal not in card, f"user-facing card must not expose '{internal}'"


@pytest.mark.parametrize("skill", ["creative-ideation", "frame-audit", "maieutic-session"])
def test_frame_rewrites_require_consent(skill: str) -> None:
    _, _, raw = _skill(skill)
    assert "consent" in raw
    for restricted in ("goal", "stakeholder", "criterion"):
        assert restricted in raw


def test_orchestrator_applies_all_eleven_frame_operators() -> None:
    _, _, raw = _skill("creative-ideation")
    operators = (
        "explicate",
        "bracket",
        "negate",
        "tetralemma",
        "re_explicate",
        "swap_metaphor",
        "recut_unit",
        "shift_stakeholder",
        "invert_criterion",
        "genealogize",
        "thought_experiment",
    )
    for operator in operators:
        assert f"`{operator}`" in raw or f"operator={operator}" in raw, operator


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_skill_has_a_worked_example_for_each_target_domain(skill: str) -> None:
    _, body, _ = _skill(skill)
    examples = body.split("## 範例", 1)[1]
    for tag in ("(a)", "(b)", "(c)"):
        assert tag in examples, f"{skill}: missing worked example {tag}"


def test_economy_of_doubt_is_spelled_out() -> None:
    ideation = _skill("creative-ideation")[2]
    audit = _skill("frame-audit")[2]
    for phrase in (
        "escalate",
        "untested_load_bearing",
        "stop_reasons",
        "hinges",
        "不會改變任何決策",
    ):
        assert phrase in ideation, f"creative-ideation: missing {phrase!r}"
        assert phrase in audit, f"frame-audit: missing {phrase!r}"
    assert "籬笆" in audit and "籬笆" in ideation, "genealogy needs the Chesterton's-fence check"


# --- agents ---------------------------------------------------------------------------


def test_exactly_the_four_agents_exist() -> None:
    assert sorted(p.name for p in AGENTS_DIR.iterdir()) == sorted(
        f"{n}.agent.md" for n in AGENT_NAMES
    )


@pytest.mark.parametrize("agent", AGENT_NAMES)
def test_agent_frontmatter(agent: str) -> None:
    meta, body = read_frontmatter(AGENTS_DIR / f"{agent}.agent.md")
    assert meta["name"] == agent
    assert isinstance(meta["description"], str) and meta["description"].strip()
    assert isinstance(meta["tools"], list) and all(isinstance(t, str) for t in meta["tools"])
    assert body.strip()


@pytest.mark.parametrize("agent", AGENT_NAMES)
def test_agent_is_a_thin_wrapper(agent: str) -> None:
    _, body = read_frontmatter(AGENTS_DIR / f"{agent}.agent.md")
    assert len(body) <= MAX_AGENT_BODY_CHARS, (
        "agents add role framing only; protocols live in skills"
    )
    assert len(body.strip().splitlines()) <= MAX_AGENT_BODY_LINES
    assert not re.search(r"^\d+\. ", body, re.MULTILINE), "numbered procedures belong in skills"


@pytest.mark.parametrize(
    ("agent", "skill"),
    [
        ("creative-facilitator", "creative-ideation"),
        ("frame-auditor", "frame-audit"),
        ("adversarial-critic", "idea-triage"),
    ],
)
def test_agent_points_at_its_skill(agent: str, skill: str) -> None:
    _, body = read_frontmatter(AGENTS_DIR / f"{agent}.agent.md")
    assert f"`{skill}`" in body


@pytest.mark.parametrize("agent", AGENT_NAMES)
def test_agent_tool_restrictions(agent: str) -> None:
    meta, _ = read_frontmatter(AGENTS_DIR / f"{agent}.agent.md")
    tools = set(meta["tools"])
    assert not tools & {"edit", "execute", "web", "*"}, "role agents never edit, execute or browse"
    if agent == "independent-ideator":
        assert tools == set(), "fan-out ideators must be isolated: no tools"
    if agent == "frame-auditor":
        assert not tools & {
            "cgu/cgu_judge",
            "cgu/cgu_material",
            "cgu/cgu_feedback",
            "cgu/cgu_evolve",
        }
        assert not tools & {"cgu/*"}, "frame-auditor is read-only and uses an explicit allow-list"
    if agent == "adversarial-critic":
        assert "cgu/cgu_judge" in tools and "cgu/cgu_frame" not in tools
    if agent == "creative-facilitator":
        assert {"agent", "cgu/*"} <= tools
