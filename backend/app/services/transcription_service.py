from ..models.transcription import Transcription
from sqlalchemy import or_
from ..extensions import db
from datetime import datetime
from flask import send_file
import io
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from ..services.ai_services import generate_deroulement, analyze_transcription
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from decouple import config
import markdown
from bs4 import BeautifulSoup
import re
import textwrap

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

    # Serialize dict or list to JSON string if needed
    if isinstance(data.get('Transcription'), (dict, list)):
        import json
        data['Transcription'] = json.dumps(data['Transcription'], ensure_ascii=False)

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

# -------------- GET NGROK URL ----------------
def get_ngrok_url():
    return config("NGROK_URL") 

# ----------- Helper Functions for Markdown Processing -----------
def parse_markdown_to_structured_text(markdown_text):
    """Parse markdown text and return structured content with hierarchy"""
    if not markdown_text:
        return []
    
    # Convert markdown to HTML while preserving order
    html = markdown.markdown(markdown_text, extensions=['fenced_code'])
    soup = BeautifulSoup(html, 'html.parser')
    
    structured_content = []
    
    # Process elements in order to maintain structure
    for element in soup.children:
        if hasattr(element, 'name') and element.name:
            if element.name.startswith('h') and len(element.name) == 2:
                level = int(element.name[1])
                text = element.get_text().strip()
                if text:
                    structured_content.append({
                        'type': 'heading',
                        'level': level,
                        'text': text,
                        'order': len(structured_content)
                    })
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:  # Only add non-empty paragraphs
                    structured_content.append({
                        'type': 'paragraph',
                        'text': text,
                        'order': len(structured_content)
                    })
            elif element.name in ['ul', 'ol']:
                list_items = []
                for li in element.find_all('li'):
                    item_text = li.get_text().strip()
                    if item_text:
                        list_items.append(item_text)
                if list_items:
                    structured_content.append({
                        'type': 'list',
                        'ordered': element.name == 'ol',
                        'items': list_items,
                        'order': len(structured_content)
                    })
    
    # If soup.children didn't work well, fall back to find_all but preserve document order
    if not structured_content:
        all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol'])
        for i, element in enumerate(all_elements):
            if element.name.startswith('h'):
                level = int(element.name[1])
                text = element.get_text().strip()
                if text:
                    structured_content.append({
                        'type': 'heading',
                        'level': level,
                        'text': text,
                        'order': i
                    })
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    structured_content.append({
                        'type': 'paragraph',
                        'text': text,
                        'order': i
                    })
            elif element.name in ['ul', 'ol']:
                list_items = []
                for li in element.find_all('li'):
                    item_text = li.get_text().strip()
                    if item_text:
                        list_items.append(item_text)
                if list_items:
                    structured_content.append({
                        'type': 'list',
                        'ordered': element.name == 'ol',
                        'items': list_items,
                        'order': i
                    })
    
    # Sort by order to ensure proper sequence
    structured_content.sort(key=lambda x: x.get('order', 0))
    
    return structured_content

