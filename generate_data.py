"""
Synthetic retail data generator.

Mimics how a real source system would hand data to a warehouse:
  - customers.csv / products.csv  -> "current state" dumps (mutate over time,
    which is exactly what dbt SNAPSHOTS are designed to historize)
  - orders / order_items / payments / marketing_spend / support_tickets
    -> append-only event data (which is what INCREMENTAL MODELS are designed
    for)

Usage:
    python generate_data.py init                # full history through today
    python generate_data.py increment            # simulate one new day

Each run writes CSVs to ./raw_data/. In 'increment' mode, customers.csv and
products.csv are OVERWRITTEN with a mutated current state (so a dbt snapshot
run afterwards captures a real change), while the event tables get a new
day's rows APPENDED.
"""

import argparse
import os
import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

OUT_DIR = "raw_data"
START_DATE = date(2023, 1, 1)

CHANNELS = ["paid_search", "paid_social", "organic", "email", "referral"]
REGIONS = ["Riyadh", "Jeddah", "Dammam", "Dubai", "Cairo", "Amman"]
TIERS = ["bronze", "silver", "gold"]
CATEGORIES = ["electronics", "home", "apparel", "beauty", "sports", "books"]
PAYMENT_METHODS = ["credit_card", "mada", "apple_pay", "cod"]
TICKET_CATEGORIES = ["delivery_delay", "wrong_item", "refund_request", "product_defect", "other"]


def _path(name):
    return os.path.join(OUT_DIR, name)


def _load_if_exists(name):
    p = _path(name)
    return pd.read_csv(p) if os.path.exists(p) else None


# ---------------------------------------------------------------------------
# INITIAL GENERATION
# ---------------------------------------------------------------------------

def gen_customers(n, as_of):
    rows = []
    for i in range(1, n + 1):
        signup = fake.date_between(start_date=START_DATE, end_date=as_of)
        # tier loosely correlated with tenure, plus noise
        tenure_days = (as_of - signup).days
        tier_weights = [0.7, 0.25, 0.05] if tenure_days < 180 else [0.4, 0.4, 0.2]
        rows.append({
            "customer_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            # ~3% missing emails, a real-world data quality wrinkle
            "email": fake.email() if random.random() > 0.03 else None,
            "signup_date": signup,
            "acquisition_channel": random.choices(CHANNELS, weights=[0.25, 0.2, 0.3, 0.15, 0.1])[0],
            "region": random.choice(REGIONS),
            "tier": random.choices(TIERS, weights=tier_weights)[0],
            "updated_at": datetime.combine(as_of, datetime.min.time()),
        })
    return pd.DataFrame(rows)


def gen_products(n, as_of):
    rows = []
    for i in range(1, n + 1):
        cost = round(random.uniform(5, 300), 2)
        margin = random.uniform(1.3, 2.5)
        rows.append({
            "product_id": i,
            "product_name": fake.catch_phrase(),
            "category": random.choice(CATEGORIES),
            "unit_cost": cost,
            "unit_price": round(cost * margin, 2),
            "is_active": random.random() > 0.05,
            "price_updated_at": datetime.combine(as_of, datetime.min.time()),
        })
    return pd.DataFrame(rows)


def _daily_order_volume(d, n_customers):
    """Growth trend + weekly seasonality + noise."""
    days_since_start = (d - START_DATE).days
    growth = 5 + days_since_start * 0.03  # slow linear growth in baseline volume
    weekday_mult = 1.3 if d.weekday() in (3, 4) else 1.0  # Thu/Fri bump (KSA weekend)
    noise = np.random.normal(1.0, 0.15)
    return max(0, int(growth * weekday_mult * noise * (n_customers / 2000)))


def gen_events(customers_df, products_df, start_date, end_date, start_ids=None):
    """Generate orders/order_items/payments/marketing_spend/support_tickets
    for [start_date, end_date] inclusive."""
    start_ids = start_ids or {}
    order_id = start_ids.get("order_id", 1)
    item_id = start_ids.get("item_id", 1)
    payment_id = start_ids.get("payment_id", 1)
    ticket_id = start_ids.get("ticket_id", 1)

    orders, items, payments, tickets, spend = [], [], [], [], []
    active_customer_ids = customers_df["customer_id"].tolist()
    active_products = products_df[products_df["is_active"]]

    d = start_date
    while d <= end_date:
        eligible_customers = customers_df[customers_df["signup_date"] <= d]["customer_id"].tolist()
        if eligible_customers:
            n_orders = _daily_order_volume(d, len(customers_df))
            for _ in range(n_orders):
                cust_id = random.choice(eligible_customers)
                status = random.choices(
                    ["completed", "cancelled", "refunded"], weights=[0.88, 0.08, 0.04]
                )[0]
                order_ts = datetime.combine(d, datetime.min.time()) + timedelta(
                    hours=random.randint(8, 23), minutes=random.randint(0, 59)
                )
                orders.append({
                    "order_id": order_id,
                    "customer_id": cust_id,
                    "order_date": order_ts,
                    "status": status,
                    "channel": random.choice(CHANNELS),
                })

                n_items = random.randint(1, 4)
                order_total = 0.0
                for _ in range(n_items):
                    prod = active_products.sample(1).iloc[0]
                    qty = random.randint(1, 3)
                    line_total = round(prod["unit_price"] * qty, 2)
                    order_total += line_total
                    items.append({
                        "order_item_id": item_id,
                        "order_id": order_id,
                        "product_id": prod["product_id"],
                        "quantity": qty,
                        "unit_price_at_order": prod["unit_price"],
                    })
                    item_id += 1

                if status != "cancelled":
                    is_late = random.random() < 0.06
                    pay_status = "failed" if status == "refunded" and random.random() < 0.3 else "paid"
                    payments.append({
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "payment_date": order_ts + timedelta(days=random.randint(2, 9) if is_late else 0),
                        "amount": round(order_total, 2),
                        "payment_method": random.choice(PAYMENT_METHODS),
                        "status": pay_status,
                        "is_late": is_late,
                    })
                    payment_id += 1

                # ~7% of orders spawn a support ticket
                if random.random() < 0.07:
                    created = order_ts + timedelta(days=random.randint(0, 5))
                    resolved = (
                        created + timedelta(days=random.randint(1, 4))
                        if random.random() > 0.15  # ~15% stay open
                        else None
                    )
                    tickets.append({
                        "ticket_id": ticket_id,
                        "customer_id": cust_id,
                        "order_id": order_id,
                        "created_at": created,
                        "resolved_at": resolved,
                        "category": random.choices(
                            TICKET_CATEGORIES, weights=[0.35, 0.2, 0.2, 0.15, 0.1]
                        )[0],
                    })
                    ticket_id += 1

                order_id += 1

        for ch in CHANNELS:
            base = {"paid_search": 400, "paid_social": 300, "organic": 0, "email": 50, "referral": 20}[ch]
            spend.append({
                "date": d,
                "channel": ch,
                "spend": round(max(0, np.random.normal(base, base * 0.2 + 1)), 2),
            })

        d += timedelta(days=1)

    next_ids = {"order_id": order_id, "item_id": item_id, "payment_id": payment_id, "ticket_id": ticket_id}
    return (
        pd.DataFrame(orders),
        pd.DataFrame(items),
        pd.DataFrame(payments),
        pd.DataFrame(tickets),
        pd.DataFrame(spend),
        next_ids,
    )


