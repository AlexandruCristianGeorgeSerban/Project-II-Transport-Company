import logging
from typing import Dict, Any
from app.models.report_model import ReportModel

class ReportController:
    """Processes business logic for generating and viewing reports."""

    def __init__(self) -> None:
        """Initializes the report model and creates the table."""
        self.model = ReportModel()
        self.model.create_table()

    def load_reports_history(self) -> Dict[str, Any]:
        """Loads all past reports for the data table."""
        data: Dict[str, Any] = {}
        try:
            data["reports"] = self.model.get_all_reports()
            return data
        except Exception as logic_error:
            logging.error(f"Error loading reports: {logic_error}")
            data["reports"] = []
            return data

    def generate_new_report(self, report_type: str, start_date: str, end_date: str, user: str) -> dict:
        """Handles the logic of 'generating' a report and saving it to history."""
        if not report_type or not start_date or not end_date:
            return {"success": False, "message": "Please fill in all report parameters (Type, Start Date, End Date)."}
            
        # Determine a generic name based on type
        report_name = f"{report_type} Summary"
        
        # Determine short type
        short_type = "Usage" if "Usage" in report_type else ("Activity" if "Activity" in report_type else "Jobs")
        
        result = self.model.insert_report(report_name, short_type, user)
        
        if result is True:
            return {"success": True, "message": f"Successfully generated '{report_name}' for period {start_date} to {end_date}!"}
        else:
            return {"success": False, "message": "Failed to save report to history."}