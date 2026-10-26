
import os
import re
import time

import streamlit as st
from groq import Groq
from retrieval import retrieve_chunks

MODEL_NAME = "qwen/qwen3.8-27b"

LEVEL_INSTRUCTIONS = {
    "Basic": (
        "لغة عربية بسيطة، جمل قصيرة، شرح خطوة بخطوة، "
        "وأسئلة مباشرة مناسبة لطالب يحتاج إلى دعم."
    ),
    "Intermediate": (
        "شرح متوسط التفصيل، ربط بين المفاهيم، "
        "وأسئلة فهم وتطبيق ومقارنة."
    ),
    "Advanced": (
        "شرح أعمق للمفاهيم نفسها، مع أسئلة تحليل "
        "واستنتاج، دون تجاوز حدود المنهاج."
    ),
}

PARTS = [
    {
        "title": "الأهداف والكروموسومات",
        "queries": [
            "عدد الكروموسومات في الكائنات الحية",
            "تضاعف DNA وتركيب الكروموسوم والسنترومير",
        ],
        "sections": (
            "## الأهداف التعليمية\n"
            "## الكروموسومات والمادة الوراثية\n"
            "## الطور البيني وتركيب الكروموسوم"
        ),
        "ids": ["C01", "C02", "C03", "C05"],
    },
    {
        "title": "الانقسام المتساوي",
        "queries": [
            "الخلايا الجسمية والانقسام المتساوي",
            "مراحل الانقسام المتساوي الأربع",
            "انقسام السيتوبلازم في النبات والحيوان",
        ],
        "sections": (
            "## الانقسام المتساوي\n"
            "## مراحل الانقسام المتساوي\n"
            "## الفرق بين الخلية الحيوانية والنباتية"
        ),
        "ids": ["C04", "C05", "C06", "C07", "C08"],
    },
    {
        "title": "الانقسام المنصف ومتلازمة داون",
        "queries": [
            "الانقسام المنصف وعدد الكروموسومات",
            "قصة فلسطينية عن متلازمة داون",
            "متلازمة داون والكروموسوم 21",
        ],
        "sections": (
            "## الانقسام المنصف\n"
            "## متلازمة داون والقصة الواردة في المنهاج"
        ),
        "ids": ["C09", "C10", "C11"],
    },
    {
        "title": "الأنشطة والمراجعة",
        "queries": [
            "مقارنة الانقسام المتساوي والمنصف",
            "مراحل انقسام الخلايا ومتلازمة داون",
        ],
        "sections": (
            "## المفردات والمفاهيم الأساسية\n"
            "## أمثلة توضيحية\n"
            "## تمارين تدريبية\n"
            "## أسئلة تقييم ذاتي\n"
            "## ملخص الدرس\n"
            "## الإجابات النموذجية"
        ),
        "ids": [
            "C01", "C02", "C03", "C04", "C05",
            "C06", "C07", "C08", "C09", "C10", "C11"
        ],
    },
]


def get_context(part, all_chunks):
    """Retrieve relevant chunks and ensure required topics are present."""
    selected = {}

    for query in part["queries"]:
        for chunk in retrieve_chunks(query, top_k=3):
            selected[chunk["node_id"]] = chunk

    by_id = {
        chunk["node_id"]: chunk
        for chunk in all_chunks
    }

    # Coverage safeguard: include curriculum chunks
    # required by this part even if retrieval misses them.
    for node_id in part["ids"]:
        if node_id in by_id:
            selected[node_id] = by_id[node_id]

    ordered = [
        by_id[node_id]
        for node_id in part["ids"]
        if node_id in selected and node_id in by_id
    ]

    return "\n\n".join(
        f"[{chunk['node_id']}]\n{chunk['text']}"
        for chunk in ordered
    )


def generate_part(client, level, part, context):
    system_prompt = """
أنت مساعد تعليمي لمادة العلوم والحياة للصف الثامن
وفق المنهاج الفلسطيني.

التزم بالقواعد التالية:
- اعتمد فقط على المقاطع المرجعية المقدمة.
- لا تخترع معلومات أو أمثلة غير موجودة في المصدر.
- غط جميع الموضوعات المطلوبة في هذا الجزء.
- استخدم لغة عربية سليمة ومصطلحات علمية دقيقة.
- وثق المعلومات بمعرفات المقاطع مثل [C06].
- لا تختلق معرفات للمراجع.
- الطور البيني مرحلة تحضيرية تسبق الانقسام المتساوي.
- الأدوار الأربعة للانقسام المتساوي هي:
  التمهيدي والاستوائي والانفصالي والنهائي.
- في الدور النهائي تصل الكروموسومات إلى القطبين
  ويبدأ تكوّن الغلاف النووي.
- استخدم مصطلح السنترومير والخلايا الجسمية.
- لا تضف تضاعف العضيات إلا إذا ذكره المصدر.
- لا تعرض إجابات التمارين إلا في قسم الإجابات.
- اكتب الأقسام المطلوبة فقط، دون مقدمة أو خاتمة إضافية.
"""

    user_prompt = f"""
الدرس: انقسام الخلايا
مستوى الطالب: {level}
التكيّف المطلوب: {LEVEL_INSTRUCTIONS[level]}

هذا هو الجزء المطلوب: {part['title']}

اكتب الأقسام التالية بنفس العناوين:
{part['sections']}

اكتب شرحًا واضحًا ومتكاملًا ومختصرًا.
في قسم الأنشطة، أنشئ 4 تمارين و3 أسئلة تقييم ذاتي،
ثم إجاباتها في قسم الإجابات النموذجية.

المصدر:
{context}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_completion_tokens=950,
    )

    choice = response.choices[0]
    content = choice.message.content or ""

    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"Generation was incomplete for: {part['title']}. "
            f"Finish reason: {choice.finish_reason}"
        )

    if not content.strip():
        raise RuntimeError(
            f"Empty response for: {part['title']}"
        )

    # Check required section headings.
    for heading in part["sections"].splitlines():
        heading_text = heading.replace("## ", "").strip()
        if heading_text not in content:
            raise RuntimeError(
                f"Missing section '{heading_text}' "
                f"in part '{part['title']}'"
            )

    return content.strip()


def generate_educational_content(level, retrieved_chunks):
    if level not in LEVEL_INSTRUCTIONS:
        raise ValueError("Invalid student level.")

    if not retrieved_chunks:
        raise ValueError("No curriculum content provided.")

    api_key = (
        st.secrets.get("GROQ_API_KEY")
        or os.getenv("GROQ_API_KEY")
    )

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    client = Groq(api_key=api_key)
    generated_parts = []

    for index, part in enumerate(PARTS):
        context = get_context(part, retrieved_chunks)

        if not context:
            raise RuntimeError(
                f"No curriculum context for: {part['title']}"
            )

        result = generate_part(
            client=client,
            level=level,
            part=part,
            context=context,
        )

        generated_parts.append(result)

        # Space requests to reduce OTPM rate-limit errors.
        if index < len(PARTS) - 1:
            time.sleep(65)

    return (
        "# انقسام الخلايا\n\n"
        + "\n\n".join(generated_parts)
    )
