# NetNinja v2.0 - Production Release 🚀

**Release Date:** October 2025

A complete rewrite of NetNinja with enhanced security, reliability, and usability. This release transforms the application into a production-ready network monitoring tool with advanced features and clean architecture.

---

## ✨ Highlights

- 🔒 **Credential Encryption** - Fernet symmetric encryption for portal passwords
- 📧 **Smart Email Retry** - Automatic retry with exponential backoff + local fallback
- 🎯 **Enhanced CLI** - Multiple execution modes, filters, and output formats
- 📊 **Multiple Report Formats** - Export to HTML, JSON, or CSV
- 📝 **File-Based Logging** - Automatic rotation (keeps latest 7 files)
- ⚙️ **Zero Hardcoding** - All configuration externalized to .env
- 🏗️ **Modular Architecture** - Clean, maintainable, testable code

---

## 🎯 Key Features

### Security
- **Password Encryption** - All portal credentials encrypted at rest
- **Automatic Key Management** - Encryption key auto-generated and managed
- **Fresh Start Policy** - New database = new encryption key

### Reliability
- **Email Retry Logic** - Up to 3 attempts with exponential backoff (1s, 2s, 4s)
- **Local Report Fallback** - Automatic HTML report generation on email failure
- **Concurrency Control** - Configurable semaphore limits
- **Error Recovery** - Automatic retry for failed scraping operations

### Usability
- **Rich CLI** - 15+ command-line options for flexible execution
- **Dry Run Mode** - Preview execution without running
- **Quick Commands** - `--list-lines`, `--show-results`, `--setup-db`
- **Multiple Formats** - HTML, JSON, CSV report generation
- **Smart Filtering** - Filter by line ID or ISP

### Architecture
- **Modular Design** - Separated concerns (CLI, Core, Services)
- **Clean Code** - 64% reduction in main.py complexity
- **Type Hints** - Full type annotations throughout
- **Standard Logging** - Python logging instead of custom implementation

---

## 📦 Installation

### New Installation

```bash
# Clone repository
git clone <repository-url>
cd net-ninja/src/execution_v1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python main.py --setup-db
```

### Upgrade from v1.0

```bash
# Backup your data
cp app.db app.db.backup
cp .secret.key .secret.key.backup  # If exists

# Pull latest code
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migration (passwords will be auto-encrypted)
python main.py --headless
```

---

## 🔄 Breaking Changes

⚠️ **Database Schema**
- `process_id` column removed from `quota_results` and `speed_test_results`
- `logs` table removed (replaced with file-based logging)
- Existing databases will continue to work (backward compatible)

⚠️ **Configuration**
- New required field: `EMAIL_SENDER` in .env
- New optional fields for execution and speedtest configuration
- See `.env.example` for complete list

⚠️ **Logging**
- Database logging removed
- All logs now in `logs/` directory
- Old `app/logger.py` removed

---

## 📋 What's Changed

### Added
- Credential encryption with Fernet
- Email retry logic with exponential backoff
- Local report generation fallback
- Enhanced CLI with 15+ options
- Multiple report formats (HTML, JSON, CSV)
- File-based logging with automatic rotation
- Modular architecture (cli/, core/ modules)
- Input validation for database entries
- Database query optimization
- Comprehensive documentation

### Changed
- main.py reduced from 352 to 128 lines (64% reduction)
- All configuration externalized to .env and config files
- Standard Python logging instead of custom logger
- Improved error handling throughout
- Better separation of concerns

### Removed
- Database logging (replaced with file-based)
- process_id tracking (unnecessary complexity)
- Custom async logger (83 lines removed)
- Hardcoded values (moved to configuration)

### Fixed
- Email function signature mismatch
- Hardcoded email sender
- Password handling for SMTP
- N+1 query issues in database

---

## 📚 Documentation

- **README.md** - Complete user guide with examples
- **.env.example** - Configuration template with comments
- **plan.md** - Technical enhancement roadmap
- **project.md** - Project architecture overview

---

## 🚀 Quick Start

```bash
# Run all checks in headless mode
python main.py --headless

# Check quota only
python main.py --quota-only --headless

# Save report to file (no email)
python main.py --output report.html --no-email

# Show last results
python main.py --show-results

# Get help
python main.py --help
```

---

## 🔧 Requirements

- Python 3.10+
- Chrome/Chromium (for Selenium)
- SQLite3

**Dependencies:**
- sqlmodel>=0.0.14
- sqlalchemy>=2.0.0
- aiosqlite>=0.19.0
- pydantic>=2.5.0
- selenium>=4.15.0
- aiohttp>=3.9.0
- cryptography>=41.0.0
- (see requirements.txt for complete list)

---

## 🐛 Known Issues

None at this time.

---

## 📝 Credits

Developed for monitoring Egyptian ISP connections (WE, Orange, Vodafone, Etisalat).

---

## 📄 License

MIT License

---

## 🔗 Links

- [Full Documentation](README.md)
- [Configuration Guide](.env.example)
- [Enhancement Plan](plan.md)
- [Project Overview](project.md)

---

**Full Changelog:** v1.0...v2.0
