select
    id,
    name,
    email,
    phone_number,
    dob,
    EXTRACT(year from CURRENT_DATE) - EXTRACT(year from birthdate) as age
from
    customers
