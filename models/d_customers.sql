Here are the updated contents for both the 'customer.sql' and 'stg_customer.sql' files:

**customer.sql:**
```sql
select
  id,
  name,
  email,
  phone_number,
  dob,
  date_part('year', age(dob)) as age
from
  customers
```

**stg_customer.sql:**
```sql
select
  id,
  name,
  email,
  phone_number,
  dob,
  date_part('year', age(dob)) as age
from
  stg_customers
```

Make sure to verify that `stg_customers` is the correct name for your staging table.