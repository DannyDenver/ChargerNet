#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
import sys
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from sqlalchemy.orm import registry, declared_attr
from authlib.integrations.flask_client import OAuth
from functools import wraps
from flask import session
from six.moves.urllib.parse import urlencode
from dotenv import dotenv_values
from tables.charger_table import ChargerTable
from tables.cars_table import CarTable
from tables.reservations_table import ReservationTable, ReservationTableItem, ReservationDriverTableItem, ReservationDriverTable
from datetime import datetime
from sqlalchemy.orm import backref


env_config = dotenv_values(".env")
print(env_config)
#----------------------------------------------------------------------------#
# App Config. 
#----------------------------------------------------------------------------#

app = Flask(__name__)

oauth = OAuth(app)

auth0 = oauth.register(
  'auth0',
  client_id='RF0NE1fGynyjE4a4o96hwUatOVu7Iedr',
  client_secret=env_config['SECRET'],
  api_base_url='https://dev-u5hxbgvm.us.auth0.com',
  access_token_url='https://dev-u5hxbgvm.us.auth0.com/oauth/token',
  authorize_url='https://dev-u5hxbgvm.us.auth0.com/authorize',
  client_kwargs={
    'scope': 'openid profile email'
  },
)

moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
  __abstract__ = True
  oauth_id = db.Column(db.String(100))
  name = db.Column(db.String(50))
  phone_number = db.Column(db.String(20))
  profile_photo=db.Column(db.String(100))

class Driver(User):
  __tablename__='Driver'
  id = db.Column(db.Integer, primary_key=True)
  frequent_charger = db.Column(db.Boolean)
  total_kwh_consumed = db.Column(db.Integer)
  
  reservations = db.relationship("Reservation", backref=db.backref("driver", cascade="all,delete"), lazy="dynamic")
  cars = db.relationship("Car", backref=db.backref("driver", cascade="all,delete"), lazy="dynamic")

  @hybrid_property
  def upcoming_reservations(self):
    return self.reservations.filter(Reservation.start_time > datetime.now()).all()

  @hybrid_property
  def upcoming_reservation_count(self):
    return len(self.reservations.filter(Reservation.start_time > datetime.now()).all())

  @hybrid_property
  def past_reservations(self):
    return self.reservations.filter(Reservation.start_time < datetime.now()).all()

  @hybrid_property
  def past_reservation_count(self):
    return len(self.reservations.filter(Reservation.start_time < datetime.now()).all())    


  def __repr__(self):
      return '<Driver ' + str(self.id) + ' ' + self.name + ' ' + self.phone_number + '>'

class Provider(User):
  __tablename__='Provider'
  id = db.Column(db.Integer, primary_key=True)
  mailing_address = db.Column(db.String(100))
  kwh_provided = db.Column(db.Integer)

class Car(db.Model):
  __tablename__ = "Car"
  id = db.Column(db.Integer, primary_key=True)
  driver_id = db.Column(db.Integer, db.ForeignKey('Driver.id'), nullable=False)
  make = db.Column(db.String(20))
  model = db.Column(db.String(20))
  year = db.Column(db.Integer)
  plug_type = db.Column(db.String(20))
  reservations = db.relationship('Reservation', backref="car", cascade='all, delete')

