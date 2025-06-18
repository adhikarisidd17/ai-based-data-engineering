select
    id,
    name,
    email,
    phone_number,
    dob,
    loyalty
from
    customers

-- Updated schema for customers model
version: 2

models:
  - name: customers
    description: "Customer data"
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
      - name: loyalty
        description: "Loyalty status of the customer"