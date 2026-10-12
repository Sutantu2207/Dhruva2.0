"""Dhruva.AI V2 — V1 API Router Aggregator."""

from fastapi import APIRouter
from src.interfaces.http.api.v1.academic import router as academic_router
from src.interfaces.http.api.v1.auth import router as auth_router
from src.interfaces.http.api.v1.curriculum import router as curriculum_router
from src.interfaces.http.api.v1.institutions import router as institutions_router
from src.interfaces.http.api.v1.platform import router as platform_router


api_v1_router = APIRouter()
api_v1_router.include_router(platform_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(institutions_router)
api_v1_router.include_router(academic_router)
api_v1_router.include_router(curriculum_router)


