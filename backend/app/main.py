from fastapi import FastAPI
from app.api.topics import router as topic_router
from app.api.questions import router as question_router
from app.api.subjective import router as subjective_router
from app.api.retest import router as retest_router
from app.api.progress import router as progress_router
from app.api.explain import router as explain_router
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.migrations import upgrade_schema
from app.db.models import User
from app.core.security import hash_password
from app.api.attempts import router as attempt_router
from app.api.auth import router as auth_router
from app.api.documents import router as document_router
from app.api.gap_reports import router as gap_report_router
from app.api.exam_questions import router as exam_question_router
from app.api.exam_importance import router as exam_importance_router
from app.api.revision_plans import router as revision_plan_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="GapFinder AI - Diagnostic Learning System"
)

Base.metadata.create_all(bind=engine)
upgrade_schema(engine)

if settings.DEMO_MODE:
    demo_db = SessionLocal()
    try:
        demo_user = demo_db.query(User).filter(User.email == settings.DEMO_EMAIL).first()
        if not demo_user:
            demo_db.add(User(
                email=settings.DEMO_EMAIL,
                password_hash=hash_password(settings.DEMO_PASSWORD),
            ))
            demo_db.commit()
    finally:
        demo_db.close()

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(topic_router)
app.include_router(question_router)
app.include_router(attempt_router)
app.include_router(gap_report_router)
app.include_router(exam_question_router)
app.include_router(exam_importance_router)
app.include_router(revision_plan_router)
app.include_router(subjective_router)
app.include_router(retest_router)
app.include_router(progress_router)
app.include_router(explain_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to GapFinder AI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }