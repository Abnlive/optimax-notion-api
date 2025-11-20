import main


def test_health():
    assert main.health() == {"status": "OptiMax API ready"}
