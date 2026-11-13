
import os
import time

import streamlit as st
from groq import Groq
from retrieval import retrieve_chunks
from quality_check import validate_educational_content


MODEL_NAME = "openai/gpt-oss-20b"

# Keep requests small for free-tier rate limits.
MAX_OUTPUT_TOKENS = 1200
REQUEST_DELAY_SECONDS = 65

# Retrieval configuration.
RETRIEVAL_TOP_K = 3


LEVEL_INSTRUCTIONS = {
    "Basic": (
        "المستوى الأساسي (Basic): "
        "الطالب يحتاج إلى دعم لفهم المفاهيم الأساسية. "
        "استخدم لغة عربية فصحى سهلة، وجملًا قصيرة، "
        "واشرح كل مفهوم خطوة بخطوة. "
        "عرّف المصطلحات العلمية قبل استخدامها، "
        "وقدّم مثالًا بسيطًا ومباشرًا لكل مفهوم رئيسي. "
        "ركّز على التعرّف والتذكر والفهم المباشر. "
        "اجعل الأسئلة قصيرة وواضحة، مثل: عرّف، اذكر، اختر. "
        "تجنّب الأسئلة المركبة والتفاصيل غير الضرورية. "
        "التزم بالمعلومات الواردة في المنهاج الفلسطيني."
    ),

    "Intermediate": (
        "المستوى المتوسط (Intermediate): "
        "الطالب يمتلك معرفة أولية بالمفاهيم العلمية. "
        "استخدم شرحًا متوسط التفصيل، "
        "ووضّح العلاقات بين المفاهيم والمراحل. "
        "استخدم المقارنة والأمثلة التطبيقية "
        "لمساعدة الطالب على تفسير العمليات. "
        "ركّز على الفهم والتطبيق والمقارنة. "
        "اجعل بعض الأسئلة تتطلب تفسير السبب، "
        "أو المقارنة بين عمليتين، أو تطبيق مفهوم "
        "على حالة جديدة ضمن حدود المنهاج. "
        "لا تكتفِ بأسئلة الحفظ والتذكر. "
        "التزم بالمعلومات الواردة في المنهاج الفلسطيني."
    ),

    "Advanced": (
        "المستوى المتقدم (Advanced): "
        "الطالب يمتلك فهمًا جيدًا للمفاهيم الأساسية. "
        "قدّم شرحًا أكثر ترابطًا وعمقًا للمفاهيم نفسها، "
        "مع إبراز العلاقات السببية بين العمليات. "
        "ركّز على التحليل والاستنتاج والتفسير العلمي. "
        "استخدم أسئلة تتطلب التنبؤ بالنتائج، "
        "وتحليل الحالات، وتبرير الإجابات بالأدلة. "
        "اجعل التحدي في مستوى التفكير وليس "
        "في إضافة معلومات خارج المنهاج. "
        "تجنّب تكرار الأسئلة المباشرة والبسيطة. "
        "التزم بالمعلومات الواردة في المنهاج الفلسطيني."
    ),
}


PARTS = [
    {
        "title": "الأهداف والكروموسومات",
        "queries": [
            "عدد الكروموسومات في الكائنات الحية",
            "تضاعف DNA وتركيب الكروموسوم",
        ],
        "ids": ["C01", "C02", "C03", "C05"],
        "headings": [
            "الأهداف التعليمية",
            "الكروموسومات والمادة الوراثية",
            "الطور البيني وتركيب الكروموسوم",
        ],
        "instruction": (
            "اكتب 3 أهداف تعليمية، ثم شرحًا مختصرًا "
            "للمادة الوراثية والكروموسومات والطور البيني."
        ),
    },
    {
        "title": "الانقسام المتساوي",
        "queries": [
            "مراحل الانقسام المتساوي",
            "انقسام السيتوبلازم في النبات والحيوان",
        ],
        "ids": ["C04", "C05", "C06", "C07", "C08"],
        "headings": [
            "الانقسام المتساوي",
            "مراحل الانقسام المتساوي",
            "الفرق بين الخلية الحيوانية والنباتية",
        ],
        "instruction": (
            "اشرح أهمية الانقسام المتساوي ومراحله الأربع "
            "والفرق بين انقسام السيتوبلازم في الخلية "
            "الحيوانية والخلية النباتية."
        ),
    },
    {
        "title": "الانقسام المنصف ومتلازمة داون",
        "queries": [
            "الانقسام المنصف وعدد الكروموسومات",
            "متلازمة داون والكروموسوم 21",
        ],
        "ids": ["C09", "C10", "C11"],
        "headings": [
            "الانقسام المنصف",
            "متلازمة داون والقصة الواردة في المنهاج",
        ],
        "instruction": (
            "اشرح الانقسام المنصف ونتيجته، ثم متلازمة "
            "داون والقصة الواردة في المنهاج إن ظهرت "
            "في المقاطع المسترجعة. "
            "لا تخترع تفاصيل غير موجودة في المراجع."
        ),
    },
    {
        "title": "المفاهيم والأمثلة",
        "queries": [
            "مقارنة الانقسام المتساوي والمنصف",
            "الكروموسومات ومراحل انقسام الخلية",
        ],
        "ids": [
            "C01", "C02", "C03", "C04", "C05",
            "C06", "C08", "C09", "C11"
        ],
        "headings": [
            "المفردات والمفاهيم الأساسية",
            "أمثلة توضيحية",
            "ملخص الدرس",
        ],
        "instruction": (
            "اكتب 4 مفردات أساسية مع تعريفات قصيرة، "
            "ومثالًا واحدًا من المصدر، "
            "ثم ملخصًا من 4 نقاط قصيرة. "
            "لا تتجاوز 180 كلمة في هذا الجزء."
        ),
    },
    {
        "title": "التمارين والتقييم",
        "queries": [
            "مراحل الانقسام المتساوي والمنصف",
            "عدد الكروموسومات ومتلازمة داون",
        ],
        "ids": [
            "C01", "C02", "C03", "C04", "C05",
            "C06", "C08", "C09", "C10", "C11"
        ],
        "headings": [
            "تمارين تدريبية",
            "أسئلة تقييم ذاتي",
            "الإجابات النموذجية",
        ],
        "instruction": (
            "اكتب 4 تمارين مرقمة ت1 إلى ت4، "
            "و3 أسئلة تقييم مرقمة س1 إلى س3. "
            "ثم قدم إجابات الأسئلة السبعة في قسم "
            "الإجابات النموذجية فقط. "
            "اجعل الأسئلة مناسبة لمستوى الطالب."
        ),
    },
]


