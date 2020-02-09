from datetime import datetime
from freezegun import freeze_time

@freeze_time("2020-01-01")
def test_get_random_time_in_range():
    from scheduler import get_random_time_in_range
    randomized_time = get_random_time_in_range(('06:00', '07:00'))
    assert randomized_time > datetime(2020, 1, 1, hour=6, minute=0).timestamp()
    assert randomized_time < datetime(2020, 1, 1, hour=7, minute=0).timestamp()

@freeze_time("2020-01-01")
def test_get_random_time_around():
    from scheduler import get_random_time_around
    rand_time = get_random_time_around(datetime(2020, 1, 1, hour=6, minute=0), interval_minutes=60)
    assert rand_time > datetime(2020, 1, 1, hour=5, minute=0).timestamp()
    assert rand_time < datetime(2020, 1, 1, hour=7, minute=0).timestamp()

def test_get_program():
    from scheduler import generate_program
    prog = generate_program()
    assert len(prog['a']) == 4
    assert len(prog['b']) == 2
