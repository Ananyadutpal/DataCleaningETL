# Makes fake raw data (with some dirty rows) so we have something to clean.
import csv
import os
import random
from datetime import date, timedelta

random.seed(1)
os.makedirs("data/raw", exist_ok=True)

cities = ["Hyderabad", "Mumbai", "Delhi", "Chennai", "Pune"]

# customers file
with open("data/raw/customers.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["customer_id", "name", "city"])
    for i in range(1, 51):
        w.writerow([i, "Customer " + str(i), random.choice(cities)])

# products file
prices = {}
with open("data/raw/products.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["product_id", "name", "category"])
    for i in range(1, 21):
        w.writerow([i, "Product " + str(i), random.choice(["Books", "Home", "Toys", "Electronics"])])
        prices[i] = round(random.uniform(5, 300), 2)

# one orders file per day
order_id = 0
start = date(2026, 1, 1)
for day in range(3):
    d = str(start + timedelta(days=day))
    rows = []
    for _ in range(200):
        order_id += 1
        product = random.randint(1, 20)
        status = random.choice(["PLACED", "SHIPPED", "DELIVERED", "CANCELLED"])
        if random.random() < 0.1:  # messy spelling like " placed"
            status = " " + status.lower()
        rows.append([order_id, random.randint(1, 50), product,
                     random.randint(1, 5), prices[product], status, d])

    # add dirty rows on purpose
    rows.append(list(rows[0]))                              # duplicate row
    rows.append(list(rows[1]))                              # duplicate row
    rows.append([order_id + 1000, "", 3, 2, 10.0, "PLACED", d])    # missing customer
    rows.append([order_id + 1001, 5, 3, -2, 10.0, "PLACED", d])    # negative quantity
    rows.append([order_id + 1002, 5, 3, 1, 10.0, "WRONG", d])      # bad status

    with open("data/raw/orders_" + d + ".csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "product_id", "quantity", "unit_price", "status", "order_date"])
        w.writerows(rows)

print("done, files are in data/raw")
