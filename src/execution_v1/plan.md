# NetNinja CMD Application - Enhancement Plan

## Executive Summary

This document outlines targeted improvements for NetNinja execution_v1 as a **command-line application**. The focus is on reliability, security, maintainability, and usability for automated execution via Windows Task Scheduler or manual runs.

**Application Type**: Command-line tool (CMD/Terminal)
**Deployment**: Single-user, scheduled execution
**Current Version**: 1.0
**Target Version**: 2.0

---

## Critical Issues Identified

### 🔴 P0 - Blocking Issues (Fix Immediately)


## Enhancement Roadmap

### Priority Levels
- **P0**: Critical bugs, security vulnerabilities (fix now)
- **P1**: High-priority features, significant improvements
- **P2**: Quality improvements, optimization
- **P3**: Nice-to-have enhancements

---

## P0 - Critical Enhancements

### 3. Security: Encrypt Portal Credentials
**Priority**: P0 - Critical
**Impact**: High
**Effort**: Medium
**Files**: `db/model.py:47`, `app/quota_checker/we.py:85,94`

**Current Issue**:
- Portal passwords stored in plaintext in `lines.portal_password` field
- Database file unencrypted on disk
- Security risk if system compromised

**Enhancement**:
Implement encryption at rest using Fernet symmetric encryption

**Implementation**:

1. **Create encryption module**
```python
# core/encryption.py
from cryptography.fernet import Fernet
from pathlib import Path

class CredentialEncryption:
    def __init__(self, key_file: Path = Path(".secret.key")):
        self.key_file = key_file
        self.cipher = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            print(f"⚠️  Encryption key created: {self.key_file}")
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

2. **Update Line model**
```python
# db/model.py - Add helper methods
from core.encryption import CredentialEncryption

crypto = CredentialEncryption()

class Line(SQLModel, table=True):
    # ... existing fields ...

    def set_password(self, plaintext: str):
        """Encrypt and store password"""
        self.portal_password = crypto.encrypt(plaintext)

    def get_password(self) -> str:
        """Decrypt and return password"""
        return crypto.decrypt(self.portal_password)
```

3. **Update scraper to use decryption**
```python
# app/quota_checker/we.py:94
self.driver.find_element(
    By.ID, "login_password_input_01"
).send_keys(self.line.get_password())  # Use decrypted password
```

4. **Migration script for existing data**
```python
# migrations/encrypt_passwords.py
async def encrypt_existing_passwords():
    async with get_session() as session:
        lines = await session.execute(select(Line))
        for line in lines.scalars():
            if not line.portal_password.startswith("gAAAAA"):  # Not encrypted
                line.set_password(line.portal_password)
        await session.commit()
```

**Dependencies**: `cryptography`
**Testing**: Verify scraping still works after encryption
**Documentation**: Update setup docs with key file warning

---

### 4. Error Handling: Email Failure Fallback
**Priority**: P0 - Critical
**Impact**: High
**Effort**: Low
**Files**: `main.py:128-134`, `services/notification_service.py`, `app/mail.py`

**Current Issue**:
- Email send failure causes application crash
- No fallback mechanism
- Results collected but lost on SMTP failure

**Enhancement**:
Add graceful error handling with local HTML report fallback

**Implementation**:

1. **Add fallback report generation**
```python
# services/report_service.py (NEW FILE)
from pathlib import Path
from datetime import datetime
from jinja2 import Environment

class ReportService:
    @staticmethod
    async def save_local_report(data: List[ResultSchema], output_dir: Path = Path("reports")):
        """Save HTML report to local file when email fails"""
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"report_{timestamp}.html"

        # Use same template as email
        env = Environment()
        template = env.from_string(html_template_string)
        html_content = template.render({"data": [item.model_dump() for item in data]})

        filepath.write_text(html_content, encoding="utf-8")
        return filepath
```

2. **Update notification service with retry and fallback**
```python
# services/notification_service.py
import asyncio
from services.report_service import ReportService

class NotificationService:
    @staticmethod
    async def send_daily_report(subject: str, sender: str, data: List[QuotaResult], max_retries: int = 3):
        async with get_session() as session:
            email_model = EmailModel(session)
            recipients = await email_model.read_all()
            recipient_emails = [r.recipient for r in recipients]

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                await send_email(subject, recipient_emails, sender, data)
                logger.info("✅ Email sent successfully")
                return True
            except Exception as e:
                logger.warning(f"⚠️  Email attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s

        # Fallback: Save local report
        try:
            filepath = await ReportService.save_local_report(data)
            logger.error(f"❌ Email failed after {max_retries} attempts")
            logger.info(f"📄 Local report saved: {filepath}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to save local report: {e}")
            return False
```

3. **Update main.py to handle email failure gracefully**
```python
# main.py:128-136
logger.info("📧 Preparing daily report...")
latest_results = await QuotaService.get_latest_results(lines)

email_success = await NotificationService.send_daily_report(
    subject=settings.email.subject,
    sender=settings.email.sender_email,
    data=latest_results,
)

if email_success:
    logger.info("✅ All tasks completed successfully!")
else:
    logger.warning("⚠️  Tasks completed but email delivery failed. Check reports/ directory.")

await engine.dispose()
```

**Acceptance Criteria**:
- Application never crashes on SMTP failure
- Up to 3 retry attempts with exponential backoff
- Local HTML report saved in `reports/` directory on failure
- User notified of fallback location

---

### 5. Configuration: Externalize All Hardcoded Values
**Priority**: P0 - Critical
**Impact**: Medium
**Effort**: Low
**Files**: Multiple

**Current Issues**:
- Magic numbers throughout code
- Hardcoded timeouts: `app/quota_checker/we.py:75,96,111,114,129,172,177`
- Hardcoded CSS selectors: `app/quota_checker/we.py:115-117,169-170`
- Hardcoded chunk sizes: `app/async_speedtest.py:15-16`
- Semaphore limit: `main.py:98`

**Enhancement**:
Create centralized configuration for all tunable parameters

**Implementation**:

1. **Create scraper configuration**
```python
# core/scraper_config.py (NEW FILE)
from pydantic import BaseModel

class ScraperTimeouts(BaseModel):
    """Timeout configurations for web scraping (shared across all ISPs)"""
    login_wait: int = 5
    page_load_wait: int = 7
    element_wait: int = 2
    post_action_delay: float = 0.5

class WEScraperSelectors(BaseModel):
    """CSS selectors for WE (Telecom Egypt) portal"""
    # Login page selectors
    login_id: str = "login_loginid_input_01"
    login_type: str = "login_input_type_01"
    login_password: str = "login_password_input_01"
    login_button: str = "login-withecare"
    account_type_selector: str = ".ant-select-item-option-active .ant-space-item:nth-child(2) > span"

    # Overview page selectors
    balance: str = "#_bes_window > main > div > div > div.ant-row > div:nth-child(2) > div > div > div > div > div:nth-child(3) > div:nth-child(1)"
    data_used: str = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)"
    data_remaining: str = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)"

    # Renewal page selectors
    renewal_cost: str = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(3) > div > span:nth-child(2) > div > div:nth-child(1)"
    renewal_date: str = "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(4) > div > span"

