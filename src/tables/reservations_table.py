from flask_table import Table, Col, ButtonCol

class ReservationTable(Table):
    classes=['table']
    id = Col('ID')
    driver_name = Col('Driver Name')
    car = Col('Car')
    charger_id = Col('Charger ID')
    location = Col('Location')
    start_time = Col('Start Time')
    end_time = Col('End Time')
    delete = ButtonCol('Delete', 'your_reservation_delete', url_kwargs=dict(id='id'), anchor_attrs={'class': 'btn btn-warning'})

class ReservationTableItem(object):
    def __init__(self,id, driver_name, car, charger_id, location, start, end):
        self.id = id
        self.driver_name = driver_name
        self.car = car
        self.charger_id = charger_id
        self.location = location,
        self.start_time = start
        self.end_time = end 

class ReservationDriverTable(Table):
    classes=['table']
    id = Col('ID')
    provider_name = Col('Provider Name')
    charger_id = Col('Charger ID')
    car = Col('Car')
    location = Col('Location')
    start_time = Col('Start Time')
    end_time = Col('End Time')
    delete = ButtonCol('Delete', 'your_reservation_delete', url_kwargs=dict(id='id'), anchor_attrs={'class': 'btn btn-warning'})

class ReservationDriverTableItem(object):
    def __init__(self,id, provider_name, charger_id, car, location, start, end):
        self.id = id
        self.provider_name = provider_name
        self.charger_id = charger_id
        self.car = car
        self.location = location
        self.start_time = start
        self.end_time = end

