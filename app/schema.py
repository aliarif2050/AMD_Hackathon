"""Pydantic models for the Track 1 batch I/O contract.

Input  (/input/tasks.json):    [ {"task_id": str, "prompt": str}, ... ]
Output (/output/results.json): [ {"task_id": str, "answer": str}, ... ]
"""
from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single unit of work read from the input file."""

    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class Result(BaseModel):
    """A single answer written to the output file (answer may be empty-string safe)."""

    task_id: str = Field(min_length=1)
    answer: str
