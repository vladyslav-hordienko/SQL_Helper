const input = document.querySelector("#sql-input");
const checkButton = document.querySelector("#check-button");
const aiButton = document.querySelector("#ai-button");
const exampleButton = document.querySelector("#example-button");
const copyButton = document.querySelector("#copy-button");
const emptyResult = document.querySelector("#empty-result");
const result = document.querySelector("#result");
const messages = document.querySelector("#messages");
const formattedSql = document.querySelector("#formatted-sql");
const sqlPreviewLabel = document.querySelector("#sql-preview-label");
const dataResult = document.querySelector("#data-result");
const resultTable = document.querySelector("#result-table");
const rowCount = document.querySelector("#row-count");
const taskSelect = document.querySelector("#task-select");
const taskTitle = document.querySelector("#task-title");
const taskGoal = document.querySelector("#task-goal");
const starterButton = document.querySelector("#starter-button");
const practiceResult = document.querySelector("#practice-result");
const schemaGrid = document.querySelector("#schema-grid");
const aiResult = document.querySelector("#ai-result");

const tasks = {
  customers_by_country: {
    title: "Customers by country",
    goal: "Show how many customers signed up in each country.",
    starter: `SELECT
  country,
  COUNT(*) AS customers
FROM customers
GROUP BY country
ORDER BY customers DESC;`,
  },
  orders_by_status: {
    title: "Orders by status",
    goal: "Show how many orders exist for each order status.",
    starter: `SELECT
  status,
  COUNT(*) AS orders
FROM orders
GROUP BY status
ORDER BY orders DESC;`,
  },
  orders_by_channel: {
    title: "Orders by channel",
    goal: "Show how many orders came from each sales channel.",
    starter: `SELECT
  channel,
  COUNT(*) AS orders
FROM orders
GROUP BY channel
ORDER BY orders DESC;`,
  },
  product_count_by_category: {
    title: "Product count by category",
    goal: "Show how many products exist in each product category.",
    starter: `SELECT
  category,
  COUNT(*) AS products
FROM products
GROUP BY category
ORDER BY products DESC;`,
  },
  payments_by_method: {
    title: "Payments by method",
    goal: "Show how many payments were made by each payment method.",
    starter: `SELECT
  payment_method,
  COUNT(*) AS payments
FROM payments
GROUP BY payment_method
ORDER BY payments DESC;`,
  },
  revenue_by_country: {
    title: "Revenue by country",
    goal: "Show revenue and order count for paid orders by customer country.",
    starter: `SELECT
  c.country,
  COUNT(DISTINCT o.order_id) AS orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.country
ORDER BY revenue DESC;`,
  },
  products_by_category: {
    title: "Products by category",
    goal: "For each product category, show product count and average price.",
    starter: `SELECT
  category,
  COUNT(*) AS products,
  ROUND(AVG(price), 2) AS average_price
FROM products
GROUP BY category
ORDER BY average_price DESC;`,
  },
  monthly_orders: {
    title: "Orders by month",
    goal: "Show how many orders were created in each month.",
    starter: `SELECT
  strftime('%Y-%m', order_date) AS month,
  COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;`,
  },
  top_customers: {
    title: "Top customers",
    goal: "Show the 10 customers with the highest paid revenue.",
    starter: `SELECT
  c.customer_id,
  c.full_name,
  ROUND(SUM(p.amount), 2) AS revenue
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.customer_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.full_name
ORDER BY revenue DESC
LIMIT 10;`,
  },
  sales_by_employee: {
    title: "Sales by employee",
    goal: "Show paid revenue and paid order count for each employee.",
    starter: `SELECT
  e.employee_id,
  e.full_name,
  COUNT(DISTINCT o.order_id) AS paid_orders,
  ROUND(SUM(p.amount), 2) AS revenue
FROM employees AS e
JOIN orders AS o ON o.employee_id = e.employee_id
JOIN payments AS p ON p.order_id = o.order_id
WHERE o.status = 'paid'
GROUP BY e.employee_id, e.full_name
ORDER BY revenue DESC;`,
  },
  refunds_by_reason: {
    title: "Refunds by reason",
    goal: "Show refund count and total refund amount for each refund reason.",
    starter: `SELECT
  reason,
  COUNT(*) AS refunds,
  ROUND(SUM(amount), 2) AS refund_amount
FROM refunds
GROUP BY reason
ORDER BY refund_amount DESC;`,
  },
};

function selectedTask() {
  return tasks[taskSelect.value];
}

function renderTask() {
  const task = selectedTask();
  taskTitle.textContent = task.title;
  taskGoal.textContent = task.goal;
}

function loadStarter() {
  input.value = selectedTask().starter;
  input.focus();
}

function offsetFromLineColumn(text, line, column) {
  const lines = text.split("\n");
  let offset = 0;

  for (let index = 0; index < line - 1 && index < lines.length; index += 1) {
    offset += lines[index].length + 1;
  }

  return Math.min(offset + Math.max(column - 1, 0), text.length);
}

function showErrorPlace(highlight) {
  const fallbackOffset = offsetFromLineColumn(input.value, highlight.line, highlight.column);
  const start = Number.isInteger(highlight.start) ? highlight.start : fallbackOffset;
  const end = Number.isInteger(highlight.end) ? highlight.end : Math.min(fallbackOffset + 1, input.value.length);
  input.focus();
  input.setSelectionRange(start, Math.max(end, start + 1));
  input.classList.add("error-focus");
  setTimeout(() => input.classList.remove("error-focus"), 1800);
}