class Reservation(db.Model): 
  __tablename__ = 'Reservation'
  id = db.Column(db.Integer, primary_key=True)
  driver_id = db.Column(db.Integer, db.ForeignKey('Driver.id', ondelete='CASCADE'), nullable=False)
  car_id = db.Column(db.Integer, db.ForeignKey('Car.id', ondelete='CASCADE'), nullable=False)
  charger_id = db.Column(db.Integer, db.ForeignKey('Charger.id', ondelete='CASCADE'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  end_time = db.Column(db.DateTime, nullable=False)
  reservation_driver = db.relationship("Driver", backref=backref("reservation", cascade="all,delete"))
  reservation_charger = db.relationship("Charger", backref=backref("reservation", cascade="all,delete"))
  reservation_car = db.relationship("Car", backref=backref("reservation", cascade="all,delete"))

  @hybrid_property
  def driver_name(self):
    return self.reservation_driver.name
  
  @hybrid_property
  def provider_name(self):
    return self.reservation_charger.provider_name


  def __repr__(self):
      return '<Reservation driver: ' + ' ' + self.driver_name + ' provider: ' + self.provider_name + "start time: " + str(self.start_time) + '>'



class Charger(db.Model): 
    __tablename__ = 'Charger'
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('Provider.id'), nullable=False)
    charger_type = db.Column(db.String(20))
    location_longitude = db.Column(db.String(100))
    location_latitude = db.Column(db.String(100))
    plug_type = db.Column(db.String(20))
    covered_parking = db.Column(db.Boolean)
    provider = db.relationship("Provider")
    reservations = db.relationship('Reservation', cascade='all, delete', passive_deletes=True, backref="charger")

    def __repr__(self):
        return f'<Charger {str(self.id)} type: {self.charger_type} covered parking: {str(self.covered_parking)}, lat: {self.location_latitude}, long: {self.location_longitude}>'

class InfoShort:
  def __init__(self, id, name, num_upcoming_reservations):
    self.id = id
    self.name = name
    self.num_upcoming_reservations = num_upcoming_reservations
    def __repr__(self):
        return '<vn ' + self.name + ' ' + self.num_upcoming_shows + '>'



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/callback')
def callback_handling():
    # Handles response from token endpoint
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()
    print(userinfo)

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }

    provider = Provider.query.filter(Provider.oauth_id==userinfo['sub']).first()
    driver = Driver.query.filter(Driver.oauth_id==userinfo['sub']).first()

    if provider is None and driver is None:
      print('creating profile')
      return redirect(url_for('create_profile_form'))
    
    if provider is not None:
      session['user_profile'] = {
        'user_id': provider.id,
        'name': provider.name,
        'picture': provider.profile_photo,
        'isProvider': True
      }
      return render_template('pages/home.html', user_profile=session['user_profile'])
    else:
      session['user_profile'] = {
        'user_id': driver.id,
        'name': driver.name,
        'picture': driver.profile_photo,
        'isProvider': False
      }
      return render_template('pages/home.html', user_profile=session['user_profile'])

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri='http://localhost:5000/callback')
  
def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in session:
      # Redirect to Login page here
      return redirect('/')
    return f(*args, **kwargs)

  return decorated

@app.route('/user/create', methods=['GET'])
@requires_auth
def create_profile_form():
    userForm = UserForm()
    
    print(session['jwt_payload']['sub'])

    return render_template('pages/create_profile.html',
                            user_profile=session['profile'],
                            userForm=userForm)

@app.route('/user/create', methods=['POST'])
@requires_auth
def create_profile_submission():
  print('creating profile post')
  error = False
  userForm = UserForm(request.form)

  if not userForm.validate():
    print('not valid')
    return render_template('pages/create_profile.html', user_profile=session['profile'], userForm=userForm)

  if request.form.get('is_provider', None) == 'y':
    provider=Provider(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=session['jwt_payload']['picture'], mailing_address=request.form['mailing_address'])
    db.session.add(provider)
    db.session.commit()
    session['user_profile'] = {
        'user_id': provider.id,
        'name': provider.name,
        'picture': provider.profile_photo,
        'isProvider': True
      }
  else: 
    driver=Driver(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=session['jwt_payload']['picture'])
    db.session.add(driver)
    db.session.commit()
    session['user_profile'] = {
        'user_id': driver.id,
        'name': driver.name,
        'picture': driver.profile_photo,
        'isProvider': False
      }

  return render_template('pages/home.html', user_profile=session['user_profile'])

@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('index', _external=True), 'client_id': 'RF0NE1fGynyjE4a4o96hwUatOVu7Iedr'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@app.route('/')
def index():
  if session.get('user_profile'):
    return render_template('pages/home.html', user_profile=session['user_profile'])
  
  return render_template('pages/home.html')

@app.route('/chargers/register', methods=['GET'])
@requires_auth
def register_charger_form():
  chargerForm = ChargerRegistrationForm()

  return render_template('pages/register_charger.html', chargerForm=chargerForm, user_profile=session['user_profile'])

