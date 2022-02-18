import datetime

import charger_net.models as models

def test_new_driver():
    """
    GIVEN a Driver model
    WHEN a new Driver is created
    THEN check the oauth_id, name, phone_number and frequent_charger fields are defined correctly
    """
    
    driver = models.Driver(oauth_id="ab32", name="Dan Driver", phone_number="303-434-5555", profile_photo="www.profilefoto.com/me", frequent_charger=True, total_kwh_consumed=4)
    assert driver.oauth_id == 'ab32'
    assert driver.name == 'Dan Driver'
    assert driver.phone_number == "303-434-5555"
    assert driver.frequent_charger != False

def test_new_provider():
    """
    GIVEN a Provider model
    WHEN a new Provid er is created
    THEN check the oauth_id, name, phone_number, profile_photo, kwh_provided and mailing_address fields are defined correctly
    """
    provider = models.Provider(oauth_id="ab543", name="Dan Provider", phone_number="303-434-5557", profile_photo="www.profilefoto.com/me2", mailing_address="443 Grove Street", kwh_provided=1434)
    assert provider.oauth_id == 'ab543'
    assert provider.name == 'Dan Provider'
    assert provider.phone_number == "303-434-5557"
    assert provider.profile_photo == "www.profilefoto.com/me2"
    assert provider.kwh_provided == 1434
    assert provider.mailing_address == "443 Grove Street"

def test_new_car():
    """
    GIVEN a Car model
    WHEN a new Car is created
    THEN check the driver_id, make,model, year and plug_type fields are defined correctly
    """
    car = models.Car(driver_id=2, make="Mazda", model="3s", year=2014, plug_type="Chademo")
    assert car.driver_id == 2
    assert car.make == 'Mazda'
    assert car.model == "3s"
    assert car.year == 2014
    assert car.plug_type == "Chademo"

def test_new_reservation():
    """
    GIVEN a Reservation model
    WHEN a new Reservation is created
    THEN check the driver_id, car_id, charger_id,end_time and start_time fields are defined correctly
    """
    res = models.Reservation(driver_id=2, car_id=4, charger_id=5, start_time=datetime.datetime(2022, 5, 17), end_time=datetime.datetime(2022, 5, 18))
    assert res.driver_id == 2
    assert res.car_id == 4
    assert res.charger_id == 5
    assert res.start_time == datetime.datetime(2022, 5, 17)
    assert res.end_time == datetime.datetime(2022, 5, 18)

def test_new_charger():
    """
    GIVEN a Charger model
    WHEN a new Charger is created
    THEN check the provider_id,charger_type,location_longitude,location_latitude,plug_type,covered_parking fields are defined correctly
    """
    charger = models.Charger(provider_id=2, charger_type="chademo", location_longitude='101.43', location_latitude="-53.4", plug_type="Type 3", covered_parking=True, )
    assert charger.provider_id == 2
    assert charger.charger_type == "chademo"
    assert charger.location_longitude == "101.43"
    assert charger.location_latitude == "-53.4"
    assert charger.plug_type == "Type 3"
    assert charger.covered_parking == True