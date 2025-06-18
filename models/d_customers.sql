select
  id,
  name,
  email,
  phone_number,
  dob,
  CASE 
    WHEN purchase_count > 10 THEN 'Gold'
    WHEN purchase_count > 5 THEN 'Silver'
    ELSE 'Bronze'
  END AS loyalty
from
  customers

---

version: 2

models:
  - name: customer
    description: "Customer information"
    columns:
      - name: id
        description: "Unique identifier for the customer"
        data_type: integer
      - name: name
        description: "Name of the customer"
        data_type: string
      - name: email
        description: "Email address of the customer"
        data_type: string
      - name: phone_number
        description: "Phone number of the customer"
        data_type: string
      - name: dob
        description: "Date of birth of the customer"
        data_type: date
      - name: loyalty
        description: "Loyalty tier of the customer based on purchase count"
        data_type: string