from flask_table import Table, Col, ButtonCol

class ChargerSearchResultTable(Table):
    classes=['table']
    id = Col('Charger ID')
    charger_type = Col('Charger Type')
    plug_type = Col('Plug Type')
    location_latitude = Col('Location Latitude')
    location_longitude = Col('Location Longitude')
    covered_parking = Col('Covered Parking?')

