from flask_table import Table, Col, ButtonCol

class CarTable(Table):
    classes=['table']
    id = Col('ID')
    make = Col('Make')
    model = Col('Model')
    year = Col('Year')
    plug_type = Col('Plug Type')
    delete = ButtonCol('Delete', 'your_car_delete', url_kwargs=dict(id='id'), anchor_attrs={'class': 'btn btn-warning'})

