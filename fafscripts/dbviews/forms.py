from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     SelectField, SelectMultipleField, StringField, TextAreaField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class FilmInputForm(FlaskForm):
    # programme = SelectField("Select a programme:", validators=[DataRequired()])
    # norwegian_mode = BooleanField("Norwegian mode")
    english_title = StringField('English title:')
    original_title = StringField('Original title:')
    technique = StringField('Technique(s):')
    synopsis = TextAreaField('Synopsis:')
    # address = TextAreaField('Your address:', validators=[DataRequired()])
    year = SelectField('Year:')
    submit = SubmitField('Run')
