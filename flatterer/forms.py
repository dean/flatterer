from flask.ext.wtf import (Form, TextField, PasswordField, BooleanField,
                           SelectField)
from flask.ext.wtf import Required, Email, EqualTo
from models import User


class Register(Form):
    """Registration form."""
    name = TextField('name', [Required()])
    username = TextField('username', [Required()])
    password = PasswordField('password', [Required()])
    confirm_pass = PasswordField('confirm_pass', [Required()])
    admin = BooleanField('admin', default=False)


class AddComplimentee(Form):
    """Form to add a complimentee."""
    name = TextField('name', [Required()])
    url = TextField('url', [Required()])
    greeting = TextField('greeting')


class AddTheme(Form):
    """Add a theme for a given user."""
    theme_path = TextField('theme_path')
    song_path = TextField('song_path')


class AddCompliment(Form):
    """Adds a compliment for a given user."""
    compliment = TextField('compliment', [Required()])
    gender = SelectField('gender', choices=[('Male', 'Male'),
                                            ('Female', 'Female'),
                                            ('Any', 'Any')])


class AddGender(Form):
    """Adds a gender to the database."""
    gender = SelectField('gender', choices=[('Male', 'Male'),
                                            ('Female', 'Female'),
                                            ('Any', 'Any')])


class Get_Info(Form):
    """Gets information to prepare a compliment."""
    name = TextField('name', [Required()])
    gender = SelectField('gender', choices=[('Male', 'Male'),
                                            ('Female', 'Female')])


class LoginForm(Form):
    """Allows users to login."""
    username = TextField('name', [Required()])
    password = PasswordField('password', [Required()])
