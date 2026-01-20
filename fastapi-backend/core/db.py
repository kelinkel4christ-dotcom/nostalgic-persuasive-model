import os
import psycopg2
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load env (Path: core/ -> fastapi-backend/ -> project_root/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/myapp"
)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def fetch_latest_context(user_id: str) -> Dict[str, Any]:
    """
    Fetch the latest stress and emotion context for a user from daily_habit_logs.

    Args:
        user_id: The user's ID

    Returns:
        Dict with 'stress_score' (float) and 'emotion' (str)
        Defaults to neutral if no log found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get the most recent log entry for this user
        # We order by date descending to get the latest one
        cursor.execute(
            """
            SELECT stress_level, emotion 
            FROM daily_habit_logs 
            WHERE user_id = %s 
            ORDER BY date DESC, created_at DESC 
            LIMIT 1;
        """,
            (user_id,),
        )

        row = cursor.fetchone()

        if row:
            stress = row[0]
            emotion = row[1]
            return {
                "stress_score": float(stress) if stress is not None else 0.5,
                "emotion": emotion if emotion else "neutral",
            }

    except Exception as e:
        print(f"Error fetching latest context: {e}")
    finally:
        cursor.close()
        conn.close()

    # Default fallback
    return {"stress_score": 0.5, "emotion": "neutral"}
