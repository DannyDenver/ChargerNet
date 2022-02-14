import pytest
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, make_response


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config.from_object('config')
    
    db = SQLAlchemy(app)
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_request_example(client):
    response = client.get("/")
    assert b'<p class="lead">Where EV Drivers find Chargers.</p>' in response.data