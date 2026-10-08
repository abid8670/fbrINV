# 🚀 FBR Digital Invoicing System - Complete Deployment Guide
**Compliance:** FBR Digital Invoicing (DI) Specification V1.12 | SRO 350(I)/2024 | Section 23 of Sales Tax Act 1990  
**Target Environments:** Standalone Windows PC, Multi-User Local Office Network (LAN), and Cloud/VPS (Docker).

---

## 📌 Executive Summary
Aapka FBR Digital Invoicing Software mukammal tor par **Commercial & Ready-to-Sell** tayyar hai. Isme:
1. **Interactive First-Run Setup Wizard (`/setup`)**: Database engine (SQLite / MySQL / PostgreSQL), Company Profile, Admin credentials, aur AI Voice auto-configure karta hai.
2. **Bilingual AI Voice Assistant**: Google AI Studio (Gemini), Google Cloud Neural TTS, aur Zero-config Native Browser Speech dono support karta hai.
3. **Flexible Deployment**: 1-Click Windows Batch, Standalone `.exe` compiler, Multi-Threaded Production WSGI Server (`Waitress`), aur Docker Cloud containers shamil hain.

---

## 🖥️ Option 1: Client PC par 1-Click Run (Recommended for Small Shops & Single PC)

Client ke computer par chalane ka sabse aasan tariqa:

### Steps:
1. Pura `fbrINV` folder client ke PC par copy karein (maslan `D:\fbrINV` ya `C:\fbrINV`).
2. **`start_app.bat`** par double click karein.
   - Yeh server start karega aur default browser me software khol dega (`http://127.0.0.1:5000`).
3. Agar pehli dafa chal raha hai, to **Setup Wizard (`/setup`)** samne aayega:
   - **Step 1:** Select **SQLite (Embedded Zero-Config)** — kisi external DB install karne ki zaroorat nahi.
   - **Step 2:** Company ka Registered NTN, STRN, aur Name darj karein.
   - **Step 3:** Admin username aur password set karein.
   - **Step 4:** AI Voice Language (Urdu/English) aur Provider select karein.
   - **Submit** par click karte hi software activate ho jayega!

---

## 🏢 Option 2: Multi-User Local Office Network / LAN (For Medium Businesses & Cashier Counters)

Agar office ya factory me multiple computers (Accountant, Salesman, Cashier, Manager) hain:

### Steps:
1. Main computer (Server PC) par **`run_production.bat`** chalayein.
2. Yeh **Waitress Production WSGI Server** (16 multi-threaded workers) start karta hai aur screen par local IP show karta hai:
   ```text
   [*] Local Machine Access:       http://127.0.0.1:5000
   [*] LAN Office / Shop Access:    http://192.168.1.15:5000
   [*] Concurrency:               16 Multi-Threaded Workers Active
   ```
3. Network me kisi bhi doosre computer ya mobile tablet se browser kholen aur IP address enter karein (e.g. `http://192.168.1.15:5000`).
4. Mukhtalif users apne alag accounts (Role: Manager, Operator, Viewer) se aik hi waqt me billing kar sakte hain.

> **💡 Database Tip:** Agar LAN me bohot zyada traffic ho, to Setup Wizard ya Settings me **MySQL** ya **PostgreSQL** select karke centralized database use karein.

---

## 📦 Option 3: Standalone Windows .EXE Packaging (Without Python Installation)

Agar aap client ko python files nahi dena chahte aur aik direct `.exe` software dena chahte hain:

### Steps:
1. Apne computer par **`build_installer.bat`** par double click karein.
2. PyInstaller khud ba khud HTML templates, static files, SQLite engine, aur tamam drivers ko pack karke standalone application bana dega.
3. Build complete hone par `dist\FBR_Digital_Invoicing` folder tayyar hoga.
4. Is folder ko zip karke kisi bhi client ko deliver kar sakte hain. Client ko sirf `FBR_Digital_Invoicing.exe` chalana hoga.

---

## ☁️ Option 4: Cloud Server / VPS par Deploy (Docker & Docker Compose)

Agar cloud server (DigitalOcean, AWS, Hetzner, Linux VPS) par deploy karna ho:

### Steps:
1. Server par repository clone karein:
   ```bash
   git clone <repo-url> fbrINV
   cd fbrINV
   ```
2. Docker Compose command chalayein:
   ```bash
   docker-compose up -d --build
   ```
