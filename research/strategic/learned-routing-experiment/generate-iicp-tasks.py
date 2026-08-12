#!/usr/bin/env python3
"""Generate the deterministic IICP heterogeneous-routing task fixture."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "iicp-heterogeneous-tasks-v1.json"
SUBTYPES = ["sort", "unique", "filter", "fact", "arithmetic", "sequence", "logic"]
CATEGORIES = ["structured", "factual", "reasoning"]


def embedding(category: str, subtype: str, difficulty: int) -> list[float]:
    return [
        *[1.0 if item == category else 0.0 for item in CATEGORIES],
        *[1.0 if item == subtype else 0.0 for item in SUBTYPES],
        difficulty / 3,
    ]


def task(
    task_id: str, category: str, subtype: str, difficulty: int, prompt: str, answer
):
    return {
        "id": task_id,
        "category": category,
        "subtype": subtype,
        "difficulty": difficulty,
        "embedding": embedding(category, subtype, difficulty),
        "prompt": prompt,
        "expected_answer": answer,
    }


def structured_tasks() -> list[dict]:
    rows: list[dict] = []
    sort_values = [
        [8, 3, 5, 1],
        [14, -2, 7, 7, 0],
        [91, 12, 44, 3, 18],
        [6, 2, 9, 4, 1, 8],
        [105, 17, 42, -9],
        [33, 31, 32, 30],
        [4, 16, 2, 8, 1],
        [72, 11, 93, 54, 20],
        [0, -5, 8, -1, 3],
        [1000, 10, 100, 1],
    ]
    for index, values in enumerate(sort_values, 1):
        rows.append(
            task(
                f"structured-sort-{index:02}",
                "structured",
                "sort",
                1 + (index > 6),
                f"Sort these integers in ascending order: {values}",
                sorted(values),
            )
        )

    unique_values = [
        [3, 1, 3, 2, 1],
        [9, 9, 8, 7, 8, 6],
        [4, 2, 4, 2, 0],
        [12, -1, 12, 5, -1],
        [20, 10, 20, 30, 10],
        [7, 5, 6, 7, 5, 4],
        [101, 99, 101, 100],
        [2, 2, 2, 1],
        [15, 13, 14, 15, 12],
        [0, -2, -2, 1, 0, -1],
    ]
    for index, values in enumerate(unique_values, 1):
        rows.append(
            task(
                f"structured-unique-{index:02}",
                "structured",
                "unique",
                1 + (index > 5),
                f"Return the unique integers in ascending order: {values}",
                sorted(set(values)),
            )
        )

    filter_cases = [
        (
            [
                {"name": "Ada", "score": 91},
                {"name": "Ben", "score": 72},
                {"name": "Cy", "score": 88},
            ],
            80,
        ),
        (
            [
                {"name": "Iris", "score": 55},
                {"name": "Jo", "score": 55},
                {"name": "Kai", "score": 54},
            ],
            55,
        ),
        (
            [
                {"name": "Mina", "score": 10},
                {"name": "Noa", "score": 30},
                {"name": "Oli", "score": 20},
            ],
            20,
        ),
        (
            [
                {"name": "Pia", "score": 99},
                {"name": "Quin", "score": 98},
                {"name": "Rae", "score": 100},
            ],
            99,
        ),
        (
            [
                {"name": "Sol", "score": -1},
                {"name": "Tao", "score": 0},
                {"name": "Uma", "score": 1},
            ],
            0,
        ),
        (
            [
                {"name": "Vik", "score": 44},
                {"name": "Wes", "score": 42},
                {"name": "Xiu", "score": 43},
            ],
            43,
        ),
        (
            [
                {"name": "Yara", "score": 7},
                {"name": "Zed", "score": 9},
                {"name": "Ari", "score": 8},
            ],
            8,
        ),
        (
            [
                {"name": "Bea", "score": 61},
                {"name": "Cal", "score": 59},
                {"name": "Dee", "score": 60},
            ],
            60,
        ),
        (
            [
                {"name": "Eli", "score": 4},
                {"name": "Fay", "score": 4},
                {"name": "Gus", "score": 3},
            ],
            4,
        ),
        (
            [
                {"name": "Hana", "score": 82},
                {"name": "Ivan", "score": 81},
                {"name": "Jae", "score": 83},
            ],
            81,
        ),
    ]
    for index, (records, threshold) in enumerate(filter_cases, 1):
        expected = sorted(
            record["name"] for record in records if record["score"] >= threshold
        )
        rows.append(
            task(
                f"structured-filter-{index:02}",
                "structured",
                "filter",
                2 + (index > 7),
                f"From these records, return an alphabetically sorted array of names with score >= {threshold}: {records}",
                expected,
            )
        )
    return rows


FACTS = [
    ("What is the capital of France?", "Paris"),
    ("What is the chemical symbol for gold?", "Au"),
    ("How many sides does a hexagon have?", 6),
    ("What planet is known as the Red Planet?", "Mars"),
    ("What is the largest ocean on Earth?", "Pacific Ocean"),
    ("What is the capital of Japan?", "Tokyo"),
    ("What is the chemical symbol for sodium?", "Na"),
    ("How many minutes are in two hours?", 120),
    ("Which gas do plants absorb from the atmosphere?", "carbon dioxide"),
    ("What is the square root of 144?", 12),
    ("What is the capital of Canada?", "Ottawa"),
    ("What is the SI unit of electric current?", "ampere"),
    ("How many continents are conventionally recognized?", 7),
    ("Which planet is closest to the Sun?", "Mercury"),
    ("What is the chemical symbol for iron?", "Fe"),
    ("Who wrote Pride and Prejudice?", "Jane Austen"),
    ("What is the capital of Brazil?", "Brasilia"),
    ("What is the freezing point of water in degrees Celsius at standard pressure?", 0),
    ("How many bytes are in 32 bits?", 4),
    ("What is the largest mammal?", "blue whale"),
    ("What is the capital of Kenya?", "Nairobi"),
    ("What is the chemical symbol for potassium?", "K"),
    ("Which language is primarily used to style web pages?", "CSS"),
    ("How many degrees are in a right angle?", 90),
    ("What is the capital of New Zealand?", "Wellington"),
    ("What is the binary representation of decimal 10?", "1010"),
    ("Which organ pumps blood through the human body?", "heart"),
    ("What is the chemical symbol for silver?", "Ag"),
    ("How many items are in a dozen?", 12),
    ("What is the capital of Iceland?", "Reykjavik"),
]


def factual_tasks() -> list[dict]:
    return [
        task(
            f"factual-{index:02}",
            "factual",
            "fact",
            1 + (index > 10) + (index > 20),
            prompt,
            answer,
        )
        for index, (prompt, answer) in enumerate(FACTS, 1)
    ]


def reasoning_tasks() -> list[dict]:
    rows: list[dict] = []
    arithmetic = [
        (17, 6, 9),
        (23, 4, 11),
        (31, 3, 17),
        (14, 8, 15),
        (27, 5, 19),
        (42, 2, 13),
        (19, 7, 21),
        (36, 4, 29),
        (28, 9, 16),
        (55, 3, 24),
    ]
    for index, (a, b, c) in enumerate(arithmetic, 1):
        rows.append(
            task(
                f"reasoning-arithmetic-{index:02}",
                "reasoning",
                "arithmetic",
                2 + (index > 6),
                f"A store has {a} boxes with {b} items each, then receives {c} more items. How many items are there in total?",
                a * b + c,
            )
        )

    sequences = [
        ([2, 5, 8, 11], 14),
        ([10, 20, 40, 80], 160),
        ([81, 27, 9, 3], 1),
        ([1, 4, 9, 16], 25),
        ([3, 6, 12, 24], 48),
        ([100, 90, 80, 70], 60),
        ([1, 1, 2, 3, 5], 8),
        ([7, 14, 21, 28], 35),
        ([64, 32, 16, 8], 4),
        ([2, 6, 12, 20, 30], 42),
    ]
    for index, (values, expected) in enumerate(sequences, 1):
        rows.append(
            task(
                f"reasoning-sequence-{index:02}",
                "reasoning",
                "sequence",
                2 + (index in {4, 7, 10}),
                f"What is the next number in this sequence? {values}",
                expected,
            )
        )

    logic_cases = [
        (
            "A box has 8 red and 5 blue balls. Two red balls are removed and three blue balls are added. How many balls are in the box?",
            14,
        ),
        (
            "Nora is older than Liam. Liam is older than Maya. Who is the youngest?",
            "Maya",
        ),
        (
            "A train leaves at 09:35 and travels for 95 minutes. At what time does it arrive in 24-hour HH:MM format?",
            "11:10",
        ),
        (
            "Four machines make 40 parts in one hour at equal rates. How many parts do six such machines make in one hour?",
            60,
        ),
        (
            "A book has 240 pages. Sam reads one quarter on Monday and 60 pages on Tuesday. How many pages remain?",
            120,
        ),
        (
            "Every zorb is blue. No blue object is red. Can a zorb be red? Answer yes or no.",
            "no",
        ),
        (
            "A farmer has chickens and cows with 12 heads and 34 legs total. How many cows are there?",
            5,
        ),
        (
            "A password has three letters followed by two digits. How many characters does it contain?",
            5,
        ),
        (
            "If today is Tuesday, what day of the week will it be 17 days from today?",
            "Friday",
        ),
        (
            "A recipe for 4 people uses 300 grams of flour. How many grams are needed for 10 people at the same rate?",
            750,
        ),
    ]
    for index, (prompt, answer) in enumerate(logic_cases, 1):
        rows.append(
            task(
                f"reasoning-logic-{index:02}",
                "reasoning",
                "logic",
                2 + (index >= 6),
                prompt,
                answer,
            )
        )
    return rows


def main() -> None:
    tasks = structured_tasks() + factual_tasks() + reasoning_tasks()
    assert len(tasks) == 90
    assert len({item["id"] for item in tasks}) == 90
    document = {
        "schema": "iicp.heterogeneous-routing-tasks.v1",
        "seed": 42,
        "answer_contract": "JSON object with exactly one field named answer",
        "categories": {
            category: sum(item["category"] == category for item in tasks)
            for category in CATEGORIES
        },
        "embedding_dimensions": [*CATEGORIES, *SUBTYPES, "difficulty_normalized"],
        "tasks": tasks,
    }
    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
