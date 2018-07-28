from zeus.election_modules import count_sav_results
from fractions import Fraction


def test_sav_results_no_votes_for_one():
    cands_data = ["A", "B", "C"]
    ballots = [[1, 2], [2], [1, 2]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("C", Fraction(6, 1)),
        ("B", Fraction(3, 1)),
        ("A", Fraction(0, 1))
    ]


def test_sav_results_tie():
    cands_data = ["B", "A", "C", "D"]
    ballots = [[0, 1], [0, 1], [2, 3], [2, 3], [2, 3]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("C", Fraction(6, 1)),
        ("D", Fraction(6, 1)),
        ("A", Fraction(4, 1)),
        ("B", Fraction(4, 1))
    ]


def test_sav_results_fractions():
    cands_data = ["A", "B", "C", "D"]
    ballots = [[0, 2, 1], [0]]

    results = count_sav_results(ballots, cands_data)

    assert results == [
        ("A", Fraction(16, 3)),
        ("B", Fraction(4, 3)),
        ("C", Fraction(4, 3)),
        ("D", Fraction(0, 1)),
    ]


def test_minimal_number_of_votes():
    cands_data = ["A", "B", "C", "D", "E"]
    minimal = 3
    ballots = [[0], [2, 3]]

    results = count_sav_results(ballots, cands_data, minimal)

    assert results == [
        ("A", Fraction(5, 3)),
        ("C", Fraction(5, 3)),
        ("D", Fraction(5, 3)),
        ("B", Fraction(0, 1)),
        ("E", Fraction(0, 1)),
    ]
