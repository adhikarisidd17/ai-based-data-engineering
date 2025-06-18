select
  id,
  name,
  email,
  phone_number,
  dob as date_of_birth
from
  customers

version: 2
models:
  - name: customer
    columns:
      - name: id
        tests:
          - unique
          - not_null
      - name: name
        tests:
          - not_null
      - name: email
        tests:
          - not_null
          - unique
      - name: phone_number
        tests:
          - not_null
      - name: date_of_birth
        tests:
          - not_null

select
  id,
  name,
  email,
  phone_number,
  dob as date_of_birth
from
  source_table_name