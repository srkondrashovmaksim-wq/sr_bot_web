from flask_wtf import FlaskForm
from wtforms import (
    IntegerField, StringField, SelectField, SubmitField,
    FileField, HiddenField, DateField
)
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileRequired, FileAllowed


class OperationForm(FlaskForm):
    telegram_id = IntegerField('Telegram ID', validators=[DataRequired()])
    block       = SelectField('Блок', choices=[], validators=[DataRequired()])
    waybill     = StringField('Накладная', validators=[DataRequired()])
    box         = StringField('Короб', validators=[DataRequired()])
    article     = StringField('Артикул', validators=[DataRequired()])
    quantity    = IntegerField('Количество', validators=[DataRequired()])
    submit      = SubmitField('Сохранить')


class FilterForm(FlaskForm):
    telegram_id = IntegerField('ID пользователя', validators=[Optional()])
    block       = SelectField('Блок', choices=[], validators=[Optional()])
    date_from   = DateField('Дата с', format='%Y-%m-%d', validators=[Optional()])
    date_to     = DateField('Дата по', format='%Y-%m-%d', validators=[Optional()])
    submit      = SubmitField('Фильтровать')


class ExcelImportForm(FlaskForm):
    block = SelectField('Блок', choices=[], validators=[DataRequired()])
    file  = FileField('Файл Excel', validators=[
        FileRequired(), FileAllowed(['xlsx'], 'Только .xlsx')
    ])
    submit = SubmitField('Импорт')


class EmployeeForm(FlaskForm):
    emp_id      = HiddenField()
    telegram_id = IntegerField('Telegram ID', validators=[Optional()])
    name        = StringField('ФИО', validators=[DataRequired()])
    submit      = SubmitField('Сохранить')
