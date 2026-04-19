import os
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found in .env file!")
        return None
    return Groq(api_key=api_key)

def ask_gemini(prompt, context_chunks):
    client = get_client()
    if not client:
        return "Error: Could not connect to Groq API."
    context = ""
    for i, chunk in enumerate(context_chunks):
        context += f"\n[Source {i+1}: {chunk['filename']} - {chunk['content_type']}]\n"
        context += chunk["text"] + "\n"
    full_prompt = f"""You are an expert academic assistant helping a student understand their study materials.

CONTEXT FROM STUDY MATERIALS:
{context}

STUDENT'S QUESTION:
{prompt}

Answer clearly using the context above. Mention the source document."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting response: {str(e)}"

def generate_study_plan(topics, available_days):
    client = get_client()
    if not client:
        return "Error connecting to Groq."
    prompt = f"""Create a detailed {available_days}-day study plan for: {', '.join(topics)}.
For each day include: topic, key concepts, practice questions, estimated time."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def identify_weak_areas(question_history):
    client = get_client()
    if not client:
        return "Error connecting to Groq."
    history_text = "\n".join(question_history[-20:])
    prompt = f"""Based on these questions a student asked:
{history_text}
Identify weak topics and recommend what to study next."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"