# services/line_service.py
from typing import List

from db.database import get_session
from db.model import Line
from db.models import LineModel


class LineService:
    """Service for line management operations"""

    @staticmethod
    async def get_all_lines() -> List[Line]:
        """Get all configured lines from database"""
        async with get_session() as session:
            line_model = LineModel(session)
            return await line_model.read_all()
