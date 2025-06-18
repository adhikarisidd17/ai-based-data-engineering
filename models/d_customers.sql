select
    id,
    name,
    email,
    phone_number,
    dob,
    sale_vat_amount / number_of_items as average_sales
from
    customers