def get_context(part, all_chunks):
    """
    Retrieve curriculum context dynamically using RAG.

    Primary chunks are selected by the retrieval system.
    Optional dependencies are added from chunk metadata.
    """

    by_id = {
        chunk["node_id"]: chunk
        for chunk in all_chunks
    }

    selected = {}

    # Step 1: Retrieve relevant chunks using RAG.
    for query in part["queries"]:
        results = retrieve_chunks(
            query,
            top_k=RETRIEVAL_TOP_K
        )

        for chunk in results:
            node_id = chunk["node_id"]

            if node_id not in by_id:
                raise RuntimeError(
                    f"Retrieved chunk {node_id} "
                    f"is missing from the provided knowledge base."
                )

            selected[node_id] = by_id[node_id]

    if not selected:
        raise RuntimeError(
            f"No retrieved curriculum context for: "
            f"{part['title']}"
        )

    # Step 2: Add required dependencies when declared.
    pending = list(selected.keys())
    visited = set()

    while pending:
        node_id = pending.pop(0)

        if node_id in visited:
            continue

        visited.add(node_id)

        metadata = by_id[node_id].get("metadata", {})
        rules = metadata.get("retrieval_rules", {})

        dependencies = rules.get("dependencies", [])

        for dependency in dependencies:
            if not isinstance(dependency, dict):
                continue

            if not dependency.get("required", False):
                continue

            dependency_id = dependency.get("chunk_id")

            if dependency_id not in by_id:
                raise RuntimeError(
                    f"Missing required dependency "
                    f"{dependency_id} for {node_id}"
                )

            if dependency_id not in selected:
                selected[dependency_id] = by_id[dependency_id]
                pending.append(dependency_id)

    # Step 3: Preserve curriculum order.
    ordered = [
        chunk
        for chunk in all_chunks
        if chunk["node_id"] in selected
    ]

    # Step 4: Construct grounded LLM context.
    context = "\n\n".join(
        f"[{chunk['node_id']}]\n{chunk['text']}"
        for chunk in ordered
    )

    return context


def generate_part(client, level, part, context):
    headings = "\n".join(
        f"## {heading}"
        for heading in part["headings"]
    )

    system_prompt = """
أنت مساعد تعليمي لمادة العلوم والحياة للصف الثامن
وفق المنهاج الفلسطيني.

القواعد:
- استخدم المقاطع المرجعية فقط.
- لا تخترع معلومات أو تفاصيل غير موجودة بالمصدر.
- استخدم لغة عربية سليمة ومصطلحات علمية دقيقة.
- استشهد بمعرفات المقاطع مثل [C06].
- لا تختلق معرفات للمراجع.
- التزم بمستوى الطالب المحدد.
- الطور البيني يسبق الانقسام المتساوي.
- مراحل الانقسام المتساوي:
  التمهيدي، الاستوائي، الانفصالي، النهائي.
- في الدور النهائي تصل الكروموسومات إلى القطبين
  ويبدأ تكوّن الغلاف النووي.
- استخدم مصطلحي السنترومير والخلايا الجسمية.
- لا تضف تضاعف العضيات إلا إذا ورد في المصدر.
- لا تضع إجابات الأسئلة خارج قسم الإجابات النموذجية.
- اكتب الأقسام المطلوبة فقط وباختصار.
"""

    user_prompt = f"""
الدرس: انقسام الخلايا
المستوى: {level}

التكيّف:
{LEVEL_INSTRUCTIONS[level]}

المطلوب:
{part['instruction']}

اكتب هذه العناوين بالترتيب وبدون حذف:
{headings}

اكتب محتوى واضحًا ومختصرًا تحت كل عنوان.
ابدأ مباشرة بأول عنوان.
لا تكتب مقدمة أو خاتمة إضافية.

المراجع:
{context}
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
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort="low",
    )

    choice = response.choices[0]
    content = choice.message.content or ""

    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"Generation was incomplete for: "
            f"{part['title']}. "
            f"Finish reason: {choice.finish_reason}"
        )

    if not content.strip():
        raise RuntimeError(
            f"Empty response for: {part['title']}"
        )

    for heading in part["headings"]:
        required_heading = f"## {heading}"

        if required_heading not in content:
            raise RuntimeError(
                f"Missing section '{heading}' "
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

    # Generate all five parts.
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

        # Wait between requests to respect rate limits.
        if index < len(PARTS) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    # Combine the package only after all parts are generated.
    content = (
        "# انقسام الخلايا\n\n"
        + "\n\n".join(generated_parts)
    )

    # Research mode: record issues without hiding content.
    is_valid, issues = validate_educational_content(content)

    if not is_valid:
        st.session_state["content_quality_issues"] = issues
    else:
        st.session_state["content_quality_issues"] = []

    return content
