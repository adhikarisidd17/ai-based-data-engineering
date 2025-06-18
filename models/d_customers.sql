version: 2

models:
  - name: customer
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
      - name: average_sales
        description: "Average sales calculated as sale_vat_amount divided by number_of_items"