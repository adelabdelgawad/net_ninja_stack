# Release Checklist for NetNinja v2.0

## 📦 Pre-Release Preparation

### 1. Build Executable

```bash
# Using PyInstaller
pyinstaller --name=netninja --onefile --icon=icon.ico main.py

# Or using your preferred build method
# Output: dist/netninja.exe
```

### 2. Create Release Package

**Files to include in `NetNinja-v2.0.zip`:**

```
NetNinja-v2.0/
├── netninja.exe           # ✅ Built executable
└── .env.example           # ✅ Configuration template
```

**DO NOT include:**
- ❌ `.env` (user-specific)
- ❌ `app.db` (will be auto-created)
- ❌ `.secret.key` (will be auto-created)
- ❌ `logs/` directory
- ❌ Python source files
- ❌ `__pycache__/`

### 3. Test the Package

1. Extract `NetNinja-v2.0.zip` to a clean folder
2. Create `.env` from `.env.example`
3. Run `netninja.exe --setup-db`
4. Verify database creation
5. Test with `netninja.exe --dry-run`
6. Test full execution: `netninja.exe --headless`

---

## 🚀 GitHub Release Steps

### 1. Create New Release

1. Go to: **Releases** → **Draft a new release**
2. **Tag version:** `v2.0`
3. **Release title:** `NetNinja v2.0 - Production Release 🚀`
4. **Target:** `main` branch

### 2. Copy Release Notes

- Copy entire content from `GITHUB_RELEASE.md`
- Paste into release description

### 3. Upload Assets

**Asset to upload:**
- `NetNinja-v2.0.zip` (executable + .env.example)

**Optional assets:**
- `README.md`
- `CHANGELOG.md`

### 4. Release Settings

- ✅ Set as latest release
- ✅ Create a discussion for this release (optional)
- ❌ Do NOT mark as pre-release

### 5. Publish

Click **Publish release**

---

## ✅ Post-Release Verification

### Check Release Page
- [ ] Release notes formatted correctly
- [ ] Expandable "What Changed" section works
- [ ] All CLI commands visible
- [ ] ZIP file downloadable
- [ ] Asset shows correct size

### Test Download
- [ ] Download ZIP from release page
- [ ] Extract and verify contents
- [ ] Follow "First Time Setup" instructions
- [ ] Verify executable runs

### Update Documentation
- [ ] Update main README.md with release link
- [ ] Update any wiki pages
- [ ] Close related issues with "Fixed in v2.0"

---

## 📝 Release Notes Structure (Reference)

The `GITHUB_RELEASE.md` contains:

1. **Download & Installation** (top section)
2. **What's New** (highlights with emojis)
3. **Expandable "Click to see all changes"** (detailed changelog)
4. **Getting Started** (first-time setup)
5. **Usage & Commands** (all CLI arguments)
6. **Security & Encryption** (how it works)
7. **Email Configuration** (setup guide)
8. **Logging** (location and rotation)
9. **Reports** (format options)
10. **Configuration Reference** (all env variables)
11. **Upgrade Instructions** (from v1.0)
12. **Breaking Changes** (warnings)
13. **Troubleshooting** (common issues)
14. **System Requirements**
15. **Files Included** (what's in the zip)
16. **Resources** (links)

---

## 🔄 For Future Releases

### Version Numbering
- Major: `v3.0` (breaking changes)
- Minor: `v2.1` (new features)
- Patch: `v2.0.1` (bug fixes)

### Release Naming
- Format: `NetNinja v{version} - {description}`
- Examples:
  - `NetNinja v2.1 - Orange ISP Support`
  - `NetNinja v2.0.1 - Critical Bug Fixes`

### Tag Format
- Use: `v2.0`, `v2.1`, `v2.0.1`
- Don't use: `2.0`, `version-2.0`, `release-2.0`

---

## 📧 Announcement Template

After release, announce on:

**GitHub Discussions:**
```
🚀 NetNinja v2.0 Released!

Major rewrite with enhanced security and reliability.

Download: [Link to release]

Highlights:
- 🔒 Credential encryption
- 📧 Smart email retry
- 🎯 Enhanced CLI
- 📊 Multiple report formats

See full release notes for details.
```

**Project README:**
```markdown
## Latest Release

**[NetNinja v2.0](../../releases/tag/v2.0)** - Production Release (Oct 2025)

Download: [NetNinja-v2.0.zip](../../releases/download/v2.0/NetNinja-v2.0.zip)
```

---

## ✅ Final Checklist

Before publishing:

- [ ] Executable tested on clean Windows machine
- [ ] All dependencies bundled in executable
- [ ] .env.example has all required fields
- [ ] ZIP file named correctly: `NetNinja-v2.0.zip`
- [ ] Release notes reviewed and proofread
- [ ] Tag matches release title: `v2.0`
- [ ] No sensitive data in release files
- [ ] License file included (if required)
- [ ] Version number updated in code

After publishing:

- [ ] Download link works
- [ ] Release appears in "Latest Release"
- [ ] Documentation links point to v2.0
- [ ] Old issues tagged with "Fixed in v2.0"
- [ ] Announcement posted (if applicable)

---

**Release Manager:** [Your Name]
**Release Date:** [Date]
**Status:** ✅ Ready for Release
