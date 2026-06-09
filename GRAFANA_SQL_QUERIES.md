# Grafana SQL Queries for Data Visualization

This guide provides SQL queries for Grafana to visualize your retail sales, products, orders, and SRE KPI data.

---

## Setup: Add PostgreSQL Data Source to Grafana

1. **Login to Grafana**
   - URL: http://localhost:3000
   - Username: admin
   - Password: admin

2. **Add PostgreSQL Data Source**
   - Go to: Settings → Data Sources → Add data source
   - Select: PostgreSQL
   - Configuration:
     ```
     Host: postgres:5432
     Database: governance
     User: postgres
     Password: admin
     SSL Mode: disable
     ```
   - Click "Save & Test"

3. **Create Dashboard**
   - Go to: Dashboards → New → New Dashboard
   - Click "Add Panel"
   - Select: PostgreSQL data source
   - Paste queries below

---

## 📊 RETAIL SALES QUERIES

### 1. Daily Sales Trend (Time Series)
**Visualization:** Graph/Time Series

```sql
SELECT 
    date as time,
    total_sales
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
ORDER BY date ASC
```

**Panel Settings:**
- Title: Daily Sales Trend
- Panel Type: Time series
- Legend: Show legend

---

### 2. Sales by Category (Bar Chart)
**Visualization:** Bar Chart

```sql
SELECT 
    product_category as category,
    SUM(total_sales) as sales,
    COUNT(*) as days,
    ROUND(AVG(total_sales), 2) as avg_daily_sales
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY product_category
ORDER BY sales DESC
```

**Panel Settings:**
- Title: Sales by Category
- Panel Type: Bar chart (horizontal)
- Legend: Show

---

### 3. Top Performing Categories (Pie Chart)
**Visualization:** Pie Chart

```sql
SELECT 
    product_category as name,
    SUM(total_sales) as value
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY product_category
ORDER BY value DESC
```

**Panel Settings:**
- Title: Sales Distribution by Category
- Panel Type: Pie chart
- Show percentages: Yes

---

### 4. Conversion Rate Trend (Gauge/Stat)
**Visualization:** Stat Panel

```sql
SELECT 
    ROUND(AVG(conversion_rate) * 100, 2) as "Avg Conversion Rate (%)"
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
```

**Panel Settings:**
- Title: Average Conversion Rate
- Panel Type: Stat
- Gauge: Yes
- Min: 0, Max: 100

---

### 5. Units Sold by Category (Time Series)
**Visualization:** Time Series

```sql
SELECT 
    date as time,
    product_category,
    unit_sold
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
ORDER BY date ASC
```

**Panel Settings:**
- Title: Units Sold Trend
- Panel Type: Time series
- Group by: product_category

---

### 6. Sales Performance Metrics (Table)
**Visualization:** Table

```sql
SELECT 
    date,
    product_category,
    total_sales,
    unit_sold,
    avg_order_value,
    customer_count,
    ROUND(conversion_rate * 100, 1) as conversion_rate_pct,
    ROUND(total_sales / NULLIF(customer_count, 0), 2) as revenue_per_customer
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
ORDER BY date DESC, total_sales DESC
```

**Panel Settings:**
- Title: Daily Sales Performance
- Panel Type: Table
- Sort: Date (descending)

---

### 7. Customer Growth (Gauge)
**Visualization:** Stat Panel

```sql
SELECT 
    SUM(customer_count) as "Total Customers"
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
```

---

### 8. Average Order Value by Category (Horizontal Bar)
**Visualization:** Bar Chart

```sql
SELECT 
    product_category,
    ROUND(AVG(avg_order_value), 2) as avg_order_value,
    MAX(avg_order_value) as max_order_value,
    MIN(avg_order_value) as min_order_value
FROM public.retail_sales
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY product_category
ORDER BY avg_order_value DESC
```

---

## 📦 INVENTORY QUERIES

### 1. Product Inventory Status (Table)
**Visualization:** Table

