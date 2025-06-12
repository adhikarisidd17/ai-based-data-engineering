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
    case
        when
            sum(f.number_of_items) > 0
            then sum(f.sale_amount_excl_vat) / sum(f.number_of_items)
        else 0
    end as avg_selling_price
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
