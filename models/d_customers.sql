Here is the updated content for the 'models/customer.sql' file with the calculated column 'age':

```sql
select
  id,
  name,
  email,
  phone_number,
  dob,
  EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM dob) as age
from
  customers
```

And here is the updated content for the 'models/staging/stg_customers.sql' file with the same calculated column 'age':

```sql
select
  id,
  name,
  email,
  phone_number,
  dob,
  EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM dob) as age
from
  customers
``` 

Make sure to replace the content of both files with the above SQL queries to include the 'age' calculation.