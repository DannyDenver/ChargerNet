import pytest
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, make_response
from dotenv import dotenv_values
import os
import charger_net.create_app as charger_net
from flask import session
import charger_net.models as models
from charger_net.models import db


@pytest.fixture(scope="module")
def client():
    app = charger_net.create_app()

    ctx = app.app_context()
    ctx.push()


    ctx = app.app_context()
    ctx.push()

    with app.test_client() as client:
        with client.session_transaction() as session:
            session['profile'] = {
            'user_id': "auth0|620eeb30c41ff0007284ec6f",
            'name': 'Test User',
            'picture': 'testphoto.png'
            }

            session['user_profile'] = {
                'user_id': 1,
                'name': 'Test User',
                'picture': 'testphoto.png',
                'isProvider': True
            }
        yield client

@pytest.fixture(scope="module")
def driver_client():
    app = charger_net.create_app()

    ctx = app.app_context()
    ctx.push()


    ctx = app.app_context()
    ctx.push()

    with app.test_client() as client:
        with client.session_transaction() as session:
            session['profile'] = {
            'user_id': "auth0|620eeb30c41ff0007284ec6f",
            'name': 'Test Driver',
            'picture': 'testphoto.png'
            }

            session['user_profile'] = {
                'user_id': 1,
                'name': 'Test Driver',
                'picture': 'testphoto.png',
                'isProvider': False
            }
        yield client

@pytest.fixture(scope="module")
def last_reservation(driver_client):
    yield db.session.query(models.Reservation).filter_by(start_time='2022-02-21 00:00:00', end_time='2022-02-23 00:00:00').first()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
