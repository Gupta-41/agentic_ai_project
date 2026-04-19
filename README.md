# 📚 StudyMate AI — Exam Preparation Assistant

An AI-powered academic assistant that helps students study smarter using their own materials.

## Setup

1. Clone the repo
   git clone <your-repo-url>
   cd subject-guide-ai

2. Install dependencies
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm

3. Add your API key
   Create a .env file and add:
   GOOGLE_API_KEY=your_key_here

4. Run the app
   streamlit run app.py

## Features
- Upload PDFs, DOCX, PPTX files
- Ask questions about any topic
- Auto-extract and solve previous year questions
- Weak area identification
- Custom study plan generator

## Tech Stack
- Streamlit, LangChain, FAISS, Google Gemini, SentenceTransformers