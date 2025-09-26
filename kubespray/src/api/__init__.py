"""API 路由套件初始化"""

from .kubespray_routes import router as kubespray_router

__all__ = [
    "kubespray_router"
]