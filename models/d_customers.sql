select
  id,
  name,
  email,
  phone_number,
  dob,
  login
from
  customers

columns:
  - name: id
    description: "The unique identifier for the customer."
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
  - name: login
    description: "The login identifier for the customer."
    data_type: "string"