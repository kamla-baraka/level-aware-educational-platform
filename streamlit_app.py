
import streamlit as st

st.set_page_config(
    page_title="Level-Aware Educational Platform",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Level-Aware Educational Platform")

st.write(
    "A knowledge-grounded educational platform "
    "for Palestinian Grade 8 Science."
)

st.subheader("Welcome to the Learning Platform")

student_name = st.text_input("Student name")

topic = st.selectbox(
    "Select a learning topic",
    ["Cell Division", "Meiosis"]
)

level = st.selectbox(
    "Learning level (temporary preview)",
    ["Basic", "Intermediate", "Advanced"]
)

if st.button("Generate Learning Content"):
    st.info(
        f"Welcome {student_name or 'Student'}! "
        f"Selected topic: {topic}. "
        f"Level: {level}."
    )
    st.warning(
        "Educational content generation "
        "will be connected to the RAG system later."
    )
