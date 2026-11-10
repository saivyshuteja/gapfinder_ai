import json
import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
API_URL = os.getenv("GAPFINDER_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="GapFinder AI",
    page_icon="🎯",
    layout="wide",
)

SESSION_DEFAULTS = {
    "token": None,
    "user_email": None,
    "authenticated": False,
    "document_id": None,
    "topic_id": None,
    "current_question": None,
    "current_questions": None,
    "question_set_topic_id": None,
    "question_set_difficulty": None,
    "question_set_version": None,
    "attempt_id": None,
}


def initialize_session_state():
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def api_request(method, path, **kwargs):
    url = f"{API_URL.rstrip('/')}{path}"
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    response = requests.request(method, url, headers=headers, timeout=120, **kwargs)

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}

    if response.status_code >= 400:
        detail = payload.get("detail", "Request failed")
        if response.status_code >= 500 and detail == "Internal Server Error":
            detail = f"{method} {path} failed with HTTP {response.status_code}. Check the backend log for the traceback."
        raise RuntimeError(detail)

    return payload


def login_user(email: str, password: str):
    response = api_request(
        "POST",
        "/auth/login",
        json={"email": email, "password": password},
    )
    st.session_state.token = response.get("access_token")
    st.session_state.user_email = email
    st.session_state.authenticated = True
    return True


def register_user(email: str, password: str):
    try:
        api_request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password},
        )
        st.success("Account created successfully. You can now log in.")
        return True
    except Exception as exc:
        st.error(str(exc))
        return False


def load_documents():
    try:
        docs = api_request("GET", "/documents")
        return docs if isinstance(docs, list) else []
    except Exception:
        return []


def load_topics(document_id):
    try:
        topics = api_request("GET", f"/topics/document/{document_id}")
        return topics if isinstance(topics, list) else []
    except Exception:
        return []


def load_gap_reports(document_id):
    try:
        reports = api_request("GET", "/gap-reports", params={"document_id": document_id})
        return reports if isinstance(reports, list) else []
    except Exception:
        return []


def load_progress_history(document_id):
    try:
        history = api_request("GET", f"/progress/document/{document_id}/history")
        return history if isinstance(history, list) else []
    except Exception:
        return []


def start_attempt(topic_id):
    result = api_request("POST", f"/attempts/start/{topic_id}")
    st.session_state.attempt_id = result["id"]
    return result


def generate_questions(topic_id, difficulty="medium", count=5):
    result = api_request(
        "POST",
        f"/questions/generate-batch/{topic_id}",
        params={"difficulty": difficulty, "count": count},
    )
    if not isinstance(result, list) or not result:
        raise RuntimeError("The question service returned no questions.")
    st.session_state.current_questions = result
    st.session_state.question_set_topic_id = topic_id
    st.session_state.question_set_difficulty = difficulty
    st.session_state.question_set_version = "competitive-python-v2"
    return result


def submit_answer(attempt_id, question_id, selected_answer):
    return api_request(
        "POST",
        f"/attempts/{attempt_id}/answer",
        json={"question_id": question_id, "student_answer": selected_answer},
    )


def complete_attempt(attempt_id):
    return api_request("POST", f"/attempts/{attempt_id}/complete")


def generate_gap_report(attempt_id):
    return api_request("POST", f"/gap-reports/generate/{attempt_id}")


def generate_revision_plan(document_id, minutes_per_day=60, total_days=5):
    return api_request(
        "POST",
        "/revision-plans/generate",
        json={
            "document_id": document_id,
            "available_minutes_per_day": minutes_per_day,
            "total_days": total_days,
            "exam_date": None,
        },
    )


def map_exam_paper(document_id, topic_document_id):
    ingestion = api_request(
        "POST",
        f"/exam-questions/ingest/{document_id}",
        params={"topic_document_id": topic_document_id},
    )
    topic_names = {
        topic["id"]: topic["name"]
        for topic in load_topics(topic_document_id)
    }
    st.success(
        f"Past paper processed: {ingestion['questions_processed']} questions mapped to syllabus topics."
    )
    if ingestion["mappings"]:
        st.dataframe(
            [
                {
                    "Past-paper question": item["question"],
                    "Page": item["page_number"],
                    "Mapped topic": topic_names.get(item["topic_id"], "Unknown topic"),
                    "Confidence": f"{item['confidence']:.0%}",
                }
                for item in ingestion["mappings"]
            ],
            width="stretch",
        )
    return ingestion


