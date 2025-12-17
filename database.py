"""Database operations for storing YouTube video data."""

import sqlite3


class Database:
    """Handles SQLite database operations for YouTube video data."""

    def __init__(self, db_name):
        """Initialize database connection."""
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish connection to the database."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def setup_table(self):
        """Create the videos table if it doesn't exist."""
        # Check if table exists and has correct schema
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'"
        )
        table_exists = self.cursor.fetchone()

        if table_exists:
            # Check if table has the new columns
            self.cursor.execute("PRAGMA table_info(videos)")
            columns = [row[1] for row in self.cursor.fetchall()]

            required_columns = [
                "id",
                "title",
                "video_url",
                "thumbnail_url",
                "published_at",
                "view_count",
                "like_count",
                "comment_count",
                "transcript",
            ]

            # If schema is outdated, backup and recreate
            if set(columns) != set(required_columns):
                print("[INFO] Updating database schema...")
                self.cursor.execute("ALTER TABLE videos RENAME TO videos_old")
                self.cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS videos (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        video_url TEXT,
                        thumbnail_url TEXT,
                        published_at TEXT,
                        view_count INTEGER,
                        like_count INTEGER,
                        comment_count INTEGER,
                        transcript TEXT
                    )
                """
                )

                # Try to migrate data from old table
                try:
                    # Get common columns
                    old_columns = ", ".join(
                        [col for col in columns if col in required_columns]
                    )
                    if old_columns:
                        self.cursor.execute(
                            f"INSERT INTO videos ({old_columns}) SELECT {old_columns} FROM videos_old"
                        )
                        print(f"[INFO] Migrated existing data from old schema")
                except Exception as e:
                    print(f"[WARNING] Could not migrate old data: {e}")

                # Drop old table
                self.cursor.execute("DROP TABLE videos_old")
                self.conn.commit()
                print("[INFO] Database schema updated successfully")
        else:
            # Create new table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    video_url TEXT,
                    thumbnail_url TEXT,
                    published_at TEXT,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    transcript TEXT
                )
            """
            )
            self.conn.commit()

    def insert_video(
        self,
        video_id,
        title,
        video_url,
        thumbnail_url,
        published_at,
        view_count,
        like_count,
        comment_count,
        transcript,
    ):
        """Insert or update a video record in the database."""
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO videos 
            (id, title, video_url, thumbnail_url, published_at, view_count, like_count, comment_count, transcript)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                video_id,
                title,
                video_url,
                thumbnail_url,
                published_at,
                view_count,
                like_count,
                comment_count,
                transcript,
            ),
        )

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
