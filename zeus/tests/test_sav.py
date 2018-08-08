from zeus.election_modules.sav import count_sav_results
from fractions import Fraction


def test_sav_results_no_votes_for_one():
    cands_data = ["A", "B", "C"]
    ballots = [[1, 2], [2], [1, 2]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("C", 2),
        ("B", 1),
        ("A", 0),
    ]


def test_sav_results_tie():
    cands_data = ["B", "A", "C", "D"]
    ballots = [[0, 1], [0, 1], [2, 3], [2, 3], [2, 3]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("C", 1.5),
        ("D", 1.5),
        ("A", 1),
        ("B", 1),
    ]


def test_sav_results_fractions():
    cands_data = ["A", "B", "C", "D"]
    ballots = [[0, 2, 1], [0]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("A", Fraction(4, 3)),
        ("B", Fraction(1, 3)),
        ("C", Fraction(1, 3)),
        ("D", 0),
    ]


def test_minimal_number_of_votes():
    cands_data = ["A", "B", "C", "D", "E"]
    minimal = 3
    ballots = [[0], [2, 3]]

    results = count_sav_results(ballots, cands_data, minimal)

    assert results == [
        ("A", Fraction(1, 3)),
        ("C", Fraction(1, 3)),
        ("D", Fraction(1, 3)),
        ("B", 0),
        ("E", 0),
    ]
