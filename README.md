<div align="center">

# ⚡ FiscalSync DI
### Enterprise FBR Digital Invoicing & Tax Compliance Suite

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0-lightgrey.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![FBR DI Spec](https://img.shields.io/badge/FBR%20DI%20Spec-V1.12%20Compliant-emerald.svg?logo=checkmarx&logoColor=white)](https://fbr.gov.pk)
[![Regulation](https://img.shields.io/badge/SRO-350(I)%2F2024-green.svg)](https://fbr.gov.pk)
[![Sales Tax Act](https://img.shields.io/badge/Sales%20Tax%20Act-1990%20Sec%2023-teal.svg)](https://fbr.gov.pk)
[![Deployment](https://img.shields.io/badge/Cloud%20Live-Vercel%20Serverless-black.svg?logo=vercel&logoColor=white)](https://fbrinv.vercel.app/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite%20%7C%20MySQL-blue.svg?logo=postgresql&logoColor=white)](https://neon.tech)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Commercial-amber.svg)](#)

<p align="center">
  <b>Pakistan's premier commercial-ready digital invoicing software engineered for real-time fiscalization with the Federal Board of Revenue (FBR) & PRAL gateway.</b>
</p>

[🌐 Live Cloud Demo](https://fbrinv.vercel.app/) • [📖 Deployment Guide](DEPLOYMENT_GUIDE.md) • [📋 FBR V1.12 Specs](https://download1.fbr.gov.pk/Docs/20257301172130815TechnicalDocumentationforDIAPIV1.12.pdf)

</div>

---

## 🌐 Live Cloud Demo

- **URL:** **[https://fbrinv.vercel.app/](https://fbrinv.vercel.app/)**
- **Default Username:** `admin`
- **Default Password:** `admin123`

---

## 📌 Executive Overview

**FiscalSync DI** is a comprehensive, production-grade enterprise tax compliance platform designed specifically to satisfy Pakistan's statutory digital invoicing mandates under **SRO 350(I)/2024** and **Section 23 of the Sales Tax Act, 1990**.

The suite bridges the gap between everyday business billing operations and the official **PRAL Digital Invoicing Gateway**, delivering real-time validation, fiscal invoice registration numbers, dynamic cryptographic QR code stamping, automated Annexure-C reconciliation, and multi-format printing (A4 and POS Thermal).

---

## 🌟 Key Features

### 1. ⚡ Real-Time FBR DI API Integration (V1.12 Specification)
- **Direct PRAL Integration:** Seamless integration with official PRAL REST API endpoints (`/api/v1/di/postinvoicedata`).
- **Tri-Mode Gateway Switch:**
  - **Mock Sandbox Mode:** Instant offline development and demonstration without IP whitelisting restrictions.
  - **PRAL Staging / Sandbox Mode:** Official test environment (`https://staging-di.pral.com.pk`).
  - **PRAL Production Mode:** Live commercial fiscal gateway (`https://di-api.pral.com.pk`).
- **Fiscal Authentication:** 5-year Bearer token management with dynamic connection health tester.
- **Payload Inspector:** Technical inspection panel showing exact JSON payloads transmitted to FBR and raw PRAL API responses.

### 2. 🇵🇰 SRO 350(I)/2024 & Section 23 Legal Compliance
- **Tax Math Engine:** Dynamic client and server calculation of **Value of Supply**, standard **18% Sales Tax**, required **4% Further Tax** (for unregistered buyers), and volume discounts.
- **Buyer Validation:** Strict verification of Buyer NTN (7/8 digits), STRN (13 digits), and CNIC (13 digits).
- **Automated Sales Returns:** Credit Note generation (Scenario `SN003`) with original invoice cross-referencing.
- **FBR QR Code Engine:** Embedded Base64 QR code generation containing verifiable fiscal registration data.

### 3. 🧾 Multi-Channel Invoice Distribution & Printing
- **A4 Formal Tax Invoice:** Official tax invoice template strictly formatted according to Section 23, with PKR amount in words, NTN/STRN credentials, and legal declaration.
- **POS Thermal Printing:** Compact 58mm and 80mm ESC/POS-compatible thermal receipts for retail cashier desks.
- **Direct WhatsApp Sharing:** Pre-formatted, one-click WhatsApp sharing copy containing full fiscal invoice breakdown and FBR number.

### 4. 🎙️ Bilingual AI Munshi Assistant (Urdu & English)
- **Interactive Audio Assistant:** Real-time speech announcements for invoice status, tax calculations, and navigation alerts.
- **Google AI Studio (Gemini 1.5 Flash):** High-quality natural voice synthesis.
- **Zero-Config Browser Fallback:** Built-in Web Speech API support requiring zero API keys or external setup.

### 5. 📊 Excel Migration Hub & Annexure-C Engine
- **Bulk Item Import:** Ingest thousands of SKU catalogs with 8-digit Pakistan Customs HS Codes in seconds.
- **Bulk Invoice Import:** Group multi-item spreadsheets by invoice number and generate draft invoices in batch.
- **Annexure-C Reconciliation:** Export monthly sales tax returns in the exact schema required for direct filing into the **FBR IRIS Portal**.

### 6. 🔐 Enterprise RBAC & Audit Trail
- **Granular User Roles:** Admin, Manager, Operator, and Viewer roles with role-based access control.
- **Tamper-Evident Audit Logs:** Complete logging of invoice creation, edits, submissions, user logins, and IP addresses.
- **Interactive First-Run Wizard:** Complete first-time deployment wizard at `/setup` for zero-friction client onboarding.

---

## 🏗️ Architecture & Tech Stack

```text
               ┌────────────────────────────────────────────────────────┐
               │                     FiscalSync DI                      │
               │                   (Enterprise Suite)                   │
               └───────────────────────────┬────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼────────────────────────────────┐
         │                                 │                                │
         ▼                                 ▼                                ▼
┌─────────────────┐             ┌─────────────────────┐          ┌──────────────────────┐
│  Presentation   │             │   Business Logic    │          │     Data Layer       │
├─────────────────┤             ├─────────────────────┤          ├──────────────────────┤
│ • Bootstrap 5   │             │ • Flask 3.0 (WSGI)  │          │ • PostgreSQL (Neon)  │
│ • Custom CSS    │ ◄─────────► │ • FBR Service V1.12 │ ◄──────► │ • SQLite3 (Embedded) │
│ • Vanilla JS    │             │ • Excel Service     │          │ • MySQL (Supported)  │
│ • Responsive UI │             │ • AI Voice Munshi   │          │ • SQLAlchemy ORM     │
└─────────────────┘             └──────────┬──────────┘          └──────────────────────┘
                                           │
                                           ▼
                                ┌─────────────────────┐
                                │   PRAL / FBR API    │
                                │   (REST Gateway)    │
                                └─────────────────────┘
```

| Component | Technology | Description |
|---|---|---|
| **Backend Core** | Python 3.10+ / Flask 3.0 | Lightweight, secure WSGI web framework |
| **ORM & Database** | SQLAlchemy / Neon PostgreSQL | High-performance ORM supporting SQLite, Postgres & MySQL |
| **Styling & UI** | Vanilla CSS + Bootstrap 5 | Custom glassmorphism, responsive emerald enterprise theme |
| **QR Generation** | `qrcode` + `Pillow` | Cryptographic QR code generation with high error-correction |
| **Spreadsheets** | `pandas` + `openpyxl` | Excel template generation, validation & bulk processing |
| **Production WSGI** | Waitress / Gunicorn | Multi-threaded production server capable of 16+ workers |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher installed on your system.

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/abid8670/fbrINV.git
cd fbrINV

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Locally

```bash
python run.py
```

Open your browser at **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 💼 Deployment Modes

FiscalSync DI supports multiple deployment environments:

| Deployment Mode | Recommended For | Launch Command |
|---|---|---|
| **1-Click Windows App** | Small shops, single accounting PC | Double click `start_app.bat` |
| **Multi-User Office LAN** | Medium enterprises, multiple cashiers | Double click `run_production.bat` |
| **Standalone Desktop EXE** | Clients without Python installed | Double click `build_installer.bat` |
| **Cloud Server (Docker)** | VPS, AWS, DigitalOcean | `docker-compose up -d --build` |
| **Serverless Cloud** | Vercel, Neon PostgreSQL | Connect repository to Vercel |

For in-depth step-by-step instructions on each method, please refer to the **[Complete Deployment Guide](DEPLOYMENT_GUIDE.md)**.

---

## 📁 Repository Structure

```text
d:\fbrINV\
├── api\
│   └── index.py              # Serverless WSGI entrypoint for Vercel
├── app\
│   ├── __init__.py           # Application factory, middleware & database init
│   ├── config.py             # Environment configurations (SQLite, Postgres, MySQL)
│   ├── models.py             # User, Customer, Item, Invoice, CompanySetting models
│   ├── fbr_service.py        # Official DI V1.12 payload builder & PRAL client
│   ├── excel_service.py      # Template generator & bulk Excel import/export
│   ├── ai_voice_service.py   # Bilingual Munshi AI voice assistant
│   ├── setup_manager.py      # First-run setup wizard state controller
│   ├── routes\               # Modular blueprints (Auth, Dashboard, Invoices, etc.)
│   ├── static\               # Custom CSS design system, JS handlers & icons
│   └── templates\            # Responsive Jinja2 HTML templates
├── run.py                    # Local development runner
├── server_production.py      # Waitress multi-threaded production server
├── build_exe.py              # PyInstaller standalone packager
├── start_app.bat             # 1-Click desktop launcher
├── run_production.bat        # 1-Click multi-user LAN launcher
├── build_installer.bat       # Standalone EXE builder script
├── backup_data.bat           # 1-Click automated database backup
├── Dockerfile                # Production container specification
├── docker-compose.yml        # Multi-container orchestration (Gunicorn + Postgres)
├── vercel.json               # Vercel serverless deployment config
└── requirements.txt          # Python package dependencies
```

---

## 📑 Statutory & Technical References

- **FBR Technical Documentation for DI API (V1.12):** [Download PDF](https://download1.fbr.gov.pk/Docs/20257301172130815TechnicalDocumentationforDIAPIV1.12.pdf)
- **PRAL Digital Invoicing Download Portal:** [DICRM Portal](https://dicrm.pral.com.pk/downloads)
- **FBR IRIS Portal:** [iris.fbr.gov.pk](https://iris.fbr.gov.pk)
- **Statutory Regulatory Order (SRO):** SRO 350(I)/2024
- **Governing Law:** Section 23 of the Sales Tax Act, 1990

---

## 📄 License & Commercial Rights

Copyright © 2026. All rights reserved. Developed for commercial deployment and enterprise tax compliance across Pakistan.
