
import re


# Required structure of the educational package
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

EXPECTED_EXERCISES = {f"ت{i}" for i in range(1, 5)}
EXPECTED_QUESTIONS = {f"س{i}" for i in range(1, 4)}

# The reference corpus contains C01 through C11.
VALID_SOURCE_IDS = {f"C{i:02d}" for i in range(1, 12)}


def normalize_text(text):
    """Normalize Arabic text for rule-based matching."""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("ـ", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_section(content, heading):
    """Extract text under a Markdown level-two heading."""
    pattern = (
        rf"(?m)^##\s+{re.escape(heading)}\s*$"
        rf"(.*?)(?=^##\s+|\Z)"
    )
    match = re.search(pattern, content, flags=re.S | re.M)
    return match.group(1).strip() if match else ""


def find_question_ids(section, prefix, maximum):
    """Extract question IDs from Markdown questions/answers."""
    pattern = (
        rf"(?m)^\s*(?:[-*]\s*)?"
        rf"(?:\*\*)?({prefix}[1-{maximum}])"
        rf"(?:\*\*)?\s*[.،:)-]"
    )
    return set(re.findall(pattern, section))


def validate_educational_content(content):
    """
    Research-mode validation.

    Returns:
        (is_valid, issues)

    The package remains visible even if is_valid is False.
    This is a rule-based screening tool, not a complete
    scientific or pedagogical evaluation.
    """
    issues = []

    if not isinstance(content, str) or not content.strip():
        return False, ["الحزمة التعليمية فارغة."]

    normalized = normalize_text(content)

    # 1. Structural completeness
    for heading in REQUIRED_HEADINGS:
        section = get_section(content, heading)

        if not section:
            issues.append(
                f"[البنية] القسم مفقود أو فارغ: {heading}"
            )

    # 2. Exercises and assessment questions
    exercises = get_section(content, "تمارين تدريبية")
    questions = get_section(content, "أسئلة تقييم ذاتي")
    answers = get_section(content, "الإجابات النموذجية")

    found_exercises = find_question_ids(
        exercises, "ت", 4
    )
    found_questions = find_question_ids(
        questions, "س", 3
    )

    for item in sorted(EXPECTED_EXERCISES - found_exercises):
        issues.append(
            f"[الأنشطة] التمرين {item} غير موجود."
        )

    for item in sorted(EXPECTED_QUESTIONS - found_questions):
        issues.append(
            f"[التقييم] السؤال {item} غير موجود."
        )

    # Check that model answers exist for every item.
    found_answers_t = find_question_ids(answers, "ت", 4)
    found_answers_s = find_question_ids(answers, "س", 3)

    for item in sorted(
        EXPECTED_EXERCISES - found_answers_t
    ):
        issues.append(
            f"[الإجابات] لا توجد إجابة مرقمة للتمرين {item}."
        )

    for item in sorted(
        EXPECTED_QUESTIONS - found_answers_s
    ):
        issues.append(
            f"[الإجابات] لا توجد إجابة مرقمة للسؤال {item}."
        )

    # 3. Citation checks
    cited_ids = set(
        re.findall(r"\bC\d{2}\b", content)
    )

    invalid_ids = cited_ids - VALID_SOURCE_IDS

    for source_id in sorted(invalid_ids):
        issues.append(
            f"[المراجع] معرف مصدر غير معروف: {source_id}."
        )

    if not cited_ids:
        issues.append(
            "[المراجع] لم يتم العثور على إحالات "
            "إلى مقاطع المنهاج."
        )

    # Check whether important source topics appear.
    topic_checks = [
        (
            "الكروموسومات",
            r"كروموسوم|كروموسومات",
        ),
        (
            "تضاعف المادة الوراثية",
            r"DNA|المادة الوراثية",
        ),
        (
            "الانقسام المتساوي",
            r"الانقسام المتساوي",
        ),
        (
            "الانقسام المنصف",
            r"الانقسام المنصف",
        ),
        (
            "متلازمة داون",
            r"متلازمة داون",
        ),
    ]

    for topic, pattern in topic_checks:
        if not re.search(pattern, normalized):
            issues.append(
                f"[التغطية] الموضوع غير ظاهر: {topic}."
            )

    # 4. Known scientific error patterns
    scientific_rules = [
        (
            r"الكروموسومات.{0,75}"
            r"(منتصف كل خلية|منتصف الخلية الجديدة)",
            "وصف غير صحيح لموقع الكروموسومات "
            "في الدور النهائي؛ يجب أن تصل إلى القطبين.",
        ),
        (
            r"مريكز\s*\(\s*سنترومير\s*\)",
            "خلط بين المريكز والسنترومير؛ "
            "وهما تركيبان مختلفان.",
        ),
        (
            r"الطور البيني.{0,100}"
            r"(تتكاثر|تضاعف)\s+العضيات",
            "وردت معلومة عن تضاعف العضيات؛ "
            "يجب التحقق من وجودها في المصدر.",
        ),
        (
            r"(الصفيحة الوسطى|الصفيحة الخلوية)"
            r".{0,75}(الطور|الدور)\s+الانفصالي",
            "احتمال خطأ في توقيت تكوّن "
            "الصفيحة الخلوية.",
        ),
        (
            r"تُنقّس|يُنقّس|تنقّس",
            "استخدام مصطلح غير مناسب "
            "لوصف انقسام الخلية.",
        ),
        (
            r"مراحل الانقسام المنصف.{0,100}"
            r"تضاعف\s+(DNA|الكروموسومات)",
            "يجب التحقق من وصف تضاعف المادة "
            "الوراثية قبل الانقسام المنصف.",
        ),
    ]

    for pattern, message in scientific_rules:
        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE | re.DOTALL
        ):
            issues.append(f"[الدقة العلمية] {message}")

    # 5. Scientific terminology
    terminology_rules = [
        (
            r"خليتين ابنتان",
            "الصياغة الأدق: خليتين بنتين.",
        ),
        (
            r"تُقسّم السيتوبلازم",
            "الصياغة الأدق: ينقسم السيتوبلازم.",
        ),
    ]

    for pattern, message in terminology_rules:
        if re.search(pattern, normalized):
            issues.append(f"[اللغة العلمية] {message}")

    # 6. Detect possible lack of source grounding
    # This is a warning, not proof of unsupported content.
    if "العضيات" in normalized:
        issues.append(
            "[الاستناد للمصدر] ورد ذكر العضيات؛ "
            "يجب التحقق من دعم هذه المعلومة "
            "في مقاطع المنهاج."
        )

    # Remove duplicate messages while preserving order.
    issues = list(dict.fromkeys(issues))

    return len(issues) == 0, issues
