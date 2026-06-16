from app.services.exercise_db import ExerciseDB


def _make_db_with_data():
    db = ExerciseDB()
    db.dataset = [
        {"id": 1, "question": "Add two numbers", "starter_code": "", "solutions": '["def add(a,b): return a+b"]', "difficulty": "introductory"},
        {"id": 2, "question": "Sort a list", "starter_code": "def sort_list(lst):", "solutions": '["def sort_list(lst): return sorted(lst)"]', "difficulty": "interview"},
        {"id": 3, "question": "Binary search", "starter_code": "", "solutions": None, "difficulty": "competition"},
    ]
    db._build_indexes()
    db._loaded = True
    return db


def test_build_indexes():
    db = _make_db_with_data()
    assert db._id_to_index == {"1": 0, "2": 1, "3": 2}
    assert len(db._all_indices) == 3
    assert len(db._difficulty_indices["introductory"]) == 1
    assert len(db._difficulty_indices["interview"]) == 1


def test_count_all():
    db = _make_db_with_data()
    assert db._count_problems_sync("Any") == 3


def test_count_by_difficulty():
    db = _make_db_with_data()
    assert db._count_problems_sync("introductory") == 1
    assert db._count_problems_sync("competition") == 1
    assert db._count_problems_sync("nonexistent") == 0


def test_get_by_id():
    db = _make_db_with_data()
    p = db._get_problem_by_id_sync("2")
    assert p is not None
    assert p["id"] == "2"
    assert p["question"] == "Sort a list"
    assert p["solution"] == "def sort_list(lst): return sorted(lst)"


def test_get_by_id_not_found():
    db = _make_db_with_data()
    assert db._get_problem_by_id_sync("999") is None


def test_parse_problem_with_solutions():
    db = _make_db_with_data()
    p = db._parse_problem(db.dataset[0])
    assert p["solution"] == "def add(a,b): return a+b"


def test_parse_problem_with_null_solutions():
    db = _make_db_with_data()
    p = db._parse_problem(db.dataset[2])
    assert p["solution"] == ""


def test_parse_problem_truncates_question():
    db = _make_db_with_data()
    long_q = {"id": 99, "question": "x" * 300, "starter_code": "", "solutions": "[]", "difficulty": "introductory"}
    p = db._parse_problem(long_q, truncate_question=True)
    assert len(p["question"]) == 203
    assert p["question"].endswith("...")


def test_list_problems_pagination():
    db = _make_db_with_data()
    page1 = db._list_problems_sync("Any", limit=2, offset=0, shuffle=False)
    page2 = db._list_problems_sync("Any", limit=2, offset=2, shuffle=False)
    assert len(page1) == 2
    assert len(page2) == 1


def test_random_problem_respects_difficulty():
    db = _make_db_with_data()
    for _ in range(20):
        p = db._get_random_problem_sync("introductory")
        assert p["difficulty"] == "introductory"
