# Simple ETL Pipeline

This is a small ETL project in Python. It reads messy sales files, cleans them, and saves them in a database.

## What it does

1. **Extract**: reads one orders CSV file for each day.
2. **Transform**: cleans the data.
   - fixes spaces and capital letters in `status`
   - removes duplicate rows
   - finds bad rows (missing customer, quantity below 1, wrong status)
   - bad rows are saved in `data/rejected/` with a reason, so nothing is lost silently
   - adds a `total` column (quantity x price)
3. **Load**: saves the clean data in a SQLite database (`data/warehouse.db`).
4. **Check**: makes sure the data is correct after loading. The program stops if a check fails.
5. **Report**: prints daily sales and revenue by city.

## Tables

- `fact_orders`: one row for each order
- `dim_customer`: customer name and city
- `dim_product`: product name and category

(This is a small star schema. Facts are the orders, and dimensions describe them.)

## How to run

```
pip install -r requirements.txt
python make_data.py     # makes fake raw data
python etl.py           # runs the pipeline
```

## Files

- `make_data.py`: makes fake data with some dirty rows on purpose
- `etl.py`: the pipeline
- `requirements.txt`: needs pandas only (sqlite3 comes with Python)

## Things I learned

- You can run the same day twice and get no duplicates. The code deletes that day's rows before loading them again.
- Bad rows should be saved and not just deleted, so you can look at them later.
- Checks after loading help to catch mistakes early.

## Results (3 days, 205 rows per day)

- 2 duplicates removed per day
- 3 bad rows rejected per day
- 200 clean rows loaded per day
- all checks passed

## What I can add later

- Move to a cloud database (like BigQuery or Snowflake)
- Run it every day with Airflow
- Keep history when a customer changes city (SCD Type 2)
- Add Kafka for real-time data
