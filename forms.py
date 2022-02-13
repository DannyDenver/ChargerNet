from datetime import datetime
from flask_wtf import Form
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL, InputRequired, Regexp

car_makes = ["Abarth",
            "Alfa Romeo",
            "Aston Martin",
            "Audi",
            "Bentley",
            "BMW",
            "Bugatti",
            "Cadillac",
            "Chevrolet",
            "Chrysler",
            "Citroën",
            "Dacia",
            "Daewoo",
            "Daihatsu",
            "Dodge",
            "Donkervoort",
            "DS",
            "Ferrari",
            "Fiat",
            "Fisker",
            "Ford",
            "Honda",
            "Hummer",
            "Hyundai",
            "Infiniti",
            "Iveco",
            "Jaguar",
            "Jeep",
            "Kia",
            "KTM",
            "Lada",
            "Lamborghini",
            "Lancia",
            "Land Rover",
            "Landwind",
            "Lexus",
            "Lotus",
            "Maserati",
            "Maybach",
            "Mazda",
            "McLaren",
            "Mercedes-Benz",
            "MG",
            "Mini",
            "Mitsubishi",
            "Morgan",
            "Nissan",
            "Opel",
            "Peugeot",
            "Porsche",
            "Renault",
            "Rolls-Royce",
            "Rover",
            "Saab",
            "Seat",
            "Skoda",
            "Smart",
            "SsangYong",
            "Subaru",
            "Suzuki",
            "Tesla",
            "Toyota",
            "Volkswagen",
            "Volvo"]

plug_choices = [('Type 1', 'Type 1'),('Type 2', 'Type 2'), ('CSS', 'CSS'), ('CHAdeMO', 'CHAdeMO')]

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
        validators=[InputRequired("Please select a charger type.")])
    location_longitude = StringField(
        'location_longitude', validators=[InputRequired("Please enter a GPS longitude.")]
    )
    location_latitude = StringField(
        'location_latitude', validators=[InputRequired("Please enter a GPS latitude.")]
    )
    plug_type = SelectField('Plug Type',
        choices=[('Type 1', 'Type 1'),('Type 2', 'Type 2'), ('CSS', 'CSS'), ('CHAdeMO', 'CHAdeMO')],
        validators=[InputRequired("Please select a charger type.")])
    covered_parking = BooleanField()

class CarRegistrationForm(Form):
    make = SelectField("Make",
        choices=[(g, g) for g in car_makes],
            validators=[InputRequired("Please select a car make.")])
    model = StringField(
        'model', validators=[InputRequired("Please enter a car model.")]
    )
    year = IntegerField(
        'year', validators=[InputRequired()]
    )
    plug_type = SelectField('Plug Type',
        choices=[('Type 1', 'Type 1'),('Type 2', 'Type 2'), ('CSS', 'CSS'), ('CHAdeMO', 'CHAdeMO')],
        validators=[InputRequired("Please select a charger type.")])
