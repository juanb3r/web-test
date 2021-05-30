from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo,ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField("Email", validators =[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators =[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=20)])
    repeat_password = PasswordField("Confirm password", validators=[DataRequired(), Length(min=8, max=20), EqualTo('password')])
    first_name = StringField("First name", validators=[DataRequired(), Length(min=2, max=55)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(min=2, max=55)])
    submit = SubmitField("Register now")

    def validate_email(self, email):
        user = User.objects(email = email.data).first()
        if user:
            raise ValidationError('Correo registrado anteriormente')