# Simple ETL: raw csv files -> clean -> sqlite database -> checks -> report
import glob
import os
import sqlite3

import pandas as pd

VALID_STATUS = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED"]

os.makedirs("data/rejected", exist_ok=True)
con = sqlite3.connect("data/warehouse.db")


# ---------- EXTRACT ----------
def extract(file):
    return pd.read_csv(file)


# ---------- TRANSFORM ----------
def transform(df):
    # fix spaces and capital letters in status
    df["status"] = df["status"].str.strip().str.upper()

    # remove exact duplicate rows
    before = len(df)
    df = df.drop_duplicates().copy()
    print("  duplicates removed:", before - len(df))

    # mark bad rows with a reason
    df["reason"] = None
    df.loc[~df["status"].isin(VALID_STATUS), "reason"] = "bad status"
    df.loc[df["quantity"] <= 0, "reason"] = "bad quantity"
    df.loc[df["customer_id"].isna(), "reason"] = "missing customer"

    rejected = df[df["reason"].notna()]
    clean = df[df["reason"].isna()].drop(columns="reason").copy()

    clean["customer_id"] = clean["customer_id"].astype(int)
    clean["total"] = clean["quantity"] * clean["unit_price"]
    return clean, rejected


# ---------- LOAD ----------
def load(clean, day):
    con.execute("""CREATE TABLE IF NOT EXISTS fact_orders (
        order_id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER,
        quantity INTEGER, unit_price REAL, status TEXT, order_date TEXT, total REAL)""")
    # delete this day first so running the same day again does not make duplicates
    con.execute("DELETE FROM fact_orders WHERE order_date = ?", (day,))
    clean.to_sql("fact_orders", con, if_exists="append", index=False)
    con.commit()


def load_dimensions():
    pd.read_csv("data/raw/customers.csv").to_sql("dim_customer", con, if_exists="replace", index=False)
    pd.read_csv("data/raw/products.csv").to_sql("dim_product", con, if_exists="replace", index=False)


# ---------- CHECKS ----------
def check(day, rows_loaded):
    problems = []

    count = con.execute("SELECT COUNT(*) FROM fact_orders WHERE order_date = ?", (day,)).fetchone()[0]
    if count != rows_loaded:
        problems.append("row count does not match")

    orphans = con.execute("""SELECT COUNT(*) FROM fact_orders
                             WHERE customer_id NOT IN (SELECT customer_id FROM dim_customer)""").fetchone()[0]
    if orphans > 0:
        problems.append("orders with unknown customer: " + str(orphans))

    wrong_total = con.execute("""SELECT COUNT(*) FROM fact_orders
                                 WHERE ABS(total - quantity * unit_price) > 0.01""").fetchone()[0]
    if wrong_total > 0:
        problems.append("wrong totals: " + str(wrong_total))

    if problems:
        raise Exception("Checks failed: " + ", ".join(problems))
    print("  checks passed")


# ---------- RUN ----------
load_dimensions()

for file in sorted(glob.glob("data/raw/orders_*.csv")):
    day = os.path.basename(file).replace("orders_", "").replace(".csv", "")
    print("Day", day)

    df = extract(file)
    print("  rows read:", len(df))

    clean, rejected = transform(df)
    print("  rows rejected:", len(rejected))
    print("  rows clean:", len(clean))

    rejected.to_csv("data/rejected/rejected_" + day + ".csv", index=False)
    load(clean, day)
    check(day, len(clean))

# ---------- REPORT ----------
print("\nSales per day")
print(pd.read_sql("""SELECT order_date, COUNT(*) AS orders, ROUND(SUM(total), 2) AS revenue
                     FROM fact_orders WHERE status != 'CANCELLED'
                     GROUP BY order_date ORDER BY order_date""", con).to_string(index=False))

print("\nRevenue by city")
print(pd.read_sql("""SELECT c.city, ROUND(SUM(f.total), 2) AS revenue
                     FROM fact_orders f JOIN dim_customer c ON f.customer_id = c.customer_id
                     WHERE f.status != 'CANCELLED'
                     GROUP BY c.city ORDER BY revenue DESC""", con).to_string(index=False))

con.close()
