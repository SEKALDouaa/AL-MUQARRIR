import google.generativeai as genai
from decouple import config

genai.configure(api_key=config("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

def generate_deroulement(texte_brut):
    prompt = f"""
    أريد منك استخراج وتحرير قسم "سير الجلسة" (Déroulement de la séance) من محضر رسمي لجلسة برلمانية مغربية، وذلك انطلاقاً من النص التالي الذي يتضمن تفريغاً حرفياً للمداخلات.

    ينبغي أن يكون هذا القسم مكتوباً باللغة العربية الفصحى، بأسلوب تقريري رسمي ومحايد كما هو معتمد في محاضر البرلمان المغربي، وأن يتضمن:
    - تسلسل المداخلات كما وقعت.
    - اسم كل متدخل وصفته (مثل: النائب، الوزير، رئيس اللجنة...).
    - تلخيص دقيق وموضوعي لمضمون كل مداخلة دون إطناب.
    - الإشارة إلى الرئاسة (من ترأس الجلسة).
    - أي وقائع تنظيمية هامة أثناء الجلسة (مقاطعات، تنبيهات، رفع الجلسة مؤقتاً... إلخ)، إن وُجدت.

    يرجى عدم تضمين المقدمة أو التوصيات الختامية، والتركيز فقط على قسم "سير الجلسة".

    نص التفريغ الكامل هو:

    {texte_brut}
    """
    response = model.generate_content(prompt)
    return response.text.strip()
