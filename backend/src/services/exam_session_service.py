"""
T031: ExamSessionService 考試會話管理
處理考試會話的完整生命週期
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.exam_session import (
    ExamSession,
    ExamSessionStatus,
    ExamSessionCreate,
    ExamSessionUpdate,
    ExamSessionResponse,
    ExamSessionDetailed
)
from ..models.question_set_data import QuestionSetData
from ..cache.redis_client import RedisClient


class ExamSessionService:
    """考試會話管理服務"""

    def __init__(self, db: Session, redis_client: RedisClient = None, question_set_manager=None):
        self.db = db
        self.redis = redis_client
        self.question_set_manager = question_set_manager

    async def list_sessions(self, status_filter: Optional[str] = None) -> List[ExamSessionResponse]:
        """列出考試會話"""
        query = self.db.query(ExamSession)

        if status_filter:
            query = query.filter(ExamSession.status == status_filter)

        sessions = query.order_by(ExamSession.created_at.desc()).all()
        return [self._to_response_model(session) for session in sessions]

    async def create_session(self, session_request: ExamSessionCreate) -> ExamSessionResponse:
        """建立新的考試會話"""
        try:
            # 檢查是否有正在進行的會話
            active_session = self.db.query(ExamSession).filter(
                ExamSession.status.in_([
                    ExamSessionStatus.IN_PROGRESS,
                    ExamSessionStatus.PAUSED
                ])
            ).first()

            if active_session:
                raise ValueError("已有正在進行的考試會話，請先完成或取消現有會話")

            # 驗證題組存在
            if self.question_set_manager:
                question_set = self.question_set_manager.get_question_set(session_request.question_set_id)
                if not question_set:
                    raise ValueError(f"題組 '{session_request.question_set_id}' 不存在")
                total_questions = len(question_set.questions)
            else:
                total_questions = 1  # 預設值，實際應該從題組取得

            # 驗證 VM 配置存在（簡化檢查）
            # TODO: 可以加入對 VMClusterConfig 的實際驗證

            # 建立會話
            session_id = str(uuid.uuid4())
            db_session = ExamSession(
                id=session_id,
                question_set_id=session_request.question_set_id,
                vm_config_id=session_request.vm_config_id,
                duration_minutes=session_request.duration_minutes,
                total_questions=total_questions,
                status=ExamSessionStatus.CREATED
            )

            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)

            # 快取會話狀態
            if self.redis:
                await self._cache_session_state(db_session)

            return self._to_response_model(db_session)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("會話建立失敗，可能存在衝突")
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"建立考試會話失敗: {str(e)}")

    async def get_session(self, session_id: str) -> Optional[ExamSessionDetailed]:
        """取得考試會話詳細資訊"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            return None

        # 取得當前題目
        current_question = None
        if self.question_set_manager:
            question_set = self.question_set_manager.get_question_set(db_session.question_set_id)
            if question_set and 0 <= db_session.current_question_index < len(question_set.questions):
                current_question = question_set.questions[db_session.current_question_index].dict()

        # 計算已用時間
        time_elapsed_minutes = 0
        if db_session.start_time:
            if db_session.status == ExamSessionStatus.IN_PROGRESS:
                time_elapsed_minutes = (datetime.utcnow() - db_session.start_time).total_seconds() / 60
            elif db_session.end_time:
                time_elapsed_minutes = (db_session.end_time - db_session.start_time).total_seconds() / 60

        # 環境狀態資訊
        environment = {
            "status": db_session.environment_status,
            "vnc_container_id": db_session.vnc_container_id,
            "bastion_container_id": db_session.bastion_container_id
        }

        return ExamSessionDetailed.from_session(
            db_session,
            current_question=current_question,
            time_elapsed_minutes=time_elapsed_minutes,
            environment=environment
        )

    async def update_session(self, session_id: str, update_request: ExamSessionUpdate) -> Optional[ExamSessionResponse]:
        """更新考試會話"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            return None

        try:
            # 更新欄位
            if update_request.current_question_index is not None:
                if 0 <= update_request.current_question_index < db_session.total_questions:
                    db_session.current_question_index = update_request.current_question_index
                else:
                    raise ValueError("題目索引超出範圍")

            if update_request.status is not None:
                db_session.status = update_request.status

            self.db.commit()
            self.db.refresh(db_session)

            # 更新快取
            if self.redis:
                await self._cache_session_state(db_session)

            return self._to_response_model(db_session)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"更新考試會話失敗: {str(e)}")

    async def start_session(self, session_id: str) -> ExamSessionResponse:
        """開始考試會話"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status != ExamSessionStatus.CREATED:
            raise ValueError("只能啟動處於 'created' 狀態的考試會話")

        try:
            db_session.status = ExamSessionStatus.IN_PROGRESS
            db_session.start_time = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_session)

            # 更新快取
            if self.redis:
                await self._cache_session_state(db_session)

            return self._to_response_model(db_session)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"啟動考試會話失敗: {str(e)}")

    async def pause_session(self, session_id: str) -> ExamSessionResponse:
        """暫停考試會話"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status != ExamSessionStatus.IN_PROGRESS:
            raise ValueError("只能暫停進行中的考試會話")

        try:
            db_session.status = ExamSessionStatus.PAUSED
            db_session.paused_time = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_session)

            # 更新快取
            if self.redis:
                await self._cache_session_state(db_session)

            return self._to_response_model(db_session)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"暫停考試會話失敗: {str(e)}")

    async def resume_session(self, session_id: str) -> ExamSessionResponse:
        """恢復考試會話"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status != ExamSessionStatus.PAUSED:
            raise ValueError("只能恢復已暫停的考試會話")

        try:
            db_session.status = ExamSessionStatus.IN_PROGRESS
            db_session.resumed_time = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_session)

            # 更新快取
            if self.redis:
                await self._cache_session_state(db_session)

            return self._to_response_model(db_session)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"恢復考試會話失敗: {str(e)}")

    async def complete_session(self, session_id: str) -> ExamSessionResponse:
        """完成考試會話"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status not in [ExamSessionStatus.IN_PROGRESS, ExamSessionStatus.PAUSED]:
            raise ValueError("只能完成進行中或已暫停的考試會話")

        try:
            db_session.status = ExamSessionStatus.COMPLETED
            db_session.end_time = datetime.utcnow()

            # 計算最終分數（簡化版本）
            scores = json.loads(db_session.scores_json) if db_session.scores_json else {}
            db_session.final_score = sum(scores.values()) if scores else 0

            self.db.commit()
            self.db.refresh(db_session)

            # 清除快取
            if self.redis:
                await self._clear_session_cache(session_id)

            return self._to_response_model(db_session)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"完成考試會話失敗: {str(e)}")

    async def submit_answer(self, session_id: str, question_id: int, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交題目答案"""
        db_session = self.db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()

        if not db_session:
            raise ValueError(f"考試會話 '{session_id}' 不存在")

        if db_session.status != ExamSessionStatus.IN_PROGRESS:
            raise ValueError("只能在進行中的考試會話提交答案")

        try:
            # 更新答案記錄
            answers = json.loads(db_session.answers_json) if db_session.answers_json else {}
            answers[str(question_id)] = {
                "data": answer_data,
                "submitted_at": datetime.utcnow().isoformat()
            }
            db_session.answers_json = json.dumps(answers)

            self.db.commit()

            return {"success": True, "message": "答案已提交"}

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"提交答案失敗: {str(e)}")

    def _to_response_model(self, db_session: ExamSession) -> ExamSessionResponse:
        """轉換為回應模型"""
        return ExamSessionResponse(
            id=db_session.id,
            question_set_id=db_session.question_set_id,
            vm_config_id=db_session.vm_config_id,
            duration_minutes=db_session.duration_minutes,
            status=db_session.status,
            current_question_index=db_session.current_question_index,
            total_questions=db_session.total_questions,
            created_at=db_session.created_at,
            start_time=db_session.start_time,
            end_time=db_session.end_time,
            final_score=db_session.final_score,
            max_possible_score=db_session.max_possible_score,
            environment_status=db_session.environment_status
        )

    async def _cache_session_state(self, session: ExamSession):
        """快取會話狀態"""
        if not self.redis:
            return

        cache_key = f"session:{session.id}"
        cache_data = {
            "id": session.id,
            "status": session.status.value,
            "current_question_index": session.current_question_index,
            "start_time": session.start_time.isoformat() if session.start_time else None
        }

        self.redis.set(cache_key, cache_data, expiry=3600)

    async def _clear_session_cache(self, session_id: str):
        """清除會話快取"""
        if not self.redis:
            return

        cache_key = f"session:{session_id}"
        self.redis.delete(cache_key)