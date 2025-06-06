from ..models.transcription import Transcription
from sqlalchemy import or_
from ..extensions import db
from datetime import datetime
from ..services.ai_services import generate_deroulement, analyze_transcription


def create_transcription(data):

    data['dateSceance'] = datetime.strptime(data['dateSceance'], "%Y-%m-%d").date()
    data['DateRedaction'] = datetime.strptime(data['DateRedaction'], "%Y-%m-%d").date()

    if data.get('DateProchaineReunion'):
        data['DateProchaineReunion'] = datetime.strptime(data['DateProchaineReunion'], "%Y-%m-%d").date()
    else:
        data['DateProchaineReunion'] = None

    # Convert time strings to time objects
    data['HeureDebut'] = datetime.strptime(data['HeureDebut'], "%H:%M:%S").time()
    data['HeureFin'] = datetime.strptime(data['HeureFin'], "%H:%M:%S").time()

    transcription = Transcription(**data)
    db.session.add(transcription)
    db.session.commit()
    return transcription

def get_transcription_by_id(transcription_id):
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return None
    return transcription

def get_all_transcriptions(user_email=None):
    if user_email:
        return Transcription.query.filter_by(user_email=user_email).all()
    else:
        return Transcription.query.all()

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
    
    # Convert string dates/times to proper Python objects before setting
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
    results = Transcription.query.filter(
        or_(
            Transcription.titreSceance.ilike(f"%{query}%"),
            Transcription.President.ilike(f"%{query}%"),
            Transcription.OrdreDuJour.ilike(f"%{query}%"),
            Transcription.Resume.ilike(f"%{query}%"),
            Transcription.PV.ilike(f"%{query}%")
        )
    ).all()
    return results

def update_transcription_with_deroulement(transcription_id: int) -> Transcription:
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        raise ValueError("Transcription not found.")
    
    if not transcription.Transcription:
        raise ValueError("Transcription text is missing.")

    deroulement = generate_deroulement(transcription.Transcription)
    transcription.Deroulement = deroulement
    db.session.commit()
    return transcription

def update_transcription_with_analysis(transcription_id: int) -> Transcription:
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        raise ValueError("Transcription not found.")
    
    if not transcription.Transcription:
        raise ValueError("Transcription text is missing.")

    analysis = analyze_transcription(transcription.Transcription)
    transcription.Analyse = analysis
    db.session.commit()
    return transcription