import json
import os
import re
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import sqlglot
from sqlglot.errors import ParseError


ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
DATABASE = ROOT / "sales.db"
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

PRACTICE_TASKS = {
    "customers_by_country": {
        "title": "Customers by country",
        "goal": "Show how many customers signed up in each country.",
        "starter": """SELECT
  country,
  COUNT(*) AS customers
FROM customers
GROUP BY country
ORDER BY customers DESC;""",
        "expected_sql": """SELECT
  country,
  COUNT(*) AS customers
FROM customers
GROUP BY country
ORDER BY customers DESC;""",
        "required": ["group by", "count(", "order by"],
        "tables": ["customers"],
        "hints": {
            "group by": "Use GROUP BY country so every country becomes one row.",
            "count(": "Use COUNT(*) to count customer rows.",
            "order by": "Use ORDER BY customers DESC to show the biggest countries first.",
        },
    },
    "orders_by_status": {
        "title": "Orders by status",
        "goal": "Show how many orders exist for each order status.",
        "starter": """SELECT
  status,
  COUNT(*) AS orders
FROM orders
GROUP BY status
ORDER BY orders DESC;""",
        "expected_sql": """SELECT
  status,
  COUNT(*) AS orders
FROM orders
GROUP BY status
ORDER BY orders DESC;""",
        "required": ["group by", "count(", "order by"],
        "tables": ["orders"],
        "hints": {
            "group by": "Use GROUP BY status to calculate one row per status.",
            "count(": "Use COUNT(*) to count order rows.",
            "order by": "Use ORDER BY orders DESC to put the largest statuses first.",
        },
    },
    "orders_by_channel": {
        "title": "Orders by channel",
        "goal": "Show how many orders came from each sales channel.",
        "starter": """SELECT
  channel,
  COUNT(*) AS orders
FROM orders
GROUP BY channel
ORDER BY orders DESC;""",
        "expected_sql": """SELECT
  channel,
  COUNT(*) AS orders
FROM orders
GROUP BY channel
ORDER BY orders DESC;""",
        "required": ["group by", "count(", "order by"],
        "tables": ["orders"],
        "hints": {
            "group by": "Use GROUP BY channel so every channel becomes one row.",
            "count(": "Use COUNT(*) to count order rows.",
            "order by": "Use ORDER BY orders DESC to show the biggest channels first.",
        },
    },
    "product_count_by_category": {
        "title": "Product count by category",
        "goal": "Show how many products exist in each product category.",
        "starter": """SELECT
  category,
  COUNT(*) AS products
FROM products
GROUP BY category
ORDER BY products DESC;""",
        "expected_sql": """SELECT
  category,
  COUNT(*) AS products
FROM products
GROUP BY category
ORDER BY products DESC;""",
        "required": ["group by", "count(", "order by"],
        "tables": ["products"],
        "hints": {
            "group by": "Use GROUP BY category so every product category becomes one row.",
            "count(": "Use COUNT(*) to count product rows.",
            "order by": "Use ORDER BY products DESC to show the biggest categories first.",
        },
    },
    "payments_by_method": {
        "title": "Payments by method",
        "goal": "Show how many payments were made by each payment method.",
        "starter": """SELECT
  payment_method,
  COUNT(*) AS payments
FROM payments
GROUP BY payment_method
ORDER BY payments DESC;""",
        "expected_sql": """SELECT
  payment_method,
  COUNT(*) AS payments
FROM payments
GROUP BY payment_method
ORDER BY payments DESC;""",
        "required": ["group by", "count(", "order by"],
        "tables": ["payments"],
        "hints": {
            "group by": "Use GROUP BY payment_method so every payment method becomes one row.",
            "count(": "Use COUNT(*) to count payment rows.",
            "order by": "Use ORDER BY payments DESC to show the biggest payment methods first.",
        },
    },
    "revenue_by_country": {
        "title": "Revenue by country",
        "goal": "Show revenue and order count for paid orders by customer country.",
        "starter": """SELECT
  c.country,
  COUNT(DISTINCT o.order_id) AS orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.country
ORDER BY revenue DESC;""",
        "expected_sql": """SELECT
  c.country,
  COUNT(DISTINCT o.order_id) AS orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.country
ORDER BY revenue DESC;""",
        "required": ["join", "group by", "sum(", "count(", "where"],
        "tables": ["customers", "orders", "payments"],
        "hints": {
            "join": "This task needs JOIN because country is in customers, order status is in orders, and money is in payments.",
            "group by": "You need GROUP BY c.country because the result should have one row per country.",
            "sum(": "Revenue usually means SUM(amount), not COUNT(amount).",
            "count(": "The task also asks for order count, so use COUNT().",
            "where": "Use WHERE o.status = 'paid' so unpaid orders do not enter revenue.",
        },
    },
    "products_by_category": {
        "title": "Products by category",
        "goal": "For each product category, show product count and average price.",
        "starter": """SELECT
  category,
  COUNT(*) AS products,
  ROUND(AVG(price), 2) AS average_price
FROM products
GROUP BY category
ORDER BY average_price DESC;""",
        "expected_sql": """SELECT
  category,
  COUNT(*) AS products,
  ROUND(AVG(price), 2) AS average_price
FROM products
GROUP BY category
ORDER BY average_price DESC;""",
        "required": ["group by", "count(", "avg("],
        "tables": ["products"],
        "hints": {
            "group by": "You need GROUP BY category to calculate numbers separately for each category.",
            "count(": "Use COUNT(*) to count how many product rows are inside each category.",
            "avg(": "Use AVG(price) to calculate the average price.",
        },
    },
    "monthly_orders": {
        "title": "Orders by month",
        "goal": "Show how many orders were created in each month.",
        "starter": """SELECT
  strftime('%Y-%m', order_date) AS month,
  COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;""",
        "expected_sql": """SELECT
  strftime('%Y-%m', order_date) AS month,
  COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;""",
        "required": ["strftime", "group by", "count("],
        "tables": ["orders"],
        "hints": {
            "strftime": "In SQLite, strftime('%Y-%m', order_date) cuts the date down to month level.",
            "group by": "You need GROUP BY month so each month becomes one result row.",
            "count(": "Use COUNT(*) to count order rows in each month.",
        },
    },
    "top_customers": {
        "title": "Top customers",
        "goal": "Show the 10 customers with the highest paid revenue.",
        "starter": """SELECT
  c.customer_id,
  c.full_name,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.full_name
ORDER BY revenue DESC
LIMIT 10;""",
        "expected_sql": """SELECT
  c.customer_id,
  c.full_name,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.full_name
ORDER BY revenue DESC
LIMIT 10;""",
        "required": ["join", "group by", "sum(", "order by", "limit"],
        "tables": ["customers", "orders", "payments"],
        "hints": {
            "join": "You need JOIN: customer names are in customers, orders link customers to payments.",
            "group by": "Group by customer_id and full_name so each customer becomes one row.",
            "sum(": "Use SUM(p.amount) to calculate revenue per customer.",
            "order by": "Use ORDER BY revenue DESC to put the biggest customers first.",
            "limit": "Use LIMIT 10 because the task asks for the top 10 customers.",
        },
    },
    "sales_by_employee": {
        "title": "Sales by employee",
        "goal": "Show paid revenue and paid order count for each employee.",
        "starter": """SELECT
  e.employee_id,
  e.full_name,
  COUNT(DISTINCT o.order_id) AS paid_orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM employees AS e
JOIN orders AS o ON o.employee_id = e.employee_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY e.employee_id, e.full_name
ORDER BY revenue DESC;""",
        "expected_sql": """SELECT
  e.employee_id,
  e.full_name,
  COUNT(DISTINCT o.order_id) AS paid_orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM employees AS e
JOIN orders AS o ON o.employee_id = e.employee_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY e.employee_id, e.full_name
ORDER BY revenue DESC;""",
        "required": ["join", "group by", "sum(", "count(", "where"],
        "tables": ["employees", "orders", "payments"],
        "hints": {
            "join": "You need JOIN: employee names are in employees, order links are in orders, and money is in payments.",
            "group by": "Group by employee_id and full_name so each employee becomes one row.",
            "sum(": "Use SUM(p.amount) to calculate paid revenue.",
            "count(": "Use COUNT(DISTINCT o.order_id) to count paid orders.",
            "where": "Use WHERE o.status = 'paid' so cancelled/shipped unpaid orders do not count as paid revenue.",
        },
    },
    "refunds_by_reason": {
        "title": "Refunds by reason",
        "goal": "Show refund count and total refund amount for each refund reason.",
        "starter": """SELECT
  reason,
  COUNT(*) AS refunds,
  ROUND(SUM(amount), 2) AS refund_amount
FROM refunds
GROUP BY reason
ORDER BY refund_amount DESC;""",
        "expected_sql": """SELECT
  reason,
  COUNT(*) AS refunds,
  ROUND(SUM(amount), 2) AS refund_amount
FROM refunds
GROUP BY reason
ORDER BY refund_amount DESC;""",
        "required": ["group by", "count(", "sum(", "order by"],
        "tables": ["refunds"],
        "hints": {
            "group by": "Use GROUP BY reason so every refund reason becomes one row.",
            "count(": "Use COUNT(*) to count refund rows.",
            "sum(": "Use SUM(amount) to calculate total refunded money.",
            "order by": "Use ORDER BY refund_amount DESC to show the largest refund reasons first.",
        },
    },
}


