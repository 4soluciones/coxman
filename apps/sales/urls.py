from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.sales.views import *
from apps.sales.views_SUNAT import query_dni
from apps.sales.views_PDF import product_print, kardex_glp_pdf, account_order_list_pdf, all_account_order_list_pdf
from apps.sales.views_EXCEL import kardex_glp_excel

urlpatterns = [
    path('', login_required(Home.as_view()), name='home'),
    path('product_list/', login_required(ProductList.as_view()), name='product_list'),
    path('json_product_create/', login_required(JsonProductCreate.as_view()), name='json_product_create'),
    path('json_product_list/', login_required(JsonProductList.as_view()), name='json_product_list'),
    path('json_product_edit/<int:pk>/',
         login_required(JsonProductUpdate.as_view()), name='json_product_edit'),
    path('get_product/', get_product, name='get_product'),
    path('new_quantity_on_hand/', new_quantity_on_hand, name='new_quantity_on_hand'),

    path('get_kardex_by_product/', get_kardex_by_product, name='get_kardex_by_product'),
    path('get_list_kardex/', get_list_kardex, name='get_list_kardex'),

    path('client_list/', login_required(ClientList.as_view()), name='client_list'),

    path('new_client/', new_client, name='new_client'),
    path('get_client/', get_client, name='get_client'),

    # path('new_sales/', new_sales, name='new_sales'),

    path('sales_list/', login_required(SalesList.as_view()), name='sales_list'),
    path('sales_list/<int:pk>/', login_required(SalesList.as_view()), name='sales_list'),
    path('sales_list/<str:letter>/', login_required(SalesList.as_view()), name='sales_list'),

    path('set_product_detail/', set_product_detail, name='set_product_detail'),
    path('get_product_detail/', get_product_detail, name='get_product_detail'),
    path('update_product_detail/', update_product_detail, name='update_product_detail'),
    path('toogle_status_product_detail/', toogle_status_product_detail,
         name='toogle_status_product_detail'),

    path('get_rate_product/', get_rate_product, name='get_rate_product'),
    path('create_order_detail/', create_order_detail, name='create_order_detail'),
    path('query_dni/', query_dni, name='query_dni'),

    path('generate_invoice/', generate_invoice, name='generate_invoice'),
    path('get_sales_by_subsidiary_store/', get_sales_by_subsidiary_store,
         name='get_sales_by_subsidiary_store'),
    path('get_products_by_subsidiary/', get_products_by_subsidiary, name='get_products_by_subsidiary'),
    path('new_subsidiary_store/', new_subsidiary_store, name='new_subsidiary_store'),
    path('get_recipe/', login_required(get_recipe), name='get_recipe'),
    path('create_recipe/', login_required(create_recipe), name='create_recipe'),
    path('get_manufacture/', login_required(get_manufacture), name='get_manufacture'),
    # path('get_product_recipe/', get_product_recipe, name='get_product_recipe'),
    path('get_unit_by_product/', get_unit_by_product, name='get_unit_by_product'),
    path('get_price_by_product/', get_price_by_product, name='get_price_by_product'),
    path('get_price_and_total_by_product_recipe/', get_price_and_total_by_product_recipe,
         name='get_price_and_total_by_product_recipe'),
    path('get_stock_insume_by_product_recipe/', login_required(get_stock_insume_by_product_recipe),
         name='get_stock_insume_by_product_recipe'),
    path('create_order_manufacture/', login_required(create_order_manufacture),
         name='create_order_manufacture'),
    path('orders_manufacture/', login_required(orders_manufacture), name='orders_manufacture'),
    path('update_manufacture_by_id/', login_required(update_manufacture_by_id),
         name='update_manufacture_by_id'),

    # product get recipe
    path('get_recipe_by_product/', get_recipe_by_product, name='get_recipe_by_product'),

    # ReportLab
    path('product_print/', product_print, name='product_print'),
    path('product_print/<int:pk>/', product_print, name='product_print_one'),
    path('all_account_order_list_pdf/', all_account_order_list_pdf, name='all_account_order_list_pdf'),

    # GlP KARDEX
    path('get_kardex_glp/', login_required(get_kardex_glp), name='get_kardex_glp'),
    path('get_only_grid_kardex_glp/<int:pk>/',
         get_only_grid_kardex_glp, name='get_only_grid_kardex_glp'),

    # PDFKIT
    path('kardex_glp_pdf/<int:pk>/', login_required(kardex_glp_pdf), name='kardex_glp_pdf'),
    path('account_order_list_pdf/<int:pk>/',
         login_required(account_order_list_pdf), name='account_order_list_pdf'),

    # PANDA
    path('kardex_glp_excel/<int:pk>/', login_required(kardex_glp_excel), name='kardex_glp_excel'),

    # ESTADO DE CUENTA
    path('order_list/', login_required(order_list), name='order_list'),
    path('get_orders_by_client/', get_orders_by_client, name='get_orders_by_client'),
    path('get_order_detail_for_pay/', get_order_detail_for_pay, name='get_order_detail_for_pay'),
    path('new_loan_payment/', login_required(new_loan_payment), name='new_loan_payment'),
    path('get_order_detail_for_ball_change/', login_required(get_order_detail_for_ball_change),
         name='get_order_detail_for_ball_change'),
    path('new_ball_change/', login_required(new_ball_change), name='new_ball_change'),
    path('get_expenses/', login_required(get_expenses), name='get_expenses'),
    path('new_expense/', login_required(new_expense), name='new_expense'),

    # GENERADOR DE BOLETAS
    path('generate_receipt/', login_required(generate_receipt), name='generate_receipt'),
    path('generate_receipt_random/', login_required(generate_receipt_random), name='generate_receipt_random'),

    # PERCEPTRON
    path('PerceptronList/', login_required(PerceptronList), name='PerceptronList'),

    # SEND_SUNAT
    path('send_invoices_sunat/', login_required(send_invoices_sunat), name='send_invoices_sunat'),

]
