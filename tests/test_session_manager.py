"""
測試 Interactive Session Manager

涵蓋：
- 完整互動流程：start → submit → evolve → finalize
- 狀態轉移驗證
- 無效操作防護
- 多會話管理
- 品質追蹤
"""

import pytest
from cgu.core.session import (
    SessionManager,
    SessionState,
    get_session_manager,
)


class TestSessionLifecycle:
    """完整會話生命週期測試"""

    def test_start_session(self):
        mgr = SessionManager()
        session = mgr.start_session("智慧城市")
        assert session.topic == "智慧城市"
        assert session.status == "awaiting_ideas"
        assert session.session_id

    def test_full_lifecycle(self):
        mgr = SessionManager()
        session = mgr.start_session("遠端教育")

        # Step 1: 提交想法
        result1 = mgr.submit_ideas(session.session_id, [
            "用 VR 模擬實驗室",
            "AI 個人化學習路徑",
        ])
        assert result1["status"] == "challenges_generated"
        assert len(result1["challenges"]) > 0

        # Step 2: 提交進化想法
        result2 = mgr.submit_evolved_ideas(session.session_id, [
            "VR 實驗室 + 同儕協作空間，解決實驗安全和成本問題",
            "AI 學習路徑 + 情緒偵測，動態調整難度和節奏",
        ])
        assert result2["status"] == "cross_pollinated"
        assert len(result2["cross_pollinations"]) > 0
        assert "quality_score" in result2

        # Step 3: 結束
        result3 = mgr.finalize_session(session.session_id)
        assert result3["status"] == "finalized"
        assert result3["final_output"]
        assert result3["total_rounds"] > 0

    def test_iterate_multiple_rounds(self):
        """測試多輪迭代"""
        mgr = SessionManager()
        session = mgr.start_session("永續農業")

        # Round 1
        mgr.submit_ideas(session.session_id, ["垂直農場"])
        mgr.submit_evolved_ideas(session.session_id, ["太陽能垂直農場"])

        # Round 2 (回到 submit ideas)
        mgr.submit_ideas(session.session_id, ["結合社區的太陽能垂直農場"])
        mgr.submit_evolved_ideas(session.session_id, ["社區共享太陽能垂直農場 + 教育功能"])

        # Finalize
        result = mgr.finalize_session(session.session_id)
        assert result["total_rounds"] > 4  # 至少 4 次狀態轉移


class TestSessionStateTransitions:
    """狀態轉移驗證"""

    def test_invalid_transition_raises(self):
        mgr = SessionManager()
        session = mgr.start_session("test")

        with pytest.raises(ValueError, match="無效的狀態轉移"):
            mgr.submit_evolved_ideas(session.session_id, ["idea"])

    def test_cannot_finalize_before_cross_pollinate(self):
        mgr = SessionManager()
        session = mgr.start_session("test")
        mgr.submit_ideas(session.session_id, ["idea 1"])

        with pytest.raises(ValueError, match="無效的狀態轉移"):
            mgr.finalize_session(session.session_id)

    def test_nonexistent_session_raises(self):
        mgr = SessionManager()
        with pytest.raises(ValueError, match="會話不存在"):
            mgr.submit_ideas("nonexistent", ["idea"])


class TestSessionManager:
    """會話管理器功能測試"""

    def test_list_sessions(self):
        mgr = SessionManager()
        mgr.start_session("topic A")
        mgr.start_session("topic B")

        sessions = mgr.list_sessions()
        assert len(sessions) == 2
        topics = {s["topic"] for s in sessions}
        assert "topic A" in topics
        assert "topic B" in topics

    def test_get_session(self):
        mgr = SessionManager()
        session = mgr.start_session("test")
        retrieved = mgr.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.topic == "test"

    def test_get_nonexistent_session(self):
        mgr = SessionManager()
        assert mgr.get_session("nope") is None


class TestChallengeGeneration:
    """挑戰生成測試"""

    def test_challenges_are_specific_to_ideas(self):
        mgr = SessionManager()
        session = mgr.start_session("AI")
        result = mgr.submit_ideas(session.session_id, [
            "自動寫程式的 AI",
            "AI 作曲",
        ])
        # 框架模式下，挑戰數量 = 想法數量
        assert len(result["challenges"]) == 2


class TestQualityTracking:
    """品質追蹤測試"""

    def test_quality_score_between_0_and_1(self):
        mgr = SessionManager()
        session = mgr.start_session("test")
        mgr.submit_ideas(session.session_id, ["簡短想法"])
        result = mgr.submit_evolved_ideas(session.session_id, [
            "經過深入思考後的更完整更具體的想法，包含具體步驟和理由"
        ])
        assert 0 <= result["quality_score"] <= 1


class TestSessionState:
    """會話狀態模型測試"""

    def test_default_state(self):
        state = SessionState(topic="test")
        assert state.status == "awaiting_ideas"
        assert state.round_count == 0
        assert state.submitted_ideas == []

    def test_session_id_is_unique(self):
        s1 = SessionState(topic="a")
        s2 = SessionState(topic="b")
        assert s1.session_id != s2.session_id


class TestGlobalManager:
    """全域管理器測試"""

    def test_get_session_manager_singleton(self):
        # 重置全域狀態
        import cgu.core.session as mod
        mod._manager = None

        m1 = get_session_manager()
        m2 = get_session_manager()
        assert m1 is m2
