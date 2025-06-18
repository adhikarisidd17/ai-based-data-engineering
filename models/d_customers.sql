select
    id,
    name,
    email,
    phone_number,
    dob,
    case
        when purchase_count > 10 then 'Gold'
        when purchase_count > 5 then 'Silver'
        else 'Bronze'
    end as loyalty
from
    customers
