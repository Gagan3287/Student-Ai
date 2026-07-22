"""
Regression test script for FastAPI GET endpoints.
Verifies that all Pydantic response schemas serialize SQLAlchemy models cleanly
without throwing 500 Internal Server Errors (e.g. str vs UUID type mismatches).
"""

import sys
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure backend package is in python path
from main import app
from app.database import get_db, Base, engine, SessionLocal
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.chat import ChatSession, ChatMessage


def run_regression_tests():
    db: Session = SessionLocal()
    try:
        # 1. Ensure test user exists in DB
        test_email = "regression_test_user@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=test_email,
                password_hash="hashed_test_pass",
                full_name="Regression Test User",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Ensure at least one test document and flashcard exist for full serialization testing
        doc = db.query(Document).filter(Document.user_id == user.id).first()
        if not doc:
            doc = Document(
                id=uuid.uuid4(),
                user_id=user.id,
                title="Test Document.pdf",
                file_name="Test Document.pdf",
                storage_path=f"{user.id}/test.pdf",
                content_type="application/pdf",
                status="ready",
                summary="Test summary",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

        card = db.query(Flashcard).filter(Flashcard.user_id == user.id).first()
        if not card:
            card = Flashcard(
                id=uuid.uuid4(),
                user_id=user.id,
                document_id=doc.id,
                question="What is testing?",
                answer="Verification of system behavior.",
                difficulty=2.5,
                sm2_interval=1,
                next_review_at=datetime.now(timezone.utc),
            )
            db.add(card)
            db.commit()
            db.refresh(card)

        session = db.query(ChatSession).filter(ChatSession.user_id == user.id).first()
        if not session:
            session = ChatSession(
                id=uuid.uuid4(),
                user_id=user.id,
                title="Test Session",
                document_id=doc.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # Override auth middleware to return our test user
        app.dependency_overrides[get_current_user] = lambda: user

        client = TestClient(app)

        endpoints_to_test = [
            ("/api/v1/documents", 200, "Documents list"),
            (f"/api/v1/documents/{doc.id}", 200, "Single Document detail"),
            ("/api/v1/flashcards", 200, "Flashcards list"),
            ("/api/v1/flashcards/due", 200, "Due Flashcards list"),
            (f"/api/v1/flashcards?document_id={doc.id}", 200, "Flashcards filtered by document"),
            ("/api/v1/quizzes/history/all", 200, "Quiz attempt history"),
            ("/api/v1/chat/sessions", 200, "Chat sessions list"),
            (f"/api/v1/chat/sessions/{session.id}", 200, "Chat session detail"),
            ("/api/v1/concepts", 200, "Concepts list"),
            ("/api/v1/concepts/graph", 200, "Concepts graph"),
            ("/api/v1/dashboard/stats", 200, "Dashboard stats"),
            ("/api/v1/dashboard/quiz-history", 200, "Dashboard quiz history"),
        ]

        passed = 0
        failed = 0

        print("\n--- Running Endpoints Regression Tests ---")
        for path, expected_status, label in endpoints_to_test:
            res = client.get(path)
            if res.status_code == expected_status:
                print(f"[PASS] {label} ({path}) -> Status {res.status_code}")
                passed += 1
            else:
                print(f"[FAIL] {label} ({path}) -> Expected {expected_status}, got {res.status_code}. Detail: {res.text}")
                failed += 1

        # Test POST /api/v1/resume/analyze endpoint
        sample_resume = "Experienced Python & React developer with SQL and PostgreSQL knowledge."
        sample_jd = "Looking for a Full Stack Developer with Python, React, PostgreSQL, Docker, and AWS skills."
        resume_res = client.post(
            "/api/v1/resume/analyze",
            json={"resume_text": sample_resume, "job_description_text": sample_jd}
        )
        if resume_res.status_code == 200:
            data = resume_res.json()
            if "matched_skills" in data and "missing_skills" in data and "roadmap" in data:
                print(f"[PASS] Resume Gap Analyzer (POST /api/v1/resume/analyze) -> Status 200, Matched: {len(data['matched_skills'])}, Missing: {len(data['missing_skills'])}, Roadmap: {len(data['roadmap'])}")
                passed += 1
            else:
                print(f"[FAIL] Resume Gap Analyzer -> Status 200 but missing required keys: {data}")
                failed += 1
        else:
            print(f"[FAIL] Resume Gap Analyzer -> Expected 200, got {resume_res.status_code}. Detail: {resume_res.text}")
            failed += 1

        total_tests = len(endpoints_to_test) + 1
        print(f"\nSummary: {passed} passed, {failed} failed out of {total_tests} endpoints.\n")
        app.dependency_overrides.clear()
        
        if failed > 0:
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_regression_tests()
