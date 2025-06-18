select
  id,
  name,
  email,
  phone_number,
  dob,
  date_of_birth as date_of_birth
from
  customers

---

version: 2

models:
  - name: customers
    description: "This model contains customer information."
    columns:
      - name: id
        description: "The unique identifier for each customer."
      - name: name
        description: "The name of the customer."
      - name: email
        description: "The email address of the customer."
      - name: phone_number
        description: "The phone number of the customer."
      - name: dob
        description: "The date of birth of the customer."
      - name: date_of_birth
        description: "Calculated date of birth for the customer."