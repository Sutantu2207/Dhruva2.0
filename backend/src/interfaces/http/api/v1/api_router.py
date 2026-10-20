"""Dhruva.AI V2 — V1 API Router Aggregator."""

from fastapi import APIRouter
from src.interfaces.http.api.v1.academic import router as academic_router
from src.interfaces.http.api.v1.assessment import router as assessment_router
from src.interfaces.http.api.v1.auth import router as auth_router
from src.interfaces.http.api.v1.curriculum import router as curriculum_router
from src.interfaces.http.api.v1.ingestion import router as ingestion_router
from src.interfaces.http.api.v1.institutions import router as institutions_router
from src.interfaces.http.api.v1.analytics import router as analytics_router
from src.interfaces.http.api.v1.mastery import router as mastery_router
from src.interfaces.http.api.v1.placement import router as placement_router
from src.interfaces.http.api.v1.platform import router as platform_router


api_v1_router = APIRouter()
api_v1_router.include_router(platform_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(institutions_router)
api_v1_router.include_router(academic_router)
api_v1_router.include_router(curriculum_router)
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(assessment_router)
api_v1_router.include_router(mastery_router)
api_v1_router.include_router(placement_router)
api_v1_router.include_router(analytics_router)


