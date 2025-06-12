ALTER TABLE customers
ADD COLUMN age INT GENERATED ALWAYS AS (EXTRACT(year from CURRENT_DATE) - EXTRACT(year from dob)) STORED;

SELECT
    id,
    name,
    email,
    phone_number,
    dob,
    age
FROM
    customers;