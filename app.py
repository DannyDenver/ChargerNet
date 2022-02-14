#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, make_response
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
from datetime import datetime, date
from sqlalchemy.orm import registry, declared_attr
from authlib.integrations.flask_client import OAuth
from functools import wraps
from flask import session
from six.moves.urllib.parse import urlencode
from dotenv import dotenv_values
from tables.charger_table import ChargerTable
from tables.cars_table import CarTable
from tables.reservations_table import ReservationTable, ReservationTableItem, ReservationDriverTableItem, ReservationDriverTable
from sqlalchemy.orm import backref
import flask_excel as excel

env_config = dotenv_values(".env")
#----------------------------------------------------------------------------#
# App Config. 
#----------------------------------------------------------------------------#
def create_app(env_config):
  app = Flask(__name__)
  excel.init_excel(app) 
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

  return (app, db, auth0)

app, db, auth0 = create_app(env_config)


    
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
    try:
      provider=Provider(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=session['jwt_payload']['picture'], mailing_address=request.form['mailing_address'])
      db.session.add(provider)
      db.session.commit()
      session['user_profile'] = {
          'user_id': provider.id,
          'name': provider.name,
          'picture': provider.profile_photo,
          'isProvider': True
        }
    except:
      db.session.rollback()
    finally:
      db.session.close()

  else: 
    try:
      driver=Driver(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=session['jwt_payload']['picture'])
      db.session.add(driver)
      db.session.commit()
      session['user_profile'] = {
          'user_id': driver.id,
          'name': driver.name,
          'picture': driver.profile_photo,
          'isProvider': False
        }
    except:
      db.session.rollback()
    finally:
      db.session.close()

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

  try:
    charger=Charger(provider_id=session['user_profile']['user_id'], charger_type=request.form.get('charger_type'), plug_type=request.form.get('plug_type'), location_latitude=request.form.get('location_latitude'), location_longitude=request.form.get('location_longitude'), covered_parking=True if request.form.get('covered_parking') is 'y' else False)
    db.session.add(charger)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('your_chargers'))


@app.route('/chargers/your-chargers', methods=["GET"])
@requires_auth
def your_chargers():
  chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
  charger_table = ChargerTable(chargers)

  return render_template('pages/your_chargers.html', chargers=chargers, table=charger_table, user_profile=session['user_profile'])

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

  try:
    car=Car(driver_id=session['user_profile']['user_id'], make=request.form.get('make'), model=request.form.get('model'), year=request.form.get('year'), plug_type=request.form.get('plug_type'))
    db.session.add(car)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

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

  try:
    reservation=Reservation(driver_id=session['user_profile']['user_id'], car_id=request.form.get('car_id'), charger_id=request.form.get('charger_id'), start_time=request.form.get('start_time'), end_time=request.form.get('end_time'))
    db.session.add(reservation)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  
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
    db.session.query(Reservation).filter_by(id=id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('your_reservations'))

@app.route('/download-reservations')
@requires_auth
def download_reservations():
  data = []

  if session.get('user_profile').get('isProvider'):
    chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
    ids = [charger.id for charger in chargers]
    reservations = Reservation.query.filter(Reservation.charger_id.in_(ids)).order_by(Reservation.start_time).all()
    data.append([f"Reservation Report for {session['user_profile']['name']}"])
    data.append([f"Created on {date.today()}"])
    data.append([])
    
    data.append(["Reservation ID", "Driver", "Car", "Charger ID", "Latitude", "Longitude", "Start", "End"])

    for res in reservations:
      data.append([res.id, res.reservation_driver.name, f'{res.reservation_car.make} - {res.reservation_car.model}', res.charger_id, res.reservation_charger.location_latitude, res.reservation_charger.location_longitude, res.start_time, res.end_time])
    
    output = excel.make_response_from_array(data, 'csv')
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output
  else:
    reservations = Reservation.query.filter(Reservation.driver_id==session['user_profile']['user_id']).order_by(Reservation.start_time).all()
    data.append([f"Reservation Report for {session['user_profile']['name']}"])
    data.append([f"Created on {date.today()}"])
    data.append([])
    
    data.append(["Reservation ID", "Provider", "Car", "Charger ID", "Latitude", "Longitude", "Start", "End"])

    for res in reservations:
      data.append([res.id, res.reservation_charger.provider.name, f'{res.reservation_car.make} - {res.reservation_car.model}', res.charger_id, res.reservation_charger.location_latitude, res.reservation_charger.location_longitude, res.start_time, res.end_time])
  
    output = excel.make_response_from_array(data, 'csv')
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

    # if session.get('user_profile').get('isProvider'):
    #   chargers = Charger.query.filter(Charger.provider_id==session.get('user_profile').get('user_id')).all()
    #   ids = [charger.id for charger in chargers]
    #   reservations = Reservation.query.filter(Reservation.charger_id.in_(ids)).order_by(Reservation.start_time).all()

    #   for res in reservations:
    #     cw.writerow({'reservation id': res.id, 'start time': res.start_time})
    #   output = make_response(si.getvalue())
    #   output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    #   output.headers["Content-type"] = "text/csv"
    #   return output
    # else:
    #   reservations = Reservation.query.filter(Reservation.driver_id==session['user_profile']['user_id']).order_by(Reservation.start_time).all()
    #   for res in reservations:
    #     cw.writerow({'reservation id': res.id, 'start time': res.start_time})
    #   output = make_response(si.getvalue())
    #   output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    #   output.headers["Content-type"] = "text/csv"
    #   return output

# Default port:
if __name__ == '__main__':
    app.run()
