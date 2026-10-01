# SQL Helper — AI-Assisted SQL Practice Tool

SQL Helper is a beginner-friendly web application for practicing, validating, explaining, and safely running SQL queries against a local sample database.

The project was built as a portfolio-ready learning tool for data analytics and applied AI workflows. It is intentionally simple, but it demonstrates several important engineering ideas: SQL parsing, safe query execution, backend/frontend communication, synthetic data generation, result previews, practice tasks, and optional AI-powered query explanations.

## Project goal

The main idea behind SQL Helper is not to replace real database tools or write SQL automatically for the user. Instead, the app is designed as a training assistant for people learning SQL.

It helps the user:

- write SQL manually;
- check whether the query is syntactically valid;
- understand common beginner mistakes;
- run safe read-only queries;
- see real query results immediately;
- practice realistic analytics tasks on a local sales dataset;
- optionally ask an AI tutor to explain errors, results, and possible improvements.

## Main features

- SQL syntax validation using SQLGlot
- Safe local execution against SQLite
- Only `SELECT` and `WITH` queries are allowed
- Destructive SQL commands are blocked
- Query result preview directly in the browser
- Formatted SQL output for easier reading
- Error messages with highlighted error location
- Database schema viewer with table names, columns, and row counts
- Practice tasks for beginner and lower-intermediate SQL
- Trainer hints for topics like `COUNT`, `SUM`, `AVG`, `GROUP BY`, `JOIN`, and filtering
- Optional OpenAI-powered AI tutor through a backend API endpoint
- API key is handled through environment variables and is never exposed to the browser

## Tech stack

- Python
- SQLite
- SQLGlot
- OpenAI Python SDK
- HTML
- CSS
- JavaScript

## How it works

The application has a simple backend and frontend structure.

The frontend provides the SQL editor, buttons, schema view, validation messages, formatted SQL, AI assistant panel, and query results table.

The backend receives SQL from the browser, validates it, checks that it is safe, reads the SQLite query plan, executes valid read-only queries, and returns a limited result preview.

The AI assistant is optional. If an `OPENAI_API_KEY` is configured, the backend can send the SQL query, schema information, validation messages, query plan, and a small result preview to the OpenAI API. The browser never receives the API key.

## Safety design

This project is built for learning, so query safety is a core part of the design.

- Only `SELECT` and `WITH` statements are allowed.
- Commands like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and schema changes are blocked.
- SQLite is opened in read-only/query-only mode during execution.
- Query results are limited to keep the app lightweight.
- The generated database is synthetic and contains no real user or company data.
- Real API keys should never be committed to GitHub.
- `.env`, local databases, virtual environments, caches, and compiled files are ignored by Git.

## AI integration

The project includes an optional AI explanation feature.

When enabled, the AI tutor can help explain:

- why a query is invalid;
- what the SQL query is trying to do;
- what the query result means;
- how to fix common SQL mistakes;
- how to improve query readability;
- how joins, grouping, and aggregate functions affect the final result.

The app still works without AI. If no API key is configured, the SQL checker, parser, trainer tasks, schema viewer, and result preview continue to work normally.

## Sample database

`setup_db.py` creates a local synthetic SQLite database called `sales.db`.

The database contains 7 tables:

- `customers` — customer names, emails, countries, and signup dates
- `products` — product names, categories, prices, and costs
- `employees` — employee names, departments, and hire dates
- `orders` — customer orders with dates, statuses, channels, and assigned employees
- `order_items` — products inside each order, including quantity and unit price
- `payments` — payment method, payment date, and paid amount for orders
- `refunds` — refund date, reason, and refunded amount

The tables are connected in a realistic sales-style structure:

- `orders.customer_id` connects to `customers.customer_id`
- `orders.employee_id` connects to `employees.employee_id`
- `order_items.order_id` connects to `orders.order_id`
- `order_items.product_id` connects to `products.product_id`
- `payments.order_id` connects to `orders.order_id`
- `refunds.order_id` connects to `orders.order_id`

This structure makes it possible to practice common analytics questions such as revenue by country, product counts by category, average order value, refund totals, sales by channel, and joins between customers, orders, payments, and products.

## Improvements and fixes included

During development, several practical improvements were added:

- Added a larger synthetic sales database instead of a tiny one-table example.
- Expanded the schema to 7 connected tables for more realistic SQL practice.
- Added browser-based query result previews.
- Added validation before query execution.
- Added protection against destructive SQL statements.
- Added formatted SQL output.
- Added beginner practice tasks.
- Added rule-based trainer hints.
- Added clearer explanations for common mistakes like incorrect alias syntax.
- Added error-location highlighting for invalid SQL.
- Added an optional AI assistant button.
- Added a backend AI endpoint that keeps the API key away from the frontend.
- Added `.gitignore` to prevent unsafe or unnecessary files from being uploaded.
- Removed local-only generated files from the GitHub-safe version.

## Project structure

```text
sql-helper/
├── app.py
├── setup_db.py
├── requirements.txt
├── static/
│   ├── index.html
│   ├── checker.html
│   ├── connection.html
│   ├── app.js
│   └── style.css
├── .env.example
├── .gitignore
└── README.md
```

## How to run

Create a virtual environment:

```bash
python3 -m venv venv
```

Install dependencies:

```bash
venv/bin/pip install -r requirements.txt
```

Generate the local sample database:

```bash
venv/bin/python setup_db.py
```

Start the application:

```bash
venv/bin/python app.py
```

Open the app in the browser:

```text
http://127.0.0.1:8000
```

## Optional AI setup

The AI feature is optional.

To enable it, set the environment variables before starting the app:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4.1-mini"
venv/bin/python app.py
```

Important: do not commit a real API key. Use `.env.example` only as a template.

## Files intentionally not included in Git

The GitHub-safe version should not include:

- `venv/`
- `.env`
- `sales.db`
- `__pycache__/`
- `*.pyc`
- `.DS_Store`
- logs or local temporary files

The database is generated locally with `setup_db.py`, so the repository stays clean and safe to share.

## Portfolio summary

Built a Python-based SQL helper for practicing, validating, and troubleshooting SQL queries. The project uses a synthetic SQLite sales database, safe read-only query execution, SQL parsing with SQLGlot, practice tasks, result previews, error-location highlighting, and optional OpenAI API integration for AI-powered query explanations.
