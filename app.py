import streamlit as st
import os
from dotenv import load_dotenv

from utils.document_processor import process_uploaded_file
from utils.vector_store import build_vector_store, search_vector_store
from utils.llm_handler import ask_gemini, generate_study_plan, identify_weak_areas
from utils.exam_helper import extract_questions_from_text, categorize_question, build_exam_query

load_dotenv()

# ---- page config ----
st.set_page_config(
    page_title="StudyMate AI - Exam Prep Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- session state init ----
# keeping everything in session state so it persists across reruns
if "documents" not in st.session_state:
    st.session_state.documents = []
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "metadata" not in st.session_state:
    st.session_state.metadata = []
if "question_history" not in st.session_state:
    st.session_state.question_history = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "extracted_questions" not in st.session_state:
    st.session_state.extracted_questions = []


# ---- sidebar ----
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=60)
    st.title("📚 StudyMate AI")
    st.caption("Your personal exam prep assistant")
    st.divider()

    # document upload section
    st.subheader("📂 Upload Study Materials")
    uploaded_files = st.file_uploader(
        "Upload PDFs, DOCX, or PPTX files",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=True,
        help="Upload your textbooks, notes, lab manuals, and previous year question papers"
    )

    if uploaded_files:
        if st.button("🔄 Process Files", type="primary", use_container_width=True):
            with st.spinner("Reading your documents..."):
                new_docs = []
                for f in uploaded_files:
                    result = process_uploaded_file(f)
                    if result:
                        new_docs.append(result)
                        st.success(f"✅ {f.name} ({result['content_type']})")

                if new_docs:
                    st.session_state.documents = new_docs
                    with st.spinner("Building search index... this takes a moment"):
                        index, meta = build_vector_store(new_docs)
                        st.session_state.faiss_index = index
                        st.session_state.metadata = meta

                    # also try to extract questions from question papers
                    extracted = []
                    for doc in new_docs:
                        if doc["content_type"] == "question_paper":
                            qs = extract_questions_from_text(doc["text"])
                            extracted.extend(qs)
                    st.session_state.extracted_questions = extracted
                    st.success(f"✅ {len(new_docs)} documents indexed!")

    st.divider()

    # show uploaded documents
    if st.session_state.documents:
        st.subheader("📋 Loaded Documents")
        type_icons = {
            "textbook": "📗",
            "notes": "📝",
            "question_paper": "📄",
            "lab_manual": "🔬"
        }
        for doc in st.session_state.documents:
            icon = type_icons.get(doc["content_type"], "📁")
            st.write(f"{icon} {doc['filename'][:30]}...")
            st.caption(f"Type: {doc['content_type']} | {doc['char_count']} chars")

    st.divider()
    if st.button("🗑️ Clear Everything", use_container_width=True):
        for key in ["documents", "faiss_index", "metadata", "question_history", "chat_history", "extracted_questions"]:
            st.session_state[key] = [] if key != "faiss_index" else None
        st.rerun()


# ---- main content ----
st.title("🎓 StudyMate AI — Exam Preparation Assistant")

if not st.session_state.documents:
    # welcome screen
    st.info("👈 Upload your study materials from the sidebar to get started!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📗 What to upload")
        st.write("- Textbook chapters (PDF)")
        st.write("- Lecture notes (PDF/DOCX)")
        st.write("- Lab manuals (PDF/DOCX)")
        st.write("- Previous year papers (PDF)")
    with col2:
        st.markdown("### 🤔 What you can ask")
        st.write("- Explain a topic in detail")
        st.write("- Solve a question from the paper")
        st.write("- Compare two concepts")
        st.write("- Generate a study plan")
    with col3:
        st.markdown("### ✨ Features")
        st.write("- Multi-document search")
        st.write("- Question bank solver")
        st.write("- Weak area identification")
        st.write("- Custom study plans")
    st.stop()


# ---- tabs ----
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Ask Anything",
    "📄 Question Bank",
    "📊 Progress Tracker",
    "🗺️ Study Plan"
])


# ---- TAB 1: Ask Anything ----
with tab1:
    st.subheader("💬 Ask about any topic or question")

    # show chat history
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.write(chat["content"])

    user_input = st.chat_input("Ask a question, e.g. 'Explain database normalization' or 'Solve Q3 from 2023 paper'")

    if user_input:
        # add to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.question_history.append(user_input)

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Searching your documents and thinking..."):
                # search vector store
                relevant_chunks = search_vector_store(
                    user_input,
                    st.session_state.faiss_index,
                    st.session_state.metadata,
                    top_k=3
                )

                if relevant_chunks:
                    # show which sources were used
                    sources = list(set([c["filename"] for c in relevant_chunks]))
                    st.caption(f"📎 Sources used: {', '.join(sources)}")

                answer = ask_gemini(user_input, relevant_chunks)
                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ---- TAB 2: Question Bank ----
