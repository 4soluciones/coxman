from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.accounting.views import *

urlpatterns = [
    path('', login_required(Home.as_view()), name='home'),
    # path('get_purchases_list/', login_required(get_purchases_list), name='get_purchases_list'),
    path('get_dict_purchases/', login_required(get_dict_purchases), name='get_dict_purchases'),
    path('new_opening_balance/', login_required(new_opening_balance), name='new_opening_balance'),

    # cash
    path('get_cash_control_list/', login_required(get_cash_control_list), name='get_cash_control_list'),
    path('open_cash/', login_required(open_cash), name='open_cash'),
    path('close_cash/', login_required(close_cash), name='close_cash'),
    path('get_initial_balance/', login_required(get_initial_balance), name='get_initial_balance'),
    path('get_cash_date/', login_required(get_cash_date), name='get_cash_date'),

    # accounts
    path('get_account_list/', login_required(get_account_list), name='get_account_list'),
    path('new_account/', login_required(new_account), name='new_account'),
    path('new_entity/', login_required(new_entity), name='new_entity'),
    path('get_entity/', login_required(get_entity), name='get_entity'),
    path('update_entity/', login_required(update_entity), name='update_entity'),

    # banks
    path('get_bank_control_list/', login_required(get_bank_control_list), name='get_bank_control_list'),

    # transactions
    path('new_bank_transaction/', login_required(new_bank_transaction), name='new_bank_transaction'),
    path('new_cash_disbursement/', login_required(new_cash_disbursement), name='new_cash_disbursement'),
    path('new_transfer_bank/', login_required(new_transfer_bank), name='new_transfer_bank'),
    path('get_cash_by_subsidiary/', login_required(get_cash_by_subsidiary), name='get_cash_by_subsidiary'),
    path('new_cash_transfer_to_cash/', login_required(new_cash_transfer_to_cash), name='new_cash_transfer_to_cash'),
    path('get_confirm_cash_to_cash_transfer/', login_required(get_confirm_cash_to_cash_transfer), name='get_confirm_cash_to_cash_transfer'),
    path('new_cash_to_bank/', login_required(new_cash_to_bank), name='new_cash_to_bank'),
    path('accept_cash_to_cash_transfer/', login_required(accept_cash_to_cash_transfer), name='accept_cash_to_cash_transfer'),
    path('desist_cash_to_cash_transfer/', login_required(desist_cash_to_cash_transfer), name='desist_cash_to_cash_transfer'),
    path('new_bank_to_cash_transfer/', login_required(new_bank_to_cash_transfer), name='new_bank_to_cash_transfer'),

]
