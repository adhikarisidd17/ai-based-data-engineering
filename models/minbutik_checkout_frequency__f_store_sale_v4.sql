{% set partition_cutoff = (run_started_at-modules.datetime.timedelta(config.require("partition_expiration_days")|int)).strftime("%Y-%m-%d") %}
{% set conlayap_f_sale_receipt_line = ref('conlayap_consumer_sales_secure__f_sale_receipt_line') %}
{% set conbiprep_sale_partitions = ref('conbiprep_consumer_sales_secure__conbiprep_sales_partitions') %}
{% set partition_list = updated_partition_list_v2(partition_timestamps(conbiprep_sale_partitions, first_partition=partition_cutoff|replace("-", "")), config.require("backfill_max_partitions")) %}
{% set demo_store_id = '12740' %}
{% set ref_store_id = '00561' %}

with sale_receipt_line as (
    select 
        d_store_key,
        d_store_local_item_key,
        d_checkout_method_key,
        d_sale_receipt_info_key,
        f_sale_receipt_key,
        max(consumer_store_sales_indicator) over (partition by f_sale_receipt_key) as is_receipt_store_sale, -- the receipt is considered as store sale if the indicator is true for one of the receipt lines
        d_date_sale,
        datetime(timestamp_seconds(900 * div(unix_seconds(timestamp(sale_datetime)), 900))) as sale_datetime_rounded, -- Bucketing the timestamp into 15 mins intervals
        extract(hour from sale_datetime) as sale_hour,
        store_sale_amount,
        store_sale_vat_amount,
        commission_amount,
        commission_vat_amount,
        margin_amount,
        number_of_items,
        d_store_cashier_key,
        case
            when number_of_returns_only
            then true else false
        end as is_receipt_returns_only,
    from {{ conlayap_f_sale_receipt_line }}
    where {{ in_list_filter("d_date_sale", partition_list) }}
    and d_date_sale >= "{{ partition_cutoff }}"
),
real_stores as (
select
    ds.store_id,
    f.d_date_sale,
    f.sale_datetime_rounded,
    f.sale_hour,
    li.store_department_id,
    li.store_department_name,
    d_r_info.checkout_station_id,
    d_checkout.checkout_method_type_name_sw,
    d_checkout.checkout_method_code,
    d_checkout.checkout_method_name_sw,
    f.f_sale_receipt_key,
    f.is_receipt_store_sale,
    f.d_store_cashier_key,
    f.is_receipt_returns_only,
    sum(f.number_of_items) as number_of_items,
    sum(f.store_sale_amount) as sale_amount_excl_vat,
    sum(f.store_sale_vat_amount) as sale_vat_amount,
    sum(f.commission_amount) as commission_amount_excl_vat,
    sum(f.commission_vat_amount) as commission_vat_amount,
    sum(f.margin_amount) as margin_amount,
    sum(f.store_sale_amount) / nullif(sum(f.number_of_items), 0) as avg_selling_price -- New column for average selling price
from sale_receipt_line as f
inner join {{ ref('conlaybi_store__d_store') }} ds using (d_store_key)
inner join {{ ref("minbutik_article_analysis__d_store") }} fl using (store_id)
inner join {{ ref('conlaybi_item__d_store_local_item_temporary') }} li using(d_store_local_item_key)
inner join {{ ref('conlaybi_consumer_sales__d_sale_receipt_info') }} d_r_info using (d_sale_receipt_info_key)
left join {{ ref('conlaybi_consumer_sales__d_checkout_method') }} d_checkout using (d_checkout_method_key)
group by
    ds.store_id,
    f.d_date_sale,
    f.sale_datetime_rounded,
    f.sale_hour,
    li.store_department_id,
    li.store_department_name,
    d_r_info.checkout_station_id,
    d_checkout.checkout_method_type_name_sw,
    d_checkout.checkout_method_code,
    d_checkout.checkout_method_name_sw,
    f.f_sale_receipt_key,
    f.is_receipt_store_sale,
    f.d_store_cashier_key,
    f.is_receipt_returns_only
),
demo_store as (
    select
        "{{ demo_store_id }}" as store_id,
        d_date_sale,
        sale_datetime_rounded,
        sale_hour,
        store_department_id,
        store_department_name,
        checkout_station_id,
        checkout_method_type_name_sw,
        checkout_method_code,
        checkout_method_name_sw,
        farm_fingerprint("{{ demo_store_id }}" || "|##|" || cast(f_sale_receipt_key as string)) as f_sale_receipt_key,
        is_receipt_store_sale,
        d_store_cashier_key,
        is_receipt_returns_only,
        round(sum(number_of_items * rand())) as number_of_items,
        round(sum(sale_amount_excl_vat * rand()), 2) as sale_amount_excl_vat,
        round(sum(sale_vat_amount * rand()), 2) as sale_vat_amount,
        round(sum(commission_amount_excl_vat * rand()), 2) as commission_amount_excl_vat,
        round(sum(commission_vat_amount * rand()), 2) as commission_vat_amount,
        round(sum(margin_amount * rand()), 2) as margin_amount
    from real_stores
    where store_id = "{{ ref_store_id }}"
    group by 
        store_id,
        d_date_sale,
        sale_datetime_rounded,
        sale_hour,
        store_department_id,
        store_department_name,
        checkout_station_id,
        checkout_method_type_name_sw,
        checkout_method_code,
        checkout_method_name_sw,
        f_sale_receipt_key,
        is_receipt_store_sale,
        d_store_cashier_key,
        is_receipt_returns_only
)
select *
from real_stores
union all
select *
from demo_store

# In the corresponding YAML file (minbutik_checkout_frequency__f_store_sale.yml), add the following line under the appropriate section:
# - avg_selling_price: 
#     description: "Average selling price calculated as sum(store_sales_amount) / sum(number_of_items)"