with tab2:
    st.subheader("📄 Question Bank — Solve Previous Year Questions")

    if st.session_state.extracted_questions:
        st.success(f"Found {len(st.session_state.extracted_questions)} questions from your uploaded papers!")

        # filter by type
        q_type_filter = st.selectbox(
            "Filter by question type",
            ["All", "definition/listing", "explanation", "comparison", "numerical/problem", "implementation"]
        )

        filtered_qs = st.session_state.extracted_questions
        if q_type_filter != "All":
            filtered_qs = [q for q in filtered_qs if categorize_question(q) == q_type_filter]

        st.write(f"Showing {len(filtered_qs)} questions")

        for i, question in enumerate(filtered_qs[:30]):  # show max 30
            q_type = categorize_question(question)
            with st.expander(f"Q{i+1}: {question[:80]}... [{q_type}]"):
                st.write(f"**Question:** {question}")
                st.write(f"**Type:** {q_type}")

                if st.button(f"🤖 Get Answer", key=f"ans_{i}"):
                    with st.spinner("Generating model answer..."):
                        search_query = build_exam_query(question)
                        chunks = search_vector_store(
                            search_query,
                            st.session_state.faiss_index,
                            st.session_state.metadata,
                            top_k=3
                        )
                        answer = ask_gemini(
                            f"Provide a detailed model answer for this exam question: {question}",
                            chunks
                        )
                        st.markdown("**Model Answer:**")
                        st.write(answer)
                        st.session_state.question_history.append(question)
    else:
        st.info("Upload a previous year question paper (name it with 'question' or 'exam' or 'paper' in the filename) to auto-extract questions.")

        # manual question entry
        st.subheader("Or type a question manually:")
        manual_q = st.text_area("Enter your exam question here", height=100)
        if st.button("🤖 Solve This Question") and manual_q:
            with st.spinner("Working on it..."):
                chunks = search_vector_store(
                    manual_q,
                    st.session_state.faiss_index,
                    st.session_state.metadata,
                    top_k=3
                )
                answer = ask_gemini(
                    f"Provide a detailed model answer for: {manual_q}",
                    chunks
                )
                st.markdown("**Model Answer:**")
                st.write(answer)


# ---- TAB 3: Progress Tracker ----
with tab3:
    st.subheader("📊 Your Study Progress")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions Asked", len(st.session_state.question_history))
        st.metric("Documents Loaded", len(st.session_state.documents))
    with col2:
        # count by content type
        type_counts = {}
        for doc in st.session_state.documents:
            t = doc["content_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, count in type_counts.items():
            st.metric(t.replace("_", " ").title(), count)

    st.divider()

    if len(st.session_state.question_history) >= 3:
        st.subheader("🔍 Weak Area Analysis")
        if st.button("Analyze My Weak Areas"):
            with st.spinner("Analyzing your question patterns..."):
                analysis = identify_weak_areas(st.session_state.question_history)
                st.write(analysis)
    else:
        st.info("Ask at least 3 questions to get a weak area analysis!")

    if st.session_state.question_history:
        st.subheader("📜 Recent Questions")
        for q in reversed(st.session_state.question_history[-10:]):
            st.write(f"• {q}")


# ---- TAB 4: Study Plan ----
with tab4:
    st.subheader("🗺️ Generate a Custom Study Plan")

    topics_input = st.text_area(
        "Enter the topics you need to study (one per line)",
        placeholder="Database Normalization\nSQL Joins\nTransaction Management\nIndexing",
        height=150
    )
    days = st.slider("How many days do you have to study?", 1, 30, 7)

    if st.button("📅 Generate Study Plan", type="primary"):
        topics = [t.strip() for t in topics_input.split("\n") if t.strip()]
        if not topics:
            st.warning("Please enter at least one topic!")
        else:
            with st.spinner("Creating your personalized study plan..."):
                plan = generate_study_plan(topics, days)
                st.markdown("### Your Study Plan")
                st.write(plan)

                # download button
                st.download_button(
                    "📥 Download Study Plan",
                    plan,
                    file_name="my_study_plan.txt",
                    mime="text/plain"
                )