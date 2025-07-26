from datetime import datetime
from crewai.tools import BaseTool


class DateTool(BaseTool):
    name: str = "Get Current Date"
    description: str = "Returns the current date in a readable format"

    def _run(self) -> str:
        """Get the current date"""
        return datetime.now().strftime("%B %d, %Y")