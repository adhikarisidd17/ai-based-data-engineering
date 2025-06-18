select
    id,
    name,
    email,
    phone_number,
    dob,
    loyalty
from
    customers

with loyalty as (
    select
        id,
        case
            when purchase_count > 10 then 1
            when purchase_count > 5 then 0
            else -1
        end as loyalty
    from
        customer_purchases
)