import cix


def test_package_imports():
    assert cix.__version__ == "0.1.0"
    assert cix.INDEX_VERSION == "1.0.0"