@app.route('/chargers/register', methods=['POST'])
@requires_auth
def register_charger_submission():
  chargerForm = ChargerRegistrationForm(request.form)  

  if not chargerForm.validate():
    return render_template('pages/register_charger.html',
                          chargerForm=chargerForm)

  charger=Charger(provider_id=session['user_profile']['user_id'], charger_type=request.form.get('charger_type'), plug_type=request.form.get('plug_type'), location_latitude=request.form.get('location_latitude'), location_longitude=request.form.get('location_longitude'), covered_parking=True if request.form.get('covered_parking') is 'y' else False)
  
  db.session.add(charger)
  db.session.commit()

  return redirect(url_for('your_chargers'))


@app.route('/chargers/your-chargers', methods=["GET"])
@requires_auth
def your_chargers():
  chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
  charger_table = ChargerTable(chargers)

  return render_template('pages/your_chargers.html', table=charger_table, user_profile=session['user_profile'])

@app.route('/chargers/your-chargers/<id>', methods=["POST"])
@requires_auth
def your_chargers_delete(id):
  try:
    db.session.query(Charger).filter_by(provider_id=session.get('user_profile').get('user_id')).filter_by(id=id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
  charger_table = ChargerTable(chargers)

  return render_template('pages/your_chargers.html', table=charger_table, user_profile=session['user_profile'])

@app.route('/cars/register', methods=['GET'])
@requires_auth
def register_car_form():
  carForm = CarRegistrationForm()

  return render_template('pages/register_car.html', carForm=carForm, user_profile=session['user_profile'])

@app.route('/cars/register', methods=['POST'])
@requires_auth
def register_car_submission():
  carForm = CarRegistrationForm(request.form)

  if not carForm.validate():
    return render_template('pages/register_car.html',
                          carForm=carForm)

  car=Car(driver_id=session['user_profile']['user_id'], make=request.form.get('make'), model=request.form.get('model'), year=request.form.get('year'), plug_type=request.form.get('plug_type'))
  db.session.add(car)
  db.session.commit()

  cars = Car.query.filter(Car.driver_id==session['user_profile']['user_id']).all()
  cars_table = CarTable(cars)

  return render_template('pages/your_cars.html', table=cars_table, user_profile=session['user_profile'])

@app.route('/cars', methods=["GET"])
@requires_auth
def your_cars():
  cars = Car.query.filter(Car.driver_id==session['user_profile']['user_id']).all()
  cars_table = CarTable(cars)

  return render_template('pages/your_cars.html', table=cars_table, user_profile=session['user_profile'])

@app.route('/cars/<id>', methods=["POST"])
@requires_auth
def your_car_delete(id):
  try:
    db.session.query(Car).filter_by(driver_id=session['user_profile']['user_id']).filter_by(id=id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  cars = Car.query.filter(Car.driver_id==session['user_profile']['user_id']).all()
  cars_table = CarTable(cars)

  return render_template('pages/your_cars.html', table=cars_table, user_profile=session['user_profile'])

@app.route('/chargers', methods=["GET"])
@requires_auth
def find_charger():
  chargers = Charger.query.all()

  return render_template('pages/find_charger.html', chargers=chargers, user_profile=session['user_profile'])

@app.route('/chargers/<id>', methods=["GET"])
@requires_auth
def reserve_charger(id):
  charger = Charger.query.get(id)

  cars = Car.query.filter_by(driver_id=session['user_profile']['user_id']).filter_by(plug_type=charger.plug_type).all()

  return render_template('pages/reserve_charger.html', charger=charger, cars=cars, user_profile=session['user_profile'])

@app.route('/chargers/<id>', methods=["POST"])
@requires_auth
def reserve_charger_submission(id):
  charger = Charger.query.get(id)
  time_error = []

  if request.form.get('start_time') > request.form.get('end_time'):
    time_error.append('Start time must be before end time')
    cars = Car.query.filter_by(driver_id=session['user_profile']['user_id']).filter_by(plug_type=charger.plug_type).all()
    return render_template('pages/reserve_charger.html', charger=charger, cars=cars, time_error=time_error, user_profile=session['user_profile'])



  reservation=Reservation(driver_id=session['user_profile']['user_id'], car_id=request.form.get('car_id'), charger_id=request.form.get('charger_id'), start_time=request.form.get('start_time'), end_time=request.form.get('end_time'))
  
  db.session.add(reservation)
  db.session.commit()
  
  return redirect(url_for('your_reservations'))


@app.route('/your-reservations', methods=['GET'])
@requires_auth
def your_reservations():
  past_reservation_table_items = []
  upcoming_reservation_table_items = []
  if session['user_profile']['isProvider'] == True:
    chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
    
    ids = [charger.id for charger in chargers]
    reservations = Reservation.query.filter(Reservation.charger_id.in_(ids)).order_by(Reservation.start_time).all()
    for res in reservations:
      location = str(res.reservation_charger.location_latitude + ", " + res.reservation_charger.location_longitude)
      if res.end_time < datetime.now():
        past_reservation_table_items.append(ReservationTableItem(res.id, res.reservation_driver.name, f'{res.reservation_car.make} - {res.reservation_car.model}', res.charger_id, location, res.start_time, res.end_time))
      else: 
        upcoming_reservation_table_items.append(ReservationTableItem(res.id, res.reservation_driver.name, f'{res.reservation_car.make} - {res.reservation_car.model}', res.charger_id, location, res.start_time, res.end_time))

    past_reservation_table = ReservationTable(past_reservation_table_items)
    upcoming_reservation_table = ReservationTable(upcoming_reservation_table_items)
  else:
    reservations = Reservation.query.filter(Reservation.driver_id==session['user_profile']['user_id']).order_by(Reservation.start_time).all()
    for res in reservations:
      location = str(res.reservation_charger.location_latitude + ", " + res.reservation_charger.location_longitude)
      if res.end_time < datetime.now(): 
        past_reservation_table_items.append(ReservationDriverTableItem(res.id, res.reservation_charger.provider.name, res.charger_id, f'{res.reservation_car.make} - {res.reservation_car.model}', location, res.start_time, res.end_time))
      else: 
        upcoming_reservation_table_items.append(ReservationDriverTableItem(res.id, res.reservation_charger.provider.name, res.charger_id, f'{res.reservation_car.make} - {res.reservation_car.model}', location, res.start_time, res.end_time))

    past_reservation_table = ReservationDriverTable(past_reservation_table_items)
    upcoming_reservation_table = ReservationDriverTable(upcoming_reservation_table_items)

  return render_template('pages/your_reservations.html', upcoming_reservation_table=upcoming_reservation_table, reservations=reservations, past_reservation_table=past_reservation_table, user_profile=session['user_profile'])

@app.route('/reservations/<id>', methods=["POST"])
@requires_auth
def your_reservation_delete(id):
  try:
    print(id)
    db.session.query(Reservation).filter_by(id=id).delete()
    db.session.commit()
  except:
    print('exception thrown')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('your_reservations'))

#  Venues
#  ----------------------------------------------------------------

# @app.route('/chargers')
# def venues():
#   unique_locations = []
#   areas = []

#   for venue in Venue.query.all():
#     if [venue.city, venue.state] not in unique_locations:
#       unique_locations.append([venue.city, venue.state])
#       venuesInLoc = Venue.query.filter_by(city=venue.city).filter_by(state=venue.state)
#       vnShort = []
#       for vn in venuesInLoc:
#         vnShort.append(InfoShort(vn.id, vn.name, vn.upcoming_shows_count))
#       areas.append(Area(venue.city, venue.state, vnShort))

#   return render_template('pages/venues.html', areas=areas)

# @app.route('/venues/search', methods=['POST'])
# def search_venues():
#   search_term=request.form.get('search_term')
#   venues=Venue.query.filter(func.lower(Venue.name).contains(func.lower(search_term))).all()

#   venuesShort = []
#   for vn in venues:
#     venuesShort.append(InfoShort(vn.id, vn.name, vn.upcoming_shows_count))

#   response={
#     "count": len(venuesShort),
#     "data": venuesShort
#   }
#   return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

# @app.route('/venues/<int:venue_id>')
# def show_venue(venue_id):
#   # shows the venue page with the given venue_id
#   return render_template('pages/show_venue.html', venue=Venue.query.get(venue_id))

# #  Create Venue
# #  ----------------------------------------------------------------

# @app.route('/charger/create', methods=['GET'])
# def create_venue_form():
#   form = VenueForm()
#   form.validate_on_submit()
#   return render_template('forms/new_venue.html', form=form)

# @app.route('/venues/create', methods=['POST'])
# def create_venue_submission():
#   error = False
#   print(request.form)

#   venueForm = VenueForm(request.form)
#   if not venueForm.validate():
#     return render_template('forms/new_venue.html', form=venueForm)

#   duplicate = Venue.query.filter(func.lower(Venue.name)==func.lower(request.form['name'])).first()
#   print(duplicate)
#   if duplicate:
#     print('duplicate venue')
#     flash('Venue already created. Duplicate venue not added.', 'error')
#     return render_template('pages/home.html')

#   try:
#     venue=Venue(name=request.form['name'], city=request.form['city'], state=request.form['state'], address=request.form['address'], phone=request.form['phone'], website=request.form['website'], genres=request.form.getlist('genres'), facebook_link=request.form['facebook_link'], image_link=request.form['image_link'])
#     db.session.add(venue)
#     db.session.commit()
#   except:
#     db.session.rollback()
#     error = True
#     print(sys.exc_info())
#   finally:
#     db.session.close()

#   if error:
#     flash('An error occurred. Venue ' + request.form["name"] + ' could not be listed.', 'error')
#   if not error:
#     flash('Venue ' + request.form['name'] + ' was successfully listed!')

#   return render_template('pages/home.html')

# @app.route('/venues/<venue_id>', methods=['DELETE'])
# def delete_venue(venue_id):
#   try:
#     db.session.query(Venue).filter_by(id=venue_id).delete()
#     db.session.commit()
#   except:
#     db.session.rollback()
#   finally:
#     db.session.close()
#   return jsonify({ 'success': True })

# #  Artists
# #  ----------------------------------------------------------------
# @app.route('/artists')
# def artists():
#   return render_template('pages/artists.html', artists=Artist.query.all())

# @app.route('/artists/search', methods=['POST'])
# def search_artists():
#   search_term=request.form.get('search_term')
#   artists=Artist.query.filter(func.lower(Artist.name).contains(func.lower(search_term))).all()

#   artistInfo = []
#   for art in artists:
#     artistInfo.append(InfoShort(art.id, art.name, art.upcoming_shows_count))
  
#   response={
#     "count": len(artistInfo),
#     "data": artistInfo
#   }
#   return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# @app.route('/artists/<int:artist_id>')
# def show_artist(artist_id):
#   # shows the venue page with the given venue_id
#   artist=Artist.query.get(artist_id)
#   return render_template('pages/show_artist.html', artist=artist)

# #  Update
# #  ----------------------------------------------------------------
# @app.route('/artists/<int:artist_id>/edit', methods=['GET'])
# def edit_artist(artist_id):
#   artist = Artist.query.get(artist_id)
#   form = ArtistForm()
#   return render_template('forms/edit_artist.html', form=form, artist=artist)

# @app.route('/artists/<int:artist_id>/edit', methods=['POST'])
# def edit_artist_submission(artist_id):
#   artistForm = ArtistForm(request.form)

#   if not artistForm.validate():
#     artist = Artist.query.get(artist_id)
#     return render_template('forms/edit_artist.html', form=artistForm, artist=artist)

#   try:
#     artist = Artist.query.get(artist_id)
#     artist.name = request.form['name']
#     artist.city = request.form['city']
#     artist.state = request.form['state']
#     artist.phone = request.form['phone']
#     artist.genres = request.form.getlist('genres')
#     artist.image_link = request.form['image_link']
#     artist.facebook_link = request.form['facebook_link']
#     db.session.commit()
#   except:
#     print(sys.exc_info)
#     print("Eeeech!")
#     db.session.rollback()
#   finally:
#     db.session.close()

#   return redirect(url_for('show_artist', artist_id=artist_id))

# @app.route('/venues/<int:venue_id>/edit', methods=['GET'])
# def edit_venue(venue_id):
#   form = VenueForm()
#   venue= Venue.query.get(venue_id)
#   return render_template('forms/edit_venue.html', form=form, venue=venue)

# @app.route('/venues/<int:venue_id>/edit', methods=['POST'])
# def edit_venue_submission(venue_id):
#   venueForm = VenueForm(request.form)

#   if not venueForm.validate():
#     venue = Venue.query.get(venue_id)
#     return render_template('forms/edit_venue.html', form=venueForm, venue=venue)

#   try:
#     venue = Venue.query.get(venue_id)
#     venue.name = request.form['name']
#     venue.city = request.form['city']
#     venue.state = request.form['state']
#     venue.address = request.form['address']
#     venue.phone = request.form['phone']
#     venue.genres = request.form.getlist('genres')
#     venue.image_link = request.form['image_link']
#     venue.facebook_link = request.form['facebook_link']
#     db.session.commit()
#   except:
#     print(sys.exc_info)
#     print("Eeeech! Venue edits not saved")
#     db.session.rollback()
#   finally:
#     db.session.close()

#   return redirect(url_for('show_venue', venue_id=venue_id))

# #  Create Artist
# #  ----------------------------------------------------------------

# @app.route('/artists/create', methods=['GET'])
# def create_artist_form():
#   form = ArtistForm()
#   form.validate_on_submit()
#   return render_template('forms/new_artist.html', form=form)

# @app.route('/artists/create', methods=['POST'])
# def create_artist_submission():
#   # called upon submitting the new artist listing form
#   error = False
#   print(request.form)

#   artistForm = ArtistForm(request.form)
#   print(artistForm.errors)
#   if not artistForm.validate():
#     return render_template('forms/new_artist.html', form=artistForm)

#   duplicate = Artist.query.filter(func.lower(Artist.name)==func.lower(request.form['name'])).first()
#   print(Artist.query.filter(func.lower(Artist.name)==func.lower(request.form['name'])).first())
#   if duplicate:
#     print("duplicate")
#     print(duplicate)
#     flash('Artist already created. Duplicate artist with same name not added.', 'error')
#     return render_template('pages/home.html')

#   try:
#     artist=Artist(name=request.form['name'], city=request.form['city'], state=request.form['state'], phone=request.form['phone'], genres=request.form.getlist('genres'), facebook_link=request.form['facebook_link'], image_link=request.form['image_link'])
#     db.session.add(artist)
#     db.session.commit()
#   except:
#     db.session.rollback()
#     error = True
#     print(sys.exc_info())
#   finally:
#     db.session.close()  

#   if error:
#     flash('An error occurred. Artist ' + request.form["name"] + ' could not be listed.', 'error')
#   if not error:
#     flash('Artist ' + request.form['name'] + ' was successfully listed!')

#   return render_template('pages/home.html')

# @app.route('/artists/<artist_id>', methods=['DELETE'])
# def delete_artist(artist_id):
#   try:
#     db.session.query(Artist).filter_by(id=artist_id).delete()
#     db.session.commit()
#   except:
#     db.session.rollback()
#   finally:
#     db.session.close()
#   return jsonify({ 'success': True })

# #  Shows
# #  ----------------------------------------------------------------

# @app.route('/shows')
# def shows():
#   # displays list of shows at /shows
#   return render_template('pages/shows.html', shows=Show.query.all())

# @app.route('/shows/create')
# def create_shows():
#   # renders form. do not touch.
#   form = ShowForm()
#   return render_template('forms/new_show.html', form=form)

# @app.route('/shows/create', methods=['POST'])
# def create_show_submission():
#   # called to create new shows in the db, upon submitting new show listing form
#   error = False
#   print(request.form)

#   showForm = ShowForm(request.form)
#   if not showForm.validate():
#     return render_template('forms/new_show.html', form=showForm)

#   duplicate = Show.query.filter_by(venue_id=request.form['venue_id']).filter_by(artist_id=request.form['artist_id']).filter_by(start_time=request.form['start_time']).first()
#   if duplicate:
#     flash('Show already created. Duplicate show was not added.', 'error')
#     return render_template('pages/home.html')

#   try:
#     show = Show(venue_id=request.form['venue_id'], artist_id=request.form['artist_id'], start_time=request.form['start_time'])
#     db.session.add(show)
#     db.session.commit()
#   except:
#     db.session.rollback()
#     error = True
#     print(sys.exc_info())
#   finally:
#     db.session.close()
  
#   if error:
#     flash('An error occurred. Show could not be listed.', 'error')
#   if not error:
#     flash('Show was successfully listed!')
  
#   return render_template('pages/home.html')

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('errors/404.html'), 404

# @app.errorhandler(500)
# def server_error(error):
#     return render_template('errors/500.html'), 500


# if not app.debug:
#     file_handler = FileHandler('error.log')
#     file_handler.setFormatter(
#         Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
#     )
#     app.logger.setLevel(logging.INFO)
#     file_handler.setLevel(logging.INFO)
#     app.logger.addHandler(file_handler)
#     app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 80))
#     app.run(host='0.0.0.0', port=port)