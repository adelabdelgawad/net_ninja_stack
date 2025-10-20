# cli/parser.py
import argparse


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for NetNinja CLI"""

    parser = argparse.ArgumentParser(
        description="NetNinja - Network Monitoring for Egyptian ISPs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --headless                    # Run all checks headless
  %(prog)s --quota-only                  # Only check quota (skip speedtest)
  %(prog)s --speedtest-only              # Only run speedtest (skip quota)
  %(prog)s --no-email                    # Run checks but don't send email
  %(prog)s --dry-run                     # Show what would run without executing
  %(prog)s --line-id 1                   # Run for specific line only
  %(prog)s --verbose                     # Detailed output
  %(prog)s --quiet                       # Minimal output
  %(prog)s --output report.html          # Save report to file instead of email
  %(prog)s --list-lines                  # List all configured lines
  %(prog)s --show-results                # Show last results
        """,
    )

    # Execution modes
    mode_group = parser.add_argument_group("Execution Modes")
    mode_group.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no GUI)",
    )
    mode_group.add_argument(
        "--quota-only",
        action="store_true",
        help="Only perform quota checks (skip speedtest)",
    )
    mode_group.add_argument(
        "--speedtest-only",
        action="store_true",
        help="Only perform speed tests (skip quota)",
    )
    mode_group.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email notification (save to file instead)",
    )
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )

    # Filtering
    filter_group = parser.add_argument_group("Filtering")
    filter_group.add_argument(
        "--line-id",
        type=int,
        metavar="ID",
        help="Run for specific line ID only",
    )
    filter_group.add_argument(
        "--isp",
        choices=["WE", "Orange", "Vodafone", "Etisalat"],
        help="Run for specific ISP only",
    )

    # Output control
    output_group = parser.add_argument_group("Output Control")
    output_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show all details)",
    )
    output_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (minimal output)",
    )
    output_group.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Save report to file instead of sending email",
    )
    output_group.add_argument(
        "--format",
        choices=["html", "json", "csv"],
        default="html",
        help="Output format (default: html)",
    )

    # Database operations
    db_group = parser.add_argument_group("Database Operations")
    db_group.add_argument(
        "--setup-db", action="store_true", help="Initialize database and exit"
    )
    db_group.add_argument(
        "--list-lines",
        action="store_true",
        help="List all configured lines and exit",
    )
    db_group.add_argument(
        "--show-results",
        action="store_true",
        help="Show last results and exit",
    )

    return parser
