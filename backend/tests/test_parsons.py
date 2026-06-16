from app.services.parsons import check_puzzle_solution, generate_puzzle


def test_generate_puzzle_returns_correct_structure():
    code = "def add(a, b):\n    result = a + b\n    return result"
    puzzle = generate_puzzle(code)
    assert "correct_order" in puzzle
    assert "shuffled_lines" in puzzle
    assert len(puzzle["correct_order"]) == 3
    assert len(puzzle["shuffled_lines"]) == 3


def test_generate_puzzle_strips_empty_lines():
    code = "line1\n\nline2\n\nline3"
    puzzle = generate_puzzle(code)
    assert len(puzzle["correct_order"]) == 3


def test_generate_puzzle_shuffled_differs_from_correct():
    code = "line1\nline2\nline3\nline4\nline5"
    puzzle = generate_puzzle(code)
    assert set(puzzle["shuffled_lines"]) == set(puzzle["correct_order"])


def test_check_solution_correct():
    assert check_puzzle_solution(["a", "b", "c"], ["a", "b", "c"]) is True


def test_check_solution_incorrect():
    assert check_puzzle_solution(["b", "a", "c"], ["a", "b", "c"]) is False


def test_check_solution_empty():
    assert check_puzzle_solution([], []) is True
