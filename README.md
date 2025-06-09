# Bachelor Project

This repository contains a React frontend and a Django-pgvector backend for your bachelor project.

## 1. Clone the repository

```bash
git clone https://github.com/NotnAK/bachelor_project.git
cd bachelor_project
```

---

## 2. Frontend Setup

1. **Install Node.js & npm**
   Make sure you have Node.js (v16+) and npm installed:

   ```bash
   node --version
   npm --version
   ```

2. **Install dependencies**

   ```bash
   cd frontend
   npm ci
   ```

3. **Check API URL**
   In `frontend/src/config.js` you have:

   ```js
   export const API_URL = 'http://localhost:8000';
   ```

   Make sure your backend will run on port 8000 (default for Django).

4. **Run the dev server**

   ```bash
   npm start
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 3. Backend Setup

### 3.1. Prepare heavy data (media & models)

We don’t commit large files to GitHub. You need to download two ZIP archives from Google Drive:

[https://drive.google.com/drive/folders/1zvDDUdfyF5faHSku7d\_bo2hDAEbb-H3b?usp=sharing](https://drive.google.com/drive/folders/1zvDDUdfyF5faHSku7d_bo2hDAEbb-H3b?usp=sharing)

* **media.zip** (contains `extracted_paintings/` where our media is stored)
* **models.zip** (contains our fine-tuned version of paligemma and tokenizer)

Further your task is to unpack these zip archives and copy the contents of **media** and **models** folders to the corresponding folders in your project. 

After this, you should have:

```
bachelor_project/
├── media/
│   └── extracted_paintings/…
├── models/
│   └── paligemma-3b-mix-448.f16.npz
│   └── paligemma_tokenizer.model
└── (other project files…)
```

### 3.2. Install PostgreSQL & pgvector

1. **Install PostgreSQL**

   * **Ubuntu/Debian**

     ```bash
     sudo apt update
     sudo apt install postgresql postgresql-contrib
     ```
   * **macOS (Homebrew)**

     ```bash
     brew install postgresql
     ```

2. **Install pgvector**

   * **Ubuntu/Debian** (PostgreSQL 15 example)

     ```bash
     sudo apt install postgresql-15-pgvector
     ```
   * **From source**

     ```bash
     git clone https://github.com/pgvector/pgvector.git
     cd pgvector
     make && sudo make install
     ```

3. **Start PostgreSQL** (if not already running)

   ```bash
   sudo systemctl start postgresql
   ```

### 3.3. Create database & user, enable extension

Switch to the `postgres` superuser and run:

```bash
sudo -u postgres psql
```

In the `psql>` prompt:

```sql
-- 1) Create a dedicated user
CREATE ROLE gallery_user LOGIN PASSWORD 'gallery_pass';

-- 2) Create the database
CREATE DATABASE gallery_db OWNER gallery_user;

-- 3) Enable pgvector extension in that DB
\c gallery_db
CREATE EXTENSION IF NOT EXISTS vector;

\q
```

### 3.4. Restore the dump (schema + data + migrations)

We shipped a `db/dump/db.dump` (custom format) with the full database snapshot. To restore:

```bash
pg_restore \
  --verbose \
  --clean \
  --no-acl \
  --no-owner \
  -h localhost -p 5432 \
  -U gallery_user \
  -d gallery_db \
  db/dump/db.dump
```

* When prompted for a password, enter `gallery_pass`.
* `--clean` will drop existing objects before recreating them.
* After this, **all tables**, **data**, and **records of applied migrations** will be in place.

### 3.5. Python virtual environment & dependencies

1. **Create & activate a venv**

   ```bash
   cd bachelor_project
   python3 -m venv .venv
   source .venv/bin/activate       # Linux/macOS
   # .venv\Scripts\activate.bat    # Windows
   ```

2. **Install Python dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 3.6. Run migrations & start the server

> **Note:** Because the dump includes all past migrations (table `django_migrations`), running `migrate` will skip them and apply only any new ones.

```bash
# Apply any outstanding migrations (if you add new ones later)
python manage.py migrate

# (Optional) Create a superuser
python manage.py createsuperuser

# Start Django dev server on port 8000
python manage.py runserver 0.0.0.0:8000
```

Open [http://localhost:8000](http://localhost:8000) to verify your API is up.

---

## 4. Summary

1. **Clone**

   ```bash
   git clone https://github.com/NotnAK/bachelor_project.git
   cd bachelor_project
   ```

2. **Frontend**

   ```bash
   cd frontend
   npm ci
   npm start
   ```

3. **Backend**

   ```bash
   cd ../
   # download & unzip media.zip → media/, models.zip → models/
   # install PostgreSQL & pgvector
   # create user, database, extension
   pg_restore … db/dump/db.dump
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. **Browse**

   * Frontend: [http://localhost:3000](http://localhost:3000)
   * Backend API: [http://localhost:8000](http://localhost:8000)