# Shared timeout configuration
timeouts = ScraperTimeouts()

# WE-specific selectors
we_selectors = WEScraperSelectors()

# Note: When implementing Orange, create OrangeScraperSelectors class
# orange_selectors = OrangeScraperSelectors()
```

2. **Update environment config**
```python
# core/config.py - Add new settings classes
class ExecutionSettings(BaseSettings):
    """Execution control settings"""
    semaphore_limit: int = 2
    max_retry_attempts: int = 1

    model_config = SettingsConfigDict(
        env_prefix="EXEC_",
        env_file=".env",
        extra="ignore"
    )

class SpeedTestSettings(BaseSettings):
    """Speed test configuration"""
    download_chunk_size: int = 102400  # 100KB
    upload_chunk_size: int = 4194304   # 4MB
    test_count: int = 10
    latency_test_count: int = 3
    timeout: int = 30
    max_download_time: int = 15
    max_upload_time: int = 10

    model_config = SettingsConfigDict(
        env_prefix="SPEEDTEST_",
        env_file=".env",
        extra="ignore"
    )

class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    email: EmailSettings = EmailSettings()
    execution: ExecutionSettings = ExecutionSettings()
    speedtest: SpeedTestSettings = SpeedTestSettings()
```

3. **Update code to use config**
```python
# main.py:98
semaphore = asyncio.Semaphore(settings.execution.semaphore_limit)

# app/quota_checker/we.py - Import and use WE-specific config
from core.scraper_config import timeouts, we_selectors

# Replace line 75:
await WebDriverWait(self.driver, timeouts.login_wait).until(...)

# Replace line 82:
self.driver.find_element(By.ID, we_selectors.login_id).click()

# Replace line 84-85:
self.driver.find_element(By.ID, we_selectors.login_id).send_keys(self.line.portal_username)

# Replace line 88-89 (account type selector):
self.driver.find_element(By.CSS_SELECTOR, we_selectors.account_type_selector).click()

# Replace line 91:
self.driver.find_element(By.ID, we_selectors.login_password).click()

# Replace line 93-94:
self.driver.find_element(By.ID, we_selectors.login_password).send_keys(self.line.portal_password)

# Replace line 95:
self.driver.find_element(By.ID, we_selectors.login_button).click()

# Replace line 132-134 (overview page):
self.balance = self.driver.find_element(By.CSS_SELECTOR, we_selectors.balance).text
self.used = float(self.driver.find_element(By.CSS_SELECTOR, we_selectors.data_used).text)
self.remaining = float(self.driver.find_element(By.CSS_SELECTOR, we_selectors.data_remaining).text)

# Replace line 184-187 (renewal page):
self.renewal_cost = float(self.driver.find_element(By.CSS_SELECTOR, we_selectors.renewal_cost).text)
renewal_date_element = self.driver.find_element(By.CSS_SELECTOR, we_selectors.renewal_date).text

# app/async_speedtest.py - Use config
from core.config import settings

DOWNLOAD_CHUNK_SIZE = settings.speedtest.download_chunk_size
UPLOAD_CHUNK_SIZE = settings.speedtest.upload_chunk_size
```

4. **Create .env.example**
```bash
# .env.example
# Database Configuration
DATABASE_NAME=app.db
DATABASE_SERVER=localhost
DATABASE_PORT=1433
DATABASE_USERNAME=user
DATABASE_PASSWORD=pass

# Email Configuration
EMAIL_SUBJECT=Daily Network Check
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SENDER=your.email@gmail.com
EMAIL_SENDER_ALIAS=NetNinja Monitor
EMAIL_CC_ADDRESS=

# Execution Configuration
EXEC_SEMAPHORE_LIMIT=2
EXEC_MAX_RETRY_ATTEMPTS=1

# Speed Test Configuration
SPEEDTEST_DOWNLOAD_CHUNK_SIZE=102400
SPEEDTEST_UPLOAD_CHUNK_SIZE=4194304
SPEEDTEST_TEST_COUNT=10
SPEEDTEST_TIMEOUT=30
```

**Benefits**:
- Easy portal selector updates without code changes
- Tunable performance parameters
- Environment-specific configurations
- Better maintainability

---

## P1 - High Priority Enhancements

### 6. Logging: Replace Database Logging with File-Based Rotation
**Priority**: P1 - High
**Impact**: High (Simplification)
**Effort**: Medium
**Files**: `app/logger.py`, `db/model.py`, All scrapers and services

**Current Issues**:
- Database logging adds unnecessary complexity
- Custom async logger with singleton pattern (`app/logger.py`)
- Process ID generation and tracking across all operations
- Logs stored in database table consuming storage
- No easy way to view logs without database queries
- Dual logging: Both standard logging AND database logging
- Log table grows indefinitely without rotation

**Enhancement**:
Replace database logging with standard Python file-based logging with automatic rotation (keep latest 7 files)

**Implementation**:

1. **Remove database logging infrastructure**
```python
# Files to modify/remove:
# - DELETE: app/logger.py (entire custom logger)
# - DELETE: db/model.py - Log model and table
# - DELETE: db/models/log_model.py (if exists)
# - MODIFY: All files using `from app.logger import logger`

# Remove Log model from db/model.py
class Log(SQLModel, table=True):  # ❌ DELETE THIS ENTIRE CLASS
    __tablename__ = "logs"
    id: int | None = Field(default=None, primary_key=True)
    process_id: str | None = Field(default=None, max_length=50, index=True)
    # ... DELETE ALL
