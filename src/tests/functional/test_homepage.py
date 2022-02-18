from flask import session

def test_index(client):
    response = client.get("/")
    assert b"Charger NET" in response.data

def test_username_on_homepage(client):
    response = client.get("/")
    assert session.get('profile', None) is not None

    assert session.get('user_profile', None) is not None
    assert b"Test User" in response.data

def test_logout(client):
    response = client.get("/logout")
    assert session.get('user_profile', None) is None
    assert session.get('profile', None) is None