for (const [id, task] of Object.entries(tasks)) {
  const option = document.createElement("option");
  option.value = id;
  option.textContent = task.title;
  taskSelect.append(option);
}
renderTask();

async function loadSchema() {
  try {
    const response = await fetch("/api/schema");
    const data = await response.json();
    schemaGrid.innerHTML = "";

    for (const table of data.tables) {
      const card = document.createElement("article");
      card.className = "schema-table";

      const title = document.createElement("div");
      title.className = "schema-table-title";
      const name = document.createElement("strong");
      name.textContent = table.name;
      const rows = document.createElement("span");
      rows.textContent = `${table.rows} rows`;
      title.append(name, rows);

      const list = document.createElement("ul");
      for (const column of table.columns) {
        const item = document.createElement("li");
        item.innerHTML = `<code>${column.name}</code> <span>${column.type}${column.primary_key ? " · PK" : ""}</span>`;
        list.append(item);
      }

      card.append(title, list);
      schemaGrid.append(card);
    }
  } catch {
    schemaGrid.innerHTML = "<p class='schema-error'>Schema is not available. Start the server and refresh.</p>";
  }
}

loadSchema();

async function checkSql() {
  checkButton.disabled = true;
  checkButton.textContent = "Checking...";

  try {
    const response = await fetch("/api/check", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        sql: input.value,
        task_id: taskSelect.value,
      }),
    });
    const data = await response.json();

    messages.innerHTML = "";
    for (const message of data.messages) {
      const card = document.createElement("article");
      card.className = `message ${message.level}`;
      const title = document.createElement("strong");
      title.textContent = message.title;
      const text = document.createElement("p");
      text.textContent = message.text;
      card.append(title, text);
      if (message.highlight) {
        const button = document.createElement("button");
        button.className = "error-place-button";
        button.type = "button";
        button.textContent = "Show error place";
        button.addEventListener("click", () => showErrorPlace(message.highlight));
        card.append(button);
      }
      messages.append(card);
    }

    sqlPreviewLabel.textContent = data.ok ? "FORMATTED SQL" : "ORIGINAL SQL";
    formattedSql.textContent = data.formatted_sql || "—";
    emptyResult.hidden = true;
    result.hidden = false;
    copyButton.hidden = !data.formatted_sql;

    practiceResult.innerHTML = "";
    if (data.practice) {
      practiceResult.hidden = false;
      practiceResult.className = `practice-result ${data.practice.ok ? "success" : "hint"}`;

      const title = document.createElement("strong");
      title.textContent = data.practice.ok ? "Practice passed" : "Trainer hints";
      practiceResult.append(title);

      const list = document.createElement("ul");
      for (const item of data.practice.messages) {
        const row = document.createElement("li");
        row.textContent = item;
        list.append(row);
      }
      practiceResult.append(list);
    } else {
      practiceResult.hidden = true;
    }

    resultTable.innerHTML = "";
    if (data.ok && data.result) {
      const header = document.createElement("tr");
      for (const column of data.result.columns) {
        const cell = document.createElement("th");
        cell.textContent = column;
        header.append(cell);
      }
      resultTable.append(header);

      for (const row of data.result.rows) {
        const tableRow = document.createElement("tr");
        for (const value of row) {
          const cell = document.createElement("td");
          cell.textContent = value === null ? "NULL" : value;
          if (value === null) cell.className = "null-value";
          tableRow.append(cell);
        }
        resultTable.append(tableRow);
      }

      const suffix = data.result.truncated ? " (first 100)" : "";
      rowCount.textContent = `${data.result.shown_rows} rows shown${suffix}`;
      dataResult.hidden = false;
    } else {
      dataResult.hidden = true;
    }
  } catch {
    alert("The server is not available. Start app.py and try again.");
  } finally {
    checkButton.disabled = false;
    checkButton.innerHTML = "Check query <span>⌘ Enter</span>";
  }
}

async function askAi() {
  aiButton.disabled = true;
  aiButton.textContent = "Asking AI...";
  aiResult.hidden = false;
  aiResult.className = "ai-result";
  aiResult.textContent = "Thinking...";

  try {
    const response = await fetch("/api/ai-help", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        sql: input.value,
        task_id: taskSelect.value,
      }),
    });
    const data = await response.json();
    aiResult.className = `ai-result ${data.ok ? "success" : "warning"}`;
    aiResult.textContent = data.message || "AI returned an empty response.";
    emptyResult.hidden = true;
    result.hidden = false;
  } catch {
    aiResult.className = "ai-result warning";
    aiResult.textContent = "AI request failed. Check that the server is running.";
  } finally {
    aiButton.disabled = false;
    aiButton.textContent = "Ask AI";
  }
}

checkButton.addEventListener("click", checkSql);
aiButton.addEventListener("click", askAi);
exampleButton.addEventListener("click", () => {
  loadStarter();
});
starterButton.addEventListener("click", loadStarter);
taskSelect.addEventListener("change", renderTask);
copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(formattedSql.textContent);
  copyButton.textContent = "Copied";
  setTimeout(() => (copyButton.textContent = "Copy SQL"), 1200);
});
input.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") checkSql();
});
