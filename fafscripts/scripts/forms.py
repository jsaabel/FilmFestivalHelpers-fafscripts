from xmlrpc.client import Boolean
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     SelectField, SelectMultipleField, StringField, TextAreaField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class CatalogueCategoryChoiceForm(FlaskForm):
    categories = SelectMultipleField(
        "Select categories to export:", validators=[DataRequired()])
    programmes = SelectMultipleField(
        "(Optional: Choose specific short film programmes to export.)")
    text = BooleanField("Export text: ", default=True)
    img = BooleanField("Export images: ", default=True)
    submit = SubmitField('Run')


class DBChoiceForm(FlaskForm):
    db = SelectField("Select db to analyze:", choices=["Films", "Guests",
                                                       "Events", "Catalogue"],
                     validators=[DataRequired()])
    submit = SubmitField('Run')


class ProgrammeChoiceForm(FlaskForm):
    programme = SelectField("Select a programme:", validators=[DataRequired()])
    norwegian_mode = BooleanField("Norwegian mode")
    submit = SubmitField('Run')


class GuestChoiceForm(FlaskForm):
    name = SelectField("Select guest:", validators=[DataRequired()])
    all = BooleanField("Export all")
    pdf = BooleanField("Convert to pdf")
    submit = SubmitField('Run')


class PassBucketChoiceForm(FlaskForm):
    pass_buckets = SelectMultipleField(
        "Select pass buckets to export:", validators=[DataRequired()])
    day_diff = SelectField("Only export passes from the past x days (-1 for all): ",
                           validators=[DataRequired()])
    sort = SelectField("Sort/beginning of filename: ")
    submit = SubmitField('Run')


class SimpleSubmitForm(FlaskForm):
    submit = SubmitField('Run')


class SimpleInputForm(FlaskForm):
    link = StringField('Enter link:')
    submit = SubmitField('Run')


class ReimbursementsForm(FlaskForm):
    name = SelectField("Select name:", validators=[DataRequired()])
    address = TextAreaField('Your address:', validators=[DataRequired()])
    account_number = StringField(
        'Your account number:', validators=[DataRequired()])
    id_number = StringField('Your id number:', validators=[DataRequired()])
    export_files = BooleanField("Export all files")
    submit = SubmitField('Run')


class VenueChoiceForm(FlaskForm):
    venues = SelectMultipleField(
        "Select venues to export:", validators=[DataRequired()])
    combine = BooleanField("Combine into one document: ")
    submit = SubmitField('Run')


class VirtualScreeningForm(FlaskForm):
    programmes = SelectMultipleField(
        "Select programme(s) to include in screening: ", validators=[DataRequired()])
    geo_blocking = SelectField(
        "Select geoblocking level: ", validators=[DataRequired()])
    submit = SubmitField('Run')
