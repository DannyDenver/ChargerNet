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

def test_provider_chargers(client):
    res = client.get("/chargers/your-chargers")
    assert b"Test User's Chargers" in res.data

def test_add_charger(client):
    res = client.post('/chargers/register', data=dict(
        charger_type="Level 1",
        location_longitude="-102.432",
        location_latitude="40.321",
        plug_type="CSS",
        covered_parking=True
    ), follow_redirects=True)
    assert b"Test User's Chargers" in res.data

def test_provider_unauthoroized_car_register(client):
    res = client.get('/cars/register')
    assert b'You should be redirected automatically to target' in res.data

def test_get_chargers(client):
    res = client.get('/chargers')
    assert b'<div id="map" style="height: 500px"></div>' in res.data

def test_get_single_charger(client):
    res = client.get('/chargers/2')
    assert b'<h1>Charger ID: 2</h1>' in res.data
    assert b'<h1>Charger ID: 3</h1>' not in res.data

def test_get_reservations(client):
    res = client.get('/your-reservations')
    assert b"<h2>Test User's Upcoming Reservations</h2>" in res.data

def test_reserve_charger_start_after_end_time_error(driver_client):
    res = driver_client.post('/chargers/2', data=dict(
        end_time='2022-02-21 00:00:00',
        start_time='2022-02-23 00:00:00',
        car_id=1,
        charger_id=2
    ), follow_redirects=True)

    assert b"<h2>Test Driver's Upcoming Reservations</h2>" not in res.data
    assert b'Start time must be before end time' in res.data

def test_reserve_charger(driver_client):
    res = driver_client.post('/chargers/2', data=dict(
        start_time='2022-02-21 00:00:00',
        end_time='2022-02-23 00:00:00',
        car_id=1,
        charger_id=2
    ), follow_redirects=True)

    assert b"<h2>Test Driver's Upcoming Reservations</h2>" in res.data

def test_delete_reservation(driver_client, last_reservation):
    res = driver_client.post('/reservations/' + str(last_reservation.id), follow_redirects=True)

    assert b"<h2>Test Driver's Upcoming Reservations</h2>" in res.data

def test_download_reservations(driver_client):
    res = driver_client.get('/download-reservations')
    assert res is not None

def test_logout(client):
    response = client.get("/logout")
    assert session.get('user_profile', None) is None
    assert session.get('profile', None) is None





