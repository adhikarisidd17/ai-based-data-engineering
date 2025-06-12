select
    id,
    name,
    email,
    phone_number,
    dob,
    DATEDIFF(CURRENT_DATE, dob) / 365 as age
from
    customers