def database_check(sql):
    """Ask SQLite to validate tables, columns and build a query plan."""
    connection = sqlite3.connect(DATABASE)
    try:
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
        return [row[3] for row in rows]
    finally:
        connection.close()


def run_query(sql):
    """Execute a validated SELECT in a read-only connection."""
    connection = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only = ON")
        cursor = connection.execute(sql)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchmany(101)
        truncated = len(rows) > 100
        return columns, rows[:100], truncated
    finally:
        connection.close()


def offset_from_line_column(text, line, column):
    lines = text.splitlines(keepends=True)
    offset = 0
    for index in range(max(line - 1, 0)):
        if index >= len(lines):
            return len(text)
        offset += len(lines[index])
    return min(offset + max(column - 1, 0), len(text))


def error_highlight(sql, line, column):
    """Build a human-friendly highlight range around a parser error."""
    if not isinstance(line, int) or not isinstance(column, int):
        return None

    offset = offset_from_line_column(sql, line, column)
    if not sql:
        return {"line": line, "column": column, "start": 0, "end": 0}

    offset = min(offset, len(sql) - 1)
    while offset > 0 and sql[offset].isspace():
        offset -= 1

    start = offset
    end = offset + 1
    while start > 0 and (sql[start - 1].isalnum() or sql[start - 1] == "_"):
        start -= 1
    while end < len(sql) and (sql[end].isalnum() or sql[end] == "_"):
        end += 1

    current_word = sql[start:end].lower()
    if current_word == "as":
        previous_end = start
        while previous_end > 0 and sql[previous_end - 1].isspace():
            previous_end -= 1
        previous_start = previous_end
        while previous_start > 0 and (sql[previous_start - 1].isalnum() or sql[previous_start - 1] == "_"):
            previous_start -= 1
        if previous_start < previous_end:
            start = previous_start

    return {"line": line, "column": column, "start": start, "end": end}