```sql
SELECT 
    product_id,
    product_name,
    category,
    price,
    stock_quantity,
    CASE 
        WHEN stock_quantity < 20 THEN 'Low'
        WHEN stock_quantity < 50 THEN 'Medium'
        ELSE 'High'
    END as stock_status,
    ROUND(price * stock_quantity, 2) as inventory_value
FROM public.retail_products
ORDER BY stock_quantity ASC
```

**Panel Settings:**
- Title: Product Inventory
- Panel Type: Table
- Highlight cells: Yes

---

### 2. Low Stock Alert (Stat)
**Visualization:** Stat Panel

```sql
SELECT 
    COUNT(*) as "Products Below 20 Units"
FROM public.retail_products
WHERE stock_quantity < 20
```

**Panel Settings:**
- Title: Low Stock Alert
- Thresholds: 0 (green) → 5 (yellow) → 10 (red)

---

### 3. Category Inventory Value (Pie Chart)
**Visualization:** Pie Chart

```sql
SELECT 
    category as name,
    ROUND(SUM(price * stock_quantity)::numeric, 2) as value
FROM public.retail_products
GROUP BY category
ORDER BY value DESC
```

---

### 4. Price Range by Category (Box Plot/Stat)
**Visualization:** Table

```sql
SELECT 
    category,
    COUNT(*) as product_count,
    ROUND(MIN(price), 2) as min_price,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(MAX(price), 2) as max_price,
    ROUND(SUM(stock_quantity), 0) as total_stock
FROM public.retail_products
GROUP BY category
ORDER BY avg_price DESC
```

---

## 🛒 ORDER ANALYSIS QUERIES

### 1. Daily Order Volume (Time Series)
**Visualization:** Time Series

```sql
SELECT 
    DATE(order_date) as time,
    COUNT(*) as order_count,
    ROUND(SUM(order_total), 2) as daily_revenue,
    ROUND(AVG(order_total), 2) as avg_order_value
FROM public.retail_orders
GROUP BY DATE(order_date)
ORDER BY time DESC
```

---

### 2. Order Status Distribution (Pie Chart)
**Visualization:** Pie Chart

```sql
SELECT 
    status as name,
    COUNT(*) as value
FROM public.retail_orders
GROUP BY status
```

---

### 3. Revenue by Customer (Top 10)
**Visualization:** Bar Chart

```sql
SELECT 
    customer_id,
    COUNT(*) as order_count,
    ROUND(SUM(order_total), 2) as total_spent,
    ROUND(AVG(order_total), 2) as avg_order_value
FROM public.retail_orders
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 10
```

---

### 4. Order Completion Rate (Gauge)
**Visualization:** Stat Panel

```sql
SELECT 
    ROUND(
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::numeric / COUNT(*) * 100,
        2
    ) as "Completion Rate (%)"
FROM public.retail_orders
```

---

## 🚀 SRE KPI QUERIES

### 1. Service Error Rates (Multi-Series)
**Visualization:** Time Series

```sql
SELECT 
    collected_at as time,
    service_name,
    metric_value as error_rate
FROM public.sample_kpis
WHERE metric_name = 'error_rate'
AND collected_at >= NOW() - INTERVAL '24 hours'
ORDER BY collected_at ASC
```

**Panel Settings:**
- Title: Error Rates by Service
- Group by: service_name

---

### 2. Latency Metrics (Table)
**Visualization:** Table

```sql
SELECT 
    service_name,
    metric_name,
    ROUND(metric_value, 2) as value,
    status,
    collected_at
FROM public.sample_kpis
WHERE metric_name LIKE '%latency%'
AND collected_at >= NOW() - INTERVAL '24 hours'
ORDER BY collected_at DESC
```

---

### 3. Service Health Status (Stat Panels)
**Visualization:** Multiple Stat Panels

```sql
SELECT 
    service_name,
    CASE 
        WHEN status = 'ok' THEN 'Healthy'
        WHEN status = 'warning' THEN 'Warning'
        WHEN status = 'critical' THEN 'Critical'
        ELSE 'Unknown'
    END as health_status,
    COUNT(*) as issues,
    MAX(collected_at) as last_updated
FROM public.sample_kpis
WHERE collected_at >= NOW() - INTERVAL '1 hour'
GROUP BY service_name, status
ORDER BY service_name, 
    CASE WHEN status = 'critical' THEN 1 
         WHEN status = 'warning' THEN 2 
         ELSE 3 END
```

