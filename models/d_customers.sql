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
current_date - date_of_birth as customer_age  -- Assuming there is a date_of_birth column in stg_customers
from {{ ref('stg_customers') }}
where is_active = true
```