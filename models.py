from dataclasses import dataclass


@dataclass
class Task:
    task_id: int
    seed: int
    code: str
    error_message_pointer: str
    error_message_underline: str
    error_message_none: str
    first_erroneous_operator_index: int
    correct_answer: int


@dataclass
class TaskResponse:
    answer_index: int
    time_taken: str
