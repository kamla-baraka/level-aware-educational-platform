
import json
import os
import re

import streamlit as st
from groq import Groq

from generation import MODEL_NAME, LEVEL_INSTRUCTIONS


POST_TEST_SIZE = 10
MASTERY_THRESHOLD = 8

LEVELS = ("Basic", "Intermediate", "Advanced")


def _extract_json(text):
    """Extract a JSON object from the model response."""
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)

        if not match:
            raise ValueError("No JSON object in response.")

        return json.loads(match.group(0))


def validate_posttest(questions):
    """Check question structure and answer consistency."""
    if not isinstance(questions, list):
        raise ValueError("Questions must be a list.")

    if len(questions) != POST_TEST_SIZE:
        raise ValueError("Post-test must contain 10 questions.")

    seen_questions = set()

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError("Invalid question format.")

        text = question.get("question")
        options = question.get("options")
        answer = question.get("answer")

        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Question {index} has no text.")

        normalized = " ".join(text.split())

        if normalized in seen_questions:
            raise ValueError("Duplicate question detected.")

        seen_questions.add(normalized)

        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(
                f"Question {index} must have 4 options."
            )

        if not all(
            isinstance(option, str) and option.strip()
            for option in options
        ):
            raise ValueError("Invalid answer option.")

        if len(set(options)) != 4:
            raise ValueError("Duplicate answer options.")

        if not isinstance(answer, str) or answer not in options:
            raise ValueError(
                f"Invalid correct answer in question {index}."
            )

    return True


def generate_posttest(educational_content, level):
    """Generate 10 MCQs from the student's actual lesson."""

    if level not in LEVELS:
        raise ValueError("Invalid student level.")

    if not isinstance(educational_content, str):
        raise ValueError("Invalid educational content.")

    if not educational_content.strip():
        raise ValueError("Educational content is empty.")

    api_key = (
        st.secrets.get("GROQ_API_KEY")
        or os.getenv("GROQ_API_KEY")
    )

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    client = Groq(api_key=api_key)

    system_prompt = """
أنت متخصص في إعداد اختبارات العلوم للصف الثامن
وفق المنهاج الفلسطيني.

أنشئ اختبارًا بعديًا من 10 أسئلة اختيار من متعدد.

القواعد:
- استخدم المحتوى التعليمي المرفق فقط.
- اجعل الأسئلة مناسبة لمستوى الطالب.
- غطِّ المفاهيم الأساسية المتنوعة في الدرس.
- لا تنسخ أسئلة التمارين أو التقييم الذاتي حرفيًا.
- لا تطرح سؤالًا عن معلومة غير موجودة في الشرح.
- تجنب العبارات العلمية المتناقضة أو غير الواضحة.
- لكل سؤال أربعة خيارات مختلفة وإجابة صحيحة واحدة.
- لا تكرر الأسئلة.
- لا تضع الإجابة الصحيحة دائمًا في الموضع نفسه.
- أرجع JSON صالحًا فقط، دون Markdown أو شرح.

الشكل المطلوب:
{
  "questions": [
    {
      "question": "نص السؤال",
      "options": [
        "الخيار الأول",
        "الخيار الثاني",
        "الخيار الثالث",
        "الخيار الرابع"
      ],
      "answer": "نص الخيار الصحيح"
    }
  ]
}
"""

    user_prompt = f"""
المستوى: {level}

تعليمات التكيّف:
{LEVEL_INSTRUCTIONS[level]}

أنشئ اختبارًا بعديًا من 10 أسئلة من الشرح التالي:

{educational_content}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
        max_completion_tokens=3500,
        reasoning_effort="low",
    )

    choice = response.choices[0]

    if choice.finish_reason != "stop":
        raise RuntimeError("Post-test generation was incomplete.")

    content = choice.message.content or ""

    data = _extract_json(content)
    questions = data.get("questions")

    validate_posttest(questions)

    for index, question in enumerate(questions, start=1):
        question["id"] = f"POST_Q{index:02d}"

    return questions


def calculate_posttest_score(answers, questions):
    """Calculate score using the saved post-test answer key."""
    validate_posttest(questions)

    return sum(
        answers.get(question["id"]) == question["answer"]
        for question in questions
    )


def determine_progression(level, score):
    """Apply the provisional mastery threshold."""
    if level not in LEVELS:
        raise ValueError("Invalid student level.")

    if not isinstance(score, int) or not 0 <= score <= 10:
        raise ValueError("Score must be between 0 and 10.")

    if score < MASTERY_THRESHOLD:
        return {
            "decision": "Stay",
            "next_level": level,
            "mastered": False,
        }

    if level == "Advanced":
        return {
            "decision": "Mastered",
            "next_level": "Advanced",
            "mastered": True,
        }

    next_level = LEVELS[LEVELS.index(level) + 1]

    return {
        "decision": "Promote",
        "next_level": next_level,
        "mastered": True,
    }
