id: 
  description: "Unique identifier for the customer"
  tests:
    - unique
    - not_null
name: 
  description: "Name of the customer"
  tests:
    - not_null
email: 
  description: "Email address of the customer"
  tests:
    - unique
    - not_null
phone_number: 
  description: "Phone number of the customer"
dob: 
  description: "Date of birth of the customer"