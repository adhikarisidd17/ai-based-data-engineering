```sql
select 
    name as customer_name,
    email as customer_email,
    revenue as revenue,
    years,
    phone as customer_phone,
    address as customer_address,
    city as customer_city,
    state as customer_state,
    zip_code as customer_zip_code,
    country as customer_country,
    revenue / nullif(count(distinct years), 0) as customer_lifetime_value
from {{ ref('stg_customers') }}
where is_active = true
group by 
    name, 
    email, 
    revenue, 
    years, 
    phone, 
    address, 
    city, 
    state, 
    zip_code, 
    country
``` 

In this updated SQL, I added the `customer_lifetime_value` column, which calculates the revenue divided by the count of distinct years for each customer. The `nullif` function is used to avoid division by zero. The `group by` clause ensures that the grain of the table remains unchanged.