def show_login_page():
    initialize_session_state()

    st.title("🎯 GapFinder AI")
    st.caption("A diagnostic learning system that finds what the student does not know.")

    if os.getenv("DEMO_MODE", "true").lower() in {"true", "1", "yes"}:
        st.info(
            "Judge demo login: "
            f"{os.getenv('DEMO_EMAIL', 'demo@gapfinder.ai')} / "
            f"{os.getenv('DEMO_PASSWORD', 'GapFinderDemo2026!')}"
        )

    login_tab, register_tab = st.tabs(["🔐 Login", "📝 Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                try:
                    login_user(email, password)
                    st.success("Login successful")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input("Email", key="reg_email")
            register_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            submitted = st.form_submit_button("Create Account")

        if submitted:
            if not register_email or not register_password:
                st.warning("Please complete all registration fields.")
            elif register_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(register_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                register_user(register_email, register_password)


def status_badge(status: str):
    status = (status or "").lower()
    if status == "weak":
        return "🔴 Weak"
    if status == "medium":
        return "🟡 Medium"
    return "🟢 Strong"


def navigate_dashboard(page: str):
    st.session_state["dashboard_page"] = page


def show_overview():
    st.title("📊 Learning Dashboard")
    st.caption("Diagnosis first. Revision follows the evidence.")

    documents = load_documents()
    topic_details = {}
    reports = []
    for document in documents:
        for topic in load_topics(document["id"]):
            topic_details[(document["id"], topic["id"])] = {
                **topic,
                "document_name": document["filename"],
            }
        reports.extend(load_gap_reports(document["id"]))

    latest_reports = {}
    for report in reports:
        key = (report.get("document_id"), report.get("topic_id"))
        previous = latest_reports.get(key)
        if previous is None or report.get("created_at", "") > previous.get("created_at", ""):
            latest_reports[key] = report
    reports = list(latest_reports.values())

    weak_topics = sum(1 for report in reports if report.get("status") == "weak")
    medium_topics = sum(1 for report in reports if report.get("status") == "medium")
    strong_topics = sum(1 for report in reports if report.get("status") == "strong")
    total_questions = sum(report.get("total_questions", 0) for report in reports)
    total_correct = sum(report.get("correct_answers", 0) for report in reports)
    overall_accuracy = (
        f"{(total_correct / total_questions) * 100:.0f}%"
        if total_questions
        else "—"
    )

    cols = st.columns(4)
    with cols[0]:
        st.metric("Materials", len(documents))
    with cols[1]:
        st.metric("Topics", len(topic_details))
    with cols[2]:
        st.metric("Weak Topics", weak_topics if reports else "—")
    with cols[3]:
        st.metric("Overall Accuracy", overall_accuracy)

    st.markdown("---")
    st.subheader("🎯 Your diagnosis")
    status_cols = st.columns(3)
    status_cols[0].metric("🔴 Weak", weak_topics)
    status_cols[1].metric("🟡 Medium", medium_topics)
    status_cols[2].metric("🟢 Strong", strong_topics)

    if reports:
        focus_candidates = [report for report in reports if report.get("status") in {"weak", "medium"}]
        if not focus_candidates:
            focus_candidates = reports

        def revision_priority(report):
            topic = topic_details.get((report.get("document_id"), report.get("topic_id")), {})
            weakness = 1 - report.get("accuracy", 0) / 100
            importance = topic.get("exam_importance", 0)
            return 0.7 * weakness + 0.3 * importance

        focus = max(focus_candidates, key=revision_priority)
        topic = topic_details.get((focus.get("document_id"), focus.get("topic_id")), {})
        with st.container(border=True):
            st.markdown(f"#### Next revision focus: {topic.get('name', 'Topic')}")
            st.write(focus.get("reason", "Review this topic before your next quiz."))
            st.caption(
                f"{topic.get('document_name', 'Study material')} · "
                f"{focus.get('correct_answers', 0)} correct, "
                f"{focus.get('incorrect_answers', 0)} wrong · "
                f"Exam frequency {topic.get('exam_importance', 0):.2f}"
            )
        action_cols = st.columns(2)
        action_cols[0].button(
            "Re-test a topic",
            on_click=navigate_dashboard,
            args=("Diagnostic",),
        )
        action_cols[1].button(
            "Open revision plan",
            on_click=navigate_dashboard,
            args=("Revision Plan",),
        )
    else:
        st.info("No diagnosis yet. Upload study material, then take a diagnostic to discover your weak topics.")
        st.button(
            "Start diagnostic",
            on_click=navigate_dashboard,
            args=("Diagnostic",),
        )

    if topic_details:
        diagnosis_rows = []
        for key, topic in topic_details.items():
            report = latest_reports.get(key)
            diagnosis_rows.append({
                "Unit": topic.get("unit") or "—",
                "Topic": topic["name"],
                "Status": status_badge(report.get("status")) if report else "Not tested",
                "Correct": str(report.get("correct_answers", 0)) if report else "—",
                "Wrong": str(report.get("incorrect_answers", 0)) if report else "—",
                "Accuracy": f"{report.get('accuracy', 0):.0f}%" if report else "—",
            })
        st.dataframe(diagnosis_rows, width="stretch")

    progress_history = []
    for document in documents:
        for item in load_progress_history(document["id"]):
            progress_history.append({
                **item,
                "document": document["filename"],
                "series": f"{document['filename']} · {item['topic_name']}",
                "attempt": f"Attempt {item['attempt_number']}",
                "topic_attempt": f"Topic attempt {item['topic_attempt_number']}",
            })

    st.markdown("---")
    st.subheader("📈 Progress over time")
    if progress_history:
        history_frame = pd.DataFrame(progress_history)
        st.line_chart(
            history_frame,
            x="attempt_number",
            y="accuracy",
            color="series",
        )
        st.dataframe(
            history_frame[["document", "attempt", "topic_attempt", "topic_name", "accuracy", "total_questions", "completed_at"]],
            width="stretch",
        )
    else:
        st.info("Complete a diagnostic assessment to start tracking topic accuracy over time.")

def show_materials():
    st.title("📚 Materials")
    document_type = st.selectbox(
        "What are you uploading?",
        ["syllabus", "material", "exam"],
        format_func=lambda value: {
            "syllabus": "Syllabus",
            "material": "Textbook / Notes",
            "exam": "Past exam paper",
        }[value],
    )
    existing_documents = load_documents()
    curriculum_documents = [
        doc for doc in existing_documents
        if doc.get("document_type") != "exam"
    ]
    curriculum_id = None
    if document_type == "exam":
        if not curriculum_documents:
            st.warning("Upload a syllabus or study material before adding past papers.")
        else:
            curriculum_id = st.selectbox(
                "Map questions to this syllabus",
                [doc["id"] for doc in curriculum_documents],
                format_func=lambda value: next(
                    doc["filename"] for doc in curriculum_documents if doc["id"] == value
                ),
            )

    uploaded_file = st.file_uploader("Upload PDF material", type=["pdf"])
    can_upload = document_type != "exam" or curriculum_id is not None
    if uploaded_file is not None and can_upload and st.button("Upload and Process"):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(
                f"{API_URL.rstrip('/')}/documents/upload",
                files=files,
                data={"document_type": document_type},
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=120,
            )
            if response.status_code >= 400:
                st.error(response.text)
            else:
                uploaded_document = response.json()
                document_id = uploaded_document["id"]
                if document_type == "exam":
                    map_exam_paper(document_id, curriculum_id)
                else:
                    topics = api_request("POST", f"/topics/generate/{document_id}")
                    st.success(f"Uploaded and built a topic map with {len(topics)} topics.")
        except Exception as exc:
            st.error(str(exc))

    documents = load_documents()
    if not documents:
        st.info("No material uploaded yet.")
        return

    rows = [{"ID": doc["id"], "Filename": doc["filename"], "Type": doc.get("document_type", "material")} for doc in documents]
    st.dataframe(rows, width="stretch")

    with st.expander("Classify and map an existing past-paper PDF"):
        curriculum_documents = [doc for doc in documents if doc.get("document_type") != "exam"]
        if not curriculum_documents:
            st.info("Upload a syllabus or study material to map exam questions against.")
        else:
            existing_paper_id = st.selectbox(
                "Existing PDF",
                [doc["id"] for doc in documents],
                format_func=lambda value: next(doc["filename"] for doc in documents if doc["id"] == value),
                key="existing_exam_document",
            )
            mapping_document_id = st.selectbox(
                "Map questions to",
                [doc["id"] for doc in curriculum_documents],
                format_func=lambda value: next(doc["filename"] for doc in curriculum_documents if doc["id"] == value),
                key="existing_exam_curriculum",
            )
            if st.button("Classify and map past paper"):
                if existing_paper_id == mapping_document_id:
                    st.error("Choose a separate syllabus document for topic mapping.")
                else:
                    try:
                        api_request(
                            "PATCH",
                            f"/documents/{existing_paper_id}/type",
                            json={"document_type": "exam"},
                        )
                        map_exam_paper(existing_paper_id, mapping_document_id)
                    except Exception as exc:
                        st.error(str(exc))

            st.markdown("#### Add a question manually")
            st.caption("Use this when the PDF is scanned or its question numbering cannot be read automatically.")
            mapping_topics = load_topics(mapping_document_id)
            if not mapping_topics:
                st.warning("Generate the syllabus topic map before mapping exam questions.")
            else:
                with st.form("manual_exam_question_form"):
                    manual_question = st.text_area("Past-paper question", key="manual_exam_question")
                    manual_topic_id = st.selectbox(
                        "Syllabus topic",
                        [topic["id"] for topic in mapping_topics],
                        format_func=lambda value: next(
                            f"{topic.get('unit') or ''} · {topic['name']}"
                            for topic in mapping_topics
                            if topic["id"] == value
                        ),
                    )
                    manual_page = st.number_input("Page number", min_value=1, value=1, step=1)
                    add_question = st.form_submit_button("Save mapping and update frequency")

                if add_question:
                    if not manual_question.strip():
                        st.warning("Enter the question text before saving.")
                    elif existing_paper_id == mapping_document_id:
                        st.error("Choose a separate syllabus document for topic mapping.")
                    else:
                        try:
                            api_request(
                                "PATCH",
                                f"/documents/{existing_paper_id}/type",
                                json={"document_type": "exam"},
                            )
                            api_request(
                                "POST",
                                "/exam-questions",
                                json={
                                    "document_id": existing_paper_id,
                                    "topic_id": manual_topic_id,
                                    "question": manual_question.strip(),
                                    "source_page": int(manual_page),
                                },
                            )
                            st.success("Question mapped. Topic exam frequency has been updated.")
                        except Exception as exc:
                            st.error(str(exc))


def show_topics():
    st.title("🧩 Topics")
    documents = load_documents()
    documents = [doc for doc in documents if doc.get("document_type") != "exam"]
    if not documents:
        st.info("Upload a PDF before generating topics.")
        return

    selected_doc_id = st.selectbox("Select material", [doc["id"] for doc in documents], format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x))
    st.session_state.document_id = selected_doc_id

    if st.button("Generate Topics"):
        try:
            topic_data = api_request("POST", f"/topics/generate/{selected_doc_id}")
            st.success("Topics generated successfully.")
            st.json(topic_data)
        except Exception as exc:
            st.error(str(exc))

    topics = load_topics(selected_doc_id)
    if not topics:
        st.info("No topic map generated yet.")
        return

    st.subheader(f"Topic and subtopic map ({len(topics)} topics)")
    reports_by_topic = {}
    for report in load_gap_reports(selected_doc_id):
        topic_id = report.get("topic_id")
        previous = reports_by_topic.get(topic_id)
        if previous is None or report.get("created_at", "") > previous.get("created_at", ""):
            reports_by_topic[topic_id] = report

    topics_by_unit = {}
    topics_by_id = {topic["id"]: topic for topic in topics}
    children_by_parent = {}
    roots = []
    for topic in topics:
        parent_id = topic.get("parent_topic_id")
        if parent_id in topics_by_id:
            children_by_parent.setdefault(parent_id, []).append(topic)
        else:
            roots.append(topic)

    for topic in roots:
        topics_by_unit.setdefault(topic.get("unit") or "Topics", []).append(topic)

    def show_topic_summary(topic, prefix=""):
        report = reports_by_topic.get(topic["id"])
        st.markdown(f"{prefix}**{topic['name']}**")
        st.caption(
            f"Past-paper questions: {topic.get('exam_question_count', 0)} · "
            f"Exam frequency: {topic.get('exam_importance', 0):.0%}"
        )
        if report:
            st.caption(
                f"{status_badge(report.get('status'))} · "
                f"{report.get('correct_answers', 0)}/{report.get('total_questions', 0)} correct · "
                f"{report.get('accuracy', 0):.0f}% accuracy"
            )
        else:
            st.caption("Not diagnosed yet")

    for unit, unit_topics in topics_by_unit.items():
        st.markdown(f"### {unit}")
        for parent in unit_topics:
            show_topic_summary(parent)
            children = children_by_parent.get(parent["id"], [])
            if children:
                with st.expander(f"Subtopics ({len(children)})"):
                    for child in children:
                        show_topic_summary(child, "↳ ")
            st.markdown("---")


def show_diagnostic():
    st.title("🧪 Diagnostic Assessment")
    documents = load_documents()
    if not documents:
        st.info("Upload learning material before starting a diagnosis.")
        return

    selected_doc_id = st.selectbox("Select material", [doc["id"] for doc in documents], format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x), key="diag_doc")
    topics = load_topics(selected_doc_id)
    if not topics:
        st.warning("Generate topics first.")
        return

    selected_topic = st.selectbox("Select topic", [topic["id"] for topic in topics], format_func=lambda x: next(topic["name"] for topic in topics if topic["id"] == x), key="diag_topic")
    selected_document = next(doc for doc in documents if doc["id"] == selected_doc_id)
    selected_topic_data = next(topic for topic in topics if topic["id"] == selected_topic)
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    question_count = st.number_input("Questions per topic", min_value=5, max_value=6, value=5, step=1)

    if st.button("Generate Diagnostic Questions"):
        try:
            questions = generate_questions(selected_topic, difficulty, int(question_count))
            st.success(f"Generated {len(questions)} questions from the selected topic.")
        except Exception as exc:
            st.error(str(exc))

    questions = st.session_state.get("current_questions")
    if st.session_state.get("question_set_version") != "competitive-python-v2":
        st.session_state.current_questions = None
        st.session_state.question_set_topic_id = None
        st.session_state.question_set_difficulty = None
        st.session_state.question_set_version = None
        questions = None
    if (
        not questions
        or st.session_state.get("question_set_topic_id") != selected_topic
        or st.session_state.get("question_set_difficulty") != difficulty
    ):
        return

    answers = {}
    for index, question in enumerate(questions, start=1):
        st.subheader(f"Question {index} of {len(questions)}")
        st.write(question.get("question", "Question"))
        if not question.get("source_page") or not question.get("source_excerpt"):
            st.warning("This question has no verified source citation. Generate a fresh question set before answering.")
            return
        citation = [selected_document["filename"]]
        if selected_topic_data.get("unit"):
            citation.append(selected_topic_data["unit"])
        citation.append(f"Section: {selected_topic_data['name']}")
        citation.append(f"Page {question['source_page']}")
        st.caption("Source: " + " · ".join(citation))
        options = question.get("options") or []
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                options = [options]
        if not options:
            st.warning("This question has no answer options.")
            continue
        selected_answer = st.radio(
            "Choose your answer",
            options,
            key=f"diagnostic_answer_{question['id']}",
        )
        answers[question["id"]] = chr(ord("A") + options.index(selected_answer))

    if len(answers) == len(questions) and st.button("Submit Diagnostic Assessment"):
        submission_stage = "starting the attempt"
        try:
            attempt = start_attempt(selected_topic)
            feedback = []
            for answer_number, (question_id, selected_answer) in enumerate(answers.items(), start=1):
                submission_stage = f"saving answer {answer_number} of {len(answers)}"
                result = submit_answer(attempt["id"], question_id, selected_answer)
                question = next(item for item in questions if item["id"] == question_id)
                feedback.append((question, result))

            st.subheader("Answer feedback")
            for question, result in feedback:
                options = question.get("options") or []
                if isinstance(options, str):
                    options = json.loads(options)
                correct_key = (question.get("correct_answer") or "").strip().upper()
                correct_index = ord(correct_key) - ord("A") if len(correct_key) == 1 else -1
                correct_option = (
                    options[correct_index]
                    if 0 <= correct_index < len(options)
                    else correct_key
                )
                if result.get("is_correct"):
                    st.success(f"Question {question['id']}: Correct")
                else:
                    st.error(f"Question {question['id']}: Not quite. Correct answer: {correct_option}")
                st.write(question.get("explanation") or result.get("evaluation_reason", "No explanation was provided."))

            submission_stage = "completing the attempt"
            complete = complete_attempt(attempt["id"])
            st.info(f"Attempt completed: {complete.get('status')}")

            submission_stage = "generating the gap report"
            report = generate_gap_report(attempt["id"])
            st.subheader("📌 Topic diagnosis")
            summary_cols = st.columns(4)
            summary_cols[0].metric("Correct", report.get("correct_answers", 0))
            summary_cols[1].metric("Wrong", report.get("incorrect_answers", 0))
            summary_cols[2].metric("Accuracy", f"{report.get('accuracy', 0):.0f}%")
            summary_cols[3].metric("Status", status_badge(report.get("status")))
            st.write(report.get("reason", "No diagnosis reason was returned."))
            st.session_state.current_questions = None
            st.session_state.question_set_topic_id = None
            st.session_state.question_set_difficulty = None
            st.session_state.question_set_version = None
        except Exception as exc:
            st.error(f"Failed while {submission_stage}: {exc}")


def show_gap_reports():
    st.title("🎯 Gap Report")
    documents = [doc for doc in load_documents() if doc.get("document_type") != "exam"]
    if not documents:
        st.info("Upload a syllabus or study material to build a topic diagnosis.")
        return

    selected_doc_id = st.selectbox(
        "Select material",
        [doc["id"] for doc in documents],
        format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x),
        key="gap_doc",
    )

    try:
        reports = api_request("GET", "/gap-reports", params={"document_id": selected_doc_id})
        topics = load_topics(selected_doc_id)
        latest_by_topic = {}
        for report in reports:
            topic_id = report.get("topic_id")
            previous = latest_by_topic.get(topic_id)
            if previous is None or report.get("created_at", "") > previous.get("created_at", ""):
                latest_by_topic[topic_id] = report

        topic_rows = []
        for topic in topics:
            report = latest_by_topic.get(topic["id"])
            topic_rows.append((topic, report))

        weak = [(topic, report) for topic, report in topic_rows if report and report.get("status") == "weak"]
        medium = [(topic, report) for topic, report in topic_rows if report and report.get("status") == "medium"]
        strong = [(topic, report) for topic, report in topic_rows if report and report.get("status") == "strong"]
        untested = [(topic, report) for topic, report in topic_rows if not report]

        metric_cols = st.columns(4)
        metric_cols[0].metric("Diagnosed", len(latest_by_topic))
        metric_cols[1].metric("🔴 Weak", len(weak))
        metric_cols[2].metric("🟡 Medium", len(medium))
        metric_cols[3].metric("🟢 Strong", len(strong))

        weak_tab, medium_tab, strong_tab, untested_tab = st.tabs(
            [f"🔴 Weak ({len(weak)})", f"🟡 Medium ({len(medium)})", f"🟢 Strong ({len(strong)})", f"Not tested ({len(untested)})"]
        )
        for tab, group in (
            (weak_tab, weak),
            (medium_tab, medium),
            (strong_tab, strong),
        ):
            with tab:
                if not group:
                    st.info("No topics in this category yet.")
                    continue
                st.dataframe(
                    [
                        {
                            "Topic": topic["name"],
                            "Correct": report.get("correct_answers", 0),
                            "Wrong": report.get("incorrect_answers", 0),
                            "Total": report.get("total_questions", 0),
                            "Accuracy": f"{report.get('accuracy', 0):.0f}%",
                            "Priority": report.get("priority_score", 0),
                        }
                        for topic, report in group
                    ],
                    width="stretch",
                )
                for topic, report in group:
                    with st.expander(f"{topic['name']} · {report.get('correct_answers', 0)}/{report.get('total_questions', 0)} correct"):
                        st.write(report.get("reason", "No reason was recorded."))
                        st.caption(f"Latest result: {report.get('accuracy', 0):.1f}% · Priority {report.get('priority_score', 0)}")

        with untested_tab:
            if untested:
                st.dataframe(
                    [
                        {"Unit": topic.get("unit") or "—", "Topic": topic["name"], "Status": "Not tested"}
                        for topic, _ in untested
                    ],
                    width="stretch",
                )
                st.info("Complete a diagnostic for these topics before assigning a strength level.")
            else:
                st.info("Every topic has a diagnostic result.")
    except Exception as exc:
        st.warning(str(exc))


