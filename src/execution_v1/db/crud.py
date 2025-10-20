from enum import Enum
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db.model import Line
from db.models.isp_model import ISPModel
from db.models.quota_result_model import QuotaResultModel
from db.models.speed_test_result_model import SpeedTestResultModel
from db.schema import ResultSchema


class CheckMode(str, Enum):
    """Enum for different check modes"""

    FULL = "full"
    SPEED_TEST_ONLY = "speed_test_only"
    QUOTA_CHECK_ONLY = "quota_check_only"


async def read_last_result(
    session: AsyncSession, line: Line, mode: CheckMode = CheckMode.FULL
) -> Optional[ResultSchema]:
    """
    Read the last result for a line with optional filtering by mode.

    Args:
        session: Database session
        line: Line object to fetch results for
        mode: Check mode - full, speed_test_only, or quota_check_only

    Returns:
        ResultSchema with data based on the selected mode
    """
    isp_model = ISPModel(session)
    isp = await isp_model.read(line.isp_id)

    # Initialize default values
    quota_result = None
    speedtest_result = None

    # Fetch data based on mode
    if mode in [CheckMode.FULL, CheckMode.QUOTA_CHECK_ONLY]:
        quota_model = QuotaResultModel(session)
        quota_result = await quota_model.read_last_record(line.id)

    if mode in [CheckMode.FULL, CheckMode.SPEED_TEST_ONLY]:
        speed_test_model = SpeedTestResultModel(session)
        speedtest_result = await speed_test_model.read_last_record(line.id)

    # Build result schema
    return ResultSchema(
        line_id=line.id,
        number=line.line_number,
        name=line.name,
        isp=isp.name,
        description=line.description,
        download=speedtest_result.download_speed if speedtest_result else None,
        upload=speedtest_result.upload_speed if speedtest_result else None,
        used=int(float(quota_result.data_used)) if quota_result else None,
        usage_percentage=(
            int(float(quota_result.usage_percentage)) if quota_result else None
        ),
        remaining=(
            int(float(quota_result.data_remaining)) if quota_result else None
        ),
        renewal_date=quota_result.renewal_date if quota_result else None,
        balance=quota_result.balance if quota_result else None,
    )
