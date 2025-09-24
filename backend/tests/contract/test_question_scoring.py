"""
T015: 題目評分 API 契約測試
測試題目評分和導航相關的 API 端點契約
"""
import pytest
from fastapi.testclient import TestClient


class TestQuestionScoringContract:
    """題目評分 API 契約測試"""

    def test_submit_question_answer_contract(self, test_client: TestClient):
        """測試 POST /api/v1/exam-sessions/{session_id}/questions/{question_id}/submit 契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            question_id = "ckad-001"
            response = test_client.post(f"/api/v1/exam-sessions/{session_id}/questions/{question_id}/submit")
            assert response.status_code == 200
            data = response.json()
            assert "score" in data
            assert "max_score" in data
            assert "percentage" in data
            assert "results" in data
            assert "submitted_at" in data

    def test_question_scoring_details_contract(self, test_client: TestClient):
        """測試題目評分詳細結果契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            question_id = "ckad-001"
            response = test_client.post(f"/api/v1/exam-sessions/{session_id}/questions/{question_id}/submit")
            data = response.json()

            # 檢查評分結果結構
            results = data["results"]
            assert "verification_results" in results
            assert "feedback" in results
            assert "time_taken_seconds" in results

            # 檢查驗證結果
            verification_results = results["verification_results"]
            assert isinstance(verification_results, list)
            if verification_results:
                result = verification_results[0]
                assert "rule_type" in result
                assert "passed" in result
                assert "points_awarded" in result
                assert "message" in result

    def test_question_navigation_contract(self, test_client: TestClient):
        """測試 PATCH /api/v1/exam-sessions/{session_id}/navigation 契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            navigation_data = {
                "action": "next"
            }
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/navigation",
                json=navigation_data
            )
            assert response.status_code == 200
            data = response.json()
            assert "current_question_index" in data
            assert "current_question" in data
            assert "total_questions" in data

    def test_question_navigation_actions_contract(self, test_client: TestClient):
        """測試題目導航操作契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"

            # 下一題
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/navigation",
                json={"action": "next"}
            )
            assert response.status_code == 200

            # 上一題
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/navigation",
                json={"action": "previous"}
            )
            assert response.status_code == 200

            # 跳到指定題目
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/navigation",
                json={"action": "goto", "question_index": 2}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["current_question_index"] == 2

    def test_question_flagging_contract(self, test_client: TestClient):
        """測試題目標記契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            question_id = "ckad-001"

            # 標記題目
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/questions/{question_id}/flag",
                json={"flagged": True, "note": "需要再檢查"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["flagged"] is True
            assert data["note"] == "需要再檢查"

    def test_get_question_status_contract(self, test_client: TestClient):
        """測試題目狀態查詢契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            question_id = "ckad-001"
            response = test_client.get(f"/api/v1/exam-sessions/{session_id}/questions/{question_id}/status")
            assert response.status_code == 200
            data = response.json()
            assert "answered" in data
            assert "score" in data
            assert "flagged" in data
            assert "time_spent_seconds" in data
            assert "last_activity" in data

    def test_bulk_question_status_contract(self, test_client: TestClient):
        """測試批量題目狀態契約"""
        with pytest.raises(NotImplementedError):
            session_id = "test-session-001"
            response = test_client.get(f"/api/v1/exam-sessions/{session_id}/questions/status")
            assert response.status_code == 200
            data = response.json()
            assert "questions" in data
            assert "summary" in data

            summary = data["summary"]
            assert "total_questions" in summary
            assert "answered_questions" in summary
            assert "flagged_questions" in summary
            assert "total_score" in summary
            assert "max_possible_score" in summary

    def test_scoring_error_responses_contract(self, test_client: TestClient):
        """測試評分錯誤回應契約"""
        with pytest.raises(NotImplementedError):
            # 404 錯誤 - 會話或題目不存在
            response = test_client.post("/api/v1/exam-sessions/non-existent/questions/invalid/submit")
            assert response.status_code == 404

            # 409 錯誤 - 會話狀態不允許提交
            session_id = "test-session-001"
            question_id = "ckad-001"
            response = test_client.post(f"/api/v1/exam-sessions/{session_id}/questions/{question_id}/submit")
            if response.status_code == 409:
                data = response.json()
                assert "error" in data
                assert "session_status" in data

            # 400 錯誤 - 無效導航操作
            response = test_client.patch(
                f"/api/v1/exam-sessions/{session_id}/navigation",
                json={"action": "invalid"}
            )
            assert response.status_code == 400