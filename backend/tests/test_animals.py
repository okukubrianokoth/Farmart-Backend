# backend/tests/test_animals.py
from backend.app.animals import add_animal

def test_add_animal():
    result = add_animal("Cow", 5)
    assert result["name"] == "Cow"
    assert result["quantity"] == 5
