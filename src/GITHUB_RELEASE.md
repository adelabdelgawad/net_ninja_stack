# NetNinja v2.0 - Production Release 🚀

**Complete rewrite with enhanced security, reliability, and usability.**

---

## 📥 Download & Installation

**Download:** `NetNinja-v2.0.zip` from Assets below

### Quick Setup (3 steps)

1. **Extract** the ZIP file to your preferred location
2. **Configure** - Edit `.env.example` with your settings and save as `.env`
3. **Run** - Execute `netninja.exe --setup-db` to initialize database

The application will automatically:
- ✅ Create database on first run
- ✅ Generate encryption key for passwords
- ✅ Set up logging directory

---

## ✨ What's New in v2.0

🔒 **Credential Encryption** - All portal passwords encrypted with Fernet
📧 **Smart Email Retry** - 3 attempts with exponential backoff + local fallback
🎯 **Enhanced CLI** - 15+ command-line options for flexible execution
📊 **Multiple Formats** - Export reports as HTML, JSON, or CSV
📝 **File Logging** - Auto-rotation keeping latest 7 log files
⚙️ **Zero Hardcoding** - All configuration externalized to .env
🏗️ **Modular Code** - 64% reduction in complexity, easier to maintain

---

<details>
<summary><b>📋 Click to see all changes included in this release</b></summary>

### ✅ Added Features

#### Security & Encryption
- Fernet symmetric encryption for portal credentials
- Automatic encryption key generation and management
- Fresh key creation on new database initialization
- Secure password storage with backward compatibility

#### Email & Notifications
- Retry logic with exponential backoff (1s, 2s, 4s)
- Automatic local HTML report fallback on email failure
- Configurable retry attempts (default: 3)
- Enhanced error reporting

#### CLI Enhancements
- **Execution Modes:** `--headless`, `--quota-only`, `--speedtest-only`, `--no-email`, `--dry-run`
- **Filtering:** `--line-id`, `--isp`
- **Output Control:** `--verbose`, `--quiet`, `--output`, `--format`
- **Database Operations:** `--setup-db`, `--list-lines`, `--show-results`
- Rich help documentation with examples

#### Reporting
- Multiple output formats: HTML, JSON, CSV
- File-based report generation
- Structured JSON output for API integration
- CSV export for Excel analysis

#### Logging
- File-based logging with timestamps
- Automatic log rotation (keeps 7 most recent)
- Format: `netninja_YYYYMMDD_HHMMSS.log`
- Both console and file output
- Configurable log levels (verbose/quiet modes)

#### Architecture
- Modular code structure (cli/, core/, services/)
- Separated CLI parsing (`cli/parser.py`)
- Command handlers (`cli/commands.py`)
- Database initialization module (`core/database_init.py`)
- Execution logic module (`core/executor.py`)
- Clean 128-line main.py (was 352 lines)

#### Configuration
- All settings externalized to .env
- WE-specific scraper selectors (`WEScraperSelectors`)
- Configurable timeouts (`ScraperTimeouts`)
- Execution settings (semaphore limits, retry attempts)
- SpeedTest configuration (chunk sizes, test counts, timeouts)

#### Database
- Query optimization with eager loading
- N+1 query prevention
- Input validation with Pydantic schemas
- Automatic password encryption on first run

### 🔄 Changed

- **main.py:** Reduced from 352 to 128 lines (64% reduction)
- **Logging:** Standard Python logging instead of custom async logger
- **Configuration:** All hardcoded values moved to .env and config files
- **Error Handling:** Improved throughout application
- **Code Structure:** Better separation of concerns
- **Database Access:** Optimized with eager loading

### ❌ Removed

- **Database Logging:** Removed 83-line custom logger
- **process_id Tracking:** Unnecessary complexity removed
- **Hardcoded Values:** All moved to configuration
- **Log Table:** Replaced with file-based logging
- **Custom Logger:** Replaced with standard Python logging

### 🐛 Fixed

- Email function signature mismatch (P0 bug)
- Hardcoded email sender
- Password handling for SMTP SecretStr
- N+1 database query issues
- Log file rotation logic

### 📝 Documentation

- Comprehensive README.md with examples
- Complete .env.example with comments
- CLI reference documentation
- Security and encryption guide
- Troubleshooting section
- Windows Task Scheduler setup guide

