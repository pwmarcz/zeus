
from stv.stv import main
import tempfile
import os
import csv
import shutil
import contextlib


@contextlib.contextmanager
def temp_dir():
    d = tempfile.mkdtemp(prefix='stv')
    try:
        yield d
    finally:
        shutil.rmtree(d)


def run_stv(ballots, constituencies=None, seats=1, quota=0, separate_quota=None, random=None):
    if constituencies is None:
        constituencies = []
    if random is None:
        random = []
    with temp_dir() as d:
        ballots_fname = os.path.join(d, 'ballots.csv')
        with open(ballots_fname, 'w') as f:
            w = csv.writer(f)
            w.writerows(ballots)

        constituencies_fname = os.path.join(d, 'constituencies.csv')
        with open(constituencies_fname, 'w') as f:
            w = csv.writer(f)
            w.writerows(constituencies)

        args = [
            '--ballots', ballots_fname,
            '--constituencies', constituencies_fname,
            '--quota', str(quota),
            '--seats', str(seats),
        ]
        if random:
            args += ['--random'] + random
        if separate_quota:
            args += ['--separate-quota', ','.join(str(n) for n in separate_quota)]
        result = main(args)

    # Round the vote count
    return [
        (candidate, round_elected, round(vote_count*1000)/1000)
        for candidate, round_elected, vote_count
        in result
    ]


def make_ballots(data):
    ballots = []
    for ballot, count in data:
        for i in range(count):
            ballots.append(list(ballot))
    return ballots


def test_simple():
    # This is an example from Wikipedia:
    # https://en.wikipedia.org/wiki/Single_transferable_vote#Example
    ballots = make_ballots([
        ('A', 4),
        ('BA', 2),
        ('CD', 8),
        ('CE', 4),
        ('D', 1),
        ('E', 1),
    ])
    # Results are: (candidate, round elected, votes)
    assert run_stv(ballots, seats=3) == [
        ('C', 1, 12),
        ('A', 3, 6),
        ('D', 5, 5),
    ]


def test_constituencies():
    # Assume A and B are from the same constituency.
    ballots = make_ballots([
        ('AB', 10),
        ('BA', 5),
        ('C', 1)
    ])
    constituencies = [
        ['A', 'B'],
        ['C'],
    ]
    # With no quota, A and B win.
    assert run_stv(ballots, constituencies, seats=2) == [
        ('A', 1, 10),
        ('B', 2, 9),
    ]
    # With a quota of 1 candidate per constituency, A and C win.
    assert run_stv(ballots, constituencies, seats=2, quota=1) == [
        ('A', 1, 10),
        ('C', 3, 1),
    ]
    # With a quota of 2 for first and 1 for second constituency, A and B win again.
    assert run_stv(ballots, constituencies, seats=2, separate_quota=[2, 1]) == [
        ('A', 1, 10),
        ('B', 2, 9),
    ]


def test_random():
    ballots = make_ballots([
        ('AB', 10),
        ('BA', 10),
    ])
    assert run_stv(ballots, seats=1, random=['A']) == [('B', 2, 20)]
    assert run_stv(ballots, seats=1, random=['B']) == [('A', 2, 20)]