def wrap_arabic_text(text, max_width=70):
    """Wrap Arabic text properly for PDF generation"""
    if not text:
        return []
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# ----------- Export PV DOCX with Improved Formatting -----------
def export_transcription_pv_arabe_docx(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None

    doc = Document()
    
    # Create custom styles
    styles = doc.styles
    
    # Title style
    try:
        title_style = styles['Title']
    except KeyError:
        title_style = styles.add_style('Title', WD_STYLE_TYPE.PARAGRAPH)
    title_style.font.size = Pt(18)
    title_style.font.bold = True
    
    # Heading style
    try:
        heading_style = styles.add_style('CustomHeading', WD_STYLE_TYPE.PARAGRAPH)
    except:
        heading_style = styles['CustomHeading']
    heading_style.font.size = Pt(14)
    heading_style.font.bold = True
    
    # Normal style for Arabic
    try:
        arabic_style = styles.add_style('ArabicNormal', WD_STYLE_TYPE.PARAGRAPH)
    except:
        arabic_style = styles['ArabicNormal']
    arabic_style.font.size = Pt(12)

    def add_arabic_paragraph(text, style_name='ArabicNormal', bold=False):
        p = doc.add_paragraph(style=style_name)
        run = p.add_run(text)
        if bold:
            run.bold = True
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        return p

    def add_structured_content(content_list):
        """Add structured content from parsed markdown"""
        for item in content_list:
            if item['type'] == 'heading':
                size = max(16 - item['level'] * 2, 10)  # Decrease size with level
                p = add_arabic_paragraph(item['text'], bold=True)
                p.runs[0].font.size = Pt(size)
                doc.add_paragraph()  # Add space after heading
                
            elif item['type'] == 'paragraph':
                add_arabic_paragraph(item['text'])
                
            elif item['type'] == 'list':
                for i, list_item in enumerate(item['items']):
                    prefix = f"{i+1}. " if item['ordered'] else "• "
                    add_arabic_paragraph(f"{prefix}{list_item}")
                doc.add_paragraph()  # Add space after list

    # Main title
    add_arabic_paragraph("محضر اجتماع", style_name='Title')
    doc.add_paragraph()

    # Basic information
    fields = [
        (transcription.titreSceance, "عنوان الجلسة"),
        (transcription.dateSceance.strftime('%Y/%m/%d'), "تاريخ الجلسة"),
        (f"{transcription.HeureDebut.strftime('%H:%M')} إلى {transcription.HeureFin.strftime('%H:%M')}", "الساعة"),
        (transcription.President, "الرئيس"),
        (transcription.Secretaire, "الكاتب"),
    ]

    for value, label in fields:
        add_arabic_paragraph(f"{value} :{label}", bold=True)

    doc.add_paragraph()
    add_arabic_paragraph("الأعضاء الحاضرون:", bold=True)
    add_arabic_paragraph(transcription.Membres or "لا يوجد")

    if transcription.Absents:
        doc.add_paragraph()
        add_arabic_paragraph("الأعضاء الغائبون:", bold=True)
        add_arabic_paragraph(transcription.Absents)

    doc.add_paragraph()
    add_arabic_paragraph("جدول الأعمال:", bold=True)
    add_arabic_paragraph(transcription.OrdreDuJour or "غير متوفر")

    doc.add_paragraph()
    add_arabic_paragraph("سير الجلسة:", bold=True)
    
    # Parse and add Deroulement with proper markdown formatting
    if transcription.Deroulement:
        structured_deroulement = parse_markdown_to_structured_text(transcription.Deroulement)
        add_structured_content(structured_deroulement)
    else:
        add_arabic_paragraph("غير متوفر")

    if transcription.DateProchaineReunion:
        doc.add_paragraph()
        add_arabic_paragraph("تاريخ الاجتماع المقبل:", bold=True)
        add_arabic_paragraph(transcription.DateProchaineReunion.strftime('%Y/%m/%d'))

    # Signature section
    doc.add_paragraph()
    doc.add_paragraph()
    p_city = doc.add_paragraph("حرر بمدينة .............. في تاريخ ..............")
    p_city.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    
    p_signatures = doc.add_paragraph("الرئيس: ............................                الكاتب: ............................")
    p_signatures.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"محضر_{transcription.titreSceance or 'اجتماع'}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ----------- Export PV PDF with Improved Formatting -----------
def export_transcription_pv_arabe_pdf(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Register Arabic font
    font_path = "static/fonts/Amiri-Regular.ttf"
    try:
        pdfmetrics.registerFont(TTFont("Arabic", font_path))
        arabic_font = "Arabic"
    except:
        arabic_font = "Helvetica"  # Fallback font
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Title'],
        fontName=arabic_font,
        fontSize=18,
        alignment=2,  # Right alignment
        spaceAfter=20,
    )
    
    # Heading style
    heading_style = ParagraphStyle(
        'ArabicHeading',
        parent=styles['Heading1'],
        fontName=arabic_font,
        fontSize=14,
        alignment=2,  # Right alignment
        spaceAfter=12,
        spaceBefore=12,
    )
    
    # Normal Arabic style
    arabic_style = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=12,
        alignment=2,  # Right alignment
        spaceAfter=6,
    )
    
    # List style
    list_style = ParagraphStyle(
        'ArabicList',
        parent=arabic_style,
        leftIndent=20,
        spaceAfter=3,
    )

    def format_arabic_text(text):
        """Format Arabic text for proper display"""
        if not text:
            return ""
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except:
            return str(text)

    def create_structured_paragraphs(content_list):
        """Create paragraphs from structured markdown content"""
        paragraphs = []
        
        # Sort content by order to maintain proper sequence
        sorted_content = sorted(content_list, key=lambda x: x.get('order', 0))
        
        for item in sorted_content:
            if item['type'] == 'heading':
                # Add space before heading (except for the first one)
                if paragraphs:
                    paragraphs.append(Spacer(1, 12))
                
                # Adjust font size based on heading level
                heading_font_size = max(16 - item['level'] * 2, 10)
                custom_heading_style = ParagraphStyle(
                    f'Heading{item["level"]}_{item.get("order", 0)}',
                    parent=heading_style,
                    fontSize=heading_font_size,
                    spaceAfter=8,
                    spaceBefore=4,
                )
                text = format_arabic_text(item['text'])
                paragraphs.append(Paragraph(text, custom_heading_style))
                
            elif item['type'] == 'paragraph':
                text = format_arabic_text(item['text'])
                paragraphs.append(Paragraph(text, arabic_style))
                
            elif item['type'] == 'list':
                # Add space before list
                if paragraphs:
                    paragraphs.append(Spacer(1, 6))
                    
                list_style_local = ParagraphStyle(
                    f'ArabicList_{item.get("order", 0)}',
                    parent=arabic_style,
                    leftIndent=20,
                    spaceAfter=3,
                )
                
                for i, list_item in enumerate(item['items']):
                    prefix = f"{i+1}. " if item['ordered'] else "• "
                    text = format_arabic_text(f"{prefix}{list_item}")
                    paragraphs.append(Paragraph(text, list_style_local))
                
                # Add space after list
                paragraphs.append(Spacer(1, 6))
        
        return paragraphs

    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(format_arabic_text("محضر اجتماع"), title_style))
    story.append(Spacer(1, 20))
    
    # Basic information
    fields = [
        (transcription.titreSceance, "عنوان الجلسة"),
        (transcription.dateSceance.strftime('%Y/%m/%d'), "تاريخ الجلسة"),
        (f"{transcription.HeureDebut.strftime('%H:%M')} إلى {transcription.HeureFin.strftime('%H:%M')}", "الساعة"),
        (transcription.President, "الرئيس"),
        (transcription.Secretaire, "الكاتب"),
    ]

    for value, label in fields:
        text = format_arabic_text(f"{value} :{label}")
        story.append(Paragraph(text, arabic_style))

    story.append(Spacer(1, 12))
    
    # Members present
    story.append(Paragraph(format_arabic_text("الأعضاء الحاضرون:"), heading_style))
    members_text = format_arabic_text(transcription.Membres or "لا يوجد")
    story.append(Paragraph(members_text, arabic_style))

    # Members absent
    if transcription.Absents:
        story.append(Spacer(1, 12))
        story.append(Paragraph(format_arabic_text("الأعضاء الغائبون:"), heading_style))
        absents_text = format_arabic_text(transcription.Absents)
        story.append(Paragraph(absents_text, arabic_style))

    # Agenda
    story.append(Spacer(1, 12))
    story.append(Paragraph(format_arabic_text("جدول الأعمال:"), heading_style))
    agenda_text = format_arabic_text(transcription.OrdreDuJour or "غير متوفر")
    story.append(Paragraph(agenda_text, arabic_style))

    # Deroulement with markdown parsing
    story.append(Spacer(1, 12))
    story.append(Paragraph(format_arabic_text("سير الجلسة:"), heading_style))
    
    if transcription.Deroulement:
        structured_deroulement = parse_markdown_to_structured_text(transcription.Deroulement)
        deroulement_paragraphs = create_structured_paragraphs(structured_deroulement)
        story.extend(deroulement_paragraphs)
    else:
        story.append(Paragraph(format_arabic_text("غير متوفر"), arabic_style))

    # Next meeting date
    if transcription.DateProchaineReunion:
        story.append(Spacer(1, 12))
        story.append(Paragraph(format_arabic_text("تاريخ الاجتماع المقبل:"), heading_style))
        next_meeting_text = format_arabic_text(transcription.DateProchaineReunion.strftime('%Y/%m/%d'))
        story.append(Paragraph(next_meeting_text, arabic_style))

    # Signature section
    story.append(Spacer(1, 30))
    signature_style = ParagraphStyle(
        'Signature',
        parent=arabic_style,
        alignment=0,  # Left alignment for signatures
    )
    story.append(Paragraph("حرر بمدينة .............. في تاريخ ..............", signature_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("الرئيس: ............................                الكاتب: ............................", signature_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"محضر_{transcription.titreSceance or 'اجتماع'}.pdf",
        mimetype="application/pdf"
    )

# ----------- Export Analysis DOCX with Improved Formatting -----------
def export_transcription_analysis_arabe_docx(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Analyse:
        return None

    doc = Document()
    
    # Create styles
    styles = doc.styles
    try:
        title_style = styles['Title']
    except KeyError:
        title_style = styles.add_style('Title', WD_STYLE_TYPE.PARAGRAPH)
    title_style.font.size = Pt(18)
    title_style.font.bold = True

    def add_arabic_paragraph(text, bold=False, font_size=12):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.size = Pt(font_size)
        if bold:
            run.bold = True
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        return p

    def add_structured_content(content_list):
        """Add structured content from parsed markdown"""
        for item in content_list:
            if item['type'] == 'heading':
                size = max(16 - item['level'] * 2, 10)
                add_arabic_paragraph(item['text'], bold=True, font_size=size)
                doc.add_paragraph()
                
            elif item['type'] == 'paragraph':
                add_arabic_paragraph(item['text'])
                
            elif item['type'] == 'list':
                for i, list_item in enumerate(item['items']):
                    prefix = f"{i+1}. " if item['ordered'] else "• "
                    add_arabic_paragraph(f"{prefix}{list_item}")
                doc.add_paragraph()

    # Title
    title_p = doc.add_paragraph("تحليل محضر الاجتماع", style='Title')
    title_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    doc.add_paragraph()

    # Parse and add analysis with proper markdown formatting
    structured_analysis = parse_markdown_to_structured_text(transcription.Analyse)
    add_structured_content(structured_analysis)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"تحليل_محضر_{transcription.titreSceance or 'اجتماع'}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ----------- Export Analysis PDF with Improved Formatting -----------
def export_transcription_analysis_arabe_pdf(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription or not transcription.Analyse:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Register Arabic font
    font_path = "static/fonts/Amiri-Regular.ttf"
    try:
        pdfmetrics.registerFont(TTFont("Arabic", font_path))
        arabic_font = "Arabic"
    except:
        arabic_font = "Helvetica"
    
    # Create styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Title'],
        fontName=arabic_font,
        fontSize=18,
        alignment=1,  # Center alignment
        spaceAfter=20,
    )
    
    heading_style = ParagraphStyle(
        'ArabicHeading',
        parent=styles['Heading1'],
        fontName=arabic_font,
        fontSize=14,
        alignment=2,  # Right alignment
        spaceAfter=12,
        spaceBefore=12,
    )
    
    arabic_style = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=12,
        alignment=2,  # Right alignment
        spaceAfter=6,
    )

    def format_arabic_text(text):
        """Format Arabic text for proper display"""
        if not text:
            return ""
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except:
            return str(text)

    def create_structured_paragraphs(content_list):
        """Create paragraphs from structured markdown content"""
        paragraphs = []
        for item in content_list:
            if item['type'] == 'heading':
                heading_font_size = max(16 - item['level'] * 2, 10)
                custom_heading_style = ParagraphStyle(
                    f'Heading{item["level"]}',
                    parent=heading_style,
                    fontSize=heading_font_size,
                )
                text = format_arabic_text(item['text'])
                paragraphs.append(Paragraph(text, custom_heading_style))
                paragraphs.append(Spacer(1, 6))
                
            elif item['type'] == 'paragraph':
                text = format_arabic_text(item['text'])
                paragraphs.append(Paragraph(text, arabic_style))
                
            elif item['type'] == 'list':
                list_style = ParagraphStyle(
                    'ArabicList',
                    parent=arabic_style,
                    leftIndent=20,
                    spaceAfter=3,
                )
                for i, list_item in enumerate(item['items']):
                    prefix = f"{i+1}. " if item['ordered'] else "• "
                    text = format_arabic_text(f"{prefix}{list_item}")
                    paragraphs.append(Paragraph(text, list_style))
                paragraphs.append(Spacer(1, 6))
        
        return paragraphs

    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(format_arabic_text("تحليل محضر الاجتماع"), title_style))
    story.append(Spacer(1, 20))
    
    # Parse and add analysis with proper markdown formatting
    structured_analysis = parse_markdown_to_structured_text(transcription.Analyse)
    analysis_paragraphs = create_structured_paragraphs(structured_analysis)
    story.extend(analysis_paragraphs)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"تحليل_محضر_{transcription.titreSceance or 'اجتماع'}.pdf",
        mimetype="application/pdf"
    )