
import re


REQUIRED_HEADINGS = [
    "الأهداف التعليمية",
    "الكروموسومات والمادة الوراثية",
    "الطور البيني وتركيب الكروموسوم",
    "الانقسام المتساوي",
    "مراحل الانقسام المتساوي",
    "الفرق بين الخلية الحيوانية والنباتية",
    "الانقسام المنصف",
    "متلازمة داون والقصة الواردة في المنهاج",
    "المفردات والمفاهيم الأساسية",
    "أمثلة توضيحية",
    "ملخص الدرس",
    "تمارين تدريبية",
    "أسئلة تقييم ذاتي",
    "الإجابات النموذجية",
]


def validate_educational_content(content):
    """
    Basic structural and scientific checks.
    Returns (is_valid, issues).
    This is not a complete scientific accuracy assessment.
    """
    issues = []

    if not isinstance(content, str) or not content.strip():
        return False, ["الحزمة التعليمية فارغة."]

    # 1. Check required headings.
    for heading in REQUIRED_HEADINGS:
        pattern = rf"(?m)^##\s+{re.escape(heading)}\s*$"
        if not re.search(pattern, content):
            issues.append(f"القسم المطلوب غير موجود: {heading}")

    # 2. Check exercises and self-assessment questions.
    exercise_ids = set(
        re.findall(r"(?m)^\s*\*{0,2}(ت[1-4])\.", content)
    )
    question_ids = set(
        re.findall(r"(?m)^\s*\*{0,2}(س[1-3])\.", content)
    )

    expected_exercises = {f"ت{i}" for i in range(1, 5)}
    expected_questions = {f"س{i}" for i in range(1, 4)}

    if not expected_exercises.issubset(exercise_ids):
        issues.append("بعض التمارين التدريبية غير موجودة.")

    if not expected_questions.issubset(question_ids):
        issues.append("بعض أسئلة التقييم الذاتي غير موجودة.")

    # 3. Detect known scientific errors.
    scientific_patterns = [
        (
            r"الكروموسومات.{0,55}(منتصف كل خلية|منتصف الخلية الجديدة)",
            "احتمال خطأ في وصف موقع الكروموسومات أثناء الدور النهائي.",
        ),
        (
            r"مريكز\s*\(\s*سنترومير\s*\)",
            "خلط بين المريكز والسنترومير.",
        ),
        (
            r"الصفيحة\s+(الوسطى|الخلوية).{0,65}الانفصالي",
            "احتمال خطأ في توقيت تكوّن الصفيحة الخلوية.",
        ),
        (
            r"تُنقّس|يُنقّس|تنقّس",
            "مصطلح لغوي غير مناسب لوصف انقسام الخلية.",
        ),
    ]

    for pattern, message in scientific_patterns:
        if re.search(pattern, content):
            issues.append(message)

    return len(issues) == 0, issues
