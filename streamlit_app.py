
import streamlit as st

from assessment import QUESTIONS, calculate_score, determine_level
from retrieval import load_knowledge_base
from generation import generate_educational_content
from quality_check import validate_educational_content
from post_assessment import (
    generate_posttest,
    calculate_posttest_score,
    determine_progression,
)

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

if "posttest_questions" not in st.session_state:
    st.session_state.posttest_questions = None

if "posttest_result" not in st.session_state:
    st.session_state.posttest_result = None

if "content_quality_issues" not in st.session_state:
    st.session_state.content_quality_issues = []


# Reset all student-specific data
def reset_student_data():
    st.session_state.assessment_result = None
    st.session_state.generated_content = None
    st.session_state.generated_level = None
    st.session_state.posttest_questions = None
    st.session_state.posttest_result = None
    st.session_state.content_quality_issues = []


# Reset when student changes
if st.session_state.assessment_student != student_name:
    reset_student_data()
    st.session_state.assessment_student = student_name


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
            "نتيجتك في الاختبار القبلي",
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

    # Clear old content if the level changes
    if st.session_state.generated_level != level:
        st.session_state.generated_content = None
        st.session_state.posttest_questions = None
        st.session_state.posttest_result = None

    # Generate educational content
    if st.button(
        "إنشاء المحتوى التعليمي المناسب لمستواي",
        type="primary",
    ):

        # Invalidate the old test before generating a new lesson
        st.session_state.generated_content = None
        st.session_state.generated_level = None
        st.session_state.posttest_questions = None
        st.session_state.posttest_result = None
        st.session_state.content_quality_issues = []

        with st.spinner(
            "جارٍ قراءة محتوى المنهاج "
            "وتوليد الحزمة التعليمية..."
        ):

            try:

                curriculum_chunks = load_knowledge_base()

                educational_content = generate_educational_content(
                    level=level,
                    retrieved_chunks=curriculum_chunks,
                )

                st.session_state.generated_content = (
                    educational_content
                )

                st.session_state.generated_level = level

                st.rerun()

            except Exception as e:

                st.session_state.generated_content = None

                st.error(
                    "حدث خطأ أثناء توليد المحتوى التعليمي."
                )

                st.exception(e)

    # Display generated lesson
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

        # Revalidate saved content without calling Groq
        is_valid, quality_issues = validate_educational_content(
            st.session_state.generated_content
        )

        st.session_state.content_quality_issues = quality_issues

        if quality_issues:

            st.warning(
                "⚠️ رصد الفحص الآلي ملاحظات على الحزمة التعليمية. "
                "تحتاج الحزمة إلى مراجعة علمية وتربوية."
            )

            with st.expander("🔍 عرض تقرير فحص الجودة"):
                for issue in quality_issues:
                    st.write(f"• {issue}")

        else:

            st.success(
                "✅ اجتازت الحزمة فحوصات الجودة الآلية الأولية. "
                "ولا يغني ذلك عن المراجعة العلمية والتربوية."
            )

        st.divider()

        st.download_button(
            label="📥 تحميل المحتوى التعليمي",
            data=st.session_state.generated_content,
            file_name=f"cell_division_{level.lower()}.md",
            mime="text/markdown",
        )

        # Post-assessment
        st.divider()
        st.header("🧠 الاختبار البعدي")

        st.info(
            "بعد دراسة المحتوى التعليمي، أجب عن 10 أسئلة "
            "اختيار من متعدد لقياس مدى إتقانك للدرس."
        )

        # Generate post-test once per saved lesson
        if st.session_state.posttest_questions is None:

            if st.button(
                "بدء الاختبار البعدي",
                type="primary",
            ):

                with st.spinner(
                    "جارٍ إعداد الاختبار من المحتوى الذي درسته..."
                ):

                    try:

                        questions = generate_posttest(
                            educational_content=(
                                st.session_state.generated_content
                            ),
                            level=level,
                        )

                        st.session_state.posttest_questions = questions
                        st.session_state.posttest_result = None

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "حدث خطأ أثناء إنشاء الاختبار البعدي."
                        )

                        st.exception(e)

        # Show questions before submission
        elif st.session_state.posttest_result is None:

            st.subheader("أسئلة الاختبار البعدي")

            post_answers = {}

            with st.form("post_assessment_form"):

                for index, question in enumerate(
                    st.session_state.posttest_questions,
                    start=1,
                ):

                    st.markdown(
                        f"**السؤال {index}: {question['question']}**"
                    )

                    selected = st.radio(
                        "اختر إجابة واحدة:",
                        options=question["options"],
                        index=None,
                        key=f"post_answer_{question['id']}",
                    )

                    post_answers[question["id"]] = selected

                    st.divider()

                post_submitted = st.form_submit_button(
                    "إنهاء الاختبار البعدي",
                    type="primary",
                )

            if post_submitted:

                if not all(
                    answer is not None
                    for answer in post_answers.values()
                ):

                    st.error(
                        "يرجى الإجابة عن جميع الأسئلة قبل الإنهاء."
                    )

                else:

                    post_score = calculate_posttest_score(
                        post_answers,
                        st.session_state.posttest_questions,
                    )

                    progression = determine_progression(
                        level,
                        post_score,
                    )

                    st.session_state.posttest_result = {
                        "score": post_score,
                        "progression": progression,
                    }

                    st.rerun()

        # Display post-test results
        else:

            result_post = st.session_state.posttest_result

            post_score = result_post["score"]
            progression = result_post["progression"]

            st.success("تم إنهاء الاختبار البعدي بنجاح!")

            st.metric(
                "نتيجة الاختبار البعدي",
                f"{post_score} / 10",
            )

            st.subheader("📊 تقييم مستوى الطالب")

            if progression["decision"] == "Promote":

                st.success(
                    "أحسنت! حققت معيار الإتقان التجريبي."
                )

                st.write(
                    f"**مستواك الحالي:** {level}"
                )

                st.write(
                    "**المستوى التالي:** "
                    f"{progression['next_level']}"
                )

                st.info(
                    "أصبحت مؤهلًا للانتقال إلى المستوى التالي "
                    "وفق معيار الإتقان التجريبي."
                )

            elif progression["decision"] == "Stay":

                st.info(
                    "ستبقى في مستواك الحالي لمراجعة الدرس "
                    "وتعزيز فهم المفاهيم."
                )

                st.write(
                    f"**مستواك الحالي:** {level}"
                )

            else:

                st.success(
                    "أحسنت! حققت معيار الإتقان التجريبي "
                    "في المستوى المتقدم."
                )

                st.write(
                    "**المستوى الذي أتقنته:** Advanced"
                )

            st.caption(
                "معيار الإتقان المستخدم حاليًا هو 8/10. "
                "هذا معيار تجريبي يحتاج إلى تحقق تربوي."
            )
