To add a calculated column 'age' by subtracting the 'birthdate' (assuming 'dob' is the birthdate column) from the current date in the 'customer.sql' model, and to ensure that the 'age' column is included in the select statement in the 'stg_customer.sql' model, here are the updated contents for both files:

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

Make sure to replace `stg_customers` with the actual staging table name if it differs.