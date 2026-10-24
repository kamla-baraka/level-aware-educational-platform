
import streamlit as st

from assessment import QUESTIONS, calculate_score, determine_level


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

st.subheader("مرحبًا بك في منصة التعلم")

student_name = st.text_input("اسم الطالب")

st.write("**المادة:** العلوم والحياة – الصف الثامن")
st.write("**الدرس:** انقسام الخلايا")

st.divider()

st.header("📝 الاختبار القبلي")

st.info(
    "أجب عن الأسئلة العشرة التالية لتحديد مستواك التعليمي "
    "قبل البدء بتعلم الدرس."
)

# Store the assessment result during the session.
if "assessment_result" not in st.session_state:
    st.session_state.assessment_result = None

if "assessment_student" not in st.session_state:
    st.session_state.assessment_student = None

# Reset the result if the student name changes.
if st.session_state.assessment_student != student_name:
    st.session_state.assessment_result = None
    st.session_state.assessment_student = student_name

if st.session_state.assessment_result is None:

    answers = {}

    with st.form("pre_assessment_form"):

        for index, question in enumerate(QUESTIONS, start=1):
            st.markdown(f"**السؤال {index}: {question['question']}**")

            selected_answer = st.radio(
                "اختر إجابة واحدة:",
                options=question["options"],
                index=None,
                key=f"answer_{question['id']}"
            )

            answers[question["id"]] = selected_answer

            st.divider()

        submitted = st.form_submit_button(
            "إنهاء الاختبار وتحديد المستوى",
            type="primary"
        )

    if submitted:
        if not all(answer is not None for answer in answers.values()):
            st.error("يرجى الإجابة عن جميع الأسئلة قبل إنهاء الاختبار.")

        else:
            score = calculate_score(answers)
            level = determine_level(score)

            st.session_state.assessment_result = {
                "score": score,
                "level": level
            }

            st.rerun()

else:
    result = st.session_state.assessment_result
    score = result["score"]
    level = result["level"]

    st.success("تم إنهاء الاختبار القبلي بنجاح!")

    st.subheader(
        f"مرحبًا {student_name.strip() or 'عزيزي الطالب'}"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("نتيجتك", f"{score} / {len(QUESTIONS)}")

    with col2:
        st.metric("مستواك التعليمي المبدئي", level)

    st.info(
        "تم تحديد مستواك بناءً على إجابات الاختبار القبلي. "
        "هذا التصنيف تجريبي ويحتاج إلى تحقق تربوي."
    )

    st.divider()

    st.header("📚 المحتوى التعليمي")

    if st.button("إنشاء المحتوى التعليمي المناسب لمستواي"):
        st.info(
            f"الطالب: {student_name.strip() or 'Student'} | "
            f"الدرس: انقسام الخلايا | "
            f"المستوى: {level}"
        )

        st.warning(
            "سيتم ربط توليد المحتوى التعليمي "
            "بنظام RAG في مرحلة التطوير القادمة."
        )
