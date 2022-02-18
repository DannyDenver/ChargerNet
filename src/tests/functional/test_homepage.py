
def test_index(client):
    response = client.get("/")
    assert b"Charger NET" in response.data

def test_username_on_homepage(client):
    response = client.get("/")
    assert b"Test User" in response.data