---

### 4. Availability Percentage (Gauge)
**Visualization:** Stat Panel

```sql
SELECT 
    ROUND(AVG(metric_value), 2) as "Average Availability (%)"
FROM public.sample_kpis
WHERE metric_name = 'availability_pct'
AND collected_at >= NOW() - INTERVAL '24 hours'
```

---

### 5. Incident Count by Service (Bar Chart)
**Visualization:** Bar Chart

```sql
SELECT 
    service_name,
    SUM(metric_value) as incident_count
FROM public.sample_kpis
WHERE metric_name = 'incident_count'
AND collected_at >= NOW() - INTERVAL '24 hours'
GROUP BY service_name
ORDER BY incident_count DESC
```

---

### 6. SRE Metrics Dashboard (Table)
**Visualization:** Table

```sql
SELECT 
    service_name,
    metric_name,
    ROUND(metric_value, 2) as latest_value,
    status,
    collected_at
FROM public.sample_kpis
WHERE (service_name, collected_at) IN (
    SELECT service_name, MAX(collected_at)
    FROM public.sample_kpis
    WHERE collected_at >= NOW() - INTERVAL '1 hour'
    GROUP BY service_name
)
ORDER BY service_name, metric_name
```

---

## 📈 ADVANCED QUERIES

### 1. Daily Metrics Summary (All Tables)
**Visualization:** Table

```sql
SELECT 
    'Retail Sales' as metric_type,
    (SELECT SUM(total_sales) FROM public.retail_sales WHERE date = CURRENT_DATE) as daily_value,
    CURRENT_DATE as date
UNION ALL
SELECT 
    'Total Orders',
    COUNT(*),
    DATE(order_date)
FROM public.retail_orders
WHERE DATE(order_date) = CURRENT_DATE
GROUP BY DATE(order_date)
UNION ALL
SELECT 
    'Product Stock Value',
    ROUND(SUM(price * stock_quantity), 2),
    CURRENT_DATE
FROM public.retail_products
```

---

### 2. Data Freshness Check (Metadata)
**Visualization:** Stat Panel

```sql
SELECT 
    EXTRACT(HOUR FROM (NOW() - last_synced)) || ' hours ago' as "Last Sync"
FROM public.data_metadata
WHERE table_name = 'retail_sales'
ORDER BY last_synced DESC
LIMIT 1
```

---

### 3. Top Tables by Row Count (Table)
**Visualization:** Table

```sql
SELECT 
    table_name,
    row_count,
    last_synced,
    schema_version
FROM public.data_metadata
ORDER BY row_count DESC
```

---

## 🎨 Dashboard Panel Tips

### For Time Series:
- **Format:** Time series
- **Tooltip:** All series
- **Legend:** Show, Right side

### For Gauge/Stat:
- **Thresholds:** Set min/max values
- **Color scheme:** Green → Yellow → Red
- **Show %:** For percentages

### For Tables:
- **Sorting:** Click column headers
- **Filters:** Add regex patterns
- **Cell highlighting:** Enable for alerts

### For Pie/Donut:
- **Legend:** Show percentages
- **Tooltip:** Show value

---

## ⚡ Performance Tips

1. **Always add time range filter** to reduce data volume
2. **Use indexes** on frequently queried columns:
   ```sql
   CREATE INDEX idx_retail_sales_date ON public.retail_sales(date);
   CREATE INDEX idx_retail_orders_order_date ON public.retail_orders(order_date);
   CREATE INDEX idx_sample_kpis_service ON public.sample_kpis(service_name);
   ```

3. **Add to .env to run indexing:**
   ```bash
   # In Grafana data source, mark read-only
   ```

---

## 🔗 Custom Variables (Optional)

You can add dashboard variables for dynamic queries:

**Variable: $timeRange**
```sql
WHERE date >= NOW() - INTERVAL '$timeRange'
```

**Variable: $category**
```sql
WHERE product_category = '$category'
```

---

Start with **Daily Sales Trend** and **Product Inventory** panels for a quick overview!