def database_schema():
    """Return simple table/column metadata for the UI."""
    connection = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
    try:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """).fetchall()

        schema = []
        for (table_name,) in tables:
            columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
            row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            schema.append({
                "name": table_name,
                "rows": row_count,
                "columns": [
                    {
                        "name": column[1],
                        "type": column[2],
                        "primary_key": bool(column[5]),
                    }
                    for column in columns
                ],
            })
        return schema
    finally:
        connection.close()


def compact_schema():
    """Small schema representation for the AI prompt."""
    return [
        {
            "table": table["name"],
            "columns": [column["name"] for column in table["columns"]],
        }
        for table in database_schema()
    ]


def ai_sql_help(sql, task_id=None):
    """Ask OpenAI for a short SQL tutoring response.

    The model never executes SQL. We run local validation first and send only
    the query, schema, validation messages and a tiny result preview.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "ok": False,
            "message": "AI is not configured. Set OPENAI_API_KEY before starting the app.",
        }

    try:
        from openai import OpenAI
    except ImportError:
        return {
            "ok": False,
            "message": "The OpenAI Python package is missing. Run: venv/bin/pip install -r requirements.txt",
        }

    analysis = analyze_sql(sql, task_id)
    preview = None
    if analysis.get("result"):
        preview = {
            "columns": analysis["result"]["columns"],
            "rows": analysis["result"]["rows"][:8],
            "shown_rows": min(analysis["result"]["shown_rows"], 8),
            "truncated": analysis["result"]["truncated"],
        }

    payload = {
        "sql": sql,
        "task": PRACTICE_TASKS.get(task_id, {}),
        "schema": compact_schema(),
        "validation": {
            "ok": analysis.get("ok"),
            "messages": analysis.get("messages", []),
            "plan": analysis.get("plan", []),
            "practice": analysis.get("practice"),
        },
        "result_preview": preview,
    }

    instructions = """
You are the built-in AI tutor for a beginner SQL Helper portfolio project.
Help the user learn SQL; do not write huge answers.
Rules:
- Reply in simple English.
- Be concise: 3 to 6 bullets maximum.
- Explain the main mistake or the main result.
- If SQL is wrong, give a small corrected snippet, not a full essay.
- Mention JOIN/COUNT/DISTINCT risks when relevant.
- Never suggest INSERT, UPDATE, DELETE, DROP, ALTER, or destructive SQL.
- Do not claim you executed SQL; local validation already did that.
""".strip()

    try:
        client = OpenAI()
        response = client.responses.create(
            model=AI_MODEL,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
            max_output_tokens=500,
        )
        return {"ok": True, "message": response.output_text}
    except Exception as error:
        return {
            "ok": False,
            "message": f"AI request failed: {error}",
        }


