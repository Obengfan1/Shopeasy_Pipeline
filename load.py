import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# -------------------------------------------------------
# STEP 1: Load database credentials from .env file
# This keeps passwords out of the code
# -------------------------------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# -------------------------------------------------------
# STEP 2: Create the database tables (schema)
# We create 3 tables:
#   - categories: stores unique category names
#   - products: stores each unique book
#   - price_snapshots: stores the price each time we scrape
# This separation lets us track price changes over time
# -------------------------------------------------------
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id          UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    category_id INT REFERENCES categories(id),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id         SERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    price      NUMERIC(10, 2) NOT NULL,
    rating     SMALLINT CHECK (rating BETWEEN 0 AND 5),
    scraped_at TIMESTAMP NOT NULL
);
"""


def create_tables(engine):
    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLES_SQL))
        conn.commit()
    print("Tables created successfully")


# -------------------------------------------------------
# STEP 3: Load categories first
# We insert each unique category and get back its ID
# so we can link it to the products table
# -------------------------------------------------------
def load_categories(df, engine):
    categories = df["category"].unique().tolist()

    with engine.connect() as conn:
        for cat in categories:
            conn.execute(text("""
                INSERT INTO categories (name)
                VALUES (:name)
                ON CONFLICT (name) DO NOTHING
            """), {"name": cat})
        conn.commit()

    print(f"Loaded {len(categories)} categories")


# -------------------------------------------------------
# STEP 4: Load products
# We look up the category_id for each book's category
# then insert the book into the products table
# -------------------------------------------------------
def load_products(df, engine):
    # Fetch the category name → id mapping from DB
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name FROM categories"))
        cat_map = {row.name: row.id for row in result}

    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO products (id, name, category_id)
                VALUES (:id, :name, :category_id)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": row["id"],
                "name": row["name"],
                "category_id": cat_map.get(row["category"])
            })
        conn.commit()

    print(f"Loaded {len(df)} products")


# -------------------------------------------------------
# STEP 5: Load price snapshots
# Every time we run the pipeline, a new snapshot is added
# This is how we track price changes over time
# -------------------------------------------------------
def load_price_snapshots(df, engine):
    snapshot_df = df[["id", "price", "rating", "scraped_at"]].copy()
    snapshot_df.rename(columns={"id": "product_id"}, inplace=True)

    snapshot_df.to_sql(
        "price_snapshots",
        engine,
        if_exists="append",  # Always add, never overwrite
        index=False
    )
    print(f"Loaded {len(snapshot_df)} price snapshots")


# -------------------------------------------------------
# STEP 6: Run everything in order
# -------------------------------------------------------
def load_to_database(filepath="clean_books.csv"):
    df = pd.read_csv(filepath)
    print(f"Read {len(df)} records from {filepath}")

    engine = create_engine(CONNECTION_STRING)

    create_tables(engine)
    load_categories(df, engine)
    load_products(df, engine)
    load_price_snapshots(df, engine)

    print("\nDatabase loading complete!")


if __name__ == "__main__":
    load_to_database()
