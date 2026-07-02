from app_error import greet


def test_greet() -> None:
    assert greet("World") == "Hello, World!"


def test_greet_custom_name() -> None:
    assert greet("Python") == "Hello, Python!"
