from datetime import datetime, timezone


def utc_now():
    """Callable wrapper for datetime utc now function.

    Return a timezone naive datetime representing the current time in the UTC timezone.
    """
    tz_aware = datetime.now(timezone.utc)
    tz_naive = tz_aware.replace(tzinfo=None)
    return tz_naive
