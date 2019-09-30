from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    city = db.Column(db.String(30))
    state = db.Column(db.String(30))
    phone = db.Column(db.String(20))
    genres = db.Column(ARRAY(db.String(20)))
    image_link = db.Column(db.String(200))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref=db.backref("artist"), lazy="dynamic")

    @hybrid_property
    def upcoming_shows(self):
      return self.shows.filter(Show.start_time > datetime.now()).all()

    @hybrid_property
    def upcoming_shows_count(self):
      return len(self.shows.filter(Show.start_time > datetime.now()).all())

    @hybrid_property
    def past_shows(self):
      return self.shows.filter(Show.start_time < datetime.now()).all()

    @hybrid_property
    def past_shows_count(self):
      return len(self.shows.filter(Show.start_time < datetime.now()).all())   

    

    def __repr__(self):
        return '<Artist ' + str(self.id) + ' ' + self.name + ' ' + self.city + '>'

class Show(db.Model): 
    __tablename__ = 'show'
    
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    show_venue = db.relationship("Venue")
    show_artist = db.relationship("Artist")

    @hybrid_property
    def artist_name(self):
      return self.show_artist.name

    @hybrid_property
    def artist_image_link(self):
      return self.show_artist.image_link
    
    @hybrid_property
    def venue_name(self):
      return self.show_venue.name

    @hybrid_property
    def venue_image_link(self):
      return self.show_venue.image_link

    def __repr__(self):
        return '<Show' + ' ' + self.show_venue.name + ' ' + self.show_artist.name + ' ' + str(self.start_time) + '>'

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    city = db.Column(db.String(30))
    state = db.Column(db.String(30))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    image_link = db.Column(db.String(200))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref=db.backref("venue"))

    @hybrid_property
    def upcoming_shows(self):
      return self.shows.filter(Show.start_time > datetime.now()).all()

    @hybrid_property
    def upcoming_shows_count(self):
      return len(self.shows.filter(Show.start_time > datetime.now()).all())

    @hybrid_property
    def past_shows(self):
      return self.shows.filter(Show.start_time < datetime.now()).all()

    @hybrid_property
    def past_shows_count(self):
      return len(self.shows.filter(Show.start_time < datetime.now()).all())   

    def __repr__(self):
        return '<Venue ' + str(self.id) + ' ' + self.name + ' ' + self.city + '>'

class Info:
    def __init__(self, id, name, num_upcoming_shows):
        self.id = id
        self.name = name
        self.num_upcoming_shows = num_upcoming_shows

