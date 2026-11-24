"""
Tools
=====
Function tools used by agents and called directly by the pipeline.

  - save_progress(...)  : Persist session results to SQLite
  - get_history(...)    : Retrieve past sessions for a student
"""

import sqlite3
import os
from datetime import datetime
from agents import function_tool

DB_PATH = os.getenv("STUDY_DB_PATH", "study_progress.db")


# ─────────────────────────────────────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   TEXT    NOT NULL,
                topic        TEXT    NOT NULL,
                level_chosen TEXT    NOT NULL,
                score        INTEGER NOT NULL,
                max_score    INTEGER NOT NULL DEFAULT 5,
                timestamp    TEXT    NOT NULL
            )
        """)
        conn.commit()


# Initialise on import
_init_db()


# ─────────────────────────────────────────────────────────────────────────────
# Public functions (called directly by the pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def save_progress(student_id: str, topic: str, level_chosen: str, score: int) -> str:
    """
    Persist a completed study session to SQLite.

    Args:
        student_id:   Unique identifier for the student.
        topic:        The topic that was studied.
        level_chosen: One of 'beginner', 'intermediate', or 'advanced'.
        score:        Number of correct answers out of 5.

    Returns:
        A confirmation message string.
    """
    timestamp = datetime.now().isoformat()
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO study_sessions (student_id, topic, level_chosen, score, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, topic, level_chosen, score, timestamp),
        )
        conn.commit()
    return f"Progress saved: student={student_id}, topic={topic}, level={level_chosen}, score={score}/5"


def get_history(student_id: str) -> list[dict]:
    """
    Retrieve all past study sessions for a student.

    Args:
        student_id: Unique identifier for the student.

    Returns:
        List of session dictionaries with keys:
        id, student_id, topic, level_chosen, score, max_score, timestamp
    """
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE student_id = ? ORDER BY timestamp DESC",
            (student_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def print_history(student_id: str):
    """Pretty-print the study history for a student."""
    sessions = get_history(student_id)
    if not sessions:
        print(f"No history found for student '{student_id}'.")
        return

    print(f"\n📊 Study History for '{student_id}' ({len(sessions)} sessions)\n")
    print(f"{'#':<4} {'Date':<22} {'Topic':<35} {'Level':<15} {'Score'}")
    print("─" * 85)
    for s in sessions:
        date = s["timestamp"][:19].replace("T", " ")
        topic_short = s["topic"][:33] + ".." if len(s["topic"]) > 35 else s["topic"]
        print(f"{s['id']:<4} {date:<22} {topic_short:<35} {s['level_chosen']:<15} {s['score']}/{s['max_score']}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# @function_tool versions (for agent use if wiring into an agent loop)
# ─────────────────────────────────────────────────────────────────────────────

@function_tool
def save_progress_tool(student_id: str, topic: str, level_chosen: str, score: int) -> str:
    """
    Save a student's quiz score and chosen study level to the progress database.

    Args:
        student_id:   Unique identifier for the student.
        topic:        The topic that was studied.
        level_chosen: One of 'beginner', 'intermediate', or 'advanced'.
        score:        Number of correct answers out of 5.
    """
    return save_progress(student_id, topic, level_chosen, score)


@function_tool
def get_history_tool(student_id: str) -> str:
    """
    Retrieve the study history for a student as a formatted string.

    Args:
        student_id: Unique identifier for the student.
    """
    sessions = get_history(student_id)
    if not sessions:
        return f"No study history found for student '{student_id}'."
    lines = [f"Study history for '{student_id}':"]
    for s in sessions:
        lines.append(
            f"  [{s['timestamp'][:10]}] {s['topic']} | Level: {s['level_chosen']} | Score: {s['score']}/5"
        )
    return "\n".join(lines)
