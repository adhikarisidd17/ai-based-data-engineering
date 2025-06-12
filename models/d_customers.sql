select
    id,
    name,
    email,
    phone_number,
    dob,
    EXTRACT(year from CURRENT_DATE) - EXTRACT(year from dob) as age
from
    customers;