```

2. **Create file-based logging configuration**
```python
# core/logging_config.py (REPLACE or CREATE)
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_file_logging(log_dir: Path = Path("logs"), max_files: int = 7):
    """
    Setup file-based logging with rotation.

    Args:
        log_dir: Directory to store log files
        max_files: Number of log files to keep (default: 7)

    Creates daily log files with format: netninja_YYYYMMDD_HHMMSS.log
    Automatically removes old log files keeping only the latest 7.
    """
    # Create logs directory
    log_dir.mkdir(exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"netninja_{timestamp}.log"

    # Clean up old log files (keep only latest max_files)
    cleanup_old_logs(log_dir, max_files)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # File handler - write to daily log file
            logging.FileHandler(log_file, encoding='utf-8'),
            # Console handler - write to stdout
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_file}")

    return log_file

def cleanup_old_logs(log_dir: Path, max_files: int = 7):
    """
    Remove old log files, keeping only the latest N files.

    Args:
        log_dir: Directory containing log files
        max_files: Number of most recent files to keep
    """
    # Get all log files sorted by modification time (newest first)
    log_files = sorted(
        log_dir.glob("netninja_*.log"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    # Remove files beyond max_files limit
    for old_file in log_files[max_files:]:
        try:
            old_file.unlink()
            print(f"Removed old log file: {old_file.name}")
        except Exception as e:
            print(f"Failed to remove {old_file.name}: {e}")

def get_logger(name: str) -> logging.Logger:
    """Get logger instance for a module"""
    return logging.getLogger(name)
```

3. **Update main.py to use file logging**
```python
# main.py - Replace logging setup
from core.logging_config import setup_file_logging

# Remove old basicConfig
# logging.basicConfig(...)  # ❌ DELETE

async def main(headless: bool) -> None:
    # Initialize file-based logging at startup
    log_file = setup_file_logging(log_dir=Path("logs"), max_files=7)
    logger = logging.getLogger(__name__)

    logger.info("="*60)
    logger.info("NetNinja Execution Started")
    logger.info(f"Log file: {log_file}")
    logger.info("="*60)

    # Rest of main logic...
    # No process_id needed anymore!
```

4. **Remove process_id from all scrapers and services**
```python
# app/quota_checker/we.py - Remove process ID logic

class WEWebScraper:
    def __init__(self, line: Line, headless: Optional[bool] = False):
        # self.pid = str(uuid.uuid4())  # ❌ DELETE THIS
        self.line = line
        self.headless = headless
        # ... rest of init

    async def __aenter__(self):
        # await logger.info(self.pid, f"Launching browser...")  # ❌ OLD
        logger.info(f"Launching browser for {self.line.name}")  # ✅ NEW
        # ... rest

    async def login(self) -> bool:
        try:
            # await logger.info(self.pid, f"Logging in...")  # ❌ OLD
            logger.info(f"Logging in for {self.line.name}")  # ✅ NEW
            # ... rest
        except Exception as e:
            # await logger.error(self.pid, f"Login failed: {e}")  # ❌ OLD
            logger.error(f"Login failed for {self.line.name}: {e}")  # ✅ NEW

# Remove from QuotaResult creation:
result = QuotaResult(
    line_id=self.line.id,
    # process_id=self.pid,  # ❌ DELETE THIS
    data_used=self.used,
    # ... rest
)
```

5. **Update database models**
```python
# db/model.py - Remove process_id from results

class QuotaResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # process_id: str = Field(index=True)  # ❌ DELETE THIS
    line_id: int = Field(foreign_key="lines.id")
    data_used: int | None = None
    # ... rest (no process_id)

class SpeedTestResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # process_id: str = Field(index=True)  # ❌ DELETE THIS
    line_id: int = Field(foreign_key="lines.id")
    ping: int | None = None
    # ... rest (no process_id)
```

6. **Update all service files**
```python
# services/speedtest_service.py - Remove process_id references

class SpeedTestService:
    @staticmethod
    async def run_and_save_speedtest(line: Line) -> Optional[SpeedTestResult]:
        st = AsyncSpeedtest(line.ip_address)
        logger = logging.getLogger(__name__)  # Use standard logger

        try:
            # await logger.info(st.process_id, "Getting Configurations")  # ❌ OLD
            logger.info(f"Getting speedtest config for {line.name}")  # ✅ NEW

            if await st.get_config():
                # await logger.info(st.process_id, "Finding best server")  # ❌ OLD
                logger.info(f"Finding best server for {line.name}")  # ✅ NEW
                # ... rest

            result = SpeedTestResult(
                line_id=line.id,
                # process_id=st.process_id,  # ❌ DELETE
                ping=st.ping,
                upload_speed=upload,
                download_speed=download,
                public_ip=st.public_ip,
            )
```

7. **Update app/async_speedtest.py**
```python
# app/async_speedtest.py - Remove process_id

class AsyncSpeedtest:
    def __init__(self, source_address: Optional[str] = None, debug: bool = False):
        # self.process_id = str(uuid4())  # ❌ DELETE
        self.source_address = source_address
        self.debug = debug
        # ... rest (no process_id)

    async def fetch(self, session, url, method="GET", data=None):
        # No need to log process_id anywhere
        pass
```

8. **Create database migration to remove Log table and process_id columns**
```bash
# After Alembic is set up (Enhancement #9)
alembic revision -m "Remove logging table and process_id columns"

# In migration file:
def upgrade():
    # Drop logs table
    op.drop_table('logs')

    # Remove process_id from quota_results
    op.drop_column('quota_results', 'process_id')

    # Remove process_id from speed_test_results
    op.drop_column('speed_test_results', 'process_id')

def downgrade():
    # Restore if needed (optional)
    pass
```

**Benefits**:
- ✅ **Simpler architecture**: No custom async logger, no singleton pattern
- ✅ **Standard Python logging**: Uses built-in logging module
- ✅ **Easy log viewing**: Just open text files in `logs/` directory
- ✅ **Automatic cleanup**: Keeps only latest 7 log files
- ✅ **No database pollution**: Logs don't consume database space
- ✅ **Better debugging**: One log file per execution with timestamp
- ✅ **Smaller database**: Remove Log table and process_id columns
- ✅ **Reduced complexity**: No process ID tracking needed
- ✅ **Faster execution**: No async database writes for every log
- ✅ **Better troubleshooting**: Each execution has its own log file

**Log File Structure**:
```
logs/
├── netninja_20251020_080000.log  (Latest - today's run)
├── netninja_20251019_080000.log  (Yesterday)
├── netninja_20251018_080000.log
├── netninja_20251017_080000.log
├── netninja_20251016_080000.log
├── netninja_20251015_080000.log
└── netninja_20251014_080000.log  (7 days ago - will be deleted on next run)
```

**Log Format Example**:
```
2025-10-20 08:00:01 | INFO     | __main__ | main:75 | Database found: app.db
2025-10-20 08:00:02 | INFO     | __main__ | main:95 | Found 3 line(s) to process
2025-10-20 08:00:02 | INFO     | __main__ | main:101 | Starting quota checks...
2025-10-20 08:00:03 | INFO     | app.quota_checker.we | login:73 | Logging in for WE Line 1
2025-10-20 08:00:05 | INFO     | app.quota_checker.we | login:98 | WE Line 1 logged in successfully
2025-10-20 08:00:06 | INFO     | app.quota_checker.we | scrap_overview_page:149 | Extracted values for WE Line 1 - Balance: 50.0, Used: 120.5, Remaining: 179.5, Usage Percentage: 40.17%
2025-10-20 08:00:10 | INFO     | services.speedtest_service | run_and_save_speedtest:32 | Getting speedtest config for WE Line 1
2025-10-20 08:00:45 | INFO     | __main__ | main:136 | All tasks completed successfully!
```

**Acceptance Criteria**:
- ✅ All database logging code removed
- ✅ File-based logging implemented with rotation
- ✅ Maximum 7 log files retained
- ✅ Each execution creates new timestamped log file
- ✅ Logs written to both file and console
- ✅ No process_id in code or database
- ✅ Log table removed from database schema
- ✅ Smaller, cleaner database structure

---

### 7. CLI: Enhanced Command-Line Interface
**Priority**: P1 - High
**Impact**: High
**Effort**: Low
**Files**: `main.py:140-148`

**Current Issues**:
- Only one CLI option: `--headless`
- No ability to run specific operations
- No dry-run mode
- No verbose/quiet output control

**Enhancement**:
Rich CLI with multiple operation modes and output control

**Implementation**:

```python
# main.py - Enhanced argument parser
import argparse

def parse_arguments():
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
        """
    )

    # Execution modes
    mode_group = parser.add_argument_group('Execution Modes')
    mode_group.add_argument('--headless', action='store_true',
                           help='Run browser in headless mode (no GUI)')
    mode_group.add_argument('--quota-only', action='store_true',
                           help='Only perform quota checks (skip speedtest)')
    mode_group.add_argument('--speedtest-only', action='store_true',
                           help='Only perform speed tests (skip quota)')
    mode_group.add_argument('--no-email', action='store_true',
                           help='Skip email notification (save to file instead)')
    mode_group.add_argument('--dry-run', action='store_true',
                           help='Show what would be executed without running')

    # Filtering
    filter_group = parser.add_argument_group('Filtering')
    filter_group.add_argument('--line-id', type=int, metavar='ID',
                             help='Run for specific line ID only')
    filter_group.add_argument('--isp', choices=['WE', 'Orange', 'Vodafone', 'Etisalat'],
                             help='Run for specific ISP only')

    # Output control
    output_group = parser.add_argument_group('Output Control')
    output_group.add_argument('--verbose', '-v', action='store_true',
                             help='Verbose output (show all details)')
    output_group.add_argument('--quiet', '-q', action='store_true',
                             help='Quiet mode (minimal output)')
    output_group.add_argument('--output', '-o', metavar='FILE',
                             help='Save report to file instead of sending email')
    output_group.add_argument('--format', choices=['html', 'json', 'csv'],
                             default='html', help='Output format (default: html)')

    # Database operations
    db_group = parser.add_argument_group('Database Operations')
    db_group.add_argument('--setup-db', action='store_true',
                         help='Initialize database and exit')
    db_group.add_argument('--list-lines', action='store_true',
                         help='List all configured lines and exit')
    db_group.add_argument('--show-results', action='store_true',
                         help='Show last results and exit')

    return parser.parse_args()

async def main() -> None:
    args = parse_arguments()

    # Set logging level based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Database operations (exit after)
    if args.setup_db:
        await check_and_initialize_database()
        return

    if args.list_lines:
        lines = await LineService.get_all_lines()
        print(f"\n{'ID':<5} {'Name':<20} {'ISP':<15} {'IP Address':<15}")
        print("-" * 60)
        for line in lines:
            print(f"{line.id:<5} {line.name:<20} {line.isp.name:<15} {line.ip_address:<15}")
        return

    if args.show_results:
        await display_last_results()
        return

    # Dry run mode
    if args.dry_run:
        lines = await LineService.get_all_lines()
        if args.line_id:
            lines = [l for l in lines if l.id == args.line_id]
        print(f"\n🔍 DRY RUN MODE - Would execute:")
        print(f"  Lines: {len(lines)}")
        if not args.speedtest_only:
            print(f"  ✓ Quota checks (headless: {args.headless})")
        if not args.quota_only:
            print(f"  ✓ Speed tests")
        if not args.no_email:
            print(f"  ✓ Email notification")
        return

    # Normal execution with filters
    is_new_database = await check_and_initialize_database()
    if is_new_database:
        logger.warning("Database was just created. Please add ISP lines.")
        return

    lines = await LineService.get_all_lines()

    # Apply filters
    if args.line_id:
        lines = [l for l in lines if l.id == args.line_id]
        if not lines:
            logger.error(f"Line ID {args.line_id} not found")
            return

    if args.isp:
        lines = [l for l in lines if l.isp.name == args.isp]

    if not lines:
        logger.warning("No lines found matching filters")
        return

    logger.info(f"📊 Processing {len(lines)} line(s)")

    # Execute based on mode
    semaphore = asyncio.Semaphore(settings.execution.semaphore_limit)

    if not args.speedtest_only:
        logger.info("🔍 Starting quota checks...")
        await asyncio.gather(
            *(bound_quota_task(line, semaphore, args.headless) for line in lines),
            return_exceptions=True
        )

    if not args.quota_only:
        logger.info("🚀 Starting speed tests...")
        await asyncio.gather(
            *(SpeedTestService.run_and_save_speedtest(line) for line in lines),
            return_exceptions=True
        )

    # Generate report
    latest_results = await QuotaService.get_latest_results(lines)

    if args.output:
        # Save to file
        await ReportService.save_report(latest_results, args.output, args.format)
        logger.info(f"📄 Report saved to: {args.output}")
    elif not args.no_email:
        # Send email
        await NotificationService.send_daily_report(
            subject=settings.email.subject,
            sender=settings.email.sender_email,
            data=latest_results
        )

    logger.info("✅ Completed successfully!")
    await engine.dispose()
```

**New helper functions**:
```python
async def display_last_results():
    """Display last results in terminal"""
    lines = await LineService.get_all_lines()
    print(f"\n{'Line':<20} {'Used':<15} {'Remaining':<15} {'Download':<12} {'Upload':<12}")
    print("-" * 80)

    for line in lines:
        async with get_session() as session:
            quota = await QuotaResultModel(session).read_last_record(line_id=line.id)
            speed = await SpeedTestResultModel(session).read_last_record(line_id=line.id)

            used = f"{quota.data_used}GB ({quota.usage_percentage}%)" if quota else "N/A"
            remaining = f"{quota.data_remaining}GB" if quota else "N/A"
            download = f"{speed.download_speed}Mbps" if speed else "N/A"
            upload = f"{speed.upload_speed}Mbps" if speed else "N/A"

            print(f"{line.name:<20} {used:<15} {remaining:<15} {download:<12} {upload:<12}")
```

**Benefits**:
- Flexible execution modes for different use cases
- Better integration with automation scripts
- Quick status checks without full execution
- File output option for CI/CD pipelines

---

### 8. Output: Report Generation in Multiple Formats
**Priority**: P1 - High
**Impact**: Medium
**Effort**: Medium
**Files**: `services/report_service.py` (new)

**Enhancement**:
Generate reports in multiple formats (HTML, JSON, CSV) for different use cases

**Implementation**:

```python
# services/report_service.py
import csv
import json
from pathlib import Path
from typing import List
from datetime import datetime
from jinja2 import Environment
from db.schema import ResultSchema

class ReportService:
    @staticmethod
    async def save_report(data: List[ResultSchema], filepath: str, format: str = 'html'):
        """Save report in specified format"""
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'html':
            await ReportService.save_html_report(data, output_path)
        elif format == 'json':
            await ReportService.save_json_report(data, output_path)
        elif format == 'csv':
            await ReportService.save_csv_report(data, output_path)

    @staticmethod
    async def save_html_report(data: List[ResultSchema], filepath: Path):
        """Save HTML report (existing email template)"""
        from app.mail import html_template_string

        env = Environment()
        template = env.from_string(html_template_string)
        html_content = template.render({"data": [item.model_dump() for item in data]})

        filepath.write_text(html_content, encoding='utf-8')

    @staticmethod
    async def save_json_report(data: List[ResultSchema], filepath: Path):
        """Save JSON report for programmatic access"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "lines": [item.model_dump() for item in data]
        }
        filepath.write_text(json.dumps(report, indent=2), encoding='utf-8')

    @staticmethod
    async def save_csv_report(data: List[ResultSchema], filepath: Path):
        """Save CSV report for Excel/spreadsheet analysis"""
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'line_number', 'name', 'isp_name', 'description',
                'download_speed', 'upload_speed', 'ping',
                'data_used', 'usage_percentage', 'data_remaining',
                'balance', 'renewal_date', 'remaining_days'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in data:
                writer.writerow(item.model_dump())
```

**Usage**:
```bash
# Generate HTML report
python main.py --output reports/daily_report.html

# Generate JSON for API consumption
python main.py --output reports/daily_report.json --format json

# Generate CSV for Excel
python main.py --output reports/daily_report.csv --format csv
```

---

### 9. ISP Support: Orange Scraper Implementation
**Priority**: P1 - High
**Impact**: High
**Effort**: High
**Files**: `app/quota_checker/orange.py`, `services/quota_service.py`

**Current Issue**:
- Orange scraper is stub only
- Only WE ISP supported
- Cannot monitor Orange connections

**Enhancement**:
Full implementation of Orange Egypt portal scraper

**Implementation Steps**:

1. **Research Orange portal** (manual task)
   - URL: https://www.orange.eg/en/myorange
   - Document login flow
   - Identify quota data location
   - Map CSS selectors

2. **Implement scraper** (similar to WE)
```python
# app/quota_checker/orange.py
class OrangeWebScraper:
    """Orange Egypt Scraping Class"""

    failed_list = []
    PORTAL_URL = "https://www.orange.eg/en/myorange/login"

    def __init__(self, line: Line, headless: bool = False):
        self.pid = str(uuid.uuid4())
        self.line = line
        self.headless = headless
        # ... same structure as WE scraper

    async def login(self) -> bool:
        # Implement Orange-specific login
        pass

    async def scrap_quota_page(self) -> bool:
        # Implement Orange quota extraction
        pass
```

3. **Update quota service routing**
```python
# services/quota_service.py:32
if line.isp_id == 1:  # WE
    async with WEWebScraper(line, headless) as scraper:
        await scraper.login()
        await scraper.scrap_overview_page()
        await scraper.scrap_renewaldate_page()
elif line.isp_id == 2:  # Orange
    async with OrangeWebScraper(line, headless) as scraper:
        await scraper.login()
        await scraper.scrap_quota_page()
```

4. **Add Orange-specific selectors to config**
```python
# core/scraper_config.py - Add Orange selectors class
class OrangeScraperSelectors(BaseModel):
    """CSS selectors for Orange Egypt portal"""
    # Login page selectors (to be populated after portal research)
    login_username_id: str = "..."
    login_password_id: str = "..."
    login_button_id: str = "..."

    # Quota page selectors (to be populated)
    data_used: str = "..."
    data_remaining: str = "..."
    balance: str = "..."
    renewal_date: str = "..."

# Instantiate Orange selectors
orange_selectors = OrangeScraperSelectors()
```

**Usage in Orange scraper**:
```python
# app/quota_checker/orange.py - Import Orange-specific config
from core.scraper_config import timeouts, orange_selectors

async def login(self):
    await WebDriverWait(self.driver, timeouts.login_wait).until(...)
    self.driver.find_element(By.ID, orange_selectors.login_username_id).click()
    self.driver.find_element(By.ID, orange_selectors.login_username_id).send_keys(self.line.portal_username)
    # ... rest of login logic using orange_selectors
```

**Deliverable**: Fully functional Orange scraper with same reliability as WE

---

### 10. Database: Migration Framework with Alembic
**Priority**: P1 - High
**Impact**: Medium
**Effort**: Medium
**Files**: New alembic directory

**Current Issue**:
- No schema versioning
- Manual SQL for schema changes
- Risk of data loss on upgrades

**Enhancement**:
Add Alembic for database migrations

**Implementation**:

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic
```

```python
# alembic/env.py - Configure for async SQLite
from core.config import settings
from db.model import SQLModel

config.set_main_option('sqlalchemy.url', f'sqlite:///{settings.database.name}')
target_metadata = SQLModel.metadata
```

```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///app.db
```

```python
# Create initial migration
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Create Date: 2025-01-20
"""

def upgrade():
    # Generated schema creation
    pass

def downgrade():
    # Generated schema rollback
    pass
```

**Usage**:
```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Update setup_database.py**:
```python
# Run Alembic migrations instead of direct table creation
import subprocess

def run_migrations():
    subprocess.run(["alembic", "upgrade", "head"], check=True)
```

---

### 11. Logging: Improved Console Output (Optional with Enhancement #6)
**Priority**: P2 - Medium
**Impact**: Low
**Effort**: Low
**Files**: `main.py:16-22`, various log statements

**Note**: If Enhancement #6 (File-Based Logging) is implemented, this enhancement may not be needed as the file logging already provides good formatting.

**Current Issues**:
- Emojis may not render in all terminals
- Inconsistent log formatting
- Both file logging and DB logging (redundant)
- No progress indicators

**Enhancement**:
Clean, consistent logging with optional emoji support

**Implementation**:

```python
# core/logging_config.py (NEW FILE)
import logging
import sys
from typing import Optional

class ConsoleFormatter(logging.Formatter):
    """Custom formatter with optional emoji support"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }

    # Emoji mapping (optional)
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }

    def __init__(self, use_color: bool = True, use_emoji: bool = False):
        super().__init__()
        self.use_color = use_color and sys.stdout.isatty()
        self.use_emoji = use_emoji

    def format(self, record):
        levelname = record.levelname
        message = record.getMessage()

        # Add emoji if enabled
        if self.use_emoji:
            prefix = self.EMOJIS.get(levelname, '')
            message = f"{prefix} {message}"

        # Add color if enabled
        if self.use_color:
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            levelname = f"{color}{levelname}{self.COLORS['RESET']}"

        # Format: TIMESTAMP | LEVEL | MESSAGE
        return f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')} | {levelname:<8} | {message}"

def setup_logging(verbose: bool = False, quiet: bool = False, use_emoji: bool = False):
    """Setup console logging with formatting"""
    level = logging.DEBUG if verbose else logging.ERROR if quiet else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ConsoleFormatter(use_color=True, use_emoji=use_emoji))

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
```

**Update main.py**:
```python
from core.logging_config import setup_logging

if __name__ == "__main__":
    args = parse_arguments()
    setup_logging(verbose=args.verbose, quiet=args.quiet, use_emoji=False)

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
```

**Add progress indicators for long operations**:
```python
# For quota checks
logger.info(f"Quota checks: 0/{len(lines)} completed")
# ... after each completion
logger.info(f"Quota checks: {completed}/{len(lines)} completed")
```

---

## P2 - Medium Priority Enhancements

### 12. Testing: Comprehensive Test Suite
**Priority**: P2 - Medium
**Impact**: High
**Effort**: High

**Implementation**:

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

**Test structure**:
```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── unit/
│   ├── test_encryption.py         # Credential encryption
│   ├── test_config.py             # Configuration loading
│   ├── test_quota_service.py      # Quota service logic
│   ├── test_speedtest_service.py  # Speed test service
│   └── test_report_service.py     # Report generation
├── integration/
│   ├── test_database.py           # Database operations
│   ├── test_email.py              # Email sending (mocked SMTP)
│   └── test_end_to_end.py         # Full workflow
└── fixtures/
    ├── sample_lines.py            # Test data
    ├── mock_portal_responses.html # HTML fixtures
    └── sample_results.py          # Expected outputs
```

**Example tests**:
```python
# tests/unit/test_encryption.py
import pytest
from core.encryption import CredentialEncryption

def test_encrypt_decrypt():
    crypto = CredentialEncryption()
    plaintext = "my_password_123"
    encrypted = crypto.encrypt(plaintext)
    assert encrypted != plaintext
    assert crypto.decrypt(encrypted) == plaintext

# tests/unit/test_quota_service.py
@pytest.mark.asyncio
async def test_scrap_and_save_quota(mock_line, mock_session):
    result = await QuotaService.scrap_and_save_quota(mock_line, headless=True)
    assert result is not None
    assert result.line_id == mock_line.id

# tests/integration/test_database.py
@pytest.mark.asyncio
async def test_line_crud_operations():
    async with get_session() as session:
        line_model = LineModel(session)

        # Create
        line = await line_model.create(test_line_data)
        assert line.id is not None

        # Read
        retrieved = await line_model.read(line.id)
        assert retrieved.name == test_line_data['name']

        # Delete
        await line_model.delete(line.id)
```

**Run tests**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_encryption.py -v
```

**Target Coverage**: 70% minimum (scrapers excluded due to browser dependency)

---

### 13. Performance: Optimize Database Queries
**Priority**: P2 - Medium
**Impact**: Medium
**Effort**: Low

**Current Issues**:
- N+1 query problem when loading lines with ISPs
- Multiple database sessions for related queries

**Enhancement**:
Use eager loading and query optimization

**Implementation**:

```python
# services/line_service.py
from sqlalchemy.orm import selectinload

class LineService:
    @staticmethod
    async def get_all_lines() -> List[Line]:
        """Get all lines with eager-loaded ISP relationships"""
        async with get_session() as session:
            line_model = LineModel(session)
            # Use eager loading to avoid N+1 queries
            result = await session.execute(
                select(Line).options(selectinload(Line.isp))
            )
            return result.scalars().all()

# services/quota_service.py
@staticmethod
async def get_latest_results(lines: List[Line]) -> List[ResultSchema]:
    """Optimized: Single session for all queries"""
    results = []
    async with get_session() as session:
        quota_model = QuotaResultModel(session)
        speed_model = SpeedTestResultModel(session)

        for line in lines:
            quota = await quota_model.read_last_record(line_id=line.id)
            speed = await speed_model.read_last_record(line_id=line.id)

            if quota:
                result = ResultSchema(
                    line_number=line.line_number,
                    name=line.name,
                    isp_name=line.isp.name,  # Already loaded
                    # ... rest of fields
                )
                results.append(result)

    return results
```

**Add database indexes**:
```python
# db/model.py - Add indexes to frequently queried columns
class QuotaResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    process_id: str = Field(index=True)
    line_id: int = Field(foreign_key="lines.id", index=True)  # Add index
    created_date: datetime = Field(default_factory=cairo_now, index=True)  # Add index
```

**Create migration for indexes**:
```bash
alembic revision -m "Add indexes for performance"
```

---

### 14. Selectors: Externalize CSS Selectors to JSON (Alternative Approach)
**Priority**: P2 - Medium
**Impact**: Medium
**Effort**: Low

**Note**: This is an alternative to the Pydantic-based approach in Enhancement #5. Choose either Pydantic classes (WEScraperSelectors) OR JSON file, not both.

**Enhancement**:
Move CSS selectors to external JSON file for easy updates without code changes

**Implementation**:

```json
// config/selectors.json
{
  "we": {
    "login": {
      "username_id": "login_loginid_input_01",
      "login_type_id": "login_input_type_01",
      "password_id": "login_password_input_01",
      "submit_id": "login-withecare",
      "account_type_selector": ".ant-select-item-option-active .ant-space-item:nth-child(2) > span"
    },
    "overview": {
      "balance": "#_bes_window > main > div > div > div.ant-row > div:nth-child(2) > div > div > div > div > div:nth-child(3) > div:nth-child(1)",
      "data_used": "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(2) > span:nth-child(1)",
      "data_remaining": "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-24 > div > div > div.ant-row.ec_accountoverview_primaryBtn_Qyg-Vp > div:nth-child(2) > div > div > div.slick-list > div > div.slick-slide.slick-active.slick-current > div > div > div > div > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)"
    },
    "renewal": {
      "cost": "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(3) > div > span:nth-child(2) > div > div:nth-child(1)",
      "date": "#_bes_window > main > div > div > div.ant-row > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-14.ant-col-lg-14.ant-col-xl-14 > div > div > div > div > div:nth-child(4) > div > span"
    }
  },
  "orange": {
    "login": {
      "username_id": "...",
      "password_id": "..."
    }
  }
}
```

```python
# core/selector_loader.py
import json
from pathlib import Path
from typing import Dict

class SelectorLoader:
    """
    Vendor-agnostic selector loader - supports multiple ISPs.
    Each ISP has its own section in selectors.json.
    """
    _selectors: Dict = None

    @classmethod
    def load(cls) -> Dict:
        """Load all vendor selectors from JSON file"""
        if cls._selectors is None:
            selector_file = Path(__file__).parent.parent / "config" / "selectors.json"
            with open(selector_file) as f:
                cls._selectors = json.load(f)
        return cls._selectors

    @classmethod
    def get(cls, isp: str, section: str, key: str) -> str:
        """
        Get selector for specific ISP, section, and key.

        Args:
            isp: ISP vendor name ('we', 'orange', etc.)
            section: Page section ('login', 'overview', 'renewal')
            key: Selector key ('username_id', 'balance', etc.)

        Returns:
            CSS selector string

        Example:
            SelectorLoader.get('we', 'login', 'username_id')  # For WE login username
            SelectorLoader.get('orange', 'login', 'password_id')  # For Orange login password
        """
        selectors = cls.load()
        return selectors[isp][section][key]

# Usage examples:

# In app/quota_checker/we.py - WE-specific selectors
from core.selector_loader import SelectorLoader as Sel

async def login(self):
    self.driver.find_element(By.ID, Sel.get('we', 'login', 'username_id')).click()
    self.driver.find_element(By.ID, Sel.get('we', 'login', 'password_id')).send_keys(password)
    self.driver.find_element(By.ID, Sel.get('we', 'login', 'submit_id')).click()

async def scrap_overview_page(self):
    balance = self.driver.find_element(By.CSS_SELECTOR, Sel.get('we', 'overview', 'balance')).text
    data_used = self.driver.find_element(By.CSS_SELECTOR, Sel.get('we', 'overview', 'data_used')).text

# In app/quota_checker/orange.py - Orange-specific selectors
from core.selector_loader import SelectorLoader as Sel

async def login(self):
    self.driver.find_element(By.ID, Sel.get('orange', 'login', 'username_id')).click()
    self.driver.find_element(By.ID, Sel.get('orange', 'login', 'password_id')).send_keys(password)
```

**Benefits**:
- Update selectors without code changes
- Version control for selector changes
- Easy ISP portal update tracking
- Non-developers can update selectors

---

### 15. Validation: Input Validation for Database Entries
**Priority**: P2 - Medium
**Impact**: Medium
**Effort**: Low

**Enhancement**:
Add Pydantic validation for all database inputs

**Implementation**:

```python
# db/validators.py (NEW FILE)
from pydantic import BaseModel, validator, Field
import re

class LineCreate(BaseModel):
    """Validation for line creation"""
    line_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    isp_id: int = Field(..., gt=0)
    ip_address: str
    portal_username: str = Field(..., min_length=1)
    portal_password: str = Field(..., min_length=1)
    gateway_ip: str

    @validator('ip_address', 'gateway_ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid IP address format')
        octets = v.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError('IP address octets must be 0-255')
        return v

    @validator('line_number')
    def validate_line_number(cls, v):
        """Validate line number format"""
        if not v.strip():
            raise ValueError('Line number cannot be empty')
        return v.strip()

class EmailCreate(BaseModel):
    """Validation for email recipient"""
    recipient: str

    @validator('recipient')
    def validate_email(cls, v):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
```

**Usage in models**:
```python
# db/models/line_model.py
from db.validators import LineCreate

async def create(self, line_data: Dict) -> Line:
    """Create line with validation"""
    # Validate input
    validated = LineCreate(**line_data)

    # Create line from validated data
    line = Line(**validated.dict())
    self.session.add(line)
    await self.session.commit()
    await self.session.refresh(line)
    return line
```

---

### 16. Documentation: Comprehensive User Guide
**Priority**: P2 - Medium
**Impact**: Low
**Effort**: Low

**Enhancement**:
Create detailed documentation for setup and usage

**Files to create**:

1. **README.md** - Overview and quick start
2. **docs/INSTALLATION.md** - Detailed installation guide
3. **docs/CONFIGURATION.md** - Configuration options
4. **docs/USAGE.md** - Command-line examples
5. **docs/SCHEDULING.md** - Windows Task Scheduler setup
6. **docs/TROUBLESHOOTING.md** - Common issues

**Example README.md**:
```markdown
# NetNinja - ISP Network Monitoring

Automated monitoring for Egyptian ISP connections with quota tracking and speed testing.

## Quick Start

# Install
pip install -r requirements.txt

# Setup
python setup_database.py

# Run
python main.py --headless

## Features

- ✅ WE & Orange ISP support
- ✅ Automated quota scraping
- ✅ Speed testing
- ✅ Email reports
- ✅ Encrypted credential storage
- ✅ Multiple output formats

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration](docs/CONFIGURATION.md)
- [Usage Examples](docs/USAGE.md)
- [Scheduling](docs/SCHEDULING.md)

## License

MIT
```

---

## P3 - Low Priority Enhancements

### 17. Notification: Multiple Notification Channels
**Priority**: P3 - Low
**Impact**: Low
**Effort**: Medium

**Enhancement**:
Support additional notification methods beyond email

**Implementation**:

```python
# integrations/telegram.py
import aiohttp

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(self, text: str):
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/sendMessage"
            data = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
            await session.post(url, json=data)

# integrations/slack.py
import aiohttp

class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_message(self, text: str):
        async with aiohttp.ClientSession() as session:
            payload = {"text": text}
            await session.post(self.webhook_url, json=payload)
```

**Configuration**:
```python
# core/config.py
class NotificationSettings(BaseSettings):
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    slack_enabled: bool = False
    slack_webhook_url: str = ""
```

---

### 18. Archive: Historical Data Management
**Priority**: P3 - Low
**Impact**: Low
**Effort**: Low

**Enhancement**:
Automatic archiving of old data to prevent database bloat

**Implementation**:

```python
# services/archive_service.py
from datetime import datetime, timedelta

class ArchiveService:
    @staticmethod
    async def archive_old_results(days_to_keep: int = 90):
        """Archive results older than N days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        async with get_session() as session:
            # Move old quota results to archive table
            old_results = await session.execute(
                select(QuotaResult).where(QuotaResult.created_date < cutoff_date)
            )
            # ... archive logic
```

**CLI option**:
```bash
python main.py --archive --keep-days 90
```

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
**Immediate blockers**

1. ✅ Fix email function signature mismatch
2. ✅ Remove hardcoded email sender
3. ✅ Add email failure fallback
4. ✅ Externalize configuration values

**Outcome**: Stable, production-ready application

---

### Phase 2: Security & Reliability (Week 2-3)
**Essential improvements**

1. ✅ Implement credential encryption (Enhancement #3)
2. ✅ Replace database logging with file-based rotation (Enhancement #6)
3. ✅ Enhanced CLI arguments (Enhancement #7)
4. ✅ Multiple report formats (Enhancement #8)
5. ✅ Database migration framework (Enhancement #10)

**Outcome**: Secure, flexible, simplified application

---

### Phase 3: Testing & Documentation (Week 4-5)
**Quality assurance**

1. ✅ Comprehensive test suite
2. ✅ User documentation
3. ✅ Code refactoring
4. ✅ Performance optimization

**Outcome**: Well-tested, documented application

---

### Phase 4: Extended Features (Week 6+)
**Additional capabilities**

1. ✅ Orange ISP implementation (Enhancement #9)
2. ✅ Selector externalization (Enhancement #14)
3. ✅ Input validation (Enhancement #15)
4. ✅ Additional notification channels (Enhancement #17)

**Outcome**: Feature-complete application

---

## Dependencies

### Required Packages
```txt
# requirements.txt (updated)
sqlmodel>=0.0.14
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
aiohttp>=3.9.0
aiosmtplib>=3.0.0
selenium>=4.15.0
selenium-async>=0.1.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
jinja2>=3.1.0
pytz>=2023.3
cryptography>=41.0.0  # NEW - for encryption
alembic>=1.13.0       # NEW - for migrations
pytest>=7.4.0         # NEW - for testing
pytest-asyncio>=0.21.0  # NEW - for async tests
pytest-cov>=4.1.0     # NEW - for coverage
pytest-mock>=3.12.0   # NEW - for mocking
```

---

## Testing Strategy

### Test Coverage Goals
- **Critical paths**: 90% (encryption, email, database)
- **Services**: 85% (quota, speedtest, notification)
- **Utils**: 80% (config, logging)
- **Scrapers**: 50% (browser-dependent, hard to mock)
- **Overall**: 75%

### Test Types
1. **Unit Tests**: Individual functions and classes
2. **Integration Tests**: Database operations, service interactions
3. **E2E Tests**: Full workflow simulation (mocked browser)

### Continuous Testing
```bash
# Pre-commit hook
pytest tests/ -v

# Coverage check
pytest --cov=. --cov-fail-under=75
```

---

## Performance Targets

### Execution Time (5 lines)
- **Current**: ~3-4 minutes
- **Target**: <2 minutes
- **Improvements**:
  - Parallel speed tests (already implemented)
  - Optimized database queries
  - Faster browser startup

### Resource Usage
- **Memory**: <500MB peak
- **Database**: <50MB for 1 year of data
- **CPU**: Moderate during scraping, minimal otherwise

---

## Success Metrics

### Reliability
- ✅ Scraping success rate: >95%
- ✅ Email delivery rate: >99%
- ✅ Zero data loss events
- ✅ Graceful failure handling

### Maintainability
- ✅ Zero hardcoded values
- ✅ All selectors externalized
- ✅ Configuration-driven behavior
- ✅ Comprehensive documentation

### Security
- ✅ Encrypted credentials
- ✅ No plaintext passwords
- ✅ Secure key management
- ✅ Input validation

### Usability
- ✅ CLI options for all use cases
- ✅ Clear error messages
- ✅ Progress indicators
- ✅ Multiple output formats

---

## Conclusion

This enhancement plan transforms NetNinja from a functional monitoring tool into a **production-grade, secure, and maintainable** command-line application. The phased approach ensures:

1. **Immediate value**: Critical fixes in Phase 1
2. **Long-term stability**: Security and testing in Phases 2-3
3. **Extended capabilities**: ISP support and features in Phase 4

**Key Architectural Improvements**:
- 🔒 **Security**: Encrypted credentials at rest
- 🪶 **Simplification**: File-based logging replaces complex database logging (removes 300+ lines of code)
- 📝 **Log Management**: Automatic rotation keeping latest 7 log files
- ⚡ **Performance**: Faster execution without database log writes
- 🎯 **Focus**: Cleaner database schema (remove Log table and process_id columns)
- 🛠️ **Maintainability**: Standard Python logging instead of custom async logger

**Next Steps**:
1. Review and approve plan
2. Set up development environment
3. Begin Phase 1 critical fixes
4. Implement Phase 2 simplifications (especially Enhancement #6 - Logging)
5. Establish testing infrastructure
6. Iterate through remaining phases

---

**Document Version**: 2.0 (CMD-focused)
**Last Updated**: 2025-10-20
**Maintained By**: Development Team