def run_init(n_customers=2000, n_products=150, end_date=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    end_date = end_date or date.today()

    customers = gen_customers(n_customers, end_date)
    products = gen_products(n_products, end_date)
    orders, items, payments, tickets, spend, next_ids = gen_events(
        customers, products, START_DATE, end_date
    )

    customers.to_csv(_path("customers.csv"), index=False)
    products.to_csv(_path("products.csv"), index=False)
    orders.to_csv(_path("orders.csv"), index=False)
    items.to_csv(_path("order_items.csv"), index=False)
    payments.to_csv(_path("payments.csv"), index=False)
    tickets.to_csv(_path("support_tickets.csv"), index=False)
    spend.to_csv(_path("marketing_spend.csv"), index=False)

    with open(_path("_next_ids.txt"), "w") as f:
        f.write(str(next_ids))

    print(f"[init] {len(customers)} customers, {len(products)} products, "
          f"{len(orders)} orders through {end_date} written to {OUT_DIR}/")


def run_increment(as_of=None, n_new_customers=15, pct_tier_change=0.03, pct_price_change=0.05):
    as_of = as_of or date.today()
    customers = _load_if_exists("customers.csv")
    products = _load_if_exists("products.csv")
    if customers is None or products is None:
        raise SystemExit("No existing raw_data/ found — run 'init' first.")

    customers["signup_date"] = pd.to_datetime(customers["signup_date"]).dt.date

    # 1. mutate a sample of existing customers' tier (simulates upgrades/downgrades)
    change_mask = np.random.rand(len(customers)) < pct_tier_change
    customers.loc[change_mask, "tier"] = [
        random.choice(TIERS) for _ in range(change_mask.sum())
    ]
    customers.loc[change_mask, "updated_at"] = str(datetime.combine(as_of, datetime.min.time()))

    # 2. add new customers signing up today
    max_id = customers["customer_id"].max()
    new_customers = gen_customers(n_new_customers, as_of)
    new_customers["customer_id"] = range(max_id + 1, max_id + 1 + n_new_customers)
    new_customers["signup_date"] = as_of
    customers = pd.concat([customers, new_customers], ignore_index=True)

    # 3. mutate a sample of product prices (simulates repricing)
    price_mask = np.random.rand(len(products)) < pct_price_change
    products.loc[price_mask, "unit_price"] = (
        products.loc[price_mask, "unit_price"] * np.random.uniform(0.9, 1.15, price_mask.sum())
    ).round(2)
    products.loc[price_mask, "price_updated_at"] = str(datetime.combine(as_of, datetime.min.time()))

    customers.to_csv(_path("customers.csv"), index=False)
    products.to_csv(_path("products.csv"), index=False)

    # 4. generate today's events only, continuing id sequences
    next_ids = {}
    ids_path = _path("_next_ids.txt")
    if os.path.exists(ids_path):
        next_ids = eval(open(ids_path).read())

    orders, items, payments, tickets, spend, next_ids = gen_events(
        customers, products, as_of, as_of, start_ids=next_ids
    )

    for name, df in [
        ("orders.csv", orders), ("order_items.csv", items),
        ("payments.csv", payments), ("support_tickets.csv", tickets),
        ("marketing_spend.csv", spend),
    ]:
        existing = _load_if_exists(name)
        combined = pd.concat([existing, df], ignore_index=True) if existing is not None else df
        combined.to_csv(_path(name), index=False)

    with open(ids_path, "w") as f:
        f.write(str(next_ids))

    print(f"[increment] as_of={as_of}: {change_mask.sum()} tier changes, "
          f"{n_new_customers} new customers, {price_mask.sum()} price changes, "
          f"{len(orders)} new orders appended.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["init", "increment"])
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--products", type=int, default=150)
    args = parser.parse_args()

    if args.mode == "init":
        run_init(n_customers=args.customers, n_products=args.products)
    else:
        run_increment()