# NetNinja v2.0 🚀

Production-ready network monitoring tool for Egyptian ISPs with enhanced security and reliability.

## 🎯 Key Features

🔒 **Credential Encryption** - Fernet encryption for portal passwords
📧 **Smart Email Retry** - 3 attempts + local fallback
🎯 **Enhanced CLI** - 15+ options, filters, dry-run mode
📊 **Multiple Formats** - HTML, JSON, CSV reports
📝 **File Logging** - Auto-rotation (7 files)
⚙️ **Zero Hardcoding** - All config in .env

## 🔄 What's New

- Credential encryption at rest
- Email retry with exponential backoff
- Enhanced CLI with multiple modes
- File-based logging with rotation
- Modular architecture (64% code reduction)
- Database query optimization
- Input validation
- Comprehensive documentation

## 📦 Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python main.py --setup-db
```

## ⚠️ Breaking Changes

- New required config: `EMAIL_SENDER`
- Database logging removed (use file-based)
- `process_id` columns removed (backward compatible)

## 🚀 Quick Start

```bash
python main.py --headless              # Run all checks
python main.py --quota-only            # Quota only
python main.py --show-results          # View results
python main.py --help                  # All options
```

## 📚 Docs

- [README.md](README.md) - Full documentation
- [.env.example](.env.example) - Configuration
- [RELEASE.md](RELEASE.md) - Detailed release notes

**Full Changelog:** v1.0...v2.0
