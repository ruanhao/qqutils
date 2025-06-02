from qqutils.dateutils import pretty_duration


def test_pretty_duration():
    assert "0s" == pretty_duration(0)
    assert "unknown" == pretty_duration(-1)
    assert "3s" == pretty_duration(3)
    assert "1m,30s" == pretty_duration(90)
    assert "1H,1m,30s" == pretty_duration(90 + 3600)
    assert "1D,1H,1m,30s" == pretty_duration(90 + 3600 + 86400)
    assert "1W,1D,1H,1m,30s" == pretty_duration(90 + 3600 + 86400 + 604800)
    assert "7W,1D,1H,1m,30s" == pretty_duration(90 + 3600 + 86400 + 604800 * 7)
