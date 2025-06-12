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
    sum(f.sale_amount_excl_vat) / nullif(sum(f.number_of_items), 0) as avg_selling_price
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

---

version: 2

models:
  - name: minbutik_checkout_frequency__f_store_sale_v5
    description: "Sales data with checkout frequency"
    columns:
      - name: store_id
        description: "Unique identifier for the store"
      - name: d_date_sale
        description: "Date of the sale"
      - name: sale_datetime_rounded
        description: "Rounded sale datetime"
      - name: sale_hour
        description: "Hour of the sale"
      - name: store_department_id
        description: "Unique identifier for the store department"
      - name: store_department_name
        description: "Name of the store department"
      - name: checkout_station_id
        description: "Unique identifier for the checkout station"
      - name: checkout_method_type_name_sw
        description: "Checkout method type name in Swedish"
      - name: checkout_method_code
        description: "Code for the checkout method"
      - name: checkout_method_name_sw
        description: "Checkout method name in Swedish"
      - name: f_sale_receipt_key
        description: "Unique identifier for the sale receipt"
      - name: is_receipt_store_sale
        description: "Indicates if the receipt is a store sale"
      - name: d_store_cashier_key
        description: "Unique identifier for the store cashier"
      - name: is_receipt_returns_only
        description: "Indicates if the receipt is for returns only"
      - name: number_of_items
        description: "Total number of items sold"
      - name: sale_amount_excl_vat
        description: "Total sale amount excluding VAT"
      - name: sale_vat_amount
        description: "Total VAT amount on sales"
      - name: commission_amount_excl_vat
        description: "Total commission amount excluding VAT"
      - name: commission_vat_amount
        description: "Total VAT amount on commission"
      - name: margin_amount
        description: "Total margin amount"
      - name: avg_selling_price
        description: "Average selling price calculated as sum(sale_amount_excl_vat) / sum(number_of_items)"