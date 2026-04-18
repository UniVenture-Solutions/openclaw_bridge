from openclaw_bridge.bridge.rate_limit import RateLimiter


def test_rate_limit_cap():
    limiter = RateLimiter(rpm=2)
    assert limiter.allow("k1")
    assert limiter.allow("k1")
    assert not limiter.allow("k1")
