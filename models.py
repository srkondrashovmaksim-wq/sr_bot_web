from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class OperationLog(db.Model):
    __tablename__ = 'operations_log'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey('users.telegram_id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )
    user = db.relationship('User', backref='operations')
    block    = db.Column(db.String(50),  nullable=False)
    waybill  = db.Column(db.String(50),  nullable=False)
    box      = db.Column(db.String(50),  nullable=False)   # ← было box_number
    article  = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer,     nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
