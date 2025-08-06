import os
from datetime import datetime
from calendar import monthrange

import pandas as pd
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, IntegerField,
    DateField, FileField, SubmitField
)
from wtforms.validators import DataRequired, Optional

# ──────────────────────────────────────────────────────────────────────────────
# Конфигурация приложения и базы
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_port = os.environ.get('DB_PORT')
db_name = os.environ.get('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqlconnector://{db_user}:{db_pass}@"
    f"{db_host}:{db_port}/{db_name}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

db = SQLAlchemy(app)

# ──────────────────────────────────────────────────────────────────────────────
# Контекст-процессор для темы (light/dark)
# ──────────────────────────────────────────────────────────────────────────────
@app.context_processor
def inject_theme_css():
    theme = request.cookies.get('theme', 'light')
    css = 'dark.css' if theme == 'dark' else 'light.css'
    return {'theme_css': css, 'theme': theme}

# ──────────────────────────────────────────────────────────────────────────────
# Модели
# ──────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.BigInteger, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    name        = db.Column(db.String(200), nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    operations  = db.relationship('OperationLog',
                                  backref='user', lazy=True)

class OperationLog(db.Model):
    __tablename__ = 'operations_log'
    id          = db.Column(db.BigInteger, primary_key=True)
    user_id     = db.Column(db.BigInteger,
                             db.ForeignKey('users.telegram_id'),
                             nullable=True)
    block       = db.Column(db.String(50), nullable=False)
    waybill     = db.Column(db.String(50), nullable=False)
    box         = db.Column(db.String(50), nullable=False)
    article     = db.Column(db.String(100), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False)
    created_at  = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)

# ──────────────────────────────────────────────────────────────────────────────
# Формы
# ──────────────────────────────────────────────────────────────────────────────
BLOCK_CHOICES = [
    ('Приемка', 'Приемка'),
    ('Упаковка', 'Упаковка'),
    ('Комплектовка', 'Комплектовка'),
]

class OperationForm(FlaskForm):
    telegram_id = SelectField(
        'ID пользователя', coerce=int, validators=[DataRequired()]
    )
    block    = SelectField('Блок', choices=BLOCK_CHOICES,
                           validators=[DataRequired()])
    waybill  = StringField('Номер накладной', validators=[DataRequired()])
    box      = StringField('Номер короба',    validators=[DataRequired()])
    article  = StringField('Артикул',         validators=[DataRequired()])
    quantity = IntegerField('Количество',     validators=[DataRequired()])
    submit   = SubmitField('Сохранить')

class FilterForm(FlaskForm):
    telegram_id = StringField('ID пользователя', validators=[Optional()])
    block       = SelectField('Блок',
                       choices=[('', 'Все блоки')] + BLOCK_CHOICES,
                       validators=[Optional()])
    date_from   = DateField('Дата с', format='%Y-%m-%d',
                            validators=[Optional()])
    date_to     = DateField('Дата по', format='%Y-%m-%d',
                            validators=[Optional()])
    submit      = SubmitField('Фильтровать')

class EmployeeForm(FlaskForm):
    telegram_id = IntegerField('Telegram ID', validators=[DataRequired()])
    name        = StringField('Имя',         validators=[DataRequired()])
    submit      = SubmitField('Сохранить')

class ImportForm(FlaskForm):
    block = SelectField('Блок', choices=BLOCK_CHOICES,
                        validators=[DataRequired()])
    file  = FileField('Файл .xlsx',        validators=[DataRequired()])
    submit= SubmitField('Загрузить')

# ──────────────────────────────────────────────────────────────────────────────
# Маршруты
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/theme/<theme>')
def set_theme(theme):
    resp = redirect(request.referrer or url_for('home'))
    resp.set_cookie('theme', theme, max_age=30*24*3600)
    return resp

# Новая запись
@app.route('/new', methods=['GET', 'POST'])
def new_record():
    form = OperationForm()
    users = User.query.order_by(User.name).all()
    form.telegram_id.choices = [
        (u.telegram_id, u.name or str(u.telegram_id)) for u in users
    ]
    if form.validate_on_submit():
        op = OperationLog(
            user_id   = form.telegram_id.data,
            block     = form.block.data,
            waybill   = form.waybill.data,
            box       = form.box.data,
            article   = form.article.data,
            quantity  = form.quantity.data
        )
        db.session.add(op)
        db.session.commit()
        flash('Запись сохранена', 'success')
        return redirect(url_for('new_record'))
    return render_template('new_record.html', form=form)

