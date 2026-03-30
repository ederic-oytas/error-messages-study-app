import csv
from io import StringIO
import time

import streamlit as st

from models import Task, TaskResponse


#
# Setup
#

N_TASKS_PER_SECTION = 10
TASK_LIMIT = 30

# st.write(st.session_state)


def ordi(n: int) -> str:
    if n % 100 <= 10 or 20 <= n % 100:
        if n % 10 == 1:
            return f"{n}st"
        elif n % 10 == 2:
            return f"{n}nd"
    return f"{n}th"


def get_task_error_message(task: Task, group_number: int) -> str:
    assert 1 <= group_number <= 3
    error_messages = (
        task.error_message_none,
        task.error_message_underline,
        task.error_message_pointer,
    )
    index = ((task.task_id - 1) // N_TASKS_PER_SECTION + (group_number - 1)) % 3
    return error_messages[index]


def get_practice_task_error_message(task: Task, group_number: int) -> str:
    assert 1 <= group_number <= 3
    if group_number == 1:
        return task.error_message_none
    elif group_number == 2:
        return task.error_message_underline
    elif group_number == 3:
        return task.error_message_pointer
    assert False, "Group number is invalid"


def load_tasks(input_file_name: str) -> tuple[Task, ...]:
    tasks: list[Task] = []
    with open(input_file_name) as f:
        reader = csv.DictReader(f)
        for row in reader:
            task = Task(
                task_id=int(row["task_id"]),
                seed=int(row["seed"]),
                code=row["code"],
                error_message_pointer=row["error_message_pointer"],
                error_message_underline=row["error_message_underline"],
                error_message_none=row["error_message_none"],
                first_erroneous_operator_index=int(
                    row["first_erroneous_operator_index"]
                ),
            )
            tasks.append(task)
    return tuple(tasks)


if "tasks" not in st.session_state:
    st.session_state["tasks"] = load_tasks("tasks.csv")
tasks: tuple[Task, ...] = st.session_state["tasks"]

if "practice_tasks" not in st.session_state:
    st.session_state["practice_tasks"] = load_tasks("practice_tasks.csv")
practice_tasks: tuple[Task, ...] = st.session_state["practice_tasks"]

if "example_task" not in st.session_state:
    st.session_state["example_task"] = load_tasks("example_task.csv")[0]
example_task: Task = st.session_state["example_task"]

if "task_responses" not in st.session_state:
    st.session_state["task_responses"] = []
task_responses = st.session_state["task_responses"]


#
# Information
#

st.write("""
# Error Messages Study
         
This study focuses on the readability of error messages. In this study, you
will completing a total of 30 tasks. At the end of it, you will be asked to
download and send your completion data to the experimenter (Ederic Oytas
<edericoytas@gmail.com>).
         
You are free to leave the experiment at any time you wish. At any point after
the experiment has ended, you may send an email to have all your data
removed from the study.

This study will track your name, major, and other demographic information, as
well as your experiment results (answers and time taken for each task). At the
end of the experiment, you will be able to download these results.

Please check the box below if you understand.
""")

st.checkbox(
    "I understand.",
    key="is_ethics_checked",
    disabled=st.session_state.get("is_ethics_checked", False),
)

if not st.session_state.get("is_ethics_checked", False):
    st.stop()


#
# Pre-survey
#

st.write("""
## Pre-Survey
         
Please answer the following questions before we begin the experiment.
""")

group_number = st.radio(
    "What is your group number? (assigned to you by the experimenter)",
    options=[1, 2, 3],
    key="group_number",
    disabled=st.session_state.get("has_submitted_presurvey", False),
    index=None,
    horizontal=True,
)
name = st.text_input(
    "What is your name? (e.g. Ederic Oytas)",
    key="name",
    disabled=st.session_state.get("has_submitted_presurvey", False),
)
major = st.text_input(
    "If you were/are in college, what was/is your major? (e.g. Computer Science, None)",
    key="major",
    disabled=st.session_state.get("has_submitted_presurvey", False),
)
has_taken_college_or_online_course = st.radio(
    "Have you taken at least one college or online course in Computer Science before?",
    key="has_taken_college_or_online_course",
    options=["Yes", "No"],
    index=None,
    disabled=st.session_state.get("has_submitted_presurvey", False),
    horizontal=True,
)
has_programmed_in_python = st.radio(
    "Have you programmed in Python before?",
    key="has_programmed_in_python",
    options=["Yes", "No"],
    index=None,
    disabled=st.session_state.get("has_submitted_presurvey", False),
    horizontal=True,
)

is_submit_enabled = (
    group_number is not None
    and len(name.strip()) >= 1
    and len(major.strip()) >= 1
    and has_taken_college_or_online_course is not None
    and has_programmed_in_python is not None
)
is_presurvey_submit_button_pressed = st.button(
    "Submit",
    disabled=(
        (not is_submit_enabled)
        or st.session_state.get("has_submitted_presurvey", False)
    ),
)

if is_presurvey_submit_button_pressed:
    st.session_state["has_submitted_presurvey"] = True
    st.rerun()

if not st.session_state.get("has_submitted_presurvey", False):
    st.stop()

assert group_number is not None


#
# Instructions
#

st.write("""
## Instructions
         
This experiment consists of two phases: a practice phase and a testing phase.
The practice phase will get you familiar with the tasks, and you may take it
as long as you wish. The testing phase is where you will complete 30 tasks.
         
For each task, you will be presented with a Python code snippet and an error
message. The last line of the code snippet will always produce a `TypeError`
because the operations between types is not supported. Your job is to select
the first operator which produced the error. (If multiple operators would
produce the error, then the leftmost one would raise an error first.)
         
We will only be using two operators: `+` and `*`. Multiplication precedes
addition and both are evaluted from left to right. We will also be only using
two types: `int` and `str`. In Python, the following operations are support and
will not raise a `TypeError`:
         
* `int + int`
* `int * int`
* `int * str` / `str * int`
* `str + str`
         
The following operations are not allowed in Python and will always raise a
`TypeError`:
         
* `int + str` / `str + int`
* `str * str`
""")

st.write(f"""
### Example

```python
{example_task.code}
```
```
{get_practice_task_error_message(example_task, group_number)}
```

Answer: The **{ordi(example_task.first_erroneous_operator_index + 1)}**
operator raises the `TypeError` (the last `+`).
""")

is_instructions_proceed_button_pressed = st.button(
    "Proceed to Practice",
    disabled=st.session_state.get("is_instructions_done", False),
)

if is_instructions_proceed_button_pressed:
    st.session_state["is_instructions_done"] = True
    st.rerun()

if not st.session_state.get("is_instructions_done", False):
    st.stop()

#
# Practice
#

if "practice_task_index" not in st.session_state:
    st.session_state["practice_task_index"] = 0
if "practice_answer" not in st.session_state:
    st.session_state["practice_answer"] = None

practice_task_index = st.session_state["practice_task_index"]
practice_task = practice_tasks[practice_task_index]

st.write("""
## Practice
Select the operator which causes the TypeError described in the error message.
""")

st.write(f"Practice Task: {practice_task.task_id} / {len(practice_tasks)}")

st.write(f"""
```python
{practice_task.code}
```
```
{get_practice_task_error_message(practice_task, group_number)}
```
""")

cols = st.columns(5, width=250)

has_selected_practice_answer = False

for i, col in enumerate(cols):
    with col:
        if st.button(
            str(i + 1),
            key=f"practice_answer_{i + 1}",
            disabled=st.session_state.get("is_practice_done", False),
        ):
            has_selected_practice_answer = True

if has_selected_practice_answer:
    st.session_state["practice_task_index"] = (practice_task_index + 1) % len(
        practice_tasks
    )
    st.rerun()

is_instructions_proceed_button_pressed = st.button(
    "Proceed to Test",
    disabled=st.session_state.get("is_practice_done", False),
)

if is_instructions_proceed_button_pressed:
    st.session_state["is_practice_done"] = True
    st.rerun()

if not st.session_state.get("is_practice_done", False):
    st.stop()

#
# Test
#

if "test_task_index" not in st.session_state:
    st.session_state["test_task_index"] = 0
if "test_answer" not in st.session_state:
    st.session_state["test_answer"] = None

test_task_index = st.session_state["test_task_index"]
test_task = practice_tasks[test_task_index]

st.write("""
## Test
Select the operator which causes the TypeError described in the error message.

Click "Start Test" to start the test.
""")

is_start_test_button_pressed = st.button(
    "Start Test",
    disabled=st.session_state.get("is_test_started", False),
)

if is_start_test_button_pressed:
    st.session_state["is_test_started"] = True
    st.rerun()

if not st.session_state.get("is_test_started", False):
    st.stop()

if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

st.write(f"Test Task: {test_task.task_id} / {TASK_LIMIT}")

st.write(f"""
```python
{test_task.code}
```
```
{get_task_error_message(test_task, group_number)}
```
""")

cols = st.columns(5, width=250)

if "is_test_done" not in st.session_state:
    st.session_state["is_test_done"] = False


for i, col in enumerate(cols):
    with col:
        st.button(
            str(i + 1),
            key=f"test_answer_{i + 1}",
            disabled=st.session_state["is_test_done"],
        )

test_answer_index = next(
    (i for i in range(1, 6) if st.session_state[f"test_answer_{i}"]), None
)


if test_answer_index is not None:  # Submit answer
    end_time = time.time()
    start_time = st.session_state["start_time"]
    time_taken = end_time - start_time

    task_response = TaskResponse(time_taken=time_taken, answer_index=test_answer_index)
    task_responses.append(task_response)

    st.session_state["test_task_index"] = (test_task_index + 1) % len(tasks)

    if st.session_state["test_task_index"] >= TASK_LIMIT:
        st.session_state["is_test_done"] = True

    st.session_state["start_time"] = time.time()

    st.rerun()

if not st.session_state["is_test_done"]:
    st.stop()


#
# Test Complete!
#


def make_results_csv() -> bytes:
    results_dict: dict[str, object] = {
        "group_number": group_number,
        "name": name,
        "major": major,
        "has_taken_college_or_online_course": has_taken_college_or_online_course,
        "has_programmed_in_python": has_programmed_in_python,
    }
    for i in range(TASK_LIMIT):
        response: TaskResponse = task_responses[i]
        results_dict[f"answer_index_{i + 1}"] = response.answer_index
        results_dict[f"time_taken_{i + 1}"] = response.time_taken
    string_io = StringIO()
    writer = csv.DictWriter(string_io, fieldnames=results_dict.keys())
    writer.writeheader()
    writer.writerow(results_dict)
    return string_io.getvalue().encode("utf-8")


st.write("""
## Test Complete!
Thank you, your test is now over. Please download and email your results to
the experimenter (Ederic Oytas <edericoytas@gmail.com>).
""")

results_csv = make_results_csv()

st.download_button(
    "Download Data",
    data=results_csv,
    file_name="data.csv",
    mime="text/csv",
    icon=":material/download:",
)
