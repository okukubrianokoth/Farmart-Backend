from app.models import Animal, AnimalType


def test_add_animal(client, auth_headers):
    data = {
        "name": "Cow A",
        "animal_type": "cattle",
        "breed": "Friesian",
        "age": 3,
        "price": 50000,
    }
    response = client.post("/api/animals", json=data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json["animal"]["name"] == "Cow A"


def test_get_animals(client, auth_headers):
    # Add one animal
    client.post(
        "/api/animals",
        json={
            "name": "Cow B",
            "animal_type": "cattle",
            "breed": "Ayrshire",
            "age": 2,
            "price": 40000,
        },
        headers=auth_headers,
    )

    response = client.get("/api/animals")
    assert response.status_code == 200
    assert len(response.json) >= 1
