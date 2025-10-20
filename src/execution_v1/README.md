# NetNinja - ISP Network Monitoring

Automated network monitoring tool for Egyptian ISP connections with quota tracking, speed testing, and comprehensive reporting.

## Features

- ✅ **WE ISP Support** - Full integration with Telecom Egypt (WE) portal
- ✅ **Automated Quota Scraping** - Monitor data usage and remaining quota
- ✅ **Speed Testing** - Integrated Ookla speedtest protocol
- ✅ **Email Reports** - Automated HTML email notifications
- ✅ **Encrypted Credentials** - Fernet symmetric encryption for portal passwords
- ✅ **Multiple Report Formats** - Export to HTML, JSON, or CSV
- ✅ **File-Based Logging** - Automatic log rotation (keeps latest 7 files)
- ✅ **Flexible CLI** - Multiple execution modes and filters
- ✅ **Retry Logic** - Automatic retry with exponential backoff for email failures

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd net-ninja/src/execution_v1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize database**
   ```bash
   python main.py --setup-db
   ```

5. **Add ISP lines** (use setup_database.py or database management tool)

### Basic Usage

```bash
# Run all checks in headless mode
python main.py --headless

# Check quota only (skip speed test)
python main.py --quota-only --headless

# Run speed test only
python main.py --speedtest-only

# Save report to file (no email)
python main.py --output report.html --no-email

# Show last results
python main.py --show-results

# List configured lines
python main.py --list-lines

# Dry run (show what would execute)
python main.py --dry-run
```

## Configuration

### Environment Variables

Edit `.env` file with your settings:

```env
# Database
DATABASE_NAME=app.db
DATABASE_SERVER=localhost
DATABASE_PORT=1433
DATABASE_USERNAME=user
DATABASE_PASSWORD=pass

# Email/SMTP
EMAIL_SUBJECT=Daily Network Check
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SENDER=your.email@gmail.com
EMAIL_SENDER_ALIAS=NetNinja Monitor

# Execution Control
EXEC_SEMAPHORE_LIMIT=2
EXEC_MAX_RETRY_ATTEMPTS=1

# Speed Test Settings
SPEEDTEST_DOWNLOAD_CHUNK_SIZE=102400
SPEEDTEST_UPLOAD_CHUNK_SIZE=4194304
SPEEDTEST_TEST_COUNT=10
SPEEDTEST_TIMEOUT=30
```

### Gmail Setup

1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password as `EMAIL_PASSWORD`

## Advanced Usage

### Filtering

```bash
# Run for specific line only
python main.py --line-id 1

# Run for specific ISP only
python main.py --isp WE
```

### Output Control

```bash
# Verbose output
python main.py --verbose

# Quiet mode (errors only)
python main.py --quiet

# Save report in different formats
python main.py --output report.json --format json
python main.py --output report.csv --format csv
```

### Scheduling with Windows Task Scheduler

Create a batch file `run_netninja.bat`:
```batch
@echo off
cd /d E:\github_repositories\net-ninja\src\execution_v1
python main.py --headless
```

Schedule it to run daily via Task Scheduler.

## Project Structure

```
execution_v1/
├── app/                    # Application modules
│   ├── async_speedtest.py  # Speed test implementation
│   ├── mail.py             # Email service
│   ├── quota_checker/      # ISP scrapers
│   │   └── we.py           # WE (Telecom Egypt) scraper
│   └── wait.py             # Selenium helpers
├── core/                   # Core configuration
│   ├── config.py           # Settings management
│   ├── encryption.py       # Credential encryption
│   ├── logging_config.py   # File-based logging
│   └── scraper_config.py   # Scraper selectors & timeouts
├── db/                     # Database layer
│   ├── model.py            # SQLModel definitions
│   ├── models/             # Repository pattern
│   ├── schema.py           # Pydantic schemas
│   └── validators.py       # Input validation
├── services/               # Business logic
│   ├── line_service.py     # Line management
│   ├── notification_service.py  # Email notifications
│   ├── quota_service.py    # Quota scraping
│   ├── report_service.py   # Report generation
│   └── speedtest_service.py  # Speed testing
├── logs/                   # Log files (auto-rotated)
├── reports/                # Generated reports
├── main.py                 # CLI entry point
└── .env                    # Configuration (create from .env.example)
```

## Security

### Credential Encryption

- Portal passwords are encrypted using Fernet symmetric encryption
- Encryption key stored in `.secret.key` file
- **IMPORTANT**: Backup `.secret.key` file - without it, encrypted passwords cannot be recovered
- Existing passwords automatically encrypted on first run

### Encryption Key Management

```bash
# Key is auto-generated on first run
python main.py --headless

# Backup your encryption key
cp .secret.key .secret.key.backup
```

## Logs

- Log files stored in `logs/` directory
- Format: `netninja_YYYYMMDD_HHMMSS.log`
- Automatic rotation keeps latest 7 files
- Both file and console output

## Troubleshooting

### Email Failures

- Email failures automatically retry 3 times with exponential backoff
- If all retries fail, report saved to `reports/` directory
- Check SMTP settings in `.env`

### Scraping Failures

- Check WE portal selector configuration in `core/scraper_config.py`
- Run in non-headless mode to debug: `python main.py` (without --headless)
- Check logs in `logs/` directory

### Database Issues

```bash
# Reinitialize database (WARNING: deletes all data)
rm app.db
python main.py --setup-db
```

## CLI Reference

### Execution Modes
- `--headless` - Run browser in headless mode (no GUI)
- `--quota-only` - Only perform quota checks
- `--speedtest-only` - Only run speed tests
- `--no-email` - Skip email notification
- `--dry-run` - Show what would execute without running

### Filtering
- `--line-id ID` - Run for specific line ID
- `--isp ISP` - Run for specific ISP (WE, Orange, Vodafone, Etisalat)

### Output Control
- `--verbose, -v` - Verbose output
- `--quiet, -q` - Quiet mode (errors only)
- `--output FILE, -o FILE` - Save report to file
- `--format FORMAT` - Output format (html, json, csv)

### Database Operations
- `--setup-db` - Initialize database and exit
- `--list-lines` - List all configured lines and exit
- `--show-results` - Show last results and exit

## Development

### Requirements

- Python 3.10+
- SQLite3
- Chrome/Chromium (for Selenium)

### Dependencies

See `requirements.txt` for full list of dependencies.

## License

MIT License

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## Changelog

### Version 2.0
- ✅ File-based logging with automatic rotation
- ✅ Credential encryption
- ✅ Enhanced CLI with multiple modes
- ✅ Multiple report formats (HTML, JSON, CSV)
- ✅ Email retry logic with fallback
- ✅ Configuration externalization
- ✅ Database query optimization
- ✅ Input validation

### Version 1.0
- Initial release
- WE ISP support
- Basic quota scraping
- Speed testing
- Email notifications