def practice_feedback(sql, task_id, result):
    task = PRACTICE_TASKS.get(task_id)
    if not task:
        return None

    normalized = re.sub(r"\s+", " ", sql.strip()).lower()
    messages = []

    if not result.get("ok"):
        text = "First make the query valid. Read the error above, then fix one thing at a time."
        error_text = " ".join(message.get("text", "") for message in result.get("messages", []))
        if "no such column" in error_text:
            text = "SQLite says a column name is wrong. Check the schema/table names and aliases."
        if "no such table" in error_text:
            text = "SQLite says a table name is wrong. Check which tables exist in the sales database."
        if "syntax" in error_text.lower():
            text = "This is a syntax problem: check commas, parentheses, SELECT/FROM order, and quotes."

        return {
            "ok": False,
            "title": task["title"],
            "messages": [text],
        }

    for table in task["tables"]:
        if table not in normalized:
            messages.append(f"Try using the {table} table.")

    for item in task["required"]:
        if item not in normalized:
            messages.append(task["hints"][item])

    expected_columns, expected_rows, _ = run_query(task["expected_sql"])
    actual = result.get("result", {})
    actual_rows = [list(row) for row in actual.get("rows", [])]
    expected_rows = [list(row) for row in expected_rows]

    if actual.get("columns") == expected_columns and actual_rows == expected_rows:
        return {
            "ok": True,
            "title": task["title"],
            "messages": ["Nice. Your result matches the practice task."],
        }

    if not messages:
        messages.append("The SQL is valid, but the result is different from the task. Check filters, grouping, ordering and selected columns.")

    return {
        "ok": False,
        "title": task["title"],
        "messages": messages[:4],
    }


