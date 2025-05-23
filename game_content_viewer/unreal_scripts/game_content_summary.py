"""Game Content Summary Module
- Aggregate asset counts by class type
- Track total asset count and size

DB_FILE_PATH: File path to the sqlite database (.db) file.
TABLE_NAME: Name of the source table containing game asset data.
SUMMARY_TABLE_NAME: Name of the table where summary statistics are stored.

"""
import imp
import datetime
import sqlite3
from pathlib import Path

import unreal

#from ..game_content_utils import config_file
file_path = (Path(__file__).parents[1] / "game_content_utils" / "config_file.py").as_posix()
config_file = imp.load_source("config_file", file_path)

DB_FILE_PATH = config_file.DB_FILE_PATH
TABLE_NAME = config_file.TABLE_NAME
SUMMARY_TABLE_NAME = config_file.SUMMARY_TABLE_NAME


class ContentSummaryDB:
    """Database handler for game content summary data."""

    def __init__(self, db_file: str) -> None:
        """Initialize database connection.

        Args:
            db_file: Path to the SQLite database file

        """
        self.db_file = Path(db_file)
        unreal.log(f"Connecting to database: {self.db_file}")
        self.conn = sqlite3.connect(self.db_file)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create the summary table if it doesn't exist."""
        schema = f"""
        CREATE TABLE IF NOT EXISTS {SUMMARY_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            computed_at TEXT NOT NULL
        );
        """
        with self.conn:
            self.conn.executescript(schema)

    def compute_summary(self) -> None:
        """Compute aggregates from game_content and store in summary table."""
        computed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_data: list[tuple[str, str, str]] = []

        with self.conn:
            cursor = self.conn.cursor()

            # check if game_content exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (TABLE_NAME,),
            )
            if not cursor.fetchone():
                unreal.log(f"Table {TABLE_NAME} not found in {self.db_file}")
                return

            # total number of assets
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_assets = cursor.fetchone()[0]
            summary_data.append(("total_assets", str(total_assets), computed_at))

            # total data size (sum of file_size_mb)
            cursor.execute(f"SELECT SUM(CAST(file_size_mb AS REAL)) FROM {TABLE_NAME}")
            total_size_mb = cursor.fetchone()[0] or 0.0
            summary_data.append(("total_size_mb", f"{total_size_mb:.3f}", computed_at))

            # store total count for each asset class
            cursor.execute(f"""
                SELECT asset_class, COUNT(*) as count 
                FROM {TABLE_NAME} 
                GROUP BY asset_class
                ORDER BY count DESC
            """)

            all_asset_classes = cursor.fetchall()
            for asset_class, count in all_asset_classes:
                # just use the asset class name as the metric name
                metric_name = asset_class
                summary_data.append((metric_name, str(count), computed_at))

            # clear existing summary data and reset id counter
            cursor.execute(f"DELETE FROM {SUMMARY_TABLE_NAME}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{SUMMARY_TABLE_NAME}'")

            # insert new summary data
            cursor.executemany(
                f"""
                INSERT INTO {SUMMARY_TABLE_NAME} (metric_name, metric_value, computed_at)
                VALUES (?, ?, ?)
                """,
                summary_data,
            )

    def get_top_asset_classes(self, limit: int = 100) -> None:
        """Retrieve and print the top asset classes by count.

        Args:
            limit: Maximum number of asset classes to retrieve.

        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                SELECT metric_name, metric_value
                FROM {SUMMARY_TABLE_NAME}
                WHERE metric_name NOT IN ('total_assets', 'total_size_mb')
                ORDER BY CAST(metric_value AS INTEGER) DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = cursor.fetchall()
            for asset_class, count in results:
                unreal.log(f"{asset_class}: {count} assets")

    def print_summary(self) -> None:
        """Print all computed summary metrics."""
        with self.conn:
            cursor = self.conn.cursor()

            # get general metrics first
            cursor.execute(f"""
                SELECT metric_name, metric_value FROM {SUMMARY_TABLE_NAME}
                WHERE metric_name IN ('total_assets', 'total_size_mb')
            """)

            results = cursor.fetchall()
            unreal.log("\n===== Game Content Summary =====")
            for metric_name, metric_value in results:
                unreal.log(f"{metric_name}: {metric_value}")

            unreal.log("\n===== Top Asset Classes =====")
            self.get_top_asset_classes()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
        unreal.log("Database connection closed")


def main(db_file_path: Path | str) -> None:
    """Main entry point for the summary generation."""
    summary_db = ContentSummaryDB(db_file_path)
    summary_db.compute_summary()
    summary_db.print_summary()
    summary_db.close()


if __name__ == "__main__":
    main(DB_FILE_PATH)
