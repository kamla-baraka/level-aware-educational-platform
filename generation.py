
import os
import streamlit as st
from groq import Groq

MODEL_NAME = "qwen/qwen3.8-27b"

LEVEL_INSTRUCTIONS = {
    "Basic": (
        "استخدم لغة عربية بسيطة وجملًا قصيرة. "
        "اشرح المفاهيم خطوة بخطوة، مع أمثلة واضحة."
    ),
    "Intermediate": (
        "استخدم شرحًا متوسط التفصيل، واربط بين المفاهيم، "
        "وأضف أسئلة تطبيقية مناسبة."
    ),
    "Advanced": (
        "استخدم شرحًا أعمق وأسئلة تتطلب المقارنة والتحليل "
        "والاستنتاج، دون تجاوز موضوعات المنهاج."
    ),
}


def generate_educational_content(level, retrieved_chunks):
    if level not in LEVEL_INSTRUCTIONS:
        raise ValueError("Invalid student level.")

    if not retrieved_chunks:
        raise ValueError("No curriculum content provided.")

    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    client = Groq(api_key=api_key)

    context = "\n\n".join(
        f"[{chunk['node_id']}]\n{chunk['text']}"
        for chunk in retrieved_chunks
    )

    system_prompt = """
أنت مساعد تعليمي متخصص في مادة العلوم للصف الثامن
وفق المنهاج الفلسطيني.

مهمتك إنشاء حزمة تعليمية عربية من محتوى الدرس المرفق.

القواعد:
1. اعتمد فقط على النصوص المرجعية المقدمة.
2. لا تضف معلومات علمية أو موضوعات من خارج الدرس.
3. يجب تغطية جميع الموضوعات الموجودة في السياق.
4. غيّر مستوى الشرح والأنشطة حسب مستوى الطالب،
   دون حذف الموضوعات الأساسية.
5. لا تختلق معلومات إذا كان السياق غير كافٍ.
6. عند شرح الدور النهائي في الانقسام المتساوي،
   اعتمد وصف الرسم العلمي: تصل الكروموسومات
   إلى قطبي الخلية ويبدأ تكوّن الغلاف النووي.
7. استخدم عناوين واضحة ولغة عربية سليمة.
8. لا تعرض معلومات غير موجودة في السياق على أنها
   مقتبسة من المنهاج.

أنشئ الحزمة بالأقسام التالية:
- عنوان الدرس
- الأهداف التعليمية
- الشرح التعليمي
- المفردات والمفاهيم الأساسية
- أمثلة توضيحية
- تمارين تدريبية
- أسئلة تقييم ذاتي
- ملخص الدرس

أضف معرفات المقاطع المرجعية مثل [C01]
عند عرض المعلومات العلمية.
"""

    user_prompt = f"""
مستوى الطالب: {level}

تعليمات تكييف المحتوى:
{LEVEL_INSTRUCTIONS[level]}

المحتوى المرجعي من المنهاج الفلسطيني:
{context}

أنشئ الآن حزمة تعليمية متكاملة مناسبة لمستوى الطالب.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_completion_tokens=4000,
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise RuntimeError(
            "Qwen returned an empty educational response."
        )

    return content