def analyze_sql(sql, task_id=None):
    messages = []
    normalized = re.sub(r"\s+", " ", sql.strip()).lower()

    if not normalized:
        result = {
            "ok": False,
            "formatted_sql": "",
            "messages": [{
                "level": "error",
                "title": "The query is empty",
                "text": "Paste a SELECT query into the editor.",
            }],
        }
        result["practice"] = practice_feedback(sql, task_id, result)
        return result

    # Step 1: the parser checks SQLite grammar.
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
        formatted_sql = parsed.sql(dialect="sqlite", pretty=True)
    except ParseError as error:
        item = error.errors[0] if error.errors else {}
        line = item.get("line", "?")
        column = item.get("col", "?")
        description = item.get("description", str(error))
        if re.search(r"count\s*\(\s*\*\s*\)\s+\w+\s+as\s+\w+", normalized):
            description = "Alias syntax is wrong. Use COUNT(*) AS count, not COUNT(*) products AS count."
        highlight = error_highlight(sql, line, column)
        result = {
            "ok": False,
            "formatted_sql": sql.strip(),
            "messages": [{
                "level": "error",
                "title": f"Syntax error at line {line}, column {column}",
                "text": description,
                "highlight": highlight,
            }],
        }
        result["practice"] = practice_feedback(sql, task_id, result)
        return result

    # Keep the first version safe: only SELECT and WITH are allowed.
    if not re.match(r"^(select|with)\b", normalized):
        result = {
            "ok": False,
            "formatted_sql": formatted_sql,
            "messages": [{
                "level": "error",
                "title": "Only SELECT queries are allowed",
                "text": "INSERT, UPDATE, DELETE and schema changes are disabled.",
            }],
        }
        result["practice"] = practice_feedback(sql, task_id, result)
        return result

    # Step 2: SQLite checks real table and column names.
    try:
        plan = database_check(sql)
        messages.append({
            "level": "success",
            "title": "The query is valid",
            "text": "The parser and the sales database both accepted it.",
        })
    except sqlite3.Error as error:
        result = {
            "ok": False,
            "formatted_sql": formatted_sql,
            "messages": [{
                "level": "error",
                "title": "Database validation failed",
                "text": str(error),
            }],
        }
        result["practice"] = practice_feedback(sql, task_id, result)
        return result

    # Step 3: our own small, readable rules.
    if re.search(r"\bselect\s+\*", normalized):
        messages.append({
            "level": "warning",
            "title": "Avoid SELECT *",
            "text": "List only the columns you need.",
        })

    if " distinct " in f" {normalized} ":
        messages.append({
            "level": "info",
            "title": "Check whether DISTINCT is necessary",
            "text": "DISTINCT can hide a bad JOIN and adds extra work.",
        })

    if " where " not in f" {normalized} ":
        messages.append({
            "level": "info",
            "title": "There is no WHERE clause",
            "text": "That may be correct, but the query can read the entire table.",
        })

    for detail in plan:
        if detail.startswith("SCAN ") and "USING" not in detail:
            messages.append({
                "level": "info",
                "title": "Full table scan",
                "text": detail,
            })
        if "USE TEMP B-TREE" in detail:
            messages.append({
                "level": "info",
                "title": "Temporary sorting structure",
                "text": detail,
            })

    # Step 4: execute the safe SELECT and return a small preview.
    columns, rows, truncated = run_query(sql)

    result = {
        "ok": True,
        "formatted_sql": formatted_sql,
        "messages": messages,
        "plan": plan,
        "result": {
            "columns": columns,
            "rows": rows,
            "shown_rows": len(rows),
            "truncated": truncated,
        },
    }
    result["practice"] = practice_feedback(sql, task_id, result)
    return result


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def send_json(self, result):
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/schema":
            self.send_json({"tables": database_schema()})
            return

        super().do_GET()

    def do_POST(self):
        if self.path not in {"/api/check", "/api/ai-help"}:
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            sql = str(payload.get("sql", ""))
            task_id = str(payload.get("task_id", "")) or None
            if self.path == "/api/check":
                result = analyze_sql(sql, task_id)
            else:
                result = ai_sql_help(sql, task_id)
            self.send_json(result)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON")


if __name__ == "__main__":
    if not DATABASE.exists():
        raise SystemExit("sales.db is missing. Run: venv/bin/python setup_db.py")

    address = ("127.0.0.1", 8000)
    print("SQL Helper is running at http://127.0.0.1:8000")
    ThreadingHTTPServer(address, Handler).serve_forever()
