# 🛒 ShopEasy Price Intelligence Pipeline

An automated web scraping ETL pipeline that extracts product data from [books.toscrape.com](https://books.toscrape.com), cleans and transforms it, loads it into a PostgreSQL database, and runs business analytics queries to generate pricing insights.

Built as a capstone project for Data Engineering — covering web scraping, data cleaning, database design, SQL analytics, and pipeline automation.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Analytics Queries](#analytics-queries)
- [Ethical Scraping](#ethical-scraping)
- [Known Issues & Fixes](#known-issues--fixes)

---

## Project Overview

ShopEasy Retail Intelligence is a price monitoring system that automates the collection and analysis of product pricing data across multiple categories. The pipeline replaces manual data collection with a fully automated, scheduled system that:

- Scrapes 1,000+ books across 50 categories
- Cleans and standardises raw data
- Stores structured data in PostgreSQL
- Generates actionable pricing insights via SQL
- Runs automatically every 24 hours

---

## Architecture

```
Website (books.toscrape.com)
        │
        ▼
  extract.py          ← Scrapes product name, price, rating, category
        │
        ▼  raw_books.json
  transform.py        ← Cleans prices, fixes encoding, removes duplicates
        │
        ▼  clean_books.csv
   load.py            ← Creates PostgreSQL schema, loads all records
        │
        ▼
  PostgreSQL (shopeasy)
        │
        ▼
  analytics.sql       ← Business intelligence queries
        │
        ▼
  pipeline.py         ← Orchestrates all steps, runs on a 24h schedule
```

---

## Features

- **Robust scraping** — retry logic with exponential backoff, SSL handling, polite delays
- **Multi-category pagination** — follows next-page links across all 50 categories
- **Data cleaning** — fixes encoding issues (`Â£` → `£`), strips currency symbols, handles nulls
- **Incremental loading** — new price snapshots added on every run (enables trend tracking)
- **Business analytics** — overpriced/underpriced detection, price variation by category, price change over time
- **Automated scheduling** — runs every 24 hours via the `schedule` library
- **Logging** — all pipeline events written to `pipeline.log`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | `requests`, `beautifulsoup4`, `lxml` |
| Data processing | `pandas`, `numpy` |
| Database | PostgreSQL 16, `psycopg2`, `SQLAlchemy` |
| Scheduling | `schedule` |
| Config | `python-dotenv` |
| Language | Python 3.13 |

---

## Project Structure

```
shopeasy-pipeline/
├── extract.py          # Task 1: Web scraping
├── transform.py        # Task 2: Data cleaning & transformation
├── load.py             # Task 3: Database design & loading
├── analytics.sql       # Task 4: Business analytics queries
├── pipeline.py         # Task 5: Pipeline automation
├── requirements.txt    # Python dependencies
├── .env                # Database credentials (not committed)
├── .env.example        # Template for .env
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+ (3.13 supported)
- PostgreSQL 16
- Git

### 1. Clone the repository

```bash
git clone https://github.com/obeng/shopeasy-pipeline.git
cd shopeasy-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shopeasy
DB_USER=your_mac_username
DB_PASSWORD=
```

### 5. Start PostgreSQL and create the database

```bash
brew services start postgresql@16

psql postgres -c "CREATE DATABASE shopeasy;"
```

---

## Usage

### Run the full pipeline once

```bash
python pipeline.py
```

This will:
1. Scrape all books from books.toscrape.com (~3–4 minutes)
2. Clean and transform the data
3. Load 1,000 records into PostgreSQL
4. Schedule the next run in 24 hours

### Run individual steps

```bash
python extract.py       # Scrape only → saves raw_books.json
python transform.py     # Clean only  → saves clean_books.csv
python load.py          # Load only   → pushes to PostgreSQL
```

### Run analytics queries

```bash
psql -d shopeasy -f analytics.sql
```

Or open `analytics.sql` in pgAdmin and run from there.

### Verify data in PostgreSQL

```bash
psql -d shopeasy -c "SELECT COUNT(*) FROM products;"
psql -d shopeasy -c "SELECT COUNT(*) FROM price_snapshots;"
psql -d shopeasy -c "SELECT COUNT(*) FROM categories;"
```

---

## Database Schema

Three tables following a normalised design:

```sql
categories
├── id   SERIAL PRIMARY KEY
└── name VARCHAR(100) UNIQUE

products
├── id          UUID PRIMARY KEY
├── name        TEXT
├── category_id INT → categories.id
└── created_at  TIMESTAMP

price_snapshots
├── id         SERIAL PRIMARY KEY
├── product_id UUID → products.id
├── price      NUMERIC(10,2)
├── rating     SMALLINT (0–5)
└── scraped_at TIMESTAMP
```

A new row is inserted into `price_snapshots` on every pipeline run, enabling price trend analysis over time.

---

## Analytics Queries

`analytics.sql` contains five business intelligence queries:

| Query | Business Question |
|---|---|
| 1 | Which products are overpriced or underpriced vs their category average? |
| 2 | Which categories show the most price variation? |
| 3 | How have prices changed over time? |
| 4 | What is the top-rated book in each category? |
| 5 | Overall catalogue summary (avg price, rating, count) |

---

## Ethical Scraping

This project follows responsible scraping practices:

- ✅ `robots.txt` checked before every run
- ✅ `time.sleep(1)` delay between every request
- ✅ `User-Agent` header identifies the scraper
- ✅ Exponential backoff on `429 Too Many Requests`
- ✅ Target site (`books.toscrape.com`) is purpose-built for educational scraping

---

## Known Issues & Fixes

| Issue | Fix Applied |
|---|---|
| `SSLEOFError` on Mac/Python 3.13 | `verify=False` + retry session with `HTTPAdapter` |
| `Â£` encoding (mojibake) | `response.encoding = "utf-8"` + `ensure_ascii=False` when saving JSON |
| `ModuleNotFoundError` on import | Removed `.py` from import statements |
| `DataFrame constructor` error | Fixed to `json.load()` before passing to `pd.DataFrame()` |
| Database doesn't exist | `create_database_if_not_exists()` auto-creates on first run |

---

## Author

**Frank Obeng** — Data Engineering  Project
