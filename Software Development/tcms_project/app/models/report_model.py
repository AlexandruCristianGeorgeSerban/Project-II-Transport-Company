import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

DB_PATH: str = "instance/database.sqlite"

class ReportModel:
    """Handles direct database operations for the reports history."""

    def create_table(self) -> bool:
        """Creates the reports table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        generated_by TEXT NOT NULL,
                        generated_date TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error: {error}")
            return False

    def insert_report(self, r_name: str, r_type: str, user: str) -> bool:
        """Inserts a new report record into the history."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT COUNT(id) FROM reports")
                count = db_cursor.fetchone()[0]
                report_id = f"R{1001 + count}"
                gen_date = datetime.now().strftime("%d/%m/%Y")
                
                db_cursor.execute(
                    "INSERT INTO reports (id, name, type, generated_by, generated_date) VALUES (?, ?, ?, ?, ?)",
                    (report_id, r_name, r_type, user, gen_date)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Insert report error: {db_error}")
            return False

    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Retrieves the history of generated reports."""
        reports_list: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM reports ORDER BY id DESC")
                rows = db_cursor.fetchall()
                for row in rows:
                    reports_list.append(dict(row))
                return reports_list
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching reports: {db_error}")
            return reports_list

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single report by its ID."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
                row = db_cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching report {report_id}: {db_error}")
            return None