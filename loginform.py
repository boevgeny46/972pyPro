from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms import SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = EmailField('Ваша почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')