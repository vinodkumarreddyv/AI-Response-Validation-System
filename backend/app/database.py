import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "evaluation.db"
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            question TEXT NOT NULL,

            ai_response TEXT NOT NULL,

            reference_answer TEXT,

            source_document TEXT,

            score REAL,

            verdict TEXT,

            reference_similarity REAL,

            reference_exact_match INTEGER,

            contradiction REAL,

            entailment REAL,

            neutral REAL,

            is_contradiction INTEGER,

            expected_fact TEXT,

            direct_fact_contradiction INTEGER,

            best_evidence_similarity REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def save_evaluation(
    question: str,
    ai_response: str,
    reference_answer: str | None,
    source_document: str | None,
    validation: dict
):
    connection = get_connection()

    contradiction_data = validation.get(
        "contradiction",
        {}
    )

    cursor = connection.execute(
        """
        INSERT INTO evaluation_submissions
        (
            question,
            ai_response,
            reference_answer,
            source_document,
            score,
            verdict,
            reference_similarity,
            reference_exact_match,
            contradiction,
            entailment,
            neutral,
            is_contradiction,
            expected_fact,
            direct_fact_contradiction,
            best_evidence_similarity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question,
            ai_response,
            reference_answer,
            source_document,

            validation.get("score"),

            validation.get("verdict"),

            validation.get(
                "reference_similarity"
            ),

            int(
                validation.get(
                    "reference_exact_match",
                    False
                )
            ),

            contradiction_data.get(
                "contradiction",
                0.0
            ),

            contradiction_data.get(
                "entailment",
                0.0
            ),

            contradiction_data.get(
                "neutral",
                1.0
            ),

            int(
                contradiction_data.get(
                    "is_contradiction",
                    False
                )
            ),

            validation.get(
                "expected_fact"
            ),

            int(
                validation.get(
                    "direct_fact_contradiction",
                    False
                )
            ),

            validation.get(
                "best_evidence_similarity"
            ),
        ),
    )

    connection.commit()

    submission_id = cursor.lastrowid

    connection.close()

    return submission_id