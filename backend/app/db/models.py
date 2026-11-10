
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pdf"
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="material"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Chunk(Base):

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False
    )

    page_number: Mapped[int] = mapped_column(
        nullable=False
    )

    unit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    content: Mapped[str] = mapped_column(
        nullable=False
    )
    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(384),
    nullable=True
   )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
class Topic(Base):

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    parent_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"),
        nullable=True,
        index=True,
    )

    unit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    exam_question_count: Mapped[int] = mapped_column(
    nullable=False,
    default=0
     )

    exam_importance: Mapped[float] = mapped_column(
    Float,
    nullable=False,
    default=0.0
    ) 
class Question(Base):

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    question: Mapped[str] = mapped_column(
        nullable=False
    )

    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="mcq"
    )

    difficulty: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="medium"
    )

    options: Mapped[str | None] = mapped_column(
        nullable=True
    )

    correct_answer: Mapped[str | None] = mapped_column(
        nullable=True
    )

    explanation: Mapped[str | None] = mapped_column(
        nullable=True
    )

    source_page: Mapped[int | None] = mapped_column(
        nullable=True
    )

    source_excerpt: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True
    )

    source_chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("chunks.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="in_progress"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id"),
        nullable=False,
        index=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
        index=True
    )

    student_answer: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    classification: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    supporting_evidence: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True
    )

    source_pages: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    evaluation_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    misconception: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class GapReport(Base):
    __tablename__ = "gap_reports"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False,
        index=True
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id"),
        nullable=False,
        index=True
    )

    total_questions: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    correct_answers: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    incorrect_answers: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    weakness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    priority_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False,
        index=True
    )

    question: Mapped[str] = mapped_column(
        nullable=False
    )

    source_page: Mapped[int | None] = mapped_column(
        nullable=True
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
class RevisionPlan(Base):
    __tablename__ = "revision_plans"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    exam_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    available_minutes_per_day: Mapped[int] = mapped_column(
        nullable=False
    )

    total_days: Mapped[int] = mapped_column(
        nullable=False
    )

    plan_data: Mapped[str] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )