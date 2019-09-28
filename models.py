## no shows property 
class Artist: 
    def __init___(self, id, name, city, state, address, phone, image_link, facebook_link, website, seeking_talent, seeking_description, shows, past_shows, past_shows_count, upcoming_shows, upcoming_shows_count):
        self.id = id
        self.name = name,
        self.city = city
        self.state = state
        self.address = address
        self.phone = phone
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.website = website
        self.seeking_talent = seeking_talent
        self.seeking_description = seeking_description
        self.upcoming_shows = upcoming_shows
        self.upcoming_shows_count = upcoming_shows_count
        self.past_shows = past_shows
        self.past_shows_count = past_shows_count

class Show:
    def __init__(self, artist_id, venue_id, start_time, artist_name, artist_image_link, venue_name, venue_image_link):
        self.artist_id = artist_id
        self.venue_id = venue_id
        self.start_time = start_time
        self.artist_name = artist_name
        self.artist_image_link = artist_image_link
        self.venue_name = venue_name
        self.venue_image_link = venue_image_link

class Info:
    def __init__(self, id, name, num_upcoming_shows):
        self.id = id
        self.name = name
        self.num_upcoming_shows = num_upcoming_shows
    
    #id
    #name
    #num_upcoming_shows

## no shows property
class Venue: 
    def __init__(self, id, name, city, state, address, phone, facebook_link, website, seeking_talent, seeking_description, upcoming_shows, upcoming_shows_count, past_shows, past_shows_count:
        self.id = id
        self.name = name
        self.city = city
        self.state = state
        self.address = address
        self.phone = phone
        self.facebook_link = facebook_link
        self.website = website
        self.seeking_talent = seeking_talent
        self.seeking_description = seeking_description
        self.upcoming_shows = self.upcoming_shows
        self.upcoming_shows_count = self.upcoming_shows_count
        self.past_shows = past_shows
        self.past_shows_count = past_shows_count