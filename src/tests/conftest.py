import pytest
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, make_response
from dotenv import dotenv_values
import os
import charger_net.create_app as charger_net
from flask import session


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


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

# @pytest.fixture
# def client():
#     app = charger_net.create_app.create_app()
#     ctx = app.app_context()
#     ctx.push()

#     print(app)

#     session['profile'] = {
#         'user_id': "auth0|620eeb30c41ff0007284ec6f",
#         'name': 'Test User',
#         'picture': 'testphoto.png'
#     }

#     session['user_profile'] = {
#         'user_id': 1,
#         'name': 'Test User',
#         'picture': 'testphoto.png',
#         'isProvider': True
#     }

#     with ctx:
#         pass

#     with app.test_client() as client:
#         yield client


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test"):
        return self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)