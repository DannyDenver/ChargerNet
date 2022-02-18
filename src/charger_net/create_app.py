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
from sqlalchemy.exc import SQLAlchemyError
from charger_net.models import *

env_config = dotenv_values(".env")

def create_app(test_configure=None):
  app = Flask(__name__)
  excel.init_excel(app) 

  moment = Moment(app)
  app.config.from_object('config')
  db = SQLAlchemy(app)
  migrate = Migrate(app, db)
    
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

  from charger_net.models import db
  db.init_app(app)

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
    
  # @app.route('/simple-login')
  # def simple_login(): 
  #   return auth0.

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
    error = False
    userForm = UserForm(request.form)

    if not userForm.validate():
      print('not valid')
      return render_template('pages/create_profile.html', user_profile=session['profile'], userForm=userForm)
    
    if session['jwt_payload'] and session['jwt_payload']['picture']:
      profile_photo = session['jwt_payload']['picture']
    else: 
      profile_photo = None

    if request.form.get('is_provider', None) == 'y':
      try:
        provider=Provider(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=profile_photo, mailing_address=request.form['mailing_address'], kwh_provided=0)

        db.session.add(provider)
        db.session.commit()
        session['user_profile'] = {
            'user_id': provider.id,
            'name': provider.name,
            'picture': profile_photo,
            'isProvider': True
          }
      except SQLAlchemyError as e:
        error = str(e.__dict__['orig']) 
        print(error)
        db.session.rollback()
        print('error')
      finally:
        db.session.close()

    else: 
      try:
        driver=Driver(oauth_id=session['jwt_payload']['sub'], name=request.form['name'], phone_number=request.form['phone_number'], profile_photo=profile_photo)
        db.session.add(driver)
        db.session.commit()
      except:
        db.session.rollback()
      finally:
        db.session.close()
        session['user_profile'] =  {
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

  return app

if __name__ == '__main__':
    create_app()