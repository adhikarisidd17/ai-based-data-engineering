select
    id,
    name,
    email,
    phone_number,
    dob,
    datediff(current_date, dob) as age
from
    customers
