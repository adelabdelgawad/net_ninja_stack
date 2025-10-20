# NetNinja - Network Monitoring & Automation Platform

## Project Overview

**NetNinja** is an automated network monitoring and testing application specifically designed for Egyptian Internet Service Providers (ISPs). It monitors internet connectivity performance and data quota consumption by automating web scraping of ISP portals, running speed tests, and generating comprehensive daily email reports.

**Target Users**: Network administrators and IT departments managing multiple ISP connections for organizations in Egypt

**Version**: 1.0
**Location**: `E:\github_repositories\net-ninja\src\execution_v1`

---

## Core Functionality

NetNinja automates the following critical tasks:

### 1. ISP Portal Scraping
- **Automated Login**: Logs into ISP customer portals using stored credentials
- **Data Extraction**: Scrapes quota usage, remaining data, balance, and renewal information
- **Multi-ISP Support**: Currently supports WE (Telecom Egypt), with Orange framework in place
- **Retry Mechanism**: Automatically retries failed scraping attempts to ensure reliability

### 2. Speed Testing
- **Bandwidth Measurement**: Tests download/upload speeds against Speedtest.net infrastructure
- **Multi-Line Testing**: Concurrent testing across multiple internet connections
- **Source IP Binding**: Binds tests to specific IP addresses for accurate per-line metrics
- **Latency Monitoring**: Measures ping/latency to closest speedtest servers

### 3. Data Persistence
- **SQLite Database**: Local database for storing all metrics and configuration
- **Historical Tracking**: Maintains history of all quota checks and speed tests with timestamps
- **Process Tracing**: Unique process IDs link all operations for debugging and auditing
- **Cairo Timezone**: All timestamps use Africa/Cairo timezone for consistency

### 4. Automated Reporting
- **HTML Email Reports**: Generates styled HTML tables with quota and speed test results
- **Color-Coded Alerts**:
  - Red background: >90% quota usage (critical)
  - Yellow background: 75-90% quota usage (warning)
  - Normal: <75% quota usage
- **Daily Summaries**: Consolidates all line metrics into single comprehensive report
- **Multiple Recipients**: Supports configurable email recipient lists with CC support

### 5. Logging & Monitoring
- **Database Logging**: Stores all application logs in database for persistence
- **Process Correlation**: Links logs to specific execution runs via process IDs
- **Multiple Log Levels**: INFO, WARNING, ERROR, DEBUG for granular troubleshooting
- **Async Logging**: Non-blocking log operations for performance

---

## Technical Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.12+ | Modern async/await support |
| **ORM** | SQLModel | Hybrid SQLAlchemy + Pydantic |
| **Database** | SQLite | Lightweight local persistence |
| **Web Scraping** | Selenium + selenium-async | Browser automation |
| **HTTP Client** | aiohttp | Async HTTP requests |
| **Speed Testing** | Custom async implementation | Speedtest.net protocol |
| **Email** | aiosmtplib | Async SMTP client |
| **Templates** | Jinja2 | HTML email rendering |
| **Configuration** | Pydantic Settings | Environment-based config |
| **Timezone** | pytz | Cairo timezone handling |

### Architecture Pattern

**Service-Oriented Architecture** with clear separation of concerns:

```
Presentation Layer (Email Reports)
         ↓
Service Layer (Business Logic)
  - QuotaService
  - SpeedTestService
  - NotificationService
  - LineService
         ↓
Data Access Layer (Repository Pattern)
  - LineModel
  - QuotaResultModel
  - SpeedTestResultModel
  - EmailModel
  - LogModel
         ↓
Database Layer (SQLModel/SQLAlchemy)
         ↓
SQLite Database
```

### Project Structure

```
execution_v1/
├── main.py                    # Application entry point & orchestration
├── setup_database.py          # Database initialization script
├── delete_database.py         # Database cleanup utility
├── app/                       # Application modules
│   ├── quota_checker/         # ISP-specific scrapers
│   │   ├── we.py             # WE (Telecom Egypt) scraper
│   │   └── orange.py         # Orange scraper (stub)
│   ├── async_speedtest.py    # Speed test implementation
│   ├── mail.py               # Email composition & sending
│   ├── logger.py             # Custom database logger
│   └── wait.py               # WebDriver utilities
├── core/                      # Configuration management
│   └── config.py             # Settings & environment handling
├── db/                        # Database layer
│   ├── model.py              # SQLModel table definitions
│   ├── schema.py             # Pydantic schemas
│   ├── database.py           # Database engine setup
│   ├── crud.py               # Base CRUD operations
│   └── models/               # Repository pattern implementations
│       ├── line_model.py
│       ├── isp_model.py
│       ├── quota_result_model.py
│       ├── speed_test_result_model.py
│       ├── email_model.py
│       └── log_model.py
├── services/                  # Business logic layer
│   ├── quota_service.py
│   ├── speedtest_service.py
│   ├── notification_service.py
│   └── line_service.py
└── templates/                 # Email templates directory
```

---

## Database Schema

### Tables

