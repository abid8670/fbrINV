# 🇵🇰 FBR Digital Invoicing (DI) System

A modern, production-grade **Flask Web Application** designed for Pakistan's **Federal Board of Revenue (FBR) Digital Invoicing (DI) API Integration** under **SRO 350(I)/2024** and the **Sales Tax Act, 1990**.

This application directly replaces manual Excel-based sales tax invoicing and spreadsheet uploads with automated REST API digital invoicing, real-time fiscal registration numbers, QR code generation, and audit logging.

---

## 🌟 Key Features

1. **🔐 Authentication & Role Management**:
   - Secure login system (Pre-configured admin account).
   - Session protection, password hashing using `werkzeug.security`.

2. **📦 Item Master Data (Catalog)**:
   - Item Code / SKU, title, and detailed descriptions.
   - **Pakistan Customs HS Codes** (Harmonized Tariff 8-digit codes e.g. `8471.3010`, `7318.1500`).
   - Unit of Measure (UOM: `NOS`, `KG`, `LTR`, `MTR`, `PKT`, etc.).
   - Base unit selling prices and customizable sales tax rates (default 18%).

3. **👥 Customer / Buyer Management**:
   - Buyer Classification: **Registered** vs **Unregistered**.
   - Tax Credentials: NTN (7/8 digits), STRN (13 digits), and CNIC (13 digits).
   - Dynamic validation: Unregistered buyers automatically receive the required **4% Further Tax**.

4. **🧾 Invoicing & FBR DI Integration**:
   - Real-time client-side calculation of **Value of Supply**, **18% Sales Tax**, **4% Further Tax**, and **Discounts**.
   - One-click **"Save & Submit to FBR DI API"** or **"Save as Draft"**.
   - Automatic generation of **FBR Fiscal Registration Number** and **Verification QR Code**.
   - Official **Sales Tax Invoice print format** conforming to Section 23 of the Sales Tax Act, 1990.
   - **Technical FBR Inspector**: Inspect transmitted JSON request payloads and FBR response logs.

5. **📊 Excel Invoicing & Migration Hub**:
   - **Download Templates**: Standard Excel spreadsheets for Items and Invoices.
   - **Bulk Invoice Import**: Upload spreadsheet files; the system groups items by Invoice Number, calculates tax, and prepares Draft invoices.
   - **Bulk Item Import**: Import your entire catalog in seconds.
   - **Excel Export**: Export FBR-registered invoices for sales tax return reconciliation.

6. **⚙️ FBR Gateway Configuration**:
   - **Mock Sandbox Mode**: Instant realistic testing without IP whitelisting delays.
   - **PRAL Staging / Sandbox Mode**: `https://staging-di.pral.com.pk/api/v1/di/postinvoicedata`
   - **PRAL Production Mode**: `https://di-api.pral.com.pk/api/v1/di/postinvoicedata`
   - **Bearer Token Management**: Pass OAuth 2.0 Bearer tokens with 5-year validity.
   - **Test Connection Tool**: Live AJAX ping to verify gateway reachability and token validity.

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure Python 3.10+ is installed on your system.

### 2. Run the Application
Open a terminal in `d:\fbrINV` and run:

```bash
python run.py
```

### 3. Access the Web Portal
- **URL**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## 📋 Directory Structure

```text
d:\fbrINV\
├── app\
│   ├── __init__.py           # Application factory & data seeders
│   ├── config.py             # App configurations & SQLite settings
│   ├── models.py             # User, Customer, Item, Invoice, CompanySetting models
│   ├── fbr_service.py        # Official DI V1.12 payload builder, QR generator & API client
│   ├── excel_service.py      # Template generator & bulk Excel import/export
│   ├── routes\
│   │   ├── auth.py           # Login/logout
│   │   ├── dashboard.py      # Analytics & KPI cards
│   │   ├── customers.py      # Customer master management
│   │   ├── items.py          # Item catalog & HS codes
│   │   ├── invoices.py       # Sales invoicing, FBR submission, print views
│   │   ├── settings.py       # Company profile & FBR token setup
│   │   └── excel_ops.py      # Bulk upload & export endpoints
│   ├── static\
│   │   ├── css\custom.css    # Modern UI styles & print rules
│   │   └── js\invoice_form.js# Live tax calculations & dynamic rows
│   └── templates\            # Jinja2 HTML views (Bootstrap 5 + Icons)
├── run.py                    # Server entrypoint
└── requirements.txt          # Python dependencies
```

---

## 📑 Official Technical References
- [FBR Technical Documentation for DI API (V1.12 PDF)](https://download1.fbr.gov.pk/Docs/20257301172130815TechnicalDocumentationforDIAPIV1.12.pdf)
- [PRAL DICRM Download Portal](https://dicrm.pral.com.pk/downloads)
- [FBR IRIS Portal](https://iris.fbr.gov.pk)
