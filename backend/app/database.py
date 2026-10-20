import os
import json
import sqlite3
import time
from pathlib import Path


DATABASE_PATH = (
    Path(os.environ["DATABASE_PATH"])
    if os.environ.get("DATABASE_PATH")
    else (
        Path(__file__).resolve().parents[2]
        / "data"
        / "evaluation.db"
    )
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def _add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_type
):
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_type}"
        )


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

    new_columns = [
        ("relevance_score", "REAL"),
        ("accuracy_score", "REAL"),
        ("hallucination_score", "REAL"),
        ("completeness_score", "REAL"),
        ("weighted_score", "REAL"),
        ("dimension_scores_json", "TEXT"),
        ("weights_json", "TEXT"),
        ("relevance_json", "TEXT"),
        ("accuracy_json", "TEXT"),
        ("hallucination_json", "TEXT"),
        ("completeness_json", "TEXT"),
        ("hallucinated_claims_json", "TEXT"),
        ("missing_aspects_json", "TEXT"),
        ("supporting_evidence_json", "TEXT"),
        ("verdict_reasoning", "TEXT"),
        ("batch_id", "TEXT"),
        ("user_id", "INTEGER")
    ]

    for column_name, column_type in new_columns:
        _add_column_if_missing(
            connection,
            "evaluation_submissions",
            column_name,
            column_type
        )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            name TEXT NOT NULL,
            avatar TEXT,
            provider TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            phone TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at REAL NOT NULL
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
    validation: dict,
    batch_id: str | None = None,
    user_id: int | None = None
):
    connection = get_connection()

    contradiction_data = validation.get(
        "contradiction",
        {}
    )

    relevance = validation.get(
        "relevance",
        {}
    )

    accuracy = validation.get(
        "accuracy",
        {}
    )

    hallucination = validation.get(
        "hallucination",
        {}
    )

    completeness = validation.get(
        "completeness",
        {}
    )

    dimension_scores = validation.get(
        "dimension_scores",
        {}
    )

    weights = validation.get(
        "weights",
        {}
    )

    hallucinated_claims = []

    if isinstance(hallucination, dict):
        hallucinated_claims = hallucination.get(
            "unsupported_claims",
            []
        )

        if not hallucinated_claims:
            hallucinated_claims = hallucination.get(
                "contradictory_claims",
                []
            )

    missing_aspects = []

    if isinstance(completeness, dict):
        missing_aspects = completeness.get(
            "missing_aspects",
            []
        )

    supporting_evidence = []

    if isinstance(accuracy, dict):
        supporting_evidence = accuracy.get(
            "supporting_evidence",
            []
        )

    relevance_score = dimension_scores.get(
        "relevance",
        relevance.get("score")
    )

    accuracy_score = dimension_scores.get(
        "accuracy",
        accuracy.get("score")
    )

    hallucination_score = dimension_scores.get(
        "hallucination"
    )

    completeness_score = dimension_scores.get(
        "completeness",
        completeness.get("score")
    )

    weighted_score = validation.get(
        "weighted_score"
    )

    final_score = validation.get(
        "final_score",
        validation.get("score")
    )

    verdict = validation.get(
        "verdict"
    )

    verdict_reasoning = validation.get(
        "verdict_reasoning",
        ""
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
            best_evidence_similarity,

            relevance_score,
            accuracy_score,
            hallucination_score,
            completeness_score,
            weighted_score,

            dimension_scores_json,
            weights_json,

            relevance_json,
            accuracy_json,
            hallucination_json,
            completeness_json,

            hallucinated_claims_json,
            missing_aspects_json,
            supporting_evidence_json,

            verdict_reasoning,
            batch_id,
            user_id
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )
        """,
        (
            question,
            ai_response,
            reference_answer,
            source_document,

            final_score,
            verdict,

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

            relevance_score,
            accuracy_score,
            hallucination_score,
            completeness_score,
            weighted_score,

            json.dumps(
                dimension_scores,
                ensure_ascii=False
            ),

            json.dumps(
                weights,
                ensure_ascii=False
            ),

            json.dumps(
                relevance,
                ensure_ascii=False
            ),

            json.dumps(
                accuracy,
                ensure_ascii=False
            ),

            json.dumps(
                hallucination,
                ensure_ascii=False
            ),

            json.dumps(
                completeness,
                ensure_ascii=False
            ),

            json.dumps(
                hallucinated_claims,
                ensure_ascii=False
            ),

            json.dumps(
                missing_aspects,
                ensure_ascii=False
            ),

            json.dumps(
                supporting_evidence,
                ensure_ascii=False
            ),

            verdict_reasoning,

            batch_id,

            user_id
        )
    )

    connection.commit()

    submission_id = cursor.lastrowid

    connection.close()

    return submission_id


def get_user_by_id(user_id: int) -> dict | None:
    connection = get_connection()
    user = connection.execute(
        "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    connection.close()
    return dict(user) if user else None


def get_or_create_user(
    identifier: str,
    provider: str,
    name: str | None = None,
    avatar: str | None = None,
    default_credits: int = 50
) -> dict:
    connection = get_connection()
    clean_id = identifier.strip().lower() if "@" in identifier else identifier.strip()

    if provider == "google":
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (clean_id,)
        ).fetchone()
        if row:
            display_name = name or row["name"]
            avatar_url = avatar or row["avatar"]
            connection.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP, name = ?, avatar = ? WHERE id = ?",
                (display_name, avatar_url, row["id"])
            )
            connection.commit()
            updated = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (row["id"],)
            ).fetchone()
            connection.close()
            return dict(updated)
        else:
            display_name = name or clean_id.split("@")[0].replace(".", " ").title()
            cursor = connection.execute(
                """
                INSERT INTO users (email, name, avatar, provider, credits)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_id, display_name, avatar or "", "google", default_credits)
            )
            connection.commit()
            new_id = cursor.lastrowid
            new_user = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (new_id,)
            ).fetchone()
            connection.close()
            return dict(new_user)

    elif provider == "phone":
        row = connection.execute(
            "SELECT * FROM users WHERE phone = ?",
            (clean_id,)
        ).fetchone()
        if row:
            display_name = name or row["name"]
            connection.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP, name = ? WHERE id = ?",
                (display_name, row["id"])
            )
            connection.commit()
            updated = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (row["id"],)
            ).fetchone()
            connection.close()
            return dict(updated)
        else:
            display_name = name or "Vinod Kumar Reddy"
            cursor = connection.execute(
                """
                INSERT INTO users (phone, name, avatar, provider, credits)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_id, display_name, avatar or "", "phone", default_credits)
            )
            connection.commit()
            new_id = cursor.lastrowid
            new_user = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (new_id,)
            ).fetchone()
            connection.close()
            return dict(new_user)

    else:  # 'guest' or demo
        guest_email = f"{clean_id}@guest.local"
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (guest_email,)
        ).fetchone()
        if row:
            connection.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],)
            )
            connection.commit()
            updated = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (row["id"],)
            ).fetchone()
            connection.close()
            return dict(updated)
        else:
            display_name = name or "Vinod Kumar Reddy"
            cursor = connection.execute(
                """
                INSERT INTO users (email, name, avatar, provider, credits)
                VALUES (?, ?, ?, ?, ?)
                """,
                (guest_email, display_name, avatar or "", "guest", default_credits)
            )
            connection.commit()
            new_id = cursor.lastrowid
            new_user = connection.execute(
                "SELECT id, email, phone, name, avatar, provider, credits, created_at, last_login FROM users WHERE id = ?",
                (new_id,)
            ).fetchone()
            connection.close()
            return dict(new_user)


def update_user_credits(user_id: int, delta: int) -> int | None:
    connection = get_connection()
    row = connection.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        connection.close()
        return None

    new_credits = max(0, row["credits"] + delta)
    connection.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    connection.commit()
    connection.close()
    return new_credits


def save_otp(phone: str, otp: str, expires_in_sec: int = 300) -> None:
    connection = get_connection()
    expires_at = time.time() + expires_in_sec
    connection.execute(
        """
        INSERT INTO otp_codes (phone, otp, expires_at)
        VALUES (?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET otp = excluded.otp, expires_at = excluded.expires_at
        """,
        (phone.strip(), otp.strip(), expires_at)
    )
    connection.commit()
    connection.close()


def verify_otp(phone: str, otp: str) -> bool:
    clean_phone = phone.strip()
    clean_otp = otp.strip()

    # Universal demo / test OTP code for 100% free operation with no external SMS API fees
    if clean_otp == "123456":
        return True

    connection = get_connection()
    row = connection.execute(
        "SELECT otp, expires_at FROM otp_codes WHERE phone = ?",
        (clean_phone,)
    ).fetchone()

    if not row:
        connection.close()
        return False

    is_valid = (row["otp"] == clean_otp) and (time.time() <= row["expires_at"])

    if is_valid:
        connection.execute("DELETE FROM otp_codes WHERE phone = ?", (clean_phone,))
        connection.commit()

    connection.close()
    return is_valid