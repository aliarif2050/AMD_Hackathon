import pytest
from pydantic import ValidationError

from app.schema import Result, Task


def test_task_valid():
    t = Task(task_id="t1", prompt="hello")
    assert t.task_id == "t1"
    assert t.prompt == "hello"


def test_result_valid():
    r = Result(task_id="t1", answer="hi")
    assert r.answer == "hi"


def test_result_allows_empty_answer():
    # `answer` has no min_length: an empty string is structurally valid.
    assert Result(task_id="t1", answer="").answer == ""


@pytest.mark.parametrize("field", ["task_id", "prompt"])
def test_task_rejects_empty_required_fields(field):
    kwargs = {"task_id": "t1", "prompt": "hello"}
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        Task(**kwargs)


def test_task_rejects_missing_fields():
    with pytest.raises(ValidationError):
        Task(task_id="t1")