def show_revision_plan():
    st.title("📅 Revision Plan")
    documents = [doc for doc in load_documents() if doc.get("document_type") != "exam"]
    if not documents:
        st.info("Upload material to generate the plan.")
        return

    selected_doc_id = st.selectbox("Select material", [doc["id"] for doc in documents], format_func=lambda x: next(doc["filename"] for doc in documents if doc["id"] == x), key="rev_doc")
    minutes = st.number_input("Available minutes per day", min_value=30, max_value=300, value=120, step=15)
    days = st.number_input("Study days", min_value=3, max_value=30, value=5)

    if st.button("Generate Revision Plan"):
        try:
            result = generate_revision_plan(selected_doc_id, minutes, int(days))
            st.success("Plan saved. It will update after each new diagnostic report.")
            st.session_state["revision_plan_data"] = json.loads(result["plan_data"])
        except Exception as exc:
            st.error(str(exc))

    try:
        saved_plans = api_request("GET", f"/revision-plans/document/{selected_doc_id}")
        plan_days = saved_plans[0]["plan"] if saved_plans else st.session_state.get("revision_plan_data", [])
    except Exception:
        plan_days = st.session_state.get("revision_plan_data", [])

    if not plan_days:
        st.info("Complete a diagnostic first so the plan can prioritize your weakest topics.")
        return

    st.caption("Priority combines your latest accuracy with exam frequency. The daily task minutes fit your available time.")
    for day in plan_days:
        with st.expander(f"Day {day['day']} · {day['date']} · {day['total_minutes']} minutes", expanded=day["day"] == 1):
            for task in day["tasks"]:
                st.markdown(f"#### {task['topic_name']} · {task['allocated_minutes']} minutes")
                st.caption(
                    f"{status_badge(task['status'])} · {task['accuracy']:.0f}% correct · "
                    f"Exam frequency {task['exam_importance']:.0%}"
                )
                st.write(task["activity"])
                st.write(task["objective"])


