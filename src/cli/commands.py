# cli/commands.py
import logging
from typing import List

from db.database import get_session
from db.model import Line
from db.models import QuotaResultModel, SpeedTestResultModel
from services.line_service import LineService

logger = logging.getLogger(__name__)


async def list_lines_command():
    """List all configured lines"""
    lines = await LineService.get_all_lines()
    print(f"\n{'ID':<5} {'Name':<20} {'ISP':<15} {'IP Address':<15}")
    print("-" * 60)
    for line in lines:
        print(
            f"{line.id:<5} {line.name:<20} {line.isp.name:<15} {line.ip_address:<15}"
        )


async def show_results_command():
    """Display last results in terminal"""
    lines = await LineService.get_all_lines()
    print(
        f"\n{'Line':<20} {'Used':<20} {'Remaining':<15} {'Download':<12} {'Upload':<12} {'Ping':<10}"
    )
    print("-" * 90)

    for line in lines:
        async with get_session() as session:
            quota_model = QuotaResultModel(session)
            speed_model = SpeedTestResultModel(session)

            quota = await quota_model.read_last_record(line_id=line.id)
            speed = await speed_model.read_last_record(line_id=line.id)

            used = (
                f"{quota.data_used}GB ({quota.usage_percentage}%)"
                if quota and quota.data_used
                else "-"
            )
            remaining = (
                f"{quota.data_remaining}GB"
                if quota and quota.data_remaining
                else "-"
            )
            download = (
                f"{speed.download_speed}Mbps"
                if speed and speed.download_speed
                else "-"
            )
            upload = (
                f"{speed.upload_speed}Mbps" if speed and speed.upload_speed else "-"
            )
            ping = f"{speed.ping}ms" if speed and speed.ping else "-"

            print(
                f"{line.name:<20} {used:<20} {remaining:<15} {download:<12} {upload:<12} {ping:<10}"
            )


def dry_run_command(lines: List[Line], args):
    """Display what would be executed in dry-run mode"""
    print(f"\n🔍 DRY RUN MODE - Would execute:")
    print(f"  Lines: {len(lines)}")
    for line in lines:
        print(f"    - {line.name} ({line.isp.name})")
    if not args.speedtest_only:
        print(f"  ✓ Quota checks (headless: {args.headless})")
    if not args.quota_only:
        print(f"  ✓ Speed tests")
    if not args.no_email:
        print(f"  ✓ Email notification")
