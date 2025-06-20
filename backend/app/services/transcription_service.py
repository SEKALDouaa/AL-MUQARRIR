from ..models.transcription import Transcription
from sqlalchemy import or_
from ..extensions import db
from datetime import datetime
from flask import send_file
import io
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ..services.ai_services import generate_deroulement, analyze_transcription
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display


def create_transcription(data):
    data['dateSceance'] = datetime.strptime(data['dateSceance'], "%Y-%m-%d").date()
    data['DateRedaction'] = datetime.strptime(data['DateRedaction'], "%Y-%m-%d").date()

    if data.get('DateProchaineReunion'):
        data['DateProchaineReunion'] = datetime.strptime(data['DateProchaineReunion'], "%Y-%m-%d").date()
    else:
        data['DateProchaineReunion'] = None

    data['HeureDebut'] = datetime.strptime(data['HeureDebut'], "%H:%M:%S").time()
    data['HeureFin'] = datetime.strptime(data['HeureFin'], "%H:%M:%S").time()

    transcription = Transcription(**data)
    db.session.add(transcription)
    db.session.commit()
    return transcription

def get_transcription_by_id(transcription_id):
    return Transcription.query.get(transcription_id)

def get_all_transcriptions(user_email=None):
    return Transcription.query.filter_by(user_email=user_email).all() if user_email else Transcription.query.all()

