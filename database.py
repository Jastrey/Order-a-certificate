from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_group = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.String(10), nullable=False)
    request_place = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='в работе')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student_name,
            'student_group': self.student_group,
            'birth_date': self.birth_date,
            'request_place': self.request_place,
            'quantity': self.quantity,
            'comment': self.comment,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }
