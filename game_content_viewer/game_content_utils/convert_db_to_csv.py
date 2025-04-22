"""Convert sqlite database files to csv."""

import sqlite3
import csv
from pathlib import Path


def sqlite_to_csv(db_file: str | Path, output_dir: str | Path) -> None:
    """Convert all tables in a SQLite database to CSV files.

    Args:
        db_file: Path to the SQLite .db file
        output_dir: Directory where CSV files will be saved

    """
    try:
        # convert inputs to Path objects
        db_file = Path(db_file)
        output_dir = Path(output_dir)
        # create output directory if missing
        output_dir.mkdir(parents=True, exist_ok=True)

        # connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # get list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        # loop through each table and export to csv
        for table_name in tables:
            table_name = table_name[0]

            # skip the sqlite_sequence table
            if table_name == "sqlite_sequence":
                continue

            print(f"Exporting table: {table_name}")

            try:
                # execute query to fetch all data
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                # get column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]

                # generate csv file path
                csv_file = output_dir / f"{table_name}.csv"

                # write to csv file
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # write header
                    writer.writerow(columns)
                    # write data rows
                    writer.writerows(rows)
                print(f"Successfully saved {table_name} to {csv_file}")

            except Exception as e:
                print(f"Error exporting table {table_name}: {e}")

        # close the connection
        conn.close()
        print("Conversion completed.")

    except Exception as e:
        print(f"Error connecting to database: {e}")
