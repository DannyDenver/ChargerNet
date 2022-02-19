ChargerNET
-----

### Introduction

Charger NET – a site where people who have electric vehicle (EV) chargers and people with EV vehicles can create a profile and register their charger or car and schedule reservations. 

The adoption of electric vehicles is being stymied by the slow build up of electric vehicle chargers. Potential EV customers are being scared away by range anxiety, ie running out of battery while they are far from a charger or are worried about long lines at the few chargers available.   Charger NET will open up EV drivers to more chargers to alleviate these anxieties, potentially lower the cost of recharging and allow EV charger providers to make some money. 


### Tech Stack

Our tech stack will include:

* **SQLAlchemy ORM** to be our ORM library of choice
* **PostgreSQL** as our database of choice
* **Python3** and **Flask** as our server language and server framework
* **Flask-Migrate** for creating and running schema migrations
* **HTML**, **CSS**, and **Javascript** with [Bootstrap 3](https://getbootstrap.com/docs/3.4/customize/) for our website's frontend

### Main Files: Project Structure

  ```sh
  ├── README.md
  ├── forms.py *** Your forms
  ├── models.py  *** Your SQL Alchemy models
  ├── requirements.txt *** The dependencies we need to install with "pip3 install -r requirements.txt"
  ├── src
      ├── app.py *** the main driver of the app. 
      │              "python app.py" to run after installing dependences
      ├── config.py
      ├── forms.py
      ├── charger_net 
      │     ├──static
      │     │    ├── css
      │     │    ├── fonts
      │     │    ├── img
      │     │    └── js
      │     ├──templates
      │     │    ├── errors
      │     │    ├── forms
      │     │    ├── layouts
      │     │    └── pages
      │     ├── create_app.py *** where the app is created
      │     └──models.py
      ├── migrations *** folder with all the sql alchemy migrations
      ├── tables
      └──tests
  ```

Overall:
* SqlAlchemy models are located in `models.py`.
* Controllers are located in `create_app.py`.
* The web frontend is located in `templates/`, which builds static assets deployed to the web server at `static/`.
* Web forms for creating data are located in `form.py`
* Tables are set up in tables folder files

Highlight folders:
* `templates/pages` -- Defines the pages that are rendered to the site. These templates render views based on data passed into the template’s view, in the controllers defined in `app.py`. These pages successfully represent the data to the user, and are already defined for you.
* `templates/layouts` -- Defines the layout that a page can be contained in to define footer and header code for a given page.
* `templates/forms` -- Defines the forms used to create new artists, shows, and venues.
* `app.py` -- Defines routes that match the user’s URL, and controllers which handle data and renders views to the user. This is the main file you will be working on to connect to and manipulate the database and render views with data to the user, based on the URL.
* `models.py` -- Defines the data models that set up the database tables.
* `config.py` -- Stores configuration variables and instructions, separate from the main application code. This is where you will need to connect to the database.

### Development Setup

First, [install Flask](http://flask.pocoo.org/docs/1.0/installation/#install-flask) if you haven't already.

  ```
  $ cd ~
  $ sudo pip3 install Flask
  ```

To start and run the local development server,

1. Initialize and activate a virtualenv:
  ```
  $ cd YOUR_PROJECT_DIRECTORY_PATH/
  $ pyton3 -m venv env
  $ source env/bin/activate
  ```

2. Install the dependencies:
  ```
  $ python -m ensurepip --upgrade
  $ pip install -r requirements.txt
  ```

3. Run the development server:
  ```
  $ export FLASK_APP=chargernet
  $ export FLASK_ENV=development # enables debug mode
  $ cd src
  $ python3 app.py

  ```

4. Navigate to Home page [http://localhost:5000](http://localhost:5000)
5. Click 'Log In' and sign in with your google account using third party Auth0