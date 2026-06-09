# Grafana Setup Guide - PostgreSQL Direct Queries

This guide walks through setting up Grafana to query PostgreSQL directly without auto-generated dashboards.

---

## 🚀 Quick Start

### 1. Start the Stack
```bash
docker-compose up --build
```

Wait for all services to be healthy:
```
✅ postgres: running on port 5432
✅ grafana: running on port 3000
✅ pipeline: completed data sync
```

---

### 2. Access Grafana
- **URL:** http://localhost:3000
- **Username:** admin
- **Password:** admin

---

## 📊 Add PostgreSQL Data Source

### Step 1: Go to Data Sources
1. Click gear icon ⚙️ (Settings) → Data Sources
2. Click "Add data source"

### Step 2: Select PostgreSQL
- Search for "PostgreSQL"
- Click "PostgreSQL"

### Step 3: Configure Connection
```
Name: PostgreSQL - Governance
Host: postgres:5432
Database: governance
User: postgres
Password: admin
SSL Mode: disable
```

### Step 4: Test Connection
- Click "Save & Test"
- You should see: ✅ "Database connection OK"

---

## 📈 Create Your First Dashboard

### 1. Create New Dashboard
1. Go to: Dashboards → + New Dashboard
2. Click "Add Panel"

### 2. Configure Panel
1. **Data source:** Select "PostgreSQL - Governance"
2. **Query:** Paste one of the SQL queries from `GRAFANA_SQL_QUERIES.md`
3. **Panel type:** Select based on query (Time Series, Bar Chart, Table, etc.)
4. **Title:** Give it a name (e.g., "Daily Sales")

### 3. Example: Daily Sales Trend Panel

**Step 1:** Go to Query editor
```sql
SELECT 
    date as time,
    total_sales
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
ORDER BY date ASC
```

**Step 2:** Set visualization
- Panel type: **Time series**
- Title: **Daily Sales Trend**
- Y-axis: **Sales ($)**

**Step 3:** Save dashboard
- Click "Save" (top-right)
- Name: "Sales Dashboard"

---

## 🎨 Common Visualizations

### Time Series (Trending data)
**Use for:** Sales over time, Errors over time, Metrics history

**Best queries:**
- `SELECT date, total_sales FROM retail_sales`
- `SELECT collected_at, metric_value FROM sample_kpis`

---

### Bar Chart (Category comparison)
**Use for:** Sales by category, Errors by service, Revenue by product

**Best queries:**
- `SELECT category, SUM(price) FROM retail_products GROUP BY category`
- `SELECT service_name, COUNT(*) FROM sample_kpis GROUP BY service_name`

---

### Pie Chart (Proportions)
**Use for:** Sales distribution, Order status breakdown

**Best queries:**
- `SELECT status, COUNT(*) FROM retail_orders GROUP BY status`
- `SELECT category, SUM(total_sales) FROM retail_sales GROUP BY category`

---

### Table (Detailed data)
**Use for:** Order details, Product inventory, Service metrics

**Best queries:**
- `SELECT * FROM retail_orders ORDER BY order_date DESC`
- `SELECT * FROM retail_products WHERE stock_quantity < 50`

---

### Stat/Gauge (Single metric)
**Use for:** KPIs, Totals, Percentages

**Best queries:**
- `SELECT SUM(total_sales) FROM retail_sales`
- `SELECT COUNT(*) FROM retail_orders WHERE status = 'completed'`

---

## 📋 Recommended Dashboard Layout

### "Executive Summary" Dashboard
1. **Top Row:**
   - Total Sales (Last 30 days) - Stat
   - Total Orders - Stat
   - Avg Order Value - Stat
   - Conversion Rate - Gauge

2. **Second Row:**
   - Daily Sales Trend - Time Series
   - Sales by Category - Bar Chart

3. **Third Row:**
   - Order Status - Pie Chart
   - Low Stock Products - Table

4. **Fourth Row:**
   - Service Health - Table
   - Error Rates - Time Series

---

## 🔍 Query Examples for Each Table

### retail_sales Table
```sql
-- Quick Stats
SELECT 
    COUNT(DISTINCT date) as days_tracked,
    SUM(total_sales) as total_revenue,
    AVG(total_sales) as avg_daily_sales,
    COUNT(DISTINCT product_category) as categories
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
```

### retail_products Table
```sql
-- Inventory Value
SELECT 
    SUM(price * stock_quantity) as total_inventory_value,
    COUNT(*) as total_products,
    COUNT(CASE WHEN stock_quantity < 20 THEN 1 END) as low_stock_count
FROM public.retail_products
```

### retail_orders Table
```sql
-- Order Metrics
SELECT 
    COUNT(*) as total_orders,
    SUM(order_total) as total_revenue,
    AVG(order_total) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
FROM public.retail_orders
WHERE order_date >= NOW() - INTERVAL '30 days'
```

### sample_kpis Table
```sql
-- Service Health
SELECT 
    service_name,
    COUNT(*) as metric_count,
    COUNT(CASE WHEN status = 'ok' THEN 1 END) as healthy,
    COUNT(CASE WHEN status = 'critical' THEN 1 END) as critical
FROM public.sample_kpis
WHERE collected_at >= NOW() - INTERVAL '24 hours'
GROUP BY service_name
```

---

## 📊 Advanced: Dashboard Variables

Variables let you create dynamic, interactive dashboards.

### Add a Time Range Variable
1. Dashboard settings (gear icon) → Variables
2. Click "New variable"
3. Name: `timeRange`
4. Type: Custom
5. Options: `7d`, `30d`, `90d`

Then use in queries:
```sql
WHERE date >= NOW() - INTERVAL '$timeRange'
```

### Add a Category Filter
1. Create variable: `category`
2. Type: Query
3. Query: `SELECT DISTINCT product_category FROM public.retail_sales`
4. Multi-select: Yes

Then use in queries:
```sql
WHERE product_category = '$category'
```

---

## 🔐 Security Considerations

### For Production (AWS RDS):
1. Don't use default credentials
2. Create a read-only PostgreSQL user:
   ```sql
   CREATE USER grafana_reader WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE governance TO grafana_reader;
   GRANT USAGE ON SCHEMA public TO grafana_reader;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;
   ```

3. Update Grafana data source with read-only user

### In docker-compose:
- Change admin password (don't use 'admin')
- Use environment variable: `GF_SECURITY_ADMIN_PASSWORD`

---

## 🐛 Troubleshooting

### "Database connection failed"
1. Check if postgres container is running: `docker-compose ps`
2. Verify connection string: `Host: postgres:5432`
3. Check password: Should be `admin` (from .env)

### "Query returned no data"
1. Check if pipeline has finished: `docker-compose logs pipeline`
2. Verify table exists: 
   ```bash
   docker-compose exec postgres psql -U postgres -d governance -c "SELECT * FROM public.retail_sales LIMIT 1;"
   ```
3. Adjust time range in query

### "Grafana won't start"
```bash
# Check logs
docker-compose logs grafana

# Restart
docker-compose down
docker-compose up --build
```

---

## 📖 Full Query Reference

See `GRAFANA_SQL_QUERIES.md` for:
- ✅ 25+ production-ready SQL queries
- ✅ Visualization recommendations
- ✅ Performance tips
- ✅ Advanced techniques

---

## 🎓 Next Steps

1. ✅ Start with "Daily Sales Trend" and "Product Inventory" panels
2. ✅ Create your first dashboard
3. ✅ Add filters and variables for interactivity
4. ✅ Set up alerts on critical metrics
5. ✅ Export/share dashboards with team

---

**Happy visualizing! 📊**
