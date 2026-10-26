import streamlit as st

from assessment import QUESTIONS, calculate_score, determine_level
from retrieval import load_knowledge_base
from generation import generate_educational_content

st.set_page_config(
    page_title="Level-Aware Educational Platform",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Set the main content and its blocks to RTL. */
    [data-testid="stMainBlockContainer"],
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
    [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* Streamlit Markdown, headings, captions, labels and questions. */
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] p,
    [data-testid="stMain"] label {
        direction: rtl !important;
        text-align: right !important;
    }

    /* Form, text field and multiple-choice answers. */
    [data-testid="stForm"],
    [data-testid="stTextInput"],
    [data-testid="stRadio"],
    [data-testid="stRadio"] [role="radiogroup"] {
        direction: rtl !important;
        text-align: right !important;
    }

    [data-testid="stTextInput"] input {
        direction: rtl !important;
        text-align: right !important;
    }

    [data-testid="stRadio"] [role="radiogroup"] label {
        direction: rtl !important;
        text-align: right !important;
        justify-content: flex-start;
    }

    /* Buttons and metrics. */
    [data-testid="stButton"],
    [data-testid="stFormSubmitButton"],
    [data-testid="stMetric"] {
        direction: rtl !important;
        text-align: right !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📚 منصة التعلم التكيفي حسب مستوى الطالب")
st.write("منصة تعليمية مستندة إلى المعرفة لمنهاج العلوم والحياة الفلسطيني للصف الثامن.")

st.subheader("مرحبًا بك في منصة التعلم")
student_name = st.text_input("اسم الطالب")
st.write("**المادة:** العلوم والحياة – الصف الثامن")
st.write("**الدرس:** انقسام الخلايا")
st.divider()

st.header("📝 الاختبار القبلي")
st.info("أجب عن الأسئلة التالية لتحديد مستواك التعليمي قبل البدء بتعلم الدرس.")

if "assessment_result" not in st.session_state:
    st.session_state.assessment_result = None
if "assessment_student" not in st.session_state:
    st.session_state.assessment_student = None

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
                key=f"answer_{question['id']}",
            )
            answers[question["id"]] = selected_answer
            st.divider()

        submitted = st.form_submit_button(
            "إنهاء الاختبار وتحديد المستوى",
            type="primary",
        )

    if submitted:
        if not all(answer is not None for answer in answers.values()):
            st.error("يرجى الإجابة عن جميع الأسئلة قبل إنهاء الاختبار.")
        else:
            score = calculate_score(answers)
            level = determine_level(score)
            st.session_state.assessment_result = {
                "score": score,
                "level": level,
            }
            st.rerun()
else:
    result = st.session_state.assessment_result
    score = result["score"]
    level = result["level"]

    st.success("تم إنهاء الاختبار القبلي بنجاح!")
    st.subheader(f"مرحبًا {student_name.strip() or 'عزيزي الطالب'}")

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

   
    # Keep generated content available across Streamlit reruns.
    if "generated_content" not in st.session_state:
        st.session_state.generated_content = None

    if "generated_level" not in st.session_state:
        st.session_state.generated_level = None

    if st.session_state.generated_level != level:
        st.session_state.generated_content = None

    if st.button(
        "إنشاء المحتوى التعليمي المناسب لمستواي",
        type="primary",
    ):
        with st.spinner(
            "جارٍ استرجاع محتوى المنهاج وتوليد الحزمة التعليمية..."
        ):
            try:
                # Use all curriculum chunks to cover the full lesson.
                curriculum_chunks = load_knowledge_base()

                educational_content = generate_educational_content(
                    level=level,
                    retrieved_chunks=curriculum_chunks,
                )

                st.session_state.generated_content = (
                    educational_content
                )
                st.session_state.generated_level = level

            except Exception:
                st.session_state.generated_content = None
                st.error(
                    "تعذر إنشاء المحتوى التعليمي حاليًا. "
                    "يرجى المحاولة لاحقًا."
                )

    if st.session_state.generated_content:
        st.success("تم إنشاء المحتوى التعليمي بنجاح!")

        st.markdown(
            st.session_state.generated_content
        )

        st.download_button(
            label="تحميل المحتوى التعليمي",
            data=st.session_state.generated_content,
            file_name=f"cell_division_{level.lower()}.md",
            mime="text/markdown",
        )