3. Docker khud PostgreSQL 15 database aur Gunicorn production web server container start kar dega.
4. Application `http://YOUR_SERVER_IP:5000` par 24/7 chalegi. Nginx reverse proxy aur SSL (Let's Encrypt HTTPS) bhi asani se add ho sakta hai.

---

## 🎙️ AI Voice & Google AI Studio Setup Guide

Software me bilingual audio assistant shamil hai jo flash alerts, invoice status, aur page summaries parhta hai:

### Google AI Studio (Gemini) Free API Key Lagane ka Tariqa:
1. `https://aistudio.google.com` par jayein aur **"Get API key"** par click karein (yeh bilkul free hai).
2. Key copy karein (`AIzaSy...`).
3. Software me **Settings > FBR Integration & Company Profile** (ya Setup Wizard) par jayein:
   - **Voice Provider**: Select karein `Google AI Studio (Gemini AI Free API Key)`.
   - **API Key**: Apni copy shuda `AIzaSy...` key paste karein.
   - **Spoken Language**: `Urdu (Pakistan - ur-PK)` ya `English (en-US)` select karein.
4. **"Test Voice & API Key"** button dabayein:
   - System live Gemini API ko verify karega aur green confirmation dega:  
     `✅ Google AI Studio (Gemini 1.5 Flash) Connected Successfully! AI Voice is active.`
5. **Browser Native Fallback**: Agar internet na ho ya API key na bhi ho, tab bhi software ka **Native Browser Speech** 100% free aur bina kisi key ke kaam karta hai!

---

## 💾 1-Click Database Backup & Disaster Recovery

Client ka tax data mehfooz rakhne ke liye automated backup system:

### 1. Backup Lena:
- Simply **`backup_data.bat`** par double click karein.
- Yeh tamam SQLite databases, app configurations, aur uploaded files ko timestamped zip archive me compress karke `backups\` folder me save kar dega:
  ```text
  [OK] BACKUP CREATED SUCCESSFULLY!
  Backup Archive: d:\fbrINV\backups\FBR_Data_Backup_20261006_173000.zip
  ```

### 2. Restore Karna:
- Kisi bhi waqt purana data restore karne ke liye command run karein:
  ```bash
  python backup_restore.py --restore backups/FBR_Data_Backup_20261006_173000.zip
  ```

---

## 📋 Pre-Deployment Client Checklist

| Item | Status | Description |
|---|:---:|---|
| **FBR Environment** | ✅ Ready | Settings me `Mock`, `Sandbox`, ya `Production` select karein |
| **Section 23 Invoices** | ✅ Ready | Auto QR code, PKR words, NTN/STRN, Tax Breakup |
| **Annexure-C Export** | ✅ Ready | Monthly return Excel export FBR IRIS format me |
| **Sales Return (Credit Note)** | ✅ Ready | 1-Click auto adjustment Scenario SN003 |
| **RBAC User Roles** | ✅ Ready | Admin, Manager, Operator, Viewer with granular permissions |
| **Audit Logs** | ✅ Ready | Complete trail of all actions with timestamps and IP |

---

## ☁️ Option 5: 100% Free Cloud Web Hosting (Vercel, Render, PythonAnywhere)

Aap is app ko internet par bilkul free host kar sakte hain taake kahin se bhi mobile ya laptop par live link se chalaya ja sake:

### 1. Koyeb.com (Highly Recommended & Super Fast - 100% Free)
- **Kyun behtar hai?** Koyeb par container 24/7 bina soye (without sleep mode) chalta hai aur hamari `Dockerfile` ya `Procfile` ko foran build kar leta hai.
- **Tariqa (Sirf 2 Minute):**
  1. Apne code ko GitHub repository me push karein.
  2. `https://www.koyeb.com` par jayein aur Free Account banayein (GitHub se sign in karein).
  3. **"Create Service"** > **"GitHub"** par click karein aur apni repo select karein.
  4. Builder me **"Buildpack"** (ya "Dockerfile") select karein.
  5. **Environment Variables** me yeh 2 cheezain add karein:
     - `DATABASE_URL`: `postgresql://FBR_owner:npg_QaPSb6HCkx5f@ep-muddy-brook-b48oeoyd-pooler.c-6.us-east-2.aws.neon.tech/FBR?sslmode=require&channel_binding=require`
     - `SECRET_KEY`: `fbr-digital-invoicing-secret-key-2026-safe-default`
  6. **Ports** me Port **8000** (ya 5000) confirm karein.
  7. **Deploy** dabayein! Koyeb 1 minute me aapko free SSL live link de dega:
     ```text
     https://<your-app-name>.koyeb.app
     ```

### 2. Render.com (Recommended for Flask & 24/7 Cloud Access - 100% Free)
- **Tariqa:**
  1. Apne code ko GitHub repository me push karein.
  2. `https://render.com` par jayein aur Free Account banayein.
  3. **New > Web Service** par click karein aur apni GitHub repo connect karein.
  4. Settings:
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn wsgi:app`
  5. 2 minute me aapka live free URL ready hoga (e.g. `https://my-fbr-system.onrender.com`).

### 3. Vercel (Serverless Cloud - 100% Free)
- **Wazaahat:** Vercel serverless platform hai jisme hard disk read-only hoti hai. Isliye Neon PostgreSQL cloud database zaroori hai.
- **Tariqa:**
  1. GitHub repo ko `https://vercel.com` par import karein.
  2. Vercel ke **Environment Variables** me add karein:
     - `DATABASE_URL`: Neon PostgreSQL link.
     - `SECRET_KEY`: `fbr-digital-invoicing-secret-key-2026-safe-default`.
  3. Repository me pehle se shamil `vercel.json` aur `wsgi.py` khud ba khud Vercel par app live kar denge!

### 4. PythonAnywhere.com (Best for Local SQLite - 100% Free)
- Agar aap koi external database nahi banana chahte aur local SQLite hi use karna chahte hain:
  1. `https://www.pythonanywhere.com` par free account banayein.
  2. **Web** tab me ja kar **Add a new web app > Flask > Python 3.10** select karein.
  3. Files upload karein aur SQLite DB ke sath 100% persistent free hosting hasil karein!


