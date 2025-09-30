"""
API v1 主路由器
整合所有 API 端點
"""
from fastapi import APIRouter

from .vm_configs import router as vm_configs_router
from .question_sets import router as question_sets_router
from .exam_sessions import router as exam_sessions_router
from .environment import router as environment_router
from .vnc_access import router as vnc_access_router
from .question_scoring import router as question_scoring_router
from .kubespray_proxy import router as kubespray_proxy_router

# 建立主路由器
api_router = APIRouter()

# 註冊各模組路由
api_router.include_router(vm_configs_router, prefix="/vm-configs", tags=["VM Management"])
api_router.include_router(question_sets_router, prefix="/question-sets", tags=["Question Sets"])
api_router.include_router(exam_sessions_router, prefix="/exam-sessions", tags=["Exam Sessions"])
api_router.include_router(environment_router, prefix="/exam-sessions", tags=["Environment"])
api_router.include_router(vnc_access_router, prefix="/exam-sessions", tags=["VNC Access"])
api_router.include_router(question_scoring_router, prefix="/exam-sessions", tags=["Question Scoring"])
api_router.include_router(kubespray_proxy_router, tags=["Kubespray Proxy"])