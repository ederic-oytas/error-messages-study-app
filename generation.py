import csv
import dataclasses
import itertools
import os
import random
import re
import string
import subprocess
import sys
from typing import Optional

import cyclopts

from models import Task


TEMP_FILE_NAME: str = "temp.py"
VARIABLE_CHOICES: tuple[str, ...] = ("a", "b", "c", "d", "e", "f")
OPERATOR_CHOICES: tuple[str, ...] = ("+", "*")
TYPE_CHOICES: tuple[type, ...] = (int, str)
EXPRESSION_SIZE: int = 6


def generate_literal_int() -> str:
    return str(random.randint(0, 99))


def generate_literal_str() -> str:
    return repr(random.choice(string.ascii_lowercase))


def generate_code(seed: int) -> str:
    random.seed(seed)

    # Randomly generate data
    variables: list[str] = [
        random.choice(VARIABLE_CHOICES) for _ in range(EXPRESSION_SIZE)
    ]
    operators: list[str] = [
        random.choice(OPERATOR_CHOICES) for _ in range(EXPRESSION_SIZE - 1)
    ]
    sorted_used_variables: list[str] = sorted(set(variables))
    variables_to_types: dict[str, type] = {
        v: random.choice(TYPE_CHOICES) for v in sorted_used_variables
    }
    variables_to_literals: dict[str, str] = {
        v: generate_literal_int() if t is int else generate_literal_str()
        for v, t in variables_to_types.items()
    }

    # Create code
    parts: list[str] = []
    for v, lt in variables_to_literals.items():
        parts.append(f"{v} = {lt}\n")
    parts.append("print(")
    for i in range(EXPRESSION_SIZE - 1):
        v = variables[i]
        o = operators[i]
        parts.append(f"{v} {o} ")
    parts.append(variables[EXPRESSION_SIZE - 1])
    parts.append(")")
    code = "".join(parts)

    return code


def extract_error_message_pointer(code: str) -> Optional[str]:
    with open(TEMP_FILE_NAME, "w") as f:
        f.write(code)
    completed_process = subprocess.run(["python", TEMP_FILE_NAME], capture_output=True)
    error_message = completed_process.stderr.decode()
    os.remove(TEMP_FILE_NAME)
    if error_message == "":
        return None
    error_message = error_message.replace("\r", "")
    return error_message


def get_error_message_underline(error_message_pointer: str) -> str:
    return error_message_pointer.replace("^", "~")


def get_error_message_none(error_message_pointer: str) -> str:
    return error_message_pointer.replace("^", "").replace("~", "")


def get_first_erroneous_operator_index(error_message_pointer: str) -> int:
    print_line_match = re.search(r".*print\(.*", error_message_pointer)
    pointer_line_match = re.search(r".*\^.*", error_message_pointer)
    assert print_line_match is not None
    assert pointer_line_match is not None
    expr_start = print_line_match.group().find("(") + 1
    pointer_index = pointer_line_match.group().find("^")
    pointer_index_in_expr = pointer_index - expr_start
    assert (pointer_index_in_expr - 2) % 4 == 0
    first_erroneous_operator_index = (pointer_index_in_expr - 2) // 4
    return first_erroneous_operator_index


def main(output_file_name: str, number_of_tasks: int, seed_start: int) -> None:

    if len(sys.argv) <= 2:
        print(f"Usage: {sys.argv[0]} OUTPUT_FILE NUMBER_OF_TASKS SEED_START")
        exit()

    # Generate data
    tasks: list[Task] = []
    for seed in itertools.count(seed_start):
        if len(tasks) >= number_of_tasks:
            break

        code = generate_code(seed)
        error_message_pointer = extract_error_message_pointer(code)
        if error_message_pointer is None:  # No error, reject.
            print(f"{seed=}, reject because no error")
            continue
        error_message_underline = get_error_message_underline(error_message_pointer)
        error_message_none = get_error_message_none(error_message_pointer)
        first_erroneous_operator_index = get_first_erroneous_operator_index(
            error_message_pointer
        )
        task = Task(
            task_id=len(tasks) + 1,
            seed=seed,
            code=code,
            error_message_pointer=error_message_pointer,
            error_message_underline=error_message_underline,
            error_message_none=error_message_none,
            first_erroneous_operator_index=first_erroneous_operator_index,
        )
        tasks.append(task)
        print(f"{seed=}, accept for task {task.task_id}")

    # Write to CSV
    with open(output_file_name, "w") as f:
        fieldnames: list[str] = [fd.name for fd in dataclasses.fields(Task)]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(dataclasses.asdict(task))

    print(f"Outputted to {output_file_name}")


if __name__ == "__main__":
    cyclopts.run(main)
