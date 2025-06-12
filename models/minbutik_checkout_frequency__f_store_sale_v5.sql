store_id: 
  type: integer
  description: "The unique identifier for the store."
d_date_sale: 
  type: date
  description: "The date of the sale."
sale_datetime_rounded: 
  type: timestamp
  description: "The sale datetime rounded to the nearest hour."
sale_hour: 
  type: integer
  description: "The hour of the sale."
store_department_id: 
  type: integer
  description: "The unique identifier for the store department."
store_department_name: 
  type: string
  description: "The name of the store department."
checkout_station_id: 
  type: integer
  description: "The unique identifier for the checkout station."
checkout_method_type_name_sw: 
  type: string
  description: "The name of the checkout method type in Swedish."
checkout_method_code: 
  type: string
  description: "The code for the checkout method."
checkout_method_name_sw: 
  type: string
  description: "The name of the checkout method in Swedish."
f_sale_receipt_key: 
  type: string
  description: "The unique key for the sale receipt."
is_receipt_store_sale: 
  type: boolean
  description: "Indicates if the receipt is for a store sale."
d_store_cashier_key: 
  type: string
  description: "The unique key for the store cashier."
is_receipt_returns_only: 
  type: boolean
  description: "Indicates if the receipt is for returns only."
number_of_items: 
  type: integer
  description: "The total number of items sold."
sale_amount_excl_vat: 
  type: decimal
  description: "The total sale amount excluding VAT."
sale_vat_amount: 
  type: decimal
  description: "The total VAT amount on the sale."
commission_amount_excl_vat: 
  type: decimal
  description: "The total commission amount excluding VAT."
commission_vat_amount: 
  type: decimal
  description: "The total VAT amount on the commission."
margin_amount: 
  type: decimal
  description: "The total margin amount."