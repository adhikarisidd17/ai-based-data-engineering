select
    id,
    name,
    email,
    phone_number,
    dob,
    customer_lifetime_value
from
    customers

version: 2

models:
  - name: customer
    description: "Customer data model"
    columns:
      - name: id
        description: "Unique identifier for the customer"
      - name: name
        description: "Name of the customer"
      - name: email
        description: "Email address of the customer"
      - name: phone_number
        description: "Phone number of the customer"
      - name: dob
        description: "Date of birth of the customer"
      - name: customer_lifetime_value
        description: "Estimated lifetime value of the customer"