**1. isp** - Internet Service Providers
- `id` (PK): ISP identifier
- `name`: ISP name (WE, Orange, Vodafone, Etisalat)

**2. lines** - Internet Connections
- `id` (PK): Line identifier
- `line_number`: Connection/account number
- `name`: Display name
- `description`: Additional details
- `isp_id` (FK): Reference to ISP
- `ip_address`: Gateway IP for speed testing
- `portal_username`: ISP portal login
- `portal_password`: ISP portal password
- `gateway_ip`: Gateway address

**3. quota_results** - Quota Snapshots
- `id` (PK): Result identifier
- `line_id` (FK): Reference to line
- `process_id`: Execution trace ID
- `data_used`: Usage in GB
- `usage_percentage`: Calculated percentage
- `data_remaining`: Remaining quota in GB
- `balance`: Account balance in LE
- `renewal_date`: Next renewal date (DD-MM-YYYY)
- `remaining_days`: Days until renewal
- `renewal_cost`: Renewal cost in LE
- `created_date`: Timestamp (Cairo TZ)

**4. speed_test_results** - Speed Test Snapshots
- `id` (PK): Result identifier
- `line_id` (FK): Reference to line
- `process_id`: Execution trace ID
- `ping`: Latency in ms
- `upload_speed`: Upload in Mbps
- `download_speed`: Download in Mbps
- `public_ip`: Detected public IP
- `created_date`: Timestamp (Cairo TZ)

**5. email** - Email Recipients
- `id` (PK): Recipient identifier
- `recipient`: Email address

**6. logs** - Application Logs
- `id` (PK): Log identifier
- `process_id`: Execution trace ID
- `function`: Function/method name
- `level`: Log level (INFO, ERROR, WARNING, DEBUG)
- `message`: Log message
- `created_date`: Timestamp (Cairo TZ)

### Relationships
- ISP → Lines (1:N)
- Line → QuotaResults (1:N with cascade delete)
- Line → SpeedTestResults (1:N with cascade delete)

---

## Execution Flow

### Application Workflow

```
1. Database Initialization Check
   ├─ If database missing: Create schema, seed ISPs, exit
   └─ If database exists: Proceed

2. Line Retrieval
   ├─ Fetch all configured lines from database
   └─ If no lines: Exit with warning

3. Concurrent Quota Checks (Semaphore: 2 max concurrent)
   ├─ For each line:
   │  ├─ Initialize WE web scraper with line credentials
   │  ├─ Login to ISP portal (https://my.te.eg)
   │  ├─ Navigate to overview page
   │  │  └─ Extract: data used, remaining, balance, usage %
   │  ├─ Navigate to renewal page
   │  │  └─ Extract: renewal date, days remaining, cost
   │  └─ Save QuotaResult to database
   │
   └─ Retry Loop: Retry all failed lines once

4. Concurrent Speed Tests (No limit)
   ├─ For each line:
   │  ├─ Bind to line's IP address
   │  ├─ Fetch speedtest.net configuration (servers, public IP)
   │  ├─ Select closest server by geographic distance
   │  ├─ Measure latency (ping)
   │  ├─ Measure download speed
   │  ├─ Measure upload speed
   │  └─ Save SpeedTestResult to database

5. Report Generation
   ├─ Retrieve latest quota result for each line
   ├─ Retrieve latest speed test result for each line
   ├─ Combine into ResultSchema objects
   └─ Fetch all email recipients from database

6. Email Notification
   ├─ Render HTML template with Jinja2
   ├─ Apply color-coding based on usage percentage
   ├─ Send email via SMTP (async)
   └─ Complete execution
```

### Concurrency Model

- **Async-First**: All I/O operations use async/await
- **Semaphore Limiting**: Maximum 2 concurrent quota scraping tasks (to avoid ISP rate limiting)
- **Concurrent Speed Tests**: All speed tests run in parallel without limit
- **Graceful Error Handling**: Exceptions captured per-task, don't halt entire execution
- **Retry Logic**: Failed quota scrapes automatically retried once

---

## Configuration

### Environment Variables (`.env`)

**Database Configuration:**
```
DATABASE_NAME=app.db
DATABASE_SERVER=localhost
DATABASE_PORT=1433
DATABASE_USERNAME=user
DATABASE_PASSWORD=pass
```

**Email Configuration:**
```
EMAIL_SUBJECT=DailyCheck
EMAIL_SERVER=smtp.example.com
EMAIL_PORT=587
EMAIL_USERNAME=sender@example.com
EMAIL_PASSWORD=secret
EMAIL_SENDER_ALIAS=NetNinja
EMAIL_CC_ADDRESS=cc@example.com
```

### Command Line Arguments

```bash
# Run with browser GUI visible (for debugging)
python main.py

# Run in headless mode (production)
python main.py --headless
```

### Windows Batch Runner

`run.bat` - Convenience script for Windows execution

---

## Current Features & Capabilities

