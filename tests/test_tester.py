import json
from openclaw_sdlc_agent.agents.tester import _extract_relevant_errors

def test_extract_pytest_failures():
    log_text = """
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.0, pluggy-1.3.0
rootdir: /app
collected 3 items

=================================== FAILURES ===================================
__________________________________ test_addition _______________________________

    def test_addition():
>       assert add(1, 2) == 4
E       assert 3 == 4

tests/test_math.py:10: AssertionError
----------------------------- Captured stdout call -----------------------------
some stdout
=============================== warnings summary ===============================
tests/test_math.py:12
  DeprecationWarning: deprecated feature
=========================== short test summary info ============================
FAILED tests/test_math.py::test_addition - assert 3 == 4
    """
    res_str = _extract_relevant_errors(log_text)
    res = json.loads(res_str)

    assert res["framework"] == "pytest"
    assert len(res["failures"]) == 1
    assert res["failures"][0]["test_name"] == "test_addition"
    assert res["failures"][0]["file"] == "tests/test_math.py"
    assert res["failures"][0]["line"] == 10
    assert res["failures"][0]["message"] == "assert 3 == 4"


def test_extract_unittest_failures():
    log_text = """
======================================================================
FAIL: test_subtraction (__main__.TestMath.test_subtraction)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_math.py", line 15, in test_subtraction
    self.assertEqual(5 - 2, 4)
AssertionError: 3 != 4

======================================================================
ERROR: test_division (__main__.TestMath.test_division)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_math.py", line 20, in test_division
    raise ZeroDivisionError("division by zero")
ZeroDivisionError: division by zero

----------------------------------------------------------------------
Ran 2 tests in 0.001s

FAILED (failures=1, errors=1)
    """
    res_str = _extract_relevant_errors(log_text)
    res = json.loads(res_str)

    assert res["framework"] == "unittest"
    assert len(res["failures"]) == 2

    assert res["failures"][0]["test_name"] == "test_subtraction"
    assert res["failures"][0]["file"] == "test_math.py"
    assert res["failures"][0]["line"] == 15
    assert res["failures"][0]["message"] == "AssertionError: 3 != 4"

    assert res["failures"][1]["test_name"] == "test_division"
    assert res["failures"][1]["file"] == "test_math.py"
    assert res["failures"][1]["line"] == 20
    assert res["failures"][1]["message"] == "ZeroDivisionError: division by zero"


def test_extract_go_test_failures():
    log_text = """
=== RUN   TestAdd
--- FAIL: TestAdd (0.00s)
    math_test.go:12: expected 3, got 4
    math_test.go:15: expected 5, got 6
=== RUN   TestSubtract
--- FAIL: TestSubtract (0.00s)
    math_test.go:25: expected 1, got 2
FAIL
coverage: 100.0% of statements
exit status 1
FAIL	example/math	0.002s
    """
    res_str = _extract_relevant_errors(log_text)
    res = json.loads(res_str)

    assert res["framework"] == "go test"
    assert len(res["failures"]) == 3

    assert res["failures"][0]["test_name"] == "TestAdd"
    assert res["failures"][0]["file"] == "math_test.go"
    assert res["failures"][0]["line"] == 12
    assert res["failures"][0]["message"] == "expected 3, got 4"

    assert res["failures"][1]["test_name"] == "TestAdd"
    assert res["failures"][1]["file"] == "math_test.go"
    assert res["failures"][1]["line"] == 15
    assert res["failures"][1]["message"] == "expected 5, got 6"

    assert res["failures"][2]["test_name"] == "TestSubtract"
    assert res["failures"][2]["file"] == "math_test.go"
    assert res["failures"][2]["line"] == 25
    assert res["failures"][2]["message"] == "expected 1, got 2"


def test_warning_filtering():
    log_text = """
============================= test session starts ==============================
collected 1 item

=============================== warnings summary ===============================
WARNING: something is deprecated
tests/test_math.py:10: UserWarning: a warning
=================================== FAILURES ===================================
__________________________________ test_fail ___________________________________
    def test_fail():
>       assert False
E       assert False
test_math.py:12: AssertionError
    """
    res_str = _extract_relevant_errors(log_text)
    res = json.loads(res_str)

    assert res["framework"] == "pytest"
    assert len(res["failures"]) == 1
    assert res["failures"][0]["test_name"] == "test_fail"
    assert res["failures"][0]["file"] == "test_math.py"
    assert res["failures"][0]["line"] == 12
    assert res["failures"][0]["message"] == "assert False"


def test_max_five_failures():
    log_text = ""
    # Create 8 failures
    for i in range(8):
        log_text += f"""
__________________________________ test_fail_{i} ___________________________________
    def test_fail_{i}():
>       assert False
E       assert False
test_math.py:{10 + i}: AssertionError
"""
    res_str = _extract_relevant_errors(log_text)
    res = json.loads(res_str)

    assert len(res["failures"]) == 5
    for i in range(5):
        assert res["failures"][i]["test_name"] == f"test_fail_{i}"
        assert res["failures"][i]["line"] == 10 + i