def show_explain():
    st.title("💡 Explain This Topic")
    documents = [doc for doc in load_documents() if doc.get("document_type") != "exam"]
    if not documents:
        st.info("Upload a syllabus, chapter, or notes before asking for an explanation.")
        return

    selected_doc_id = st.selectbox(
        "Use this material",
        [doc["id"] for doc in documents],
        format_func=lambda value: next(doc["filename"] for doc in documents if doc["id"] == value),
        key="explain_doc",
    )
    question = st.text_area("Ask about the uploaded material", placeholder="Explain Bayes theorem using only the uploaded material.")
    if st.button("Explain") and question.strip():
        try:
            answer = api_request(
                "GET",
                "/explain/",
                params={"question": question, "document_id": selected_doc_id},
            )
            st.subheader("Answer")
            st.write(answer.get("answer", "No answer returned."))
            st.subheader("Sources")
            for source in answer.get("sources", []):
                st.markdown(
                    f"- **{source.get('document_name')}** · {source.get('unit') or ''} · "
                    f"Section: {source.get('section')} · Page {source.get('page_number')}"
                )
        except Exception as exc:
            st.error(str(exc))


def show_dashboard():
    initialize_session_state()

    st.sidebar.title("GapFinder AI")
    st.sidebar.write(f"👤 {st.session_state.user_email or 'Student'}")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.authenticated = False
        st.session_state.document_id = None
        st.session_state.current_question = None
        st.session_state.current_questions = None
        st.session_state.question_set_topic_id = None
        st.session_state.question_set_difficulty = None
        st.session_state.question_set_version = None
        st.session_state.attempt_id = None
        st.rerun()

    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Materials", "Topics", "Diagnostic", "Gap Report", "Revision Plan", "Explain"],
        key="dashboard_page",
    )

    if page == "Overview":
        show_overview()
    elif page == "Materials":
        show_materials()
    elif page == "Topics":
        show_topics()
    elif page == "Diagnostic":
        show_diagnostic()
    elif page == "Gap Report":
        show_gap_reports()
    elif page == "Revision Plan":
        show_revision_plan()
    elif page == "Explain":
        show_explain()


def main():
    initialize_session_state()

    if st.session_state.authenticated:
        show_dashboard()
    else:
        show_login_page()


if __name__ == "__main__":
    main()