### Implemented Features
- Multi-line ISP management
- WE (Telecom Egypt) portal web scraping
- Async speed testing against Speedtest.net
- SQLite database persistence with relationships
- HTML email reporting with conditional styling
- Quota usage alerts (color-coded thresholds)
- Automatic retry for failed scraping operations
- Process ID correlation across logs and results
- Cairo timezone-aware timestamps
- Environment-based configuration with secrets support
- Database auto-initialization on first run
- Repository pattern for clean data access
- Comprehensive async logging to database

### ISP Support Status
| ISP | Scraper Status | Notes |
|-----|---------------|-------|
| WE (Telecom Egypt) | Full Support | Production-ready |
| Orange | Stub Only | Framework in place, implementation pending |
| Vodafone | Not Started | Requires scraper implementation |
| Etisalat | Not Started | Requires scraper implementation |

---

## Limitations & Considerations

### Current Limitations

1. **Single Execution Model**
   - Main.py runs once per invocation
   - Requires external task scheduler (Windows Task Scheduler, cron, etc.)
   - No built-in scheduling mechanism

2. **ISP Support**
   - Only WE (Telecom Egypt) fully implemented
   - Other ISPs require custom scraper development

3. **Security Concerns**
   - Portal passwords stored in plaintext in database
   - No encryption at rest for sensitive credentials
   - Recommend file system encryption or database-level encryption

4. **Database**
   - SQLite only (not suitable for distributed systems)
   - No built-in migration framework
   - Manual schema updates required

5. **Configuration**
   - Email sender hardcoded in main.py:132
   - Line management requires manual database updates
   - No web UI for configuration

6. **Extensibility**
   - No REST API for external integration
   - No webhook support for real-time notifications
   - No plugin architecture for custom scrapers

7. **Browser Dependency**
   - Requires Chrome/Chromium browser installed
   - WebDriver must be compatible with browser version
   - Resource-intensive (browser automation)

### Performance Characteristics

- **Quota Scraping**: ~30-60 seconds per line (browser automation overhead)
- **Speed Testing**: ~20-40 seconds per line (network-dependent)
- **Total Runtime**: ~2-3 minutes for 2-3 lines (with concurrency)
- **Database Size**: Minimal (KB-MB range for typical usage)

---

## Use Cases

### Primary Use Case
**Daily ISP Monitoring for IT Departments**
- Automate manual portal checking for multiple internet lines
- Receive consolidated daily reports on all connections
- Proactive alerts when quota nearing limits
- Track speed performance trends over time

### Example Scenarios

1. **Multi-Branch Organization**
   - Company with 5 branches, each with WE internet
   - NetNinja monitors all 5 lines daily
   - IT receives single email with all metrics
   - Identifies underperforming lines quickly

2. **ISP Performance Comparison**
   - Organization with WE and Orange lines
   - Compare speed test results daily
   - Make data-driven decisions on ISP contracts

3. **Quota Management**
   - Avoid overage charges by monitoring usage
   - Plan bandwidth upgrades based on trends
   - Receive alerts before hitting data caps

---

## Code Quality & Best Practices

### Strengths
- Modern Python 3.12+ async/await patterns
- Type hints throughout codebase
- Service-oriented architecture with clear separation
- Repository pattern for data access
- Environment-based configuration
- Comprehensive error handling and logging
- Process ID tracing for debugging
- Context managers for resource cleanup
- Pydantic validation for data integrity

### Areas for Improvement
- Missing unit tests and integration tests
- No API documentation (docstrings incomplete)
- Limited input validation in some areas
- Hardcoded CSS in email template (should be external)
- No database migration framework
- Magic numbers in wait times (should be configurable)
- Browser automation fragile to UI changes

---

## Dependencies

### Core Dependencies
```
sqlmodel            # ORM + validation
sqlalchemy >= 2.0   # Database toolkit
aiohttp             # Async HTTP client
aiosmtplib          # Async SMTP
selenium            # Browser automation
selenium-async      # Async Selenium wrapper
pydantic-settings   # Configuration management
jinja2              # Template engine
pytz                # Timezone support
```

### Development Tools
```
pyinstaller         # Standalone executable generation
icecream            # Debug printing
```

---

## Getting Started

### Initial Setup
1. Install Python 3.12+
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file with database and email settings
4. Run setup: `python setup_database.py` (creates database and seeds ISPs)
5. Add lines to database (via SQL or future admin interface)
6. Configure email recipients in database

### Daily Execution
```bash
# Manual run
python main.py --headless

# Windows Task Scheduler
# Schedule run.bat daily at desired time
```

---

## Summary

NetNinja is a production-grade network monitoring solution tailored for Egyptian ISPs. It combines web scraping automation, speed testing, and intelligent reporting into a single async Python application. The modular architecture allows for easy extension to support additional ISPs and features.

**Key Differentiators:**
- ISP-specific scraping for accurate quota data
- Concurrent async operations for performance
- Database persistence for historical analysis
- Intelligent alerting with color-coded thresholds
- Process tracing for complete audit trails

**Ideal For:**
- Organizations with multiple ISP connections
- IT departments needing automated monitoring
- Network administrators tracking performance trends
- Businesses requiring quota management automation
