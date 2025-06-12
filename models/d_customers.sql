In 'models/customers.sql', the updated SELECT statement with the new column 'age' would look like this:

```sql
select
  id,
  name,
  email,
  phone_number,
  dob,
  age
from
  customers
```

In 'models/schema/customers.yml', the updated content with 'age' added to the list of columns would be:

```yaml
version: 2

models:
  - name: customers
    description: "A table containing customer information."
    columns:
      - name: id
        description: "The unique identifier for each customer."
        data_type: "integer"
      - name: name
        description: "The name of the customer."
        data_type: "string"
      - name: email
        description: "The email address of the customer."
        data_type: "string"
      - name: phone_number
        description: "The phone number of the customer."
        data_type: "string"
      - name: dob
        description: "The date of birth of the customer."
        data_type: "date"
      - name: age
        description: "The age of the customer calculated from the date of birth."
        data_type: "integer"
```

This includes the new 'age' column in both the SQL SELECT statement and the YAML schema definition.