def delete_transcription(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None
    db.session.delete(transcription)
    db.session.commit()
    return transcription

def update_transcription(transcription_id, data):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None

    if 'dateSceance' in data:
        data['dateSceance'] = datetime.strptime(data['dateSceance'], "%Y-%m-%d").date()
    if 'DateRedaction' in data:
        data['DateRedaction'] = datetime.strptime(data['DateRedaction'], "%Y-%m-%d").date()
    if 'DateProchaineReunion' in data and data['DateProchaineReunion'] is not None:
        data['DateProchaineReunion'] = datetime.strptime(data['DateProchaineReunion'], "%Y-%m-%d").date()

    if 'HeureDebut' in data:
        data['HeureDebut'] = datetime.strptime(data['HeureDebut'], "%H:%M:%S").time()
    if 'HeureFin' in data:
        data['HeureFin'] = datetime.strptime(data['HeureFin'], "%H:%M:%S").time()

    for key, value in data.items():
        setattr(transcription, key, value)

    db.session.commit()
    return transcription

def search_transcriptions(query):
    return Transcription.query.filter(
        or_(
            Transcription.titreSceance.ilike(f"%{query}%"),
            Transcription.President.ilike(f"%{query}%"),
            Transcription.OrdreDuJour.ilike(f"%{query}%"),
            Transcription.Resume.ilike(f"%{query}%"),
            Transcription.PV.ilike(f"%{query}%")
        )
    ).all()

def update_transcription_with_deroulement(transcription_id: int) -> Transcription:
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Transcription:
        raise ValueError("Transcription not found or missing text.")

    transcription.Deroulement = generate_deroulement(transcription.Transcription)
    db.session.commit()
    return transcription

def update_transcription_with_analysis(transcription_id: int) -> Transcription:
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Transcription:
        raise ValueError("Transcription not found or missing text.")

    transcription.Analyse = analyze_transcription(transcription.Transcription)
    db.session.commit()
    return transcription

# ----------- Export PV DOCX -----------
def export_transcription_pv_arabe_docx(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None

    doc = Document()

    def add_arabic_paragraph(text, bold=False):
        p = doc.add_paragraph()
        run = p.add_run(text)
        if bold:
            run.bold = True
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        return p

    add_arabic_paragraph("محضر اجتماع", bold=True)

    fields = [
        (transcription.titreSceance, "عنوان الجلسة"),
        (transcription.dateSceance.strftime('%Y/%m/%d'), "تاريخ الجلسة"),
        (f"{transcription.HeureDebut.strftime('%H:%M')} إلى {transcription.HeureFin.strftime('%H:%M')}", "الساعة"),
        (transcription.President, "الرئيس"),
        (transcription.Secretaire, "الكاتب"),
    ]

    for value, label in fields:
        add_arabic_paragraph(f"{value} :{label}")

    doc.add_paragraph()
    add_arabic_paragraph(":الأعضاء الحاضرون", bold=True)
    add_arabic_paragraph(transcription.Membres or "لا يوجد")

    if transcription.Absents:
        doc.add_paragraph()
        add_arabic_paragraph(":الأعضاء الغائبون", bold=True)
        add_arabic_paragraph(transcription.Absents)

    doc.add_paragraph()
    add_arabic_paragraph(":جدول الأعمال", bold=True)
    add_arabic_paragraph(transcription.OrdreDuJour or "غير متوفر")

    doc.add_paragraph()
    add_arabic_paragraph(":سير الجلسة", bold=True)
    add_arabic_paragraph(transcription.Deroulement or "غير متوفر")

    if transcription.DateProchaineReunion:
        doc.add_paragraph()
        add_arabic_paragraph(":تاريخ الاجتماع المقبل", bold=True)
        add_arabic_paragraph(transcription.DateProchaineReunion.strftime('%Y/%m/%d'))

    doc.add_paragraph()
    p_points = doc.add_paragraph("..............  حرر بمدينة .............. في تاريخ  ")
    p_points.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    p_points = doc.add_paragraph("............................. :الرئيس: ............................الكاتب")
    p_points.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"محضر_{transcription.titreSceance}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ----------- Export PV PDF -----------
def export_transcription_pv_arabe_pdf(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Register Arabic font
    font_path = "static/fonts/Amiri-Regular.ttf"
    pdfmetrics.registerFont(TTFont("Arabic", font_path))

    def draw_right_aligned_line(text, y, font_size=12):
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        c.setFont("Arabic", font_size)
        text_width = c.stringWidth(bidi_text, "Arabic", font_size)
        c.drawString(width - text_width - 50, y, bidi_text)

    y = height - 50
    line_height = 18

    draw_right_aligned_line("محضر اجتماع", y, font_size=16)
    y -= 2 * line_height

    fields = [
        (transcription.titreSceance, "عنوان الجلسة"),
        (transcription.dateSceance.strftime('%Y/%m/%d'), "تاريخ الجلسة"),
        (f"{transcription.HeureDebut.strftime('%H:%M')} إلى {transcription.HeureFin.strftime('%H:%M')}", "الساعة"),
        (transcription.President, "الرئيس"),
        (transcription.Secretaire, "الكاتب"),
    ]

    for value, label in fields:
        draw_right_aligned_line(f"{value} :{label}", y)
        y -= line_height

    y -= line_height
    draw_right_aligned_line(":الأعضاء الحاضرون", y)
    y -= line_height
    for line in (transcription.Membres or "لا يوجد").split('\n'):
        draw_right_aligned_line(line.strip(), y)
        y -= line_height

    if transcription.Absents:
        y -= line_height
        draw_right_aligned_line(":الأعضاء الغائبون", y)
        y -= line_height
        for line in transcription.Absents.split('\n'):
            draw_right_aligned_line(line.strip(), y)
            y -= line_height

    y -= line_height
    draw_right_aligned_line(":جدول الأعمال", y)
    y -= line_height
    for line in (transcription.OrdreDuJour or "غير متوفر").split('\n'):
        draw_right_aligned_line(line.strip(), y)
        y -= line_height

    y -= line_height
    draw_right_aligned_line(":سير الجلسة", y)
    y -= line_height
    for line in (transcription.Deroulement or "غير متوفر").split('\n'):
        draw_right_aligned_line(line.strip(), y)
        y -= line_height

    if transcription.DateProchaineReunion:
        y -= line_height
        draw_right_aligned_line(":تاريخ الاجتماع المقبل", y)
        y -= line_height
        draw_right_aligned_line(transcription.DateProchaineReunion.strftime('%Y/%m/%d'), y)
        y -= line_height

    y -= 2 * line_height
    c.setFont("Arabic", 12)
    draw_right_aligned_line("..............  حرر بمدينة .............. في تاريخ  ", y)
    y -= line_height
    draw_right_aligned_line("............................. :الرئيس: ............................الكاتب", y)

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"محضر_{transcription.titreSceance}.pdf",
        mimetype="application/pdf"
    )

# ----------- Export Analysis DOCX -----------
def export_transcription_analysis_arabe_docx(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Analyse:
        return None

    doc = Document()
    doc.add_paragraph("تحليل محضر الاجتماع", style='Title').alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    p = doc.add_paragraph()
    run = p.add_run(transcription.Analyse)
    p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"تحليل_محضر_{transcription.titreSceance}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ----------- Export Analysis PDF -----------
def export_transcription_analysis_arabe_pdf(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Analyse:
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    textobject = c.beginText()
    textobject.setFont("Helvetica", 12)
    textobject.setTextOrigin(width - 50, height - 50)
    lines = transcription.Analyse.split('\n')
    for line in lines:
        textobject.textLine(line.rjust(100))  # approximate RTL look
    c.drawText(textobject)
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"تحليل_محضر_{transcription.titreSceance}.pdf",
        mimetype="application/pdf"
    )
def export_transcription_analysis_arabe_pdf(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Analyse:
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Register Arabic font
    font_path = "static/fonts/Amiri-Regular.ttf"
    pdfmetrics.registerFont(TTFont("Arabic", font_path))

    y = height - 50
    line_height = 18
    c.setFont("Arabic", 12)

    for line in transcription.Analyse.split('\n'):
        reshaped = arabic_reshaper.reshape(line)
        bidi_text = get_display(reshaped)
        text_width = c.stringWidth(bidi_text, "Arabic", 12)
        c.drawString(width - text_width - 50, y, bidi_text)
        y -= line_height

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"تحليل_محضر_{transcription.titreSceance}.pdf",
        mimetype="application/pdf"
    )
