from ..extensions import db

class User(db.Model):
    email = db.Column(db.String(25), primary_key=True)
    prenom = db.Column(db.String(25), nullable=False)
    nom = db.Column(db.String(25), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    numeroTel = db.Column(db.Integer(15), nullable=False)
    dateNaissance = db.Column(db.Date, nullable=False)
