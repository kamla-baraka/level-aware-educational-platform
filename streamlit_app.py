
import streamlit as st

from assessment import QUESTIONS, calculate_score, determine_level
from retrieval import load_knowledge_base
from generation import generate_educational_content


st.set_page_config(
    page_title="Level-Aware Educational Platform",
    page_icon="📚",
    layout="wide",
)


# Arabic RTL interface
st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"],
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
    [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"] {
        direction: rtl !important;
        text-align: right !important;
    }

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


# Platform introduction
st.title("📚 منصة التعلم التكيفي حسب مستوى الطالب")

st.write(
    "منصة تعليمية مستندة إلى المعرفة "
    "لمنهاج العلوم والحياة الفلسطيني للصف الثامن."
)

st.subheader("مرحبًا بك في منصة التعلم")

student_name = st.text_input("اسم الطالب")

st.write("**المادة:** العلوم والحياة – الصف الثامن")
st.write("**الدرس:** انقسام الخلايا")

st.divider()


# Initialize session state
if "assessment_result" not in st.session_state:
    st.session_state.assessment_result = None

if "assessment_student" not in st.session_state:
    st.session_state.assessment_student = None

if "generated_content" not in st.session_state:
    st.session_state.generated_content = None

if "generated_level" not in st.session_state:
    st.session_state.generated_level = None


# Reset assessment and content when student changes
if st.session_state.assessment_student != student_name:
    st.session_state.assessment_result = None
    st.session_state.assessment_student = student_name
    st.session_state.generated_content = None
    st.session_state.generated_level = None


# Pre-assessment
st.header("📝 الاختبار القبلي")

st.info(
    "أجب عن الأسئلة التالية لتحديد مستواك التعليمي "
    "قبل البدء بتعلم الدرس."
)


if st.session_state.assessment_result is None:

    answers = {}

    with st.form("pre_assessment_form"):

        for index, question in enumerate(QUESTIONS, start=1):

            st.markdown(
                f"**السؤال {index}: {question['question']}**"
            )

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

        if not all(
            answer is not None
            for answer in answers.values()
        ):
            st.error(
                "يرجى الإجابة عن جميع الأسئلة "
                "قبل إنهاء الاختبار."
            )

        else:

            score = calculate_score(answers)
            level = determine_level(score)

            st.session_state.assessment_result = {
                "score": score,
                "level": level,
            }

            st.rerun()


# Student result and content generation
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
        st.metric(
            "نتيجتك",
            f"{score} / {len(QUESTIONS)}"
        )

    with col2:
        st.metric(
            "مستواك التعليمي المبدئي",
            level
        )

    st.info(
        "تم تحديد مستواك بناءً على إجابات الاختبار القبلي. "
        "هذا التصنيف تجريبي ويحتاج إلى تحقق تربوي."
    )

    st.divider()

    st.header("📚 المحتوى التعليمي")

    st.write(
        "اضغط على الزر التالي لإنشاء حزمة تعليمية "
        "تناسب مستواك، اعتمادًا على محتوى المنهاج الفلسطيني."
    )

    if st.session_state.generated_level != level:
        st.session_state.generated_content = None

    # Dynamic generation on button click
    if st.button(
        "إنشاء المحتوى التعليمي المناسب لمستواي",
        type="primary",
    ):

        with st.spinner(
            "جارٍ قراءة محتوى المنهاج "
            "وتوليد الحزمة التعليمية..."
        ):

            try:

                # Load all curriculum chunks for full-lesson coverage
                curriculum_chunks = load_knowledge_base()

                # Generate content dynamically using Qwen
                educational_content = generate_educational_content(
                    level=level,
                    retrieved_chunks=curriculum_chunks,
                )

                # Save generated content in session state
                st.session_state.generated_content = (
                    educational_content
                )

                st.session_state.generated_level = level

            except Exception as e:

                st.session_state.generated_content = None

                st.error(
                    "حدث خطأ أثناء توليد المحتوى التعليمي."
                )

                # Temporary diagnostic details
                # Remove after resolving the error
                st.exception(e)

    # Display generated educational package
    if st.session_state.generated_content:

        st.success(
            "تم إنشاء المحتوى التعليمي بنجاح!"
        )

        st.subheader(
            "📖 الحزمة التعليمية الخاصة بك"
        )

        st.markdown(
            st.session_state.generated_content
        )

        st.divider()

        st.download_button(
            label="📥 تحميل المحتوى التعليمي",
            data=st.session_state.generated_content,
            file_name=(
                f"cell_division_{level.lower()}.md"
            ),
            mime="text/markdown",
        )
