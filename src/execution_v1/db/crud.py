# crud.py
import logging
from typing import Optional

from sqlalchemy.ext.asyncio.session import AsyncSession

from db.model import Line
from db.models import QuotaResultModel, SpeedTestResultModel
from db.schema import ResultSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# General read result function
async def read_last_result(
    session: AsyncSession, line: Line
) -> Optional[ResultSchema]:
    quota_model = QuotaResultModel(session)
    speed_test_model = SpeedTestResultModel(session)

    quota_result = await quota_model.read_last_record(line.id)
    speedtest_result = await speed_test_model.read_last_record(line.id)

    return ResultSchema(
        line_id=line.id,
        number=line.line_number,
        name=line.name,
        isp=line.isp,
        description=line.description,
        download=speedtest_result.download_speed if speedtest_result else None,
        upload=speedtest_result.upload_speed if speedtest_result else None,
        used=quota_result.data_used if quota_result else None,
        usage_perc=quota_result.usage_percentage if quota_result else None,
        remaining=quota_result.data_remaining if quota_result else None,
        renewal_date=quota_result.renewal_date if quota_result else None,
        balance=quota_result.balance if quota_result else None,
    )
