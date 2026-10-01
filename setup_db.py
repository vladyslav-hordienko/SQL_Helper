import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


DATABASE = Path(__file__).parent / "sales.db"
random.seed(42)

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS refunds;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    cost REAL NOT NULL
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT NOT NULL,
    hire_date TEXT NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    channel TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE,
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE refunds (
    refund_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    refund_date TEXT NOT NULL,
    reason TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_employee ON orders(employee_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_refunds_order ON refunds(order_id);
CREATE INDEX idx_refunds_reason ON refunds(reason);
""")

countries = ["Spain", "France", "Germany", "Italy", "Portugal", "UK"]
categories = ["Electronics", "Home", "Sports", "Books", "Beauty", "Clothing"]
channels = ["web", "mobile", "store"]
statuses = ["paid", "paid", "paid", "shipped", "cancelled"]
payment_methods = ["card", "paypal", "bank_transfer"]
departments = ["Sales", "Support", "Online", "Retail"]
refund_reasons = ["damaged", "late_delivery", "wrong_size", "changed_mind"]
start = date(2024, 1, 1)

customers = []
for customer_id in range(1, 501):
    signup = start + timedelta(days=random.randint(0, 600))
    customers.append((
        customer_id,
        f"Customer {customer_id}",
        f"customer{customer_id}@example.com",
        random.choice(countries),
        signup.isoformat(),
    ))
cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)

products = []
for product_id in range(1, 121):
    price = round(random.uniform(8, 500), 2)
    products.append((
        product_id,
        f"Product {product_id}",
        random.choice(categories),
        price,
        round(price * random.uniform(0.35, 0.75), 2),
    ))
cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

employees = []
for employee_id in range(1, 31):
    hire_date = start - timedelta(days=random.randint(30, 1200))
    employees.append((
        employee_id,
        f"Employee {employee_id}",
        random.choice(departments),
        hire_date.isoformat(),
    ))
cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", employees)

orders = []
items = []
payments = []
refunds = []
item_id = 1

for order_id in range(1, 5001):
    order_date = start + timedelta(days=random.randint(0, 730))
    status = random.choice(statuses)
    orders.append((
        order_id,
        random.randint(1, 500),
        random.randint(1, 30),
        order_date.isoformat(),
        status,
        random.choice(channels),
    ))

    total = 0
    for _ in range(random.randint(1, 4)):
        product = random.choice(products)
        quantity = random.randint(1, 5)
        total += product[3] * quantity
        items.append((item_id, order_id, product[0], quantity, product[3]))
        item_id += 1

    if status != "cancelled":
        payments.append((
            len(payments) + 1,
            order_id,
            (order_date + timedelta(days=random.randint(0, 3))).isoformat(),
            random.choice(payment_methods),
            round(total, 2),
        ))

        if random.random() < 0.08:
            refunds.append((
                len(refunds) + 1,
                order_id,
                (order_date + timedelta(days=random.randint(2, 30))).isoformat(),
                random.choice(refund_reasons),
                round(total * random.uniform(0.15, 1.0), 2),
            ))

cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders)
cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", items)
cursor.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?)", payments)
cursor.executemany("INSERT INTO refunds VALUES (?, ?, ?, ?, ?)", refunds)

connection.commit()
connection.close()

print("Created sales.db")
print(f"customers: {len(customers)}")
print(f"products: {len(products)}")
print(f"employees: {len(employees)}")
print(f"orders: {len(orders)}")
print(f"order_items: {len(items)}")
print(f"payments: {len(payments)}")
print(f"refunds: {len(refunds)}")
