from datetime import datetime
from flask_wtf import Form
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL, InputRequired, Regexp

class ShowForm(Form):
    artist_id = IntegerField(
        'artist_id', validators=[InputRequired()]
    )
    venue_id = IntegerField(
        'venue_id', validators=[InputRequired()]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default= datetime.today()
    )


class UserForm(Form):
    name = StringField(
        'name', validators=[InputRequired("Please enter a name.")]
    )
    phone_number = StringField(
        'phone_number', validators=[Regexp('^[2-9]\d{2}-\d{3}-\d{4}$', 0, 'Use pattern `XXX-XXX-XXXX`')]
    )
    mailing_address = StringField(
        'mailing_address', validators=[InputRequired("Please enter a mailing address.")]
    )
    is_provider = BooleanField()
    


class DriverForm(Form):
    name = StringField(
        'name', validators=[InputRequired("Please enter a name.")]
    )
    phone_number = StringField(
        'phone_number', validators=[Regexp('^[2-9]\d{2}-\d{3}-\d{4}$', 0, 'Use pattern `XXX-XXX-XXXX`')]
    )

class ChargerRegistrationForm(Form):
    charger_type = SelectField('Charger Type',
        choices=[('Level 1', 'Level 1'), ('Level 2', 'Level 2'), ('Level 3', 'Level 3')],
        validators=[InputRequired("Please enter a charger type.")])
    location_longitude = StringField(
        'location_longitude', validators=[InputRequired("Please enter a GPS longitude.")]
    )
    location_latitude = StringField(
        'location_latitude', validators=[InputRequired("Please enter a GPS latitude.")]
    )
    covered_parking = BooleanField()
