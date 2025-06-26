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

def analyze_transcription(texte_brut: str) -> str:
    prompt = f"""
    أريد منك إجراء تحليل دلالي (Analyse sémantique) لمحتوى النص التالي، وهو تفريغ حرفي لمجريات جلسة نقاشية في سياق برلماني أو مؤسسي.

    اعتمد على تقنيات معالجة اللغة الطبيعية (NLP) لاستخلاص تقرير تحليلي رسمي باللغة العربية الفصحى يتضمن المحاور التالية:

    1. تحليل المشاعر العامة (sentiment analysis): تصنيف المداخلات حسب طبيعتها (نقدية، بنّاءة، توافقية، حيادية...).
    2. تحديد المواضيع الرئيسية المتكررة (themes récurrents): أبرز القضايا التي تم التركيز عليها خلال الجلسة.
    3. رصد الإشكاليات المطروحة (problèmes soulevés): العقبات أو المشاكل التي أثيرت في المداخلات.
    4. استخلاص فرص التحسين والتوصيات (opportunités d'amélioration): مجالات يُمكن تطويرها بناءً على محتوى النقاش.

    يُرجى تقديم التحليل في صيغة تقرير منظم وواضح، باللغة العربية الفصحى، مع الحفاظ على الطابع الرسمي والحيادي، كما هو معمول به في تقارير تحليل جلسات البرلمان المغربي.

    نص التفريغ هو:

    {texte_brut}
    """

    response = model.generate_content(prompt)
    return response.text.strip()

def refine_text_with_gemini_api(text_segment, speaker_label, model):
    if not model or not text_segment or not text_segment.strip():
        return text_segment

    prompt = f"""You are an expert AI assistant specializing in refining raw speech transcriptions from Moroccan conversations.
These conversations frequently mix Moroccan Darija, Modern Standard Arabic, French, and English.
Your primary directive is to enhance the clarity, readability, and grammatical correctness of the transcription WHILE STRICTLY PRESERVING THE ORIGINAL LANGUAGE(S) USED by the speaker.

**CRITICAL INSTRUCTIONS:**
1.  **NO TRANSLATION:** Absolutely do NOT translate any part of the text into English or any other language if it wasn't originally in that language. If the input is in Arabic/Darija, the output MUST be in Arabic/Darija. If it's a mix (e.g., Darija with French words), the output MUST preserve that exact mix.
2.  **LANGUAGE PRESERVATION:** Maintain the original linguistic blend. Do not replace Darija words with MSA or vice-versa unless it's a clear ASR error of a common word.
3.  **CORRECT ASR ERRORS:** Fix obvious errors from the Automatic Speech Recognition within the original language.
4.  **PUNCTUATION & CAPITALIZATION:** Improve punctuation and capitalization for better readability, following conventions appropriate for the language(s) being used (e.g., Arabic punctuation for Arabic text, French conventions for French text).
5.  **NATURAL FLOW:** Ensure the language sounds natural as if a human wrote it down from the speech.
6.  **NO ADDITIONS/OPINIONS:** Do not add any information or opinions not present in the original text.
7.  **MINIMAL CHANGES IF GOOD:** If a segment is already high quality, return it as is or with only very minor, essential touch-ups.
8.  **OUTPUT ONLY THE REFINED TEXT:** Do not include any of your own commentary, apologies, or explanations in the response. Just the refined segment.

**EXAMPLES OF DESIRED BEHAVIOR (Illustrative - provide your own high-quality examples):**

*   **Example 1 (Darija):**
    *   Speaker: SPEAKER_A
    *   Raw Transcription Segment: "السلام عليكم لباس اش خبارك كلشي مزيان"
    *   Refined Transcription Segment: "السلام عليكم، لباس؟ اش خبارك؟ كلشي مزيان."

*   **Example 2 (Darija/French Mix):**
    *   Speaker: SPEAKER_B
    *   Raw Transcription Segment: "bonjour khouya cv ana ghaya daba on va commencer le travail"
    *   Refined Transcription Segment: "Bonjour khouya, ça va? أنا غاية دابا. On va commencer le travail."

*   **Example 3 (MSA - Modern Standard Arabic):**
    *   Speaker: SPEAKER_C
    *   Raw Transcription Segment: "نود ان نناقش هذا الموضوع الهام في جلستنا اليوم"
    *   Refined Transcription Segment: "نود أن نناقش هذا الموضوع الهام في جلستنا اليوم."

*   **Example 4 (Input is already good):**
    *   Speaker: SPEAKER_D
    *   Raw Transcription Segment: "C'est une très bonne idée, merci."
    *   Refined Transcription Segment: "C'est une très bonne idée, merci."

**TASK:**
Now, apply these instructions to the following segment:

Speaker: {speaker_label}
Raw Transcription Segment: "{text_segment}"

Refined Transcription Segment:
"""
    try:
        response = model.generate_content(
            prompt,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        if hasattr(response, 'text'):
            refined_text = response.text
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            refined_text = "".join(part.text for part in response.candidates[0].content.parts)
        else:
            print("    Warning: Could not extract text from Gemini response in the expected way.")
            print(f"    Response object: {response}")
            return text_segment
        return refined_text.strip()
    except Exception as e:
        print(f"    Error during Gemini API call for '{text_segment[:50]}...': {e}")
        if hasattr(e, 'response') and e.response:
            print(f"    Gemini API Response Error: {e.response}")
        elif hasattr(e, 'message') and e.message:
            print(f"    GenAI Exception message: {e.message}")
        return text_segment


def process_refinement_with_gemini(speaker_texts: list[dict], gemini_model_instance: genai.GenerativeModel) -> list[dict]:
    """
    Processes a list of speaker text segments using the Gemini API for refinement.
    Args:
        speaker_texts: A list of dictionaries, where each dictionary has one
                       speaker label as key and the raw text segment as value.
                       Example: [{'SPEAKER_00': 'Raw text 1'}, {'SPEAKER_01': 'Raw text 2'}]
        gemini_model_instance: An initialized instance of google.generativeai.GenerativeModel.
    Returns:
        A list of dictionaries in the same format as input, but with refined text segments.
        Returns an empty list if gemini_model_instance is None or speaker_texts is empty.
    """
    if not gemini_model_instance:
        return speaker_texts
    if not speaker_texts:
        return []
    refined_dialogue = []
    total_segments = len(speaker_texts)
    for i, entry in enumerate(speaker_texts):
        if not entry:
            continue
        speaker_label, original_text = list(entry.items())[0]
        refined_text = refine_text_with_gemini_api(original_text, speaker_label, gemini_model_instance)
        refined_dialogue.append({speaker_label: refined_text})
    return refined_dialogue