# Список записей
@app.route('/database', methods=['GET', 'POST'])
def list_records():
    form = FilterForm()
    query = OperationLog.query
    if form.validate_on_submit():
        if form.telegram_id.data:
            query = query.filter_by(
                user_id=int(form.telegram_id.data)
            )
        if form.block.data:
            query = query.filter_by(block=form.block.data)
        if form.date_from.data:
            query = query.filter(
                OperationLog.created_at >= form.date_from.data
            )
        if form.date_to.data:
            query = query.filter(
                OperationLog.created_at <= form.date_to.data
            )
    records = query.order_by(
        OperationLog.created_at.desc()
    ).all()
    return render_template('database.html',
                           records=records, form=form)

# Выработка за месяц
@app.route('/production')
def production():
    m = int(request.args.get('month',
               datetime.utcnow().month))
    y = int(request.args.get('year',
               datetime.utcnow().year))
    days_count = monthrange(y, m)[1]
    emps = [
        (u.telegram_id, u.name or str(u.telegram_id))
        for u in User.query.order_by(User.name).all()
    ]
    data = {}
    for uid, _ in emps:
        day_totals = {}
        for d in range(1, days_count+1):
            total = db.session.query(
                db.func.coalesce(db.func.sum(
                    OperationLog.quantity), 0)
            ).filter(
                db.func.day(OperationLog.created_at)==d,
                db.func.month(OperationLog.created_at)==m,
                db.func.year(OperationLog.created_at)==y,
                OperationLog.user_id==uid
            ).scalar()
            day_totals[d] = total
        data[uid] = day_totals
    return render_template(
        'production.html',
        month=m, year=y,
        days=list(range(1, days_count+1)),
        emps=emps, data=data
    )

# Управление сотрудниками
@app.route('/employees', methods=['GET', 'POST'])
def users_page():
    form = EmployeeForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            telegram_id=form.telegram_id.data
        ).first()
        if not user:
            user = User(
                telegram_id=form.telegram_id.data,
                name=form.name.data
            )
            db.session.add(user)
        else:
            user.name = form.name.data
        db.session.commit()
        flash('Сотрудник сохранён', 'success')
        return redirect(url_for('users_page'))
    users = User.query.order_by(User.name).all()
    return render_template('employees.html',
                           users=users, form=form)

@app.route('/employees/edit/<int:telegram_id>',
           methods=['GET', 'POST'])
def edit_employee(telegram_id):
    user = User.query.filter_by(
        telegram_id=telegram_id
    ).first_or_404()
    form = EmployeeForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        db.session.commit()
        flash('Имя обновлено', 'success')
        return redirect(url_for('users_page'))
    return render_template(
        'employees_edit.html',
        form=form, telegram_id=telegram_id
    )

# Импорт из Excel
@app.route('/import_excel', methods=['GET', 'POST'])
def import_excel():
    form = ImportForm()
    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(path)
        df = pd.read_excel(path, engine='openpyxl')
        added = 0
        for _, row in df.iterrows():
            tel     = int(row['B'])
            dt      = row['C']
            waybill = str(row['D'])
            box     = str(row['E'])
            art     = str(row['F'])
            qty     = int(row['G'])
            exists = OperationLog.query.filter_by(
                user_id   = tel,
                waybill   = waybill,
                box       = box,
                article   = art,
                quantity  = qty,
                created_at=dt
            ).first()
            if not exists:
                op = OperationLog(
                    user_id    = tel,
                    block      = form.block.data,
                    waybill    = waybill,
                    box        = box,
                    article    = art,
                    quantity   = qty,
                    created_at = dt
                )
                db.session.add(op)
                added += 1
        db.session.commit()
        flash(f'Импортировано: {added}', 'success')
        return redirect(url_for('list_records'))
    return render_template('import_excel.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
