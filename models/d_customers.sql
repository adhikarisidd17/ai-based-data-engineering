select
    id,
    name,
    email,
    phone_number,
    dob,
    current_date - interval '1 year' * age(dob) as date_of_birth
from
    customers
