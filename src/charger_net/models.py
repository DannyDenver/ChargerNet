# #----------------------------------------------------------------------------#
# # Imports
# #----------------------------------------------------------------------------#

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

db = SQLAlchemy()

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
    state = db.Column(db.String(50))
    town = db.Column(db.String(50))
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