</details>

---

## 🚀 Getting Started

### First Time Setup

1. **Extract Files**
   ```
   NetNinja-v2.0/
   ├── netninja.exe
   └── .env.example
   ```

2. **Create Configuration**
   - Open `.env.example` in a text editor
   - Update these required fields:
     ```env
     # Email Settings (Required)
     EMAIL_SERVER=smtp.gmail.com
     EMAIL_PORT=587
     EMAIL_USERNAME=your.email@gmail.com
     EMAIL_PASSWORD=your_app_password
     EMAIL_SENDER=your.email@gmail.com
     EMAIL_SUBJECT=Daily Network Check
     ```
   - Save as `.env` (remove .example)

3. **Initialize Database**
   ```bash
   netninja.exe --setup-db
   ```

4. **Add Your Lines**
   - Use the database setup tool to add ISP lines
   - Passwords will be automatically encrypted

5. **Test Run**
   ```bash
   # Dry run to preview
   netninja.exe --dry-run

   # Actual run
   netninja.exe --headless
   ```

---

## 📖 Usage & Commands

### Execution Modes

```bash
# Run all checks (quota + speedtest) in headless mode
netninja.exe --headless

# Only check quota (skip speedtest)
netninja.exe --quota-only --headless

# Only run speedtest (skip quota check)
netninja.exe --speedtest-only

# Run without sending email (save to file)
netninja.exe --no-email --output report.html

# Preview what would run (no execution)
netninja.exe --dry-run
```

### Filtering Options

```bash
# Run for specific line only
netninja.exe --line-id 1 --headless

# Run for specific ISP only
netninja.exe --isp WE --headless

# Combine filters
netninja.exe --isp WE --line-id 2 --headless
```

### Output Control

```bash
# Verbose output (show all details)
netninja.exe --verbose --headless

# Quiet mode (errors only)
netninja.exe --quiet --headless

# Save report to file (HTML)
netninja.exe --output report.html --headless

# Save as JSON
netninja.exe --output report.json --format json --headless

# Save as CSV
netninja.exe --output report.csv --format csv --headless
```

### Database Operations

```bash
# Initialize/setup database
netninja.exe --setup-db

# List all configured lines
netninja.exe --list-lines

# Show last results summary
netninja.exe --show-results
```

### Combined Examples

```bash
# Quota check for WE ISP, save as JSON, verbose logging
netninja.exe --quota-only --isp WE --output report.json --format json --verbose

# Speedtest only for line 1, no email
netninja.exe --speedtest-only --line-id 1 --no-email

# Full check, quiet mode, HTML report
netninja.exe --headless --quiet --output daily_report.html
```

---

## 🔒 Security & Encryption

### Automatic Encryption
- All portal passwords are **automatically encrypted** on first use
- Uses **Fernet symmetric encryption** (cryptography library)
- Encryption key stored in `.secret.key` file

### Key Management
- **Fresh database** = new encryption key automatically created
- **Existing database** = uses existing key
- **Important:** Backup `.secret.key` before deleting database

### What Happens on First Run
```
1. Application starts
2. Checks for database → Not found
3. Deletes old .secret.key (if exists)
4. Creates new database
5. On first password entry → generates new .secret.key
6. All subsequent passwords encrypted with this key
```

---

## 📧 Email Configuration

### Gmail Setup (Recommended)

1. Enable 2-factor authentication on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password in `.env` file:
   ```env
   EMAIL_USERNAME=your.email@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password
   EMAIL_SENDER=your.email@gmail.com
   ```

### Email Retry Logic
- **3 automatic retry attempts** on failure
- **Exponential backoff:** 1s, 2s, 4s between retries
- **Local fallback:** Saves HTML report to `reports/` directory if all retries fail

---

## 📝 Logging

### Location
- All logs saved to `logs/` directory
- Format: `netninja_YYYYMMDD_HHMMSS.log`

### Automatic Rotation
- Keeps **latest 7 log files**
- Older logs automatically deleted
- Both console and file output

### Log Levels
```bash
# Normal logging
netninja.exe --headless

# Verbose (debug level)
netninja.exe --verbose --headless

# Quiet (errors only)
netninja.exe --quiet --headless
```

