from ..models.transcription import Transcription
from sqlalchemy import or_
from ..extensions import db
from datetime import datetime

def create_transcription(data):

    data['dateSceance'] = datetime.strptime(data['dateSceance'], "%Y-%m-%d").date()
    data['DateRedaction'] = datetime.strptime(data['DateRedaction'], "%Y-%m-%d").date()

    if data.get('DateProchaineRéunion'):
        data['DateProchaineRéunion'] = datetime.strptime(data['DateProchaineRéunion'], "%Y-%m-%d").date()
    else:
        data['DateProchaineRéunion'] = None

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

def get_all_transcriptions():
    transcriptions = Transcription.query.all()
    if not transcriptions:
        return None
    return transcriptions

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
    if 'DateProchaineRéunion' in data and data['DateProchaineRéunion'] is not None:
        data['DateProchaineRéunion'] = datetime.strptime(data['DateProchaineRéunion'], "%Y-%m-%d").date()
    
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