from setup import Config


def test_yaml_config():
    cfg = Config("foo.conf", is_yaml=True)
    assert hasattr(cfg, "file")
    assert hasattr(cfg, "file")
    assert hasattr(cfg, "file")
    assert hasattr(cfg, "file")
    assert hasattr(cfg, "file")


def test_ini_config():
    cfg = Config("foo.ini", is_ini=True)
    assert hasattr(cfg, "file")
