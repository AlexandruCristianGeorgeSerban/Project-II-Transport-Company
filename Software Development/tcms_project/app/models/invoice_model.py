import sqlite3
import logging
from typing import Dict, List, Any

DB_PATH: str = "instance/database.sqlite"

class InvoiceModel:
    """Handles database operations for customer invoices."""

    def create_table(self) -> bool:
        """Creates the invoices table if it does not already exist."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id TEXT PRIMARY KEY,
                        request_id TEXT NOT NULL,
                        client_name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        issue_date TEXT NOT NULL,
                        status TEXT NOT NULL
                    )
                """)
                connection.commit()
                return True
        except sqlite3.Error as error:
            logging.error(f"Database error during invoices table creation: {error}")
            return False

    def get_client_invoices(self, client_name: str) -> List[Dict[str, Any]]:
        """Retrieves all invoices for a specific client."""
        invoices: List[Dict[str, Any]] = []
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row
                db_cursor = connection.cursor()
                db_cursor.execute("SELECT * FROM invoices WHERE client_name = ? ORDER BY issue_date DESC", (client_name,))
                rows = db_cursor.fetchall()
                for row in rows:
                    invoices.append(dict(row))
                
                return invoices
        except sqlite3.Error as db_error:
            logging.error(f"Error fetching invoices: {db_error}")
            return invoices

    def mark_as_paid(self, invoice_id: str) -> bool:
        """Updates the invoice status to Paid."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute("UPDATE invoices SET status = 'Paid' WHERE id = ?", (invoice_id,))
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Error paying invoice: {db_error}")
            return False

    def insert_invoice(self, invoice_id: str, request_id: str, client_name: str, amount: float, issue_date: str) -> bool:
        """Inserts a real, new invoice into the database (used by Staff/System)."""
        try:
            with sqlite3.connect(DB_PATH) as connection:
                db_cursor = connection.cursor()
                db_cursor.execute(
                    "INSERT INTO invoices (id, request_id, client_name, amount, issue_date, status) VALUES (?, ?, ?, ?, ?, 'Pending')",
                    (invoice_id, request_id, client_name, amount, issue_date)
                )
                connection.commit()
                return True
        except sqlite3.Error as db_error:
            logging.error(f"Error inserting invoice: {db_error}")
            return False