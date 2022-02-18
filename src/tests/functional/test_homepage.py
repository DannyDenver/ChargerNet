from flask import session

def test_index(client):
    response = client.get("/")
    assert b"Charger NET" in response.data

def test_username_on_homepage(client):
    response = client.get("/")
    assert session.get('profile', None) is not None

    assert session.get('user_profile', None) is not None
    assert b"Test User" in response.data

def test_charger_register(client):
    response = client.get("/chargers/register")
    assert b"Register your charger" in response.data

def test_charger_registration_redirect(client): 
    res = client.post('/chargers/register', data=dict(
        charger_type="Level 1",
        location_longitude='-102',
        location_latitude="40.21",
        plug_type="CSS",
        covered_parking=True
    ), follow_redirects=True)

    assert b"Test User's Chargers" in res.data
    assert b'div id="map" style="height: 500px"' in res.data

def test_provider_unauthoroized_car_register(client):
    res = client.get('/cars/register')
    assert b'You should be redirected automatically to target' in res.data


def test_logout(client):
    response = client.get("/logout")
    assert session.get('user_profile', None) is None
    assert session.get('profile', None) is None





