Here is the updated content for the `minbutik_checkout_frequency__f_store_sale_v5.sql` file with the new column `avg_selling_price` added:

```sql
select
    f.store_id,
    f.d_date_sale,
    f.sale_datetime_rounded,
    f.sale_hour,
    f.store_department_id,
    f.store_department_name,
    f.checkout_station_id,
    f.checkout_method_type_name_sw,
    f.checkout_method_code,
    f.checkout_method_name_sw,
    f.f_sale_receipt_key,
    f.is_receipt_store_sale,
    f.d_store_cashier_key,
    f.is_receipt_returns_only,
    sum(f.number_of_items) as number_of_items,
    sum(f.sale_amount_excl_vat) as sale_amount_excl_vat,
    sum(f.sale_vat_amount) as sale_vat_amount,
    sum(f.commission_amount_excl_vat) as commission_amount_excl_vat,
    sum(f.commission_vat_amount) as commission_vat_amount,
    sum(f.margin_amount) as margin_amount,
    case when sum(f.number_of_items) > 0 then sum(f.sale_amount_excl_vat) / sum(f.number_of_items) else 0 end as avg_selling_price
from
    {{ source('dbt_sidd','minbutik_checkout_frequency__f_store_sale_v4') }} as f
group by
    f.store_id,
    f.d_date_sale,
    f.sale_datetime_rounded,
    f.sale_hour,
    f.store_department_id,
    f.store_department_name,
    f.checkout_station_id,
    f.checkout_method_type_name_sw,
    f.checkout_method_code,
    f.checkout_method_name_sw,
    f.f_sale_receipt_key,
    f.is_receipt_store_sale,
    f.d_store_cashier_key,
    f.is_receipt_returns_only
```

And here is the updated content for the `minbutik_checkout_frequency__f_store_sale.yml` file to include the new column:

```yaml
version: 2

models:
  - name: minbutik_checkout_frequency__f_store_sale_v5
    description: "This model aggregates store sale data with additional metrics."
    columns:
      - name: store_id
        description: "The unique identifier for the store."
      - name: d_date_sale
        description: "The date of the sale."
      - name: sale_datetime_rounded
        description: "The sale datetime rounded to the nearest hour."
      - name: sale_hour
        description: "The hour of the sale."
      - name: store_department_id
        description: "The unique identifier for the store department."
      - name: store_department_name
        description: "The name of the store department."
      - name: checkout_station_id
        description: "The unique identifier for the checkout station."
      - name: checkout_method_type_name_sw
        description: "The name of the checkout method type in Swedish."
      - name: checkout_method_code
        description: "The code for the checkout method."
      - name: checkout_method_name_sw
        description: "The name of the checkout method in Swedish."
      - name: f_sale_receipt_key
        description: "The unique key for the sale receipt."
      - name: is_receipt_store_sale
        description: "Indicates if the receipt is a store sale."
      - name: d_store_cashier_key
        description: "The unique key for the store cashier."
      - name: is_receipt_returns_only
        description: "Indicates if the receipt is for returns only."
      - name: number_of_items
        description: "The total number of items sold."
      - name: sale_amount_excl_vat
        description: "The total sale amount excluding VAT."
      - name: sale_vat_amount
        description: "The total VAT amount on sales."
      - name: commission_amount_excl_vat
        description: "The total commission amount excluding VAT."
      - name: commission_vat_amount
        description: "The total VAT amount on commissions."
      - name: margin_amount
        description: "The total margin amount."
      - name: avg_selling_price
        description: "The average selling price calculated as sum(sale_amount_excl_vat) / sum(number_of_items)."
```

This includes the new column `avg_selling_price` in both the SQL model and the YAML file.