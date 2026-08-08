{%- macro cast_currency(column_name) -%}
    {{ column_name }}::number(10,2)
{%- endmacro -%}