# Geometry Home – Tax Invoice Management System
### UAE VAT-Compliant | Offline | Localhost

---

## QUICK START (Windows)

1. Install **Python 3.10+** from https://python.org (tick "Add to PATH" during install)
2. Double-click **START.bat**
3. Browser opens automatically at **http://localhost:5000**
4. Login: **admin** / **admin123** → change password immediately

---

## MANUAL INSTALLATION

```bash
# 1. Open Command Prompt in the application folder
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Open browser at
http://localhost:5000
```

---

## DEFAULT LOGIN

| Username | Password | Role          |
|----------|----------|---------------|
| admin    | admin123 | Administrator |

**Change the password immediately after first login.**

---

## APPLICATION STRUCTURE

```
GeometryHome_Invoice/
│
├── app.py                    ← Main application
├── requirements.txt          ← Python dependencies
├── START.bat                 ← Windows one-click launcher
├── geometry_home.db          ← SQLite database (auto-created)
│
├── static/
│   ├── images/
│   │   └── gh_footer_AE.png  ← Invoice footer image
│   └── uploads/
│       ├── logos/            ← Company logos
│       ├── signatures/       ← Signatory images
│       └── stamps/           ← Company stamp images
│
├── templates/                ← HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── invoice_form.html
│   ├── invoice_view.html
│   ├── invoices.html
│   ├── clients.html
│   ├── signatories.html
│   ├── reports.html
│   ├── settings.html
│   ├── users.html
│   └── audit_log.html
│
└── Invoices Archive/         ← Auto-saved PDF invoices
    ├── 2025/
    │   ├── GH-2025-0001.pdf
    │   └── ...
    └── 2026/
        └── ...
```

---

## FEATURES

### Invoice Management
- Create, edit, duplicate, delete invoices
- Auto-numbered: GH-2026-0001, GH-2026-0002…
- UAE VAT (5%) calculations
- Amount in words (automatic)
- Professional PDF generation

### Signature & Stamp
- Multiple signatories supported
- Multiple company stamps supported
- Select per invoice from dropdown
- Default signatory/stamp auto-selected

### Client Management
- Client directory with search
- Auto-fill client details when creating invoices
- Client archive

### Invoice Archive
- Every PDF auto-saved to `Invoices Archive/YEAR/` folder
- Accessible directly via Windows Explorer
- No need to open the application to retrieve files

### Reports
- Daily / Weekly / Monthly / Quarterly / Yearly
- Revenue and VAT summaries
- Bar chart visualization

### Security
- Role-based access: Admin / Standard User
- Password hashing (Werkzeug PBKDF2)
- Session management
- Full audit log

### Backup
- One-click backup from sidebar
- Downloads ZIP containing database + all uploads

---

## VAT INFORMATION

- Default VAT Rate: **5%** (UAE standard)
- TRN displayed on every invoice
- VAT calculated per line item
- VAT summary in totals section

---

## BANK DETAILS (Pre-configured)

| Field    | Value               |
|----------|---------------------|
| Bank     | WIO BUSINESS        |
| IBAN     | AE430860000009466073611 |
| Account  | 9466073611          |
| Swift    | WIOBAEADXXX         |

Change these in **Settings → Bank Details**

---

## ACCESSING INVOICES WITHOUT THE APPLICATION

All generated PDFs are stored at:
```
[Application Folder]\Invoices Archive\[YEAR]\[INVOICE-NUMBER].pdf
```
These are standard PDF files — open, copy, share, or print directly from Windows Explorer.

---

## TROUBLESHOOTING

**Port already in use:**
```bash
# Change port in app.py last line:
app.run(debug=False, host='0.0.0.0', port=5001)
```

**Python not found:**
- Install from https://python.org
- During install: tick ✅ "Add Python to PATH"

**PDF generation fails:**
```bash
pip install reportlab Pillow --upgrade
```

**Database reset (WARNING – deletes all data):**
```bash
del geometry_home.db
python app.py
```

---

## DEVELOPER

**Application Developer:** Denil Joseph  
*(Credit appears inside the application interface only — never on invoices or PDFs)*

**Company:** Geometry Home Furniture Manufacturing LLC  
**Website:** www.geometry-home.ae  
**License No:** 1173074 – Dubai, U.A.E.

---

*This software runs completely offline. No internet connection required. No cloud services. All data stored locally in SQLite.*
