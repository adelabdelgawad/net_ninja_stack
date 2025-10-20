# services/report_service.py
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from jinja2 import Environment
from db.schema import ResultSchema

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating and saving local reports in various formats"""

    @staticmethod
    async def save_local_report(data: List[ResultSchema], output_dir: Path = Path("reports")) -> Path:
        """
        Save HTML report to local file when email fails.

        Args:
            data: List of ResultSchema objects to include in report
            output_dir: Directory to save report file (default: reports/)

        Returns:
            Path to saved report file

        Raises:
            Exception: If report generation or save fails
        """
        try:
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = output_dir / f"report_{timestamp}.html"

            # Use same template as email
            from app.mail import html_template_string

            env = Environment()
            template = env.from_string(html_template_string)
            html_content = template.render({"data": [item.model_dump() for item in data]})

            filepath.write_text(html_content, encoding="utf-8")
            logger.info(f"Local report saved successfully: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save local report: {e}")
            raise

    @staticmethod
    async def save_report(data: List[ResultSchema], filepath: str, format: str = 'html'):
        """
        Save report in specified format.

        Args:
            data: List of ResultSchema objects to include in report
            filepath: Path to save report file
            format: Report format ('html', 'json', or 'csv')

        Raises:
            Exception: If report generation or save fails
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'html':
            await ReportService.save_html_report(data, output_path)
        elif format == 'json':
            await ReportService.save_json_report(data, output_path)
        elif format == 'csv':
            await ReportService.save_csv_report(data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Report saved successfully: {filepath} (format: {format})")

    @staticmethod
    async def save_html_report(data: List[ResultSchema], filepath: Path):
        """
        Save HTML report (existing email template).

        Args:
            data: List of ResultSchema objects
            filepath: Path to save HTML file
        """
        from app.mail import html_template_string

        env = Environment()
        template = env.from_string(html_template_string)
        html_content = template.render({"data": [item.model_dump() for item in data]})

        filepath.write_text(html_content, encoding='utf-8')

    @staticmethod
    async def save_json_report(data: List[ResultSchema], filepath: Path):
        """
        Save JSON report for programmatic access.

        Args:
            data: List of ResultSchema objects
            filepath: Path to save JSON file
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "NetNinja Network Monitoring Report",
            "total_lines": len(data),
            "lines": [item.model_dump() for item in data]
        }
        filepath.write_text(json.dumps(report, indent=2), encoding='utf-8')

    @staticmethod
    async def save_csv_report(data: List[ResultSchema], filepath: Path):
        """
        Save CSV report for Excel/spreadsheet analysis.

        Args:
            data: List of ResultSchema objects
            filepath: Path to save CSV file
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'line_number', 'name', 'isp_name', 'description',
                'download_speed', 'upload_speed', 'ping',
                'data_used', 'usage_percentage', 'data_remaining',
                'balance', 'renewal_date', 'remaining_days', 'renewal_cost'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in data:
                row_data = item.model_dump()
                # Ensure all fields exist with default values
                for field in fieldnames:
                    if field not in row_data:
                        row_data[field] = ''
                writer.writerow({k: row_data.get(k, '') for k in fieldnames})
