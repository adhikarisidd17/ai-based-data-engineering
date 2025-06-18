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
    description: "Customer data"
    columns:
      - name: id
        description: "Unique identifier for the customer"
        data_type: "integer"
      - name: name
        description: "Name of the customer"
        data_type: "string"
      - name: email
        description: "Email address of the customer"
        data_type: "string"
      - name: phone_number
        description: "Phone number of the customer"
        data_type: "string"
      - name: dob
        description: "Date of birth of the customer"
        data_type: "date"
      - name: created_at
        description: "Timestamp when the customer was created"
        data_type: "timestamp"