select
  id,
  name,
  email,
  phone_number,
  dob,
  created_at
from
  customers

version: 2

models:
  - name: customer
    description: "Customer information"
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
      - name: created_at
        description: "Timestamp when the customer was created"