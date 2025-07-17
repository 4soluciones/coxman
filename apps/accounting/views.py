from django.shortcuts import render
from django.contrib.auth.models import User
from apps.hrm.views import get_subsidiary_by_user
from apps.buys.models import Purchase, PurchaseDetail
from apps.sales.models import Subsidiary, SubsidiaryStore
from django.template import loader, Context
from django.http import JsonResponse
from http import HTTPStatus
from .models import *
import decimal
from django.shortcuts import render
from django.views.generic import TemplateView

from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.db import DatabaseError, IntegrityError
import json
from django.core import serializers
from django.db.models import Min, Sum

from ..comercial.models import Programming


class Home(TemplateView):
    template_name = 'accounting/home.html'


# def get_purchases_list(request):
#     if request.method == 'GET':
#         user_id = request.user.id
#         user_obj = User.objects.get(id=user_id)
#         subsidiary_obj = get_subsidiary_by_user(user_obj)
#         purchases_store = Purchase.objects.filter(subsidiary=subsidiary_obj, status='A')
#
#         return render(request, 'accounting/purchase_grid.html', {
#             'purchases_store': purchases_store,
#         })


def get_dict_purchases(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        purchases_set = Purchase.objects.filter(subsidiary=subsidiary_obj, status='A')
        dictionary = []

        for p in purchases_set:
            if p.purchasedetail_set.count() > 0:
                new = {
                    'id': p.id,
                    'supplier': p.supplier,
                    'type': p.get_status_display(),
                    'purchase_date': p.purchase_date,
                    'bill_number': p.bill_number,
                    'purchase_detail_set': [],
                    'user': p.user,
                    'subsidiary': p.subsidiary,
                    'status': p.get_status_display,
                    'details_count': p.purchasedetail_set.count(),
                    'rowspan': 0
                }
                rowspan = 1
                for d in PurchaseDetail.objects.filter(purchase=p):
                    purchase_detail = {
                        'id': d.id,
                        'product': d.product,
                        'quantity': d.quantity,
                        'unit': d.unit.description,
                        'price_unit': d.price_unit,
                        'total': decimal.Decimal(d.multiplicate()),
                        'rowspan': rowspan
                    }
                    new.get('purchase_detail_set').append(purchase_detail)
                    new['rowspan'] = new['rowspan'] + rowspan
            dictionary.append(new)

        return render(request, 'accounting/purchase_list.html', {
            'dictionary': dictionary,
        })


def get_account_list(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        account_set = AccountingAccount.objects.filter(code__startswith='10').order_by('code')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        return render(request, 'accounting/account_list.html', {
            'formatdate': formatdate,
            'subsidiary_obj': subsidiary_obj,
            'account_set': account_set,
        })


def new_opening_balance(request):
    if request.method == 'GET':
        store_request = request.GET.get('stores', '')
        data = json.loads(store_request)
        _date = str(data["Date"])
        for detail in data['Details']:
            _account_code = str(detail['AccountCode'])
            _debit = decimal.Decimal(detail['Debit'])
            _credit = decimal.Decimal(detail['Credit'])

            if _debit > 0:
                _operation = 'D'
                _amount = _debit
            elif _credit > 0:
                _operation = 'C'
                _amount = _credit

            account_obj = AccountingAccount.objects.get(code=str(_account_code))

            ledger_entry_obj = LedgerEntry(
                amount=_amount,
                type=_operation,
                account=account_obj,
            )
            ledger_entry_obj.save()

        return JsonResponse({
            'success': True,
        })


def get_cash_control_list(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        cash_set = Cash.objects.filter(subsidiary=subsidiary_obj)
        only_cash_set = cash_set.filter(accounting_account__code__startswith='101')
        cash_all_set = Cash.objects.filter(accounting_account__code__startswith='101').exclude(
            subsidiary=subsidiary_obj)

        accounts_banks_set = Cash.objects.filter(accounting_account__code__startswith='104')

        return render(request, 'accounting/cash_list.html', {
            'formatdate': formatdate,
            'only_cash_set': only_cash_set,
            'cash_all_set': cash_all_set,
            'accounts_banks_set': accounts_banks_set,
            'choices_operation_types': CashFlow._meta.get_field('operation_type').choices,
        })
    elif request.method == 'POST':
        id_cash = int(request.POST.get('cash'))
        start_date = str(request.POST.get('start-date'))
        user_type = int(request.POST.get('user'))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        # end_date = str(request.POST.get('end-date'))
        cash_flow_set = ''

        if user_type == 1:
            cash_flow_set = CashFlow.objects.filter(transaction_date=start_date, cash__id=id_cash)

        elif user_type == 2:
            cash_flow_set = CashFlow.objects.filter(transaction_date=start_date, cash__id=id_cash, user=user_obj)

        has_rows = False
        if cash_flow_set:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('accounting/cash_grid_list.html')
        context = ({
            'cash_flow_set': cash_flow_set,
            'has_rows': has_rows
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_account_cash():
    account_obj = AccountingAccount.objects.get(code='101')
    ledge_entry_set = LedgerEntry.objects.filter(account=account_obj)
    amount = 0
    if ledge_entry_set.count() > 0:
        ledge_entry_obj = ledge_entry_set.first()
        amount = ledge_entry_obj.amount
    context = {'account': account_obj, 'amount': amount}
    return context


def get_cash_by_subsidiary(request):
    if request.method == 'GET':
        pk = request.GET.get('cash_id', '')
        cash_obj = Cash.objects.get(id=pk)
        cash_subsidiary = cash_obj.subsidiary.name
        only_cash_set = AccountingAccount.objects.filter(code__startswith='10').order_by('code')

        return JsonResponse({'cash_subsidiary': cash_subsidiary}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def open_cash(request):
    if request.method == 'POST':
        _date = request.POST.get('cash-date')
        _amount = request.POST.get('cash-amount')
        _cash_id = request.POST.get('select-cash')

        cash_obj = Cash.objects.get(id=int(_cash_id))

        cash_flow_today_set = CashFlow.objects.filter(cash=cash_obj, transaction_date=_date, type='A')
        if cash_flow_today_set:  # Valid if there is an opening given a date
            data = {'error': "Ya existe una Apertura de Caja"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        else:  # there is not an opening given a date
            last_cash_flow_opening_set = CashFlow.objects.filter(cash=cash_obj, type='A')

            if last_cash_flow_opening_set:  # search last closing
                cash_flow_opening_obj = last_cash_flow_opening_set.last()
                check_closed = CashFlow.objects.filter(type='C', cash=cash_obj,
                                                       transaction_date=cash_flow_opening_obj.transaction_date)
                if check_closed:
                    cash_flow_obj = CashFlow(
                        transaction_date=_date,
                        cash=cash_obj,
                        description='APERTURA',
                        total=decimal.Decimal(_amount),
                        type='A')
                    cash_flow_obj.save()
                else:
                    data = {'error': "Debes cerrar la caja " + str(cash_flow_opening_obj.transaction_date)}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response
            else:  # create first opening record
                cash_flow_obj = CashFlow(
                    transaction_date=_date,
                    cash=cash_obj,
                    description='APERTURA',
                    total=decimal.Decimal(_amount),
                    type='A')
                cash_flow_obj.save()

        return JsonResponse({
            'message': 'Apertura de Caja exitosa.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def close_cash(request):
    if request.method == 'GET':
        _pk = request.GET.get('pk')
        _date = request.GET.get('date')
        _status = request.GET.get('status')

        cash_flow_day_obj = CashFlow.objects.get(id=int(_pk))

        if _status == 'A':
            cash_flow_closed_obj = CashFlow.objects.get(
                cash=cash_flow_day_obj.cash,
                transaction_date=cash_flow_day_obj.transaction_date,
                type='C')

            last_cash_flow_closed_set = CashFlow.objects.filter(
                cash=cash_flow_day_obj.cash,
                type='C')

            if last_cash_flow_closed_set:
                last_cash_flow_closed_obj = last_cash_flow_closed_set.last()
                if last_cash_flow_closed_obj == cash_flow_closed_obj:
                    cash_flow_closed_obj.delete()
                else:
                    data = {'error': "Ya no puede aperturar esta Caja"}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response
        else:
            cash_flow_obj = CashFlow(
                transaction_date=_date,
                cash=cash_flow_day_obj.cash,
                description='CIERRE',
                total=decimal.Decimal(cash_flow_day_obj.return_balance()),
                type='C')
            cash_flow_obj.save()

        return JsonResponse({
            'message': 'Cierre de Caja exitosa.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_account(request):
    if request.method == 'POST':
        _account_parent_code = request.POST.get('account-parent-code', '')
        _new_account_code = request.POST.get('new-account-code', '')
        _new_account_name = request.POST.get('new-account-name', '')

        account_parent_obj = AccountingAccount.objects.get(code=str(_account_parent_code))

        search_account = AccountingAccount.objects.filter(code=str(_new_account_code))
        if search_account:
            data = {'error': 'Ya existe una cuenta con este codigo'}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        else:

            try:
                accounting_account_obj = AccountingAccount(
                    code=str(_new_account_code),
                    description=str(_new_account_name),
                    parent_code=account_parent_obj.code
                )
                accounting_account_obj.save()
            except DatabaseError as e:
                data = {'error': str(e)}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

            account_set = AccountingAccount.objects.filter(code__startswith='10').order_by('code')
            tpl = loader.get_template('accounting/account_grid_list.html')
            context = ({'account_set': account_set, })
            return JsonResponse({
                'message': 'Guardado con exito.',
                'grid': tpl.render(context),
            }, status=HTTPStatus.OK)

    return JsonResponse({'error': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_entity(request):
    if request.method == 'POST':
        _entity_name = request.POST.get('entity-name', '')
        _entity_subsidiary = request.POST.get('entity-subsidiary', '')
        _entity_account_code = request.POST.get('entity-account-code', '')
        _entity_account_number = request.POST.get('entity-account-number', '')
        _entity_initial = request.POST.get('entity-initial', '')

        accounting_account_obj = AccountingAccount.objects.get(code=str(_entity_account_code))
        subsidiary_obj = Subsidiary.objects.get(id=int(_entity_subsidiary))

        try:
            cash_obj = Cash(
                name=str(_entity_name.upper()),
                subsidiary=subsidiary_obj,
                account_number=str(_entity_account_number),
                accounting_account=accounting_account_obj,
                initial=decimal.Decimal(_entity_initial),
            )
            cash_obj.save()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        account_set = AccountingAccount.objects.filter(code__startswith='10').order_by('code')
        tpl = loader.get_template('accounting/account_grid_list.html')
        context = ({'account_set': account_set, })
        return JsonResponse({
            'message': 'Guardado con exito.',
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)

    return JsonResponse({'error': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_entity(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        cash_obj = Cash.objects.filter(id=pk)
        serialized_obj = serializers.serialize('json', cash_obj)
        return JsonResponse({'obj': serialized_obj}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def update_entity(request):
    if request.method == 'POST':
        _entity_id = request.POST.get('entity', '')
        _entity_name = request.POST.get('entity-name', '')
        _entity_account_code = request.POST.get('entity-account-code', '')
        _entity_account_number = request.POST.get('entity-account-number', '')
        # _entity_initial = request.POST.get('entity-initial', '')

        cash_obj = Cash.objects.get(id=int(_entity_id))
        accounting_account_obj = AccountingAccount.objects.get(code=str(_entity_account_code))

        cash_obj.name = _entity_name.upper()
        cash_obj.account_number = str(_entity_account_number)
        cash_obj.accounting_account = accounting_account_obj
        cash_obj.save()

        account_set = AccountingAccount.objects.filter(code__startswith='10').order_by('code')
        tpl = loader.get_template('accounting/account_grid_list.html')
        context = ({'account_set': account_set, })

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)

    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_initial_balance(request):
    if request.method == 'GET':
        id_cash = request.GET.get('cash', '')
        cash_obj = Cash.objects.get(id=int(id_cash))
        initial_balance = cash_obj.current_balance()
        return JsonResponse({
            'initial_balance': initial_balance,
            'message': 'Codigo de sede recuperado.',
        }, status=HTTPStatus.OK)


def get_cash_date(request):
    if request.method == 'GET':
        pk = request.GET.get('cash_id', '')
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")

        if pk == '':
            response = JsonResponse({'error': 'Se requiere crear una caja.'})
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        cash_obj = Cash.objects.get(id=pk)
        cash_flow_set = CashFlow.objects.filter(cash=cash_obj, type='A')

        _date = ''
        if cash_flow_set.count() > 0:
            last_cash_flow_obj = cash_flow_set.last()
            _date = last_cash_flow_obj.transaction_date.strftime("%Y-%m-%d")
            is_closed = CashFlow.objects.filter(cash=cash_obj, type='C', transaction_date=_date)
            if not is_closed:
                if _date != formatdate:
                    response = JsonResponse({'error': 'Se requiere cerrar la caja del dia ' + _date, '_date': _date})
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response
                else:
                    return JsonResponse({'cash_date': _date}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_bank_transaction(request):
    if request.method == 'POST':
        _bank = request.POST.get('bank-cash')
        _operation = request.POST.get('bank-operation-type')
        _date = request.POST.get('bank-operation-date')
        _total = decimal.Decimal(request.POST.get('bank-total'))
        _code = request.POST.get('bank-operation-code')
        _description = request.POST.get('bank-description')

        bank_obj = Cash.objects.get(id=int(_bank))

        if _total <= 0:
            data = {'error': "Monto incorrecto"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        if _operation == '1':  # deposit
            _type = 'D'
        elif _operation == '2':  # withdrawal
            _type = 'R'
        elif _operation == '3':  # Purchase
            _type = 'R'
        elif _operation == '4':  # Bank withdrawal
            _type = 'R'

        cash_flow_obj = CashFlow(
            transaction_date=_date,
            cash=bank_obj,
            description=_description,
            total=_total,
            operation_type=_operation,
            operation_code=_code,
            user=user_obj,
            type=_type)
        cash_flow_obj.save()

        return JsonResponse({
            'message': 'Operación registrada con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_cash_disbursement(request):
    if request.method == 'POST':
        _cash = request.POST.get('disbursement-cash')
        _date = request.POST.get('disbursement-operation-date')
        _total = decimal.Decimal(request.POST.get('disbursement-total'))
        _description = request.POST.get('disbursement-description')
        _operation_method = request.POST.get('operationMethod')
        _modal_programming_id = request.POST.get('modal_programming_id', '')

        cash_obj = Cash.objects.get(id=int(_cash))

        cash_flow_set = CashFlow.objects.filter(transaction_date=_date, cash=cash_obj)
        programming_obj = None
        score = None
        if _modal_programming_id != '':
            programming_obj = Programming.objects.get(id=int(_modal_programming_id))

        if cash_flow_set:
            closed = cash_flow_set.filter(type='C')
            if closed:
                data = {'error': "Caja cerrada"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
            else:
                user_id = request.user.id
                user_obj = User.objects.get(id=user_id)

                cash_flow_obj = CashFlow(
                    transaction_date=_date,
                    cash=cash_obj,
                    description=_description,
                    total=_total,
                    operation_type='0',
                    user=user_obj,
                    type=_operation_method,
                    programming=programming_obj
                )
                cash_flow_obj.save()
                if programming_obj is not None:
                    tpl2 = loader.get_template('comercial/truck_plan_score.html')
                    from apps.comercial.view_passenger import get_score_programming_seat
                    score = tpl2.render(get_score_programming_seat(
                        programming_obj=programming_obj, current_subsidiary_obj=cash_obj.subsidiary), request),

        else:
            data = {'error': "Caja sin aperturar"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        return JsonResponse({
            'message': 'Operación registrada con exito.',
            'score': score,
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_cash_transfer_to_cash(request):
    if request.method == 'POST':
        _date = request.POST.get('transfer-date')
        _cash_origin = request.POST.get('cash-origin')
        _cash_destiny = request.POST.get('cash-destiny')
        _amount = request.POST.get('transfer-total-amount')
        _concept = request.POST.get('transfer-description')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        # COMPROBANDO QUE LAS CAJAS ESTEN ABIERTAS
        cashflow_set = CashFlow.objects.filter(cash_id=_cash_origin,
                                               transaction_date=_date,
                                               type='A')
        if cashflow_set.count() > 0:
            cash_origin_obj = cashflow_set.first().cash
            current_balance = cash_origin_obj.current_balance()

            if decimal.Decimal(_amount) > current_balance:
                data = {
                    'error': "El monto excede al saldo actual de la Caja"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        else:
            data = {
                'error': "No existe una Apertura de Caja, Favor de revisar los Control de Cajas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        cashflow_set = CashFlow.objects.filter(cash_id=_cash_destiny,
                                               transaction_date=_date,
                                               type='A')
        if cashflow_set.count() > 0:
            cash_destiny_obj = cashflow_set.first().cash
        else:
            data = {
                'error': "No existe una Apertura de Caja, Favor de revisar los Control de Cajas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        cash_transfer_obj = CashTransfer(status='P')
        cash_transfer_obj.save()

        # GUARDANDO EL ORIGEN
        cash_transfer_route_origin_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=cash_origin_obj,
            type='O'
        )
        cash_transfer_route_origin_obj.save()

        # GUARDANDO EL DESTINO
        cash_transfer_route_input_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=cash_destiny_obj,
            type='D'
        )
        cash_transfer_route_input_obj.save()

        # GUARDANDO EL USUARIO
        cash_transfer_action_obj = CashTransferAction(
            cash_transfer=cash_transfer_obj,
            user=user_obj,
            operation='E',
            register_date=_date,
        )
        cash_transfer_action_obj.save()

        # GUARDAMOS LA OPERACION
        cash_flow_output_obj = CashFlow(
            transaction_date=_date,
            cash=cash_origin_obj,
            description=_concept,
            total=_amount,
            operation_type='6',
            user=user_obj,
            cash_transfer=cash_transfer_obj,
            type='S')
        cash_flow_output_obj.save()

        return JsonResponse({
            'message': 'Operación registrada con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_last_cash_open(cash_id):
    cash_obj = Cash.objects.get(id=cash_id)
    last_cash = CashFlow.objects.filter(cash=cash_obj, type='A').last()
    return last_cash


def new_cash_to_bank(request):
    if request.method == 'POST':
        _date = request.POST.get('deposit-date')
        _cash_origin_deposit = request.POST.get('cash-origin-deposit')
        _current_balance_deposit = request.POST.get('current-balance-deposit')
        _bank_account = request.POST.get('bank-account')
        _amount_deposit = request.POST.get('deposit-amount')
        _description_deposit = request.POST.get('description-deposit')
        _code_operation = request.POST.get('code-operation-deposit')
        user_id = request.user.id
        bank_obj_destiny_deposit = Cash.objects.get(id=int(_bank_account))
        user_obj = User.objects.get(id=user_id)
        last_cash_date = get_last_cash_open(_cash_origin_deposit).transaction_date
        last_cash_open = get_last_cash_open(_cash_origin_deposit)
        las_cash_closed = CashFlow.objects.filter(type='C', cash=last_cash_open.cash,
                                                  transaction_date=last_cash_date.date())
        # COMPROBANDO CAJAS ABIERTAS
        if las_cash_closed:
            data = {
                'error': "No existe una Apertura de Caja, Favor de revisar los Control de Cajas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        else:
            cashflow_set = CashFlow.objects.filter(cash=_cash_origin_deposit,
                                                   type='A')
            cash_origin_obj = cashflow_set.first().cash
            current_balance = cash_origin_obj.current_balance()
            if decimal.Decimal(_amount_deposit) > current_balance:
                data = {
                    'error': "El monto excede al saldo actual de la Caja"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        cash_transfer_obj = CashTransfer(status='A')
        cash_transfer_obj.save()

        # GUARDANDO EL ORIGEN - LA CAJA
        cash_transfer_route_origin_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=cash_origin_obj,
            type='O'
        )
        cash_transfer_route_origin_obj.save()

        # GUARDANDO EL DESTINO - BANCO
        cash_transfer_route_input_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=bank_obj_destiny_deposit,
            type='D'
        )
        cash_transfer_route_input_obj.save()

        # GUARDANDO EL USUARIO
        cash_transfer_action_obj = CashTransferAction(
            cash_transfer=cash_transfer_obj,
            user=user_obj,
            operation='E',
            register_date=_date,
        )
        cash_transfer_action_obj.save()

        # GUARDAMOS LA OPERACION
        cash_flow_output_obj = CashFlow(
            transaction_date=last_cash_date,
            cash=cash_origin_obj,
            description=_description_deposit,
            total=_amount_deposit,
            operation_type='7',
            user=user_obj,
            cash_transfer=cash_transfer_obj,
            type='S')
        cash_flow_output_obj.save()

        cash_flow_input_obj = CashFlow(
            transaction_date=_date,
            cash=bank_obj_destiny_deposit,
            description=_description_deposit,
            total=_amount_deposit,
            operation_type='7',
            operation_code=_code_operation,
            user=user_obj,
            type='D')
        cash_flow_input_obj.save()

        return JsonResponse({
            'message': 'Operación registrada con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_bank_control_list(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        other_subsidiary_set = Subsidiary.objects.exclude(id=subsidiary_obj.id)

        cash_set = Cash.objects.filter(subsidiary=subsidiary_obj)
        only_bank_set = cash_set.filter(accounting_account__code__startswith='1041')
        ours_cash_set = Cash.objects.filter(accounting_account__code__startswith='101')
        only_other_bank_set = Cash.objects.filter(accounting_account__code__startswith='1041').exclude(
            subsidiary=subsidiary_obj)

        return render(request, 'accounting/banking_list.html', {
            'formatdate': formatdate,
            'subsidiary_obj': subsidiary_obj,
            'only_bank_set': only_bank_set,
            'ours_cash_set': ours_cash_set,
            'other_subsidiary_set': other_subsidiary_set,
            'only_other_bank_set': only_other_bank_set,
            'choices_operation_types': CashFlow._meta.get_field('operation_type').choices,
        })
    elif request.method == 'POST':
        id_cash = int(request.POST.get('cash'))
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))

        if start_date == end_date:
            cash_flow_set = CashFlow.objects.filter(transaction_date=start_date, cash__id=id_cash)
        else:
            cash_flow_set = CashFlow.objects.filter(transaction_date__range=[start_date, end_date],
                                                    cash__id=id_cash)

        has_rows = False
        if cash_flow_set:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('accounting/banking_grid_list.html')
        context = ({
            'cash_flow_set': cash_flow_set,
            'has_rows': has_rows,
            'current_balance': Cash.objects.get(id=id_cash).current_balance()
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def new_transfer_bank(request):
    if request.method == 'POST':

        _subsidiary_origin = request.POST.get('transfer-subsidiary-origin')
        _bank_origin = request.POST.get('transfer-bank-origin')
        _subsidiary_destiny = request.POST.get('transfer-subsidiary-destiny')
        _bank_destiny = request.POST.get('transfer-bank-destiny')

        _total = decimal.Decimal(request.POST.get('transfer-total'))
        _description = request.POST.get('transfer-description')
        _operation_code = request.POST.get('transfer-operation-code')
        _date = request.POST.get('transfer-date')

        bank_origin_obj = Cash.objects.get(id=int(_bank_origin))
        bank_destiny_obj = Cash.objects.get(id=int(_bank_destiny))

        if _total <= 0:
            data = {'error': "Monto incorrecto"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        cash_transfer_obj = CashTransfer(status='A')
        cash_transfer_obj.save()

        cash_transfer_route_origin_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=bank_origin_obj,
            type='O'
        )
        cash_transfer_route_origin_obj.save()

        cash_transfer_route_input_obj = CashTransferRoute(
            cash_transfer=cash_transfer_obj,
            cash=bank_destiny_obj,
            type='D'
        )
        cash_transfer_route_input_obj.save()

        cash_transfer_action_obj = CashTransferAction(
            cash_transfer=cash_transfer_obj,
            user=user_obj,
            operation='E',
            register_date=_date,
        )
        cash_transfer_action_obj.save()

        cash_flow_output_obj = CashFlow(
            transaction_date=_date,
            cash=bank_origin_obj,
            description=_description,
            total=_total,
            operation_type='5',
            operation_code=_operation_code,
            user=user_obj,
            cash_transfer=cash_transfer_obj,
            type='R')
        cash_flow_output_obj.save()

        cash_flow_input_obj = CashFlow(
            transaction_date=_date,
            cash=bank_destiny_obj,
            description=_description,
            total=_total,
            operation_type='5',
            operation_code=_operation_code,
            user=user_obj,
            type='D')
        cash_flow_input_obj.save()

        return JsonResponse({
            'message': 'Operación registrada con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_confirm_cash_to_cash_transfer(request):
    if request.method == 'GET':
        # pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        cash_transfer_set = CashTransfer.objects.filter(status='P', cashtransferroute__cash__subsidiary=subsidiary_obj)

        t = loader.get_template('accounting/confirm_cash_transfers.html')
        c = ({
            'cash_transfer_set': cash_transfer_set,
            'subsidiary_obj': subsidiary_obj,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })


def accept_cash_to_cash_transfer(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")

        cash_transfer_obj = CashTransfer.objects.get(id=int(pk))
        cash_destiny_obj = cash_transfer_obj.get_destiny()
        cash_origin_obj = cash_transfer_obj.get_origin()

        cash_flow_destiny_set = CashFlow.objects.filter(cash=cash_destiny_obj, transaction_date=formatdate,
                                                        type='A')
        if cash_flow_destiny_set.count() == 0:
            data = {
                'error': "No existe una Apertura de Caja, Favor de revisar los Control de Cajas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        cash_transfer_obj.status = 'A'
        cash_transfer_obj.save()

        cash_transfer_action_obj = CashTransferAction(
            cash_transfer=cash_transfer_obj,
            user=user_obj,
            operation='A',
            register_date=formatdate,
        )
        cash_transfer_action_obj.save()

        cash_flow_origin_obj = CashFlow.objects.get(cash=cash_origin_obj, cash_transfer=cash_transfer_obj)
        cash_flow_input_obj = CashFlow(
            transaction_date=formatdate,
            cash=cash_destiny_obj,
            description=cash_flow_origin_obj.description,
            total=cash_flow_origin_obj.total,
            operation_type='6',
            user=user_obj,
            type='E')
        cash_flow_input_obj.save()

        return JsonResponse({'success': True, }, status=HTTPStatus.OK)


def desist_cash_to_cash_transfer(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")

        cash_transfer_obj = CashTransfer.objects.get(id=int(pk))
        cash_transfer_obj.status = 'C'
        cash_transfer_obj.save()

        cash_transfer_action_obj = CashTransferAction(
            cash_transfer=cash_transfer_obj,
            user=user_obj,
            operation='C',
            register_date=formatdate,
        )
        cash_transfer_action_obj.save()

        cash_destiny_obj = cash_transfer_obj.get_destiny()
        cash_origin_obj = cash_transfer_obj.get_origin()

        cash_flow_origin_obj = CashFlow.objects.get(cash=cash_origin_obj, cash_transfer=cash_transfer_obj)
        cash_flow_input_obj = CashFlow(
            transaction_date=formatdate,
            cash=cash_origin_obj,
            description=str(
                'SE CANCELO LA OPERACIÓN: ' + cash_flow_origin_obj.description + ' POR EL USUARIO: ' + user_obj.worker_set.last().employee.full_name()),
            total=cash_flow_origin_obj.total,
            operation_type='6',
            user=user_obj,
            type='E')
        cash_flow_input_obj.save()

        return JsonResponse({
            'success': True,
        }, status=HTTPStatus.OK)


def new_bank_to_cash_transfer(request):
    if request.method == 'POST':
        _date = request.POST.get('btc-date')
        _bank_origin = request.POST.get('btc-bank-origin')
        _cash_destiny = request.POST.get('btc-cash-destiny')
        _current_balance = request.POST.get('btc-current-balance')
        _total = request.POST.get('btc-total')
        _description = request.POST.get('btc-description')

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        bank_origin_obj = Cash.objects.get(id=int(_bank_origin))
        cash_destiny_obj = Cash.objects.get(id=int(_cash_destiny))

        return JsonResponse({
            'message': 'Operación registrada con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def save_cash_flow(
        cash_obj=None,
        order_obj=None,
        user_obj=None,
        cash_flow_transact_date='',
        cash_flow_description='',
        cash_flow_type='',
        cash_flow_operation='',
        cash_flow_programming=None,
        cash_flow_total=0,
        document_type_attached=''
):
    cash_flow_obj = CashFlow(
        transaction_date=cash_flow_transact_date,
        document_type_attached=document_type_attached,
        description=cash_flow_description,
        order=order_obj,
        type=cash_flow_type,
        operation_code=cash_flow_operation,
        programming=cash_flow_programming,
        total=cash_flow_total,
        cash=cash_obj,
        user=user_obj
    )
    cash_flow_obj.save()
