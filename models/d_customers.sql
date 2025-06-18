select
    id,
    name,
    email,
    phone_number,
    dob,
    case
        when num_of_customers = 0 then null
        else sales / num_of_customers
    end as avg_sales
from
    customers
