from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE answers ADD COLUMN IF NOT EXISTS classification VARCHAR(30)")
        )
        connection.execute(
            text("ALTER TABLE answers ADD COLUMN IF NOT EXISTS supporting_evidence VARCHAR(2000)")
        )
        connection.execute(
            text("ALTER TABLE answers ADD COLUMN IF NOT EXISTS source_pages VARCHAR(500)")
        )
        connection.execute(
            text("ALTER TABLE answers ALTER COLUMN student_answer TYPE VARCHAR(2000)")
        )
        connection.execute(
            text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_excerpt VARCHAR(2000)")
        )
        connection.execute(
            text("ALTER TABLE topics ADD COLUMN IF NOT EXISTS parent_topic_id INTEGER REFERENCES topics(id)")
        )