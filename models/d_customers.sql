select
  id,
  name,
  email,
  phone_number,
  dob,
  CASE 
    WHEN purchase_count > 10 THEN 'Gold'
    WHEN purchase_count BETWEEN 5 AND 10 THEN 'Silver'
    ELSE 'Bronze'
  END AS loyalty
from
  customers

---

version: 2

models:
  - name: customer
    description: "Customer information including loyalty status."
    columns:
      - name: id
        description: "Unique identifier for the customer."
      - name: name
        description: "Name of the customer."
      - name: email
        description: "Email address of the customer."
      - name: phone_number
        description: "Phone number of the customer."
      - name: dob
        description: "Date of birth of the customer."
      - name: loyalty
        description: "Loyalty status of the customer based on purchase history."
        tests:
          - not_null
          - unique