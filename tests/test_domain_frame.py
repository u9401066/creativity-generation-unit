"""Frames, lineage, consent and the 11 operator cards."""

from __future__ import annotations

import re

import pytest

from cgu.domain.common import CGUError
from cgu.domain.frame import (
    RESTRICTED_KINDS,
    Assumption,
    Concept,
    Criterion,
    FrameDraft,
    Hinge,
    Metaphor,
    Stakeholder,
    build_frame,
    kind_of_id,
)
from cgu.domain.operators import (
    OPERATOR_NAMES,
    OPERATORS,
    get_operator,
    plan_commit,
    render_instructions,
)

EXPECTED = {
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
}


def make_frame():
    return build_frame(
        frame_id="f-root",
        session_id="s-1",
        problem="reduce postoperative delirium",
        created_at="2026-10-02T00:00:00+00:00",
        goal="fewer delirium days",
        unit="patient",
        elements={
            "assumption": [Assumption(text="drugs cause delirium"), Assumption(text="ICU only")],
            "concept": [Concept(term="delirium", working_definition="confusion after surgery")],
            "metaphor": [Metaphor(text="delirium is a fire to extinguish")],
            "criterion": [Criterion(text="speed", serves="surgeon")],
            "stakeholder": [Stakeholder(who="surgeon", bears_costs=False)],
            "hinge": [Hinge(text="no change of staffing")],
        },
    )


def test_all_eleven_operators_exist() -> None:
    assert set(OPERATOR_NAMES) == EXPECTED
    assert len(OPERATORS) == 11


def test_element_ids_are_assigned_per_kind() -> None:
    frame = make_frame()
    assert [a.id for a in frame.assumptions] == ["a1", "a2"]
    assert frame.criteria[0].id == "k1"
    assert frame.stakeholders[0].id == "s1"
    assert kind_of_id("a2") == "assumption"
    assert kind_of_id("goal") == "goal"
    assert kind_of_id("zz") is None


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_operator_card_is_a_complete_literal_instruction(name: str) -> None:
    card = get_operator(name)
    text = render_instructions(card, problem="PROBLEM-X", target="assumption a1")
    assert "PROBLEM-X" in text
    assert "$" not in text
    assert "護欄" in text
    assert "範例" in text
    assert "{" in text and "}" in text
    assert "FrameDraft" in text
    assert card.source and card.guardrails and card.targets
    # Traditional Chinese, identifiers in English, within the length budget
    assert len(re.findall(r"[\u4e00-\u9fff]", text)) > 150
    assert len(text) < 1500


def test_example_domains_rotate_across_the_three_domains() -> None:
    domains = {card.example_domain for card in OPERATORS.values()}
    assert domains == {"醫療研究構想", "醫療商品開發", "行政流程變革"}


def test_restricted_operators_are_marked() -> None:
    restricted = {n for n, c in OPERATORS.items() if c.restricted}
    assert restricted == {"shift_stakeholder", "invert_criterion", "genealogize"}
    assert {"goal", "stakeholder", "criterion"} == RESTRICTED_KINDS


def test_unknown_operator_is_an_error_with_a_hint() -> None:
    with pytest.raises(CGUError) as caught:
        get_operator("nope")
    assert caught.value.code == "invalid_input"
    assert "explicate" in (caught.value.hint or "")


def test_commit_builds_lineage_and_a_diff() -> None:
    parent = make_frame()
    draft = FrameDraft(
        why="reverse the drug assumption",
        assumptions=[
            Assumption(id="a1", text="delirium appears when sedation is withdrawn badly"),
            Assumption(id="a2", text="ICU only"),
        ],
    )
    plan = plan_commit(parent, "negate", draft, frame_id="f-child", created_at="t")
    assert plan.child.parent_id == "f-root"
    assert plan.child.operator == "negate"
    assert [(c.kind, c.id, c.change) for c in plan.changes] == [("assumption", "a1", "modified")]
    assert plan.changes[0].before == "[belt] drugs cause delirium"
    assert plan.restricted == []
    assert plan.child.concepts == parent.concepts


def test_new_elements_get_fresh_ids_and_removed_ones_are_reported() -> None:
    parent = make_frame()
    draft = FrameDraft(
        why="bracket a2 and add a new one",
        assumptions=[Assumption(id="a1", text="drugs cause delirium"), Assumption(text="new one")],
    )
    plan = plan_commit(parent, "explicate", draft, frame_id="f-c", created_at="t")
    kinds = {(c.id, c.change) for c in plan.changes}
    assert ("a2", "removed") in kinds
    assert ("a3", "added") in kinds


def test_restricted_changes_are_detected() -> None:
    parent = make_frame()
    draft = FrameDraft(
        why="add the neglected stakeholder",
        stakeholders=[
            Stakeholder(id="s1", who="surgeon", bears_costs=False),
            Stakeholder(who="ward nurse", bears_costs=True),
        ],
        checks={"veil_of_ignorance": "a nurse would ask for a handover checklist"},
    )
    plan = plan_commit(parent, "shift_stakeholder", draft, frame_id="f-c", created_at="t")
    assert plan.restricted == ["stakeholder"]


def test_operator_cannot_change_kinds_outside_its_targets() -> None:
    parent = make_frame()
    draft = FrameDraft(why="sneaky change", goal="a different goal")
    with pytest.raises(CGUError, match="may only change"):
        plan_commit(parent, "negate", draft, frame_id="f-c", created_at="t")


def test_required_checks_are_enforced() -> None:
    parent = make_frame()
    draft = FrameDraft(
        why="loosen the criterion",
        criteria=[Criterion(id="k1", text="speed is optional", serves="surgeon")],
    )
    with pytest.raises(CGUError, match="fence_check"):
        plan_commit(parent, "genealogize", draft, frame_id="f-c", created_at="t")
    draft.checks["fence_check"] = "it protected single-person ordering"
    assert plan_commit(parent, "genealogize", draft, frame_id="f-c", created_at="t").restricted == [
        "criterion"
    ]


def test_a_child_identical_to_its_parent_is_rejected() -> None:
    parent = make_frame()
    draft = FrameDraft(why="no actual change here", assumptions=parent.assumptions)
    with pytest.raises(CGUError, match="identical"):
        plan_commit(parent, "negate", draft, frame_id="f-c", created_at="t")


def test_unknown_ids_in_a_draft_are_rejected() -> None:
    parent = make_frame()
    draft = FrameDraft(why="use a made-up id", assumptions=[Assumption(id="a9", text="x")])
    with pytest.raises(CGUError, match="not in the parent frame"):
        plan_commit(parent, "negate", draft, frame_id="f-c", created_at="t")


def test_problem_is_the_shared_reference_of_a_lineage() -> None:
    parent = make_frame()
    draft = FrameDraft(
        why="rewrite the problem",
        problem="a different problem",
        assumptions=[Assumption(id="a1", text="changed"), Assumption(id="a2", text="ICU only")],
    )
    with pytest.raises(CGUError, match="keep the parent's problem"):
        plan_commit(parent, "negate", draft, frame_id="f-c", created_at="t")