---

## 📊 Reports

### Format Options

**HTML** (Default) - Styled table, email-ready
```bash
netninja.exe --output report.html
```

**JSON** - API integration, programmatic access
```bash
netninja.exe --output report.json --format json
```

**CSV** - Excel, spreadsheet analysis
```bash
netninja.exe --output report.csv --format csv
```

### Automatic Fallback
If email fails after 3 retries:
- Report automatically saved to `reports/netninja_TIMESTAMP.html`
- Check `reports/` directory for the file

---

## ⚙️ Configuration Reference

### Required Settings

```env
# Database (auto-created, usually don't change)
DATABASE_NAME=app.db

# Email/SMTP (REQUIRED)
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SENDER=your.email@gmail.com
EMAIL_SENDER_ALIAS=NetNinja Monitor
EMAIL_SUBJECT=Daily Network Check
```

### Optional Settings

```env
# Execution Control
EXEC_SEMAPHORE_LIMIT=2              # Concurrent operations
EXEC_MAX_RETRY_ATTEMPTS=1           # Scraping retry attempts

# Speed Test Tuning
SPEEDTEST_DOWNLOAD_CHUNK_SIZE=102400  # 100KB
SPEEDTEST_UPLOAD_CHUNK_SIZE=4194304   # 4MB
SPEEDTEST_TEST_COUNT=10
SPEEDTEST_TIMEOUT=30
SPEEDTEST_MAX_DOWNLOAD_TIME=15
SPEEDTEST_MAX_UPLOAD_TIME=10
```

---

## 🔄 Upgrade from v1.0

### Backup First
```bash
# Backup your data
copy app.db app.db.backup
copy .secret.key .secret.key.backup  # If exists
```

### Migration
1. Replace old executable with new `netninja.exe`
2. Update `.env` file with new required field:
   ```env
   EMAIL_SENDER=your.email@gmail.com
   ```
3. Run once - passwords will be auto-encrypted:
   ```bash
   netninja.exe --headless
   ```

### Breaking Changes
- New required config: `EMAIL_SENDER`
- Database logging removed (check `logs/` directory instead)
- Old `process_id` columns ignored (backward compatible)

---

## ⚠️ Breaking Changes

### Configuration
- **New Required:** `EMAIL_SENDER` field in .env
- **New Optional:** Execution and SpeedTest configuration options

### Database Schema
- `process_id` column removed (backward compatible - ignored if present)
- `logs` table no longer used (file-based logging)

### Logging
- Database logging removed
- All logs now in `logs/` directory
- Old database logs no longer accessible

---

## 🐛 Troubleshooting

### Email Not Sending
- Check SMTP settings in `.env`
- Verify Gmail App Password (not regular password)
- Check `logs/` for detailed error messages
- Report will be in `reports/` directory as fallback

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
del app.db
netninja.exe --setup-db
```

### Encryption Key Issues
- Lost `.secret.key`? Cannot decrypt old passwords
- Solution: Delete database, start fresh (key auto-recreated)

### Scraping Failures
- Run without `--headless` to see browser
- Check WE portal hasn't changed (selectors in config)
- Check `logs/` for detailed errors

---

## 📋 System Requirements

- **OS:** Windows 10/11 (64-bit)
- **Browser:** Chrome/Chromium (installed automatically with Selenium)
- **RAM:** 2GB minimum, 4GB recommended
- **Disk:** 100MB for application + log files

---

## 📄 Files Included

```
NetNinja-v2.0.zip
├── netninja.exe          # Main executable
└── .env.example          # Configuration template
```

**Generated on first run:**
```
├── app.db                # Database (auto-created)
├── .secret.key           # Encryption key (auto-created)
├── .env                  # Your configuration (you create this)
├── logs/                 # Log files (auto-created)
└── reports/              # Fallback reports (auto-created)
```

---

## 🔗 Resources

- **Full Documentation:** [README.md](README.md)
- **Configuration Guide:** See `.env.example` in download
- **Issues & Support:** [GitHub Issues](../../issues)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👥 Credits

Developed for monitoring Egyptian ISP connections (WE, Orange, Vodafone, Etisalat).

---

**Full Changelog:** [v1.0...v2.0](../../compare/v1.0...v2.0)
