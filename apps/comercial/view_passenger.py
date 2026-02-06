import decimal
from collections import Counter
from http import HTTPStatus
from django.shortcuts import render
from django.http import JsonResponse
from .forms import *
from apps.sales.models import Order, OrderDetail, OrderBill, OrderAction
from .models import Origin
from apps.sales.views import Client, ClientType, ClientAddress
from apps.sales.views_SUNAT import send_bill_passenger, send_receipt_passenger
from apps.hrm.models import Subsidiary, DocumentType, Nationality, SubsidiaryCompany, Worker, UserSubsidiary
import json
from apps.accounting.views import Cash, CashFlow, save_cash_flow
from django.template import loader
from datetime import datetime
from django.core import serializers
# from apps.comercial.views import calculate_age
from apps.comercial.view_correlative import update_correlative_passenger, get_correlative_electronic_passenger, \
    get_correlative_commodity
from ..hrm.views import get_subsidiary_by_user
from dateutil.relativedelta import relativedelta

from ..sales.api_FACT import send_bill_ticket_fact, send_receipt_passenger_fact
from ..sales.format_to_dates import utc_to_local


def get_predecessor(array_venues=None, index_current=0):
    if array_venues is None:
        array_venues = []
    predecessor = None
    if index_current > 0:
        index_predecessor = index_current - 1
        predecessor = array_venues[index_predecessor]
    return predecessor


def get_successor(array_venues=None, index_current=0):
    if array_venues is None:
        array_venues = []
    successor = None
    if index_current + 1 < len(array_venues):
        index_successor = index_current + 1
        successor = array_venues[index_successor]
    return successor


def go_to_seats_of_predecessors(seats_sold_set=None, np=None, subsidiary_obj=None, array_venues=None):
    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_obj.id)
        predecessor = get_predecessor(array_venues=array_venues, index_current=index_current)
        if predecessor is not None:
            index_predecessor = array_venues.index(predecessor)

            for ps in seats_sold_set:
                subsidiary_who_puts_limit = ps.subsidiary_who_puts_limit
                if subsidiary_who_puts_limit.id in array_venues:
                    index_who_puts_limit = array_venues.index(subsidiary_who_puts_limit.id)
                    if index_who_puts_limit <= index_current:
                        nps = ProgrammingSeat.objects.get(programming=np, plan_detail=ps.plan_detail)
                        if index_who_puts_limit < index_predecessor:
                            # green
                            nps.status = '1'
                        else:
                            # purple
                            nps.status = '8'
                        nps.save()


def go_to_seats_of_successors(seats_sold_set=None, np=None, subsidiary_obj=None, array_venues=None):
    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_obj.id)
        successor_direct = get_successor(array_venues, index_current)

        if successor_direct in array_venues:
            index_successor = array_venues.index(successor_direct)

            for ps in seats_sold_set:
                subsidiary_who_puts_limit = ps.subsidiary_who_puts_limit

                if subsidiary_who_puts_limit.id in array_venues:
                    index_who_puts_limit = array_venues.index(subsidiary_who_puts_limit.id)

                    if index_who_puts_limit > index_current:
                        nps = ProgrammingSeat.objects.get(programming=np, plan_detail=ps.plan_detail)
                        subsidiary_than_sold = ps.subsidiary_than_sold
                        index_than_sold = array_venues.index(subsidiary_than_sold.id)

                        if index_successor == index_than_sold:
                            # olive
                            nps.status = '9'
                        else:
                            # gray
                            nps.status = '7'
                        nps.save()


def get_subsidiary_associate_leader(subsidiary_obj=None):
    search = AssociateDetail.objects.filter(subsidiary=subsidiary_obj)
    if search.exists():
        subsidiary_associate_leader_obj = search.first().associate.subsidiary
    else:
        subsidiary_associate_leader_obj = subsidiary_obj
    return subsidiary_associate_leader_obj


def get_serial_subsidiary_company(subsidiary_obj=None, company_rotation_obj=None, type_document=None):
    response = None
    subsidiary_company_set = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if subsidiary_company_set.exists():
        subsidiary_company_obj = subsidiary_company_set.last()
        if type_document == 'T':
            response = subsidiary_company_obj.serial_two
        elif type_document == 'B':
            response = subsidiary_company_obj.serial_voucher_to_passenger
        elif type_document == 'F':
            response = subsidiary_company_obj.serial_invoice_to_passenger
        # 'serial_commodity': subsidiary_company_obj.serial,
    return response


def get_serial_manifest_and_commodity(subsidiary_obj=None, company_rotation_obj=None, type_document=None):
    response = None
    subsidiary_company_set = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if subsidiary_company_set.exists():
        subsidiary_company_obj = subsidiary_company_set.last()
        if type_document == 'T':
            response = subsidiary_company_obj.serial
        elif type_document == 'B':
            response = subsidiary_company_obj.serial_voucher_to_commodity
        elif type_document == 'F':
            response = subsidiary_company_obj.serial_invoice_to_commodity
        # 'serial_commodity': subsidiary_company_obj.serial,
    return response


def get_serial_manifest(subsidiary_obj=None, company_rotation_obj=None):
    context = None
    subsidiary_company_set = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if subsidiary_company_set.exists():
        subsidiary_company_obj = subsidiary_company_set.last()
        context = {
            'serial_commodity': subsidiary_company_obj.serial,
            'serial_manifest_passenger': subsidiary_company_obj.serial_three,
            'serial_commodity_voucher': subsidiary_company_obj.serial_voucher_to_commodity,
            'serial_commodity_invoice': subsidiary_company_obj.serial_invoice_to_commodity
        }
    return context


def truck_plan(request, pk):
    user_id = request.user.id
    user_obj = User.objects.get(pk=int(user_id))

    # company_rotation_obj =
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    programming_obj = None
    company_rotation_obj = None
    # cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')
    # cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, cash_type='B')
    dictionary = []
    plan_obj = None
    serials = None

    if pk:
        programming_obj = Programming.objects.get(id=pk)

        company_rotation_obj = programming_obj.company
        serials = get_serial_subsidiary_company(subsidiary_obj=subsidiary_obj,
                                                company_rotation_obj=company_rotation_obj, type_document='B')
        if programming_obj.programmingseat_set.count() == 0:
            plan_obj = programming_obj.truck.plan
            if programming_obj.parent:
                lp = programming_obj.parent
                programming_seat_set = lp.programmingseat_set.all()
                for ps in programming_seat_set:
                    programming_seat_obj = ProgrammingSeat(
                        status=ps.status,
                        plan_detail=ps.plan_detail,
                        description=ps.description,
                        programming=programming_obj,
                        subsidiary_who_puts_limit=ps.subsidiary_who_puts_limit,
                        subsidiary_than_sold=ps.subsidiary_than_sold,
                        subsidiary_than_reserve=ps.subsidiary_than_reserve,
                        parent=ps
                    )
                    programming_seat_obj.save()
                # get reds and olives
                seats_sold_set = ProgrammingSeat.objects.filter(programming=lp, status__in=['4', '9'])

                array_venues = tour_venues(lp.path)
                # green | purple
                go_to_seats_of_predecessors(
                    seats_sold_set=seats_sold_set,
                    np=programming_obj,
                    subsidiary_obj=subsidiary_obj,
                    array_venues=array_venues
                )
                # olive | gray
                go_to_seats_of_successors(
                    seats_sold_set=seats_sold_set,
                    np=programming_obj,
                    subsidiary_obj=subsidiary_obj,
                    array_venues=array_venues
                )
            else:
                for d in plan_obj.plandetail_set.all():
                    programming_seat_obj = ProgrammingSeat(status='1', plan_detail=d, programming=programming_obj)
                    programming_seat_obj.save()
        else:
            plan_obj = programming_obj.truck.plan
        dictionary = truck_dictionary(programming_obj, plan_obj)

    _score_programming_seat = get_score_programming_seat(programming_obj=programming_obj,
                                                         current_subsidiary_obj=subsidiary_obj)
    _voucher_report = get_voucher_report(programming_obj=programming_obj,
                                         current_subsidiary_obj=subsidiary_obj)

    subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)
    # serial_passenger = serials.get('serial_passenger')

    return render(request, 'comercial/truck_plan.html', {
        'programming_obj': programming_obj,
        'subsidiary_origin': subsidiary_associate_leader_obj,
        'subsidiary_current': subsidiary_obj,
        'plan_obj': plan_obj,
        'dictionary': dictionary,
        'path_obj': programming_obj.path,
        'circles': programming_obj.path.pathdetail_set.count() + 1,
        'serial': serials,
        'correlative': get_correlative_electronic_passenger(subsidiary_obj=subsidiary_obj,
                                                 company_rotation_obj=company_rotation_obj, doc_type='B'),
        'subsidiaries': Subsidiary.objects.exclude(name=subsidiary_obj.name),
        'quantity_sold': _score_programming_seat.get('quantity_sold'),
        'quantity_free': _score_programming_seat.get('quantity_free'),
        'quantity_reserved': _score_programming_seat.get('quantity_reserved'),
        'order_set': _score_programming_seat.get('order_set'),
        'associated': _score_programming_seat.get('associated'),
        'associated_with_operations': _score_programming_seat.get('associated_with_operations'),
        'totals': _score_programming_seat.get('totals'),
        'voucher_set': _voucher_report.get('voucher_set'),
        # 'choices_account': cash_set,
        'company_rotation_obj': company_rotation_obj
    })


def get_seat_of_floor(row=0, column=0, programming_obj=None, search_seat=None):
    seat = None
    programming_seat = None
    if search_seat.exists():
        seat = search_seat.first()
        programming_seat_set = ProgrammingSeat.objects.filter(
            programming=programming_obj,
            plan_detail=seat['id']
        ).values(
            'id',
            'parent_id',
            'status',
            'description',
            'subsidiary_than_reserve_id',
            'subsidiary_than_sold_id',
            'subsidiary_who_puts_limit_id',
            'subsidiary_than_reserve__short_name',
            'subsidiary_than_sold__short_name',
            'subsidiary_who_puts_limit__short_name',
        )
        programming_seat = programming_seat_set.first()
    return {
        'row': row,
        'column': column,
        'seat': seat,
        'programming_seat': programming_seat,
    }


def truck_dictionary(programming_obj, plan_obj):
    dictionary = []
    for row in range(1, plan_obj.rows + 1):
        _row = {
            '_column_2': [],
            '_column_4': [],
        }

        _column_2_set = PlanDetail.objects.filter(plan=plan_obj, row=row, type='S', position='I').values('id', 'name',
                                                                                                         'row',
                                                                                                         'column')
        _column_4_set = PlanDetail.objects.filter(plan=plan_obj, row=row, type='S', position='S').values('id', 'name',
                                                                                                         'row',
                                                                                                         'column')

        for column in range(1, plan_obj.columns + 1):
            search_seat = _column_2_set.filter(column=column)

            _row.get('_column_2').append(get_seat_of_floor(
                row=row, column=column, programming_obj=programming_obj, search_seat=search_seat))

        for column in range(1, plan_obj.columns + 1):
            search_seat = _column_4_set.filter(column=column)

            _row.get('_column_4').append(get_seat_of_floor(
                row=row, column=column, programming_obj=programming_obj, search_seat=search_seat))

        dictionary.append(_row)
    return dictionary


def fill_form_programming_seat(request):
    if request.method == 'GET':
        pk = request.GET.get('programming_seat', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_seat_obj.programming.company
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        tpl3 = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl3.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_correlative_document(request):
    if request.method == 'GET':
        doc_type = request.GET.get('document_type', '')
        programming_id = request.GET.get('programming_id', '')
        programming_obj = Programming.objects.get(id=programming_id)
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_obj.company
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'correlative': get_correlative_electronic_passenger(subsidiary_obj, company_rotation_obj, doc_type=doc_type),
            'serial': get_serial_subsidiary_company(subsidiary_obj, company_rotation_obj, type_document=doc_type)
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_correlative_document_commodity(request):
    if request.method == 'GET':
        doc_type = request.GET.get('document_type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        company_rotation_obj = user_obj.companyuser.company_rotation
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'correlative': get_correlative_commodity(subsidiary_obj, company_rotation_obj, doc_type=doc_type),
            'serial': get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj, company_rotation_obj=company_rotation_obj,
                                                        type_document=doc_type)
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def puts_seat_in_processing_of_sale_mode(
        programming_progenitor_obj=None,
        programming_seat_reserved=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_obj.id)

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            else:
                p = Programming.objects.filter(
                    parent=programming_progenitor_obj, subsidiary=passing_subsidiary)

            if p.exists():
                pos = ProgrammingSeat.objects.get(
                    programming=p.last(),
                    plan_detail=programming_seat_reserved.plan_detail)
                if pos.status == '9':  # olive
                    pos.status = '10'  # ocher
                elif pos.status == '1' or pos.status == '8':  # green | purple
                    pos.status = '2'  # yellow
                pos.save()


def puts_seat_in_processing_of_sale_wiht_limit_mode(
        programming_progenitor_obj=None,
        subsidiary_obj=None,
        array_venues=None,
        programming_seat_obj=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary
    subsidiary_limit_obj = programming_seat_obj.subsidiary_who_puts_limit

    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_progenitor_obj.id)
        index_limit = array_venues.index(subsidiary_limit_obj.id)
        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])
            index_passing = array_venues.index(passing_subsidiary.id)
            if index_current <= index_passing <= index_limit:
                if subsidiary_progenitor_obj == passing_subsidiary:
                    p = Programming.objects.filter(
                        id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
                else:
                    p = Programming.objects.filter(
                        parent=programming_progenitor_obj, subsidiary=passing_subsidiary)
                if p.exists():
                    pos = ProgrammingSeat.objects.get(
                        programming=p.last(),
                        plan_detail=programming_seat_obj.plan_detail)
                    if pos.status == '9':  # olive
                        pos.subsidiary_who_puts_limit = programming_seat_obj.subsidiary_who_puts_limit
                        pos.subsidiary_than_sold = programming_seat_obj.subsidiary_than_sold
                        pos.status = '10'  # ocher
                    pos.save()


def get_progenitor_and_children(programming_seat_obj=None, programming_progenitor_obj=None):
    seats = []
    has_parent = programming_progenitor_obj.has_parent()
    if not has_parent:  # is progenitor
        programming_child_set = programming_progenitor_obj.children.all()
        for programming_child_obj in programming_child_set:
            ps = programming_child_obj.programmingseat_set.filter(
                plan_detail=programming_seat_obj.plan_detail).values('id').first()
            seats.append(ps['id'])

    psp = ProgrammingSeat.objects.filter(programming=programming_progenitor_obj,
                                         plan_detail=programming_seat_obj.plan_detail).values('id').first()

    seats.append(psp['id'])
    list_object = list(seats)  # seems unnecessary
    seats_serialized = json.dumps(list_object)
    return seats_serialized


def go_processing_of_sale(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        array_venues = tour_venues(programming_progenitor_obj.path)
        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)
        # yellow
        puts_seat_in_processing_of_sale_mode(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_reserved=programming_seat_obj,
            subsidiary_obj=subsidiary_associate_leader_obj,
            array_venues=array_venues
        )
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_seat_obj.programming.company

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
            'type_document': _type,
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj)
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def go_selling_with_destination_limit(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('status', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        array_venues = tour_venues(programming_progenitor_obj.path)
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_seat_obj.programming.company

        programming_seat_obj.status = status
        programming_seat_obj.save()

        puts_seat_in_processing_of_sale_wiht_limit_mode(
            programming_progenitor_obj=programming_progenitor_obj,
            subsidiary_obj=subsidiary_obj,
            array_venues=array_venues,
            programming_seat_obj=programming_seat_obj
        )

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj)
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def puts_seat_in_reserve_mode(
        programming_progenitor_obj=None,
        programming_seat_reserved=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_obj.id)

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            else:
                p = Programming.objects.filter(
                    parent=programming_progenitor_obj, subsidiary=passing_subsidiary)

            if p.exists():
                pos = ProgrammingSeat.objects.get(
                    programming=p.last(),
                    plan_detail=programming_seat_reserved.plan_detail)
                if pos.status == '2' or pos.status == '5' or pos.status == '6':  # yellow | sky | blue
                    subsidiary_than_sold = pos.subsidiary_than_sold
                    subsidiary_who_puts_limit = pos.subsidiary_who_puts_limit
                    if subsidiary_than_sold is None and subsidiary_who_puts_limit is None:
                        pos.status = '1'  # green
                    else:
                        index_subsidiary_than_sold = array_venues.index(subsidiary_than_sold.id)
                        index_subsidiary_who_puts_limit = array_venues.index(subsidiary_who_puts_limit.id)
                        if index_subsidiary_who_puts_limit == index_current:
                            pos.status = '8'  # purple
                        elif index_current < index_subsidiary_than_sold:
                            pos.status = '9'  # olive

                    pos.description = None
                    pos.subsidiary_than_reserve = None
                    pos.save()


def go_release_seat(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_seat_obj.programming.company
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)

        array_venues = tour_venues(programming_progenitor_obj.path)
        puts_seat_in_reserve_mode(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_reserved=programming_seat_obj,
            subsidiary_obj=subsidiary_associate_leader_obj,
            array_venues=array_venues
        )

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def puts_seat_in_reserve_with_destination_limit_mode(
        programming_progenitor_obj=None,
        programming_seat_reserved=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    if subsidiary_obj.id in array_venues:

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            else:
                p = Programming.objects.filter(
                    parent=programming_progenitor_obj, subsidiary=passing_subsidiary)

            if p.exists():
                pos = ProgrammingSeat.objects.get(
                    programming=p.last(),
                    plan_detail=programming_seat_reserved.plan_detail)
                if pos.status in ['10']:  # ocher
                    pos.status = '9'  # olive
                    pos.save()


def go_release_seat_with_destination_limit(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        # company_rotation_obj = user_obj.companyuser.company_rotation
        company_rotation_obj = programming_seat_obj.programming.company
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)

        array_venues = tour_venues(programming_progenitor_obj.path)
        puts_seat_in_reserve_with_destination_limit_mode(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_reserved=programming_seat_obj,
            subsidiary_obj=subsidiary_associate_leader_obj,
            array_venues=array_venues
        )

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def go_reserve_seat_with_name(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('status', '')
        person = request.GET.get('person', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)

        programming_seat_obj.status = status
        programming_seat_obj.description = person
        programming_seat_obj.subsidiary_than_reserve = subsidiary_associate_leader_obj
        programming_seat_obj.save()

        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        array_venues = tour_venues(programming_progenitor_obj.path)
        reserve_seats_of_successors(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_reserved=programming_seat_obj,
            subsidiary_obj=subsidiary_obj,
            array_venues=array_venues
        )
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def go_reserve_seat_without_name(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('status', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)

        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)

        programming_seat_obj.status = status
        programming_seat_obj.subsidiary_than_reserve = subsidiary_associate_leader_obj
        programming_seat_obj.save()

        array_venues = tour_venues(programming_progenitor_obj.path)
        reserve_seats_of_successors(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_reserved=programming_seat_obj,
            subsidiary_obj=subsidiary_obj,
            array_venues=array_venues
        )

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def puts_seat_cancelled(
        programming_progenitor_obj=None,
        programming_seat_obj=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    if subsidiary_obj.id in array_venues:

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            else:
                p = Programming.objects.filter(
                    parent=programming_progenitor_obj, subsidiary=passing_subsidiary)

            if p.exists():
                pos = ProgrammingSeat.objects.get(
                    programming=p.last(),
                    plan_detail=programming_seat_obj.plan_detail)

                if pos.status in ['7', '8', '9']:  # gray | purple | olive
                    pos.subsidiary_than_sold = None
                    pos.subsidiary_who_puts_limit = None
                    pos.status = '1'  # green
                    pos.description = None
                    pos.save()


def go_cancellation_of_sale(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('status', '')
        reason = request.GET.get('reason', '')

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation

        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_seat_obj.subsidiary_than_sold = None
        programming_seat_obj.subsidiary_who_puts_limit = None
        programming_seat_obj.status = status  # green
        programming_seat_obj.save()

        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        path_progenitor_obj = programming_progenitor_obj.path
        array_venues = tour_venues(path_progenitor_obj)

        puts_seat_cancelled(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_obj=programming_seat_obj,
            subsidiary_obj=subsidiary_associate_leader_obj,
            array_venues=array_venues
        )

        order_obj = Order.objects.filter(programming_seat=programming_seat_obj).last()
        if order_obj:
            order_obj.status = 'A'
            order_obj.save()

            postponement_obj = Postponement(
                subsidiary=subsidiary_obj, user=user_obj, status='P', reason=reason, process='A')
            postponement_obj.save()

            postponement_detail_obj = PostponementDetail(postponement=postponement_obj, order=order_obj, type='A')
            postponement_detail_obj.save()

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(
                get_void_form_programming_seat(programming_seat_obj.programming, subsidiary_obj, company_rotation_obj),
                request),
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def go_postponement_of_sale(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('status', '')
        reason = request.GET.get('reason', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation

        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_seat_obj.subsidiary_than_sold = None
        programming_seat_obj.subsidiary_who_puts_limit = None
        programming_seat_obj.status = status  # green
        programming_seat_obj.save()

        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        path_progenitor_obj = programming_progenitor_obj.path
        array_venues = tour_venues(path_progenitor_obj)

        puts_seat_cancelled(
            programming_progenitor_obj=programming_progenitor_obj,
            programming_seat_obj=programming_seat_obj,
            subsidiary_obj=subsidiary_associate_leader_obj,
            array_venues=array_venues
        )

        order_obj = Order.objects.filter(programming_seat=programming_seat_obj).last()
        if order_obj:
            order_obj.status = 'A'
            order_obj.save()

            postponement_obj = Postponement(subsidiary=subsidiary_obj, user=user_obj, status='P', reason=reason,
                                            process='P')
            postponement_obj.save()

            postponement_detail_obj = PostponementDetail(postponement=postponement_obj, order=order_obj, type='A')
            postponement_detail_obj.save()

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(
                get_void_form_programming_seat(programming_seat_obj.programming, subsidiary_obj, company_rotation_obj),
                request),
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_rendered_seat(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        programming_seat = ProgrammingSeat.objects.filter(
            id=int(pk),
        ).values(
            'id',
            'parent_id',
            'status',
            'description',
            'programming_id',
            'plan_detail_id',
            'subsidiary_than_reserve_id',
            'subsidiary_than_sold_id',
            'subsidiary_who_puts_limit_id',
            'subsidiary_than_reserve__short_name',
            'subsidiary_than_sold__short_name',
            'subsidiary_who_puts_limit__short_name',
        ).first()

        seat = PlanDetail.objects.filter(
            id=programming_seat['plan_detail_id']
        ).values('id', 'name', 'row', 'column').first()

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        programming_obj = Programming.objects.get(id=programming_seat['programming_id'])

        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)

        tpl = loader.get_template('comercial/seat_render.html')
        context = ({
            'seat': seat,
            'programming_seat': programming_seat,
            'subsidiary_origin': subsidiary_associate_leader_obj,
        })
        tpl2 = loader.get_template('comercial/truck_plan_score.html')
        tpl3 = loader.get_template('comercial/truck_plan_voucher.html')

        return JsonResponse({
            'programming': programming_seat['programming_id'],
            'grid': tpl.render(context, request),
            'score': tpl2.render(get_score_programming_seat(programming_obj=programming_obj,
                                                            current_subsidiary_obj=subsidiary_obj), request),
            'vouchers': tpl3.render(get_voucher_report(programming_obj=programming_obj,
                                                       current_subsidiary_obj=subsidiary_obj), request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_seat_to_reassign(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        pk = request.GET.get('pk', '')
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        other_programming_set = Programming.objects.filter(subsidiary=subsidiary_obj,
                                                           departure_date__gte=formatdate,
                                                           path=programming_seat_obj.programming.path,
                                                           status__in=['P', 'R'],
                                                           programmingseat__isnull=False,
                                                           ).distinct('id')

        programming_seat_set = ProgrammingSeat.objects.filter(
            programming=programming_seat_obj.programming, status='4'
        )

        tpl = loader.get_template('comercial/reassign_seat_form.html')
        context = ({
            'other_programming_set': other_programming_set,
            'programming_seat_set': programming_seat_set,
            'seat_obj': programming_seat_obj.plan_detail,
            'programming_seat_obj': programming_seat_obj,
        })
        return JsonResponse({
            'form': tpl.render(context, request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def puts_seat_reassigned(
        programming_progenitor_of_new_programming_seat_obj=None,
        programming_progenitor_of_old_programming_seat_obj=None,
        new_programming_seat_obj=None,
        old_programming_seat_obj=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_of_new_programming_seat_obj.subsidiary

    if subsidiary_obj.id in array_venues:

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p_new = Programming.objects.filter(
                    id=programming_progenitor_of_new_programming_seat_obj.id, subsidiary=passing_subsidiary)
                p_old = Programming.objects.filter(
                    id=programming_progenitor_of_old_programming_seat_obj.id, subsidiary=passing_subsidiary)

            else:
                p_new = Programming.objects.filter(
                    parent=programming_progenitor_of_new_programming_seat_obj, subsidiary=passing_subsidiary)
                p_old = Programming.objects.filter(
                    parent=programming_progenitor_of_old_programming_seat_obj, subsidiary=passing_subsidiary)

            if p_old.exists() and p_new.exists():

                old_pos = ProgrammingSeat.objects.get(
                    programming=p_old.first(),
                    plan_detail=old_programming_seat_obj.plan_detail)
                new_pos = ProgrammingSeat.objects.get(
                    programming=p_new.first(),
                    plan_detail=new_programming_seat_obj.plan_detail)

                if new_pos.status in ['1']:  # green
                    new_pos.subsidiary_than_sold = old_pos.subsidiary_than_sold
                    new_pos.subsidiary_who_puts_limit = old_pos.subsidiary_than_sold
                    new_pos.status = old_pos.status
                    new_pos.save()

                if old_pos.status in ['7', '8', '9']:  # gray | purple | olive
                    old_pos.subsidiary_than_sold = None
                    old_pos.subsidiary_who_puts_limit = None
                    old_pos.status = '1'
                    old_pos.description = None
                    old_pos.save()


def save_seat_to_reassign(request):
    if request.method == 'POST':
        id_current_programming_seat = int(request.POST.get('current-programming-seat'))
        id_new_programming_seat = int(request.POST.get('new-programming-seat'))

        current_programming_seat_obj = ProgrammingSeat.objects.get(id=id_current_programming_seat)
        new_programming_seat_obj = ProgrammingSeat.objects.get(id=id_new_programming_seat)

        search_order_obj = Order.objects.filter(programming_seat=current_programming_seat_obj).last()
        search_order_obj.programming_seat = new_programming_seat_obj
        search_order_obj.save()

        new_programming_seat_obj.status = '4'
        new_programming_seat_obj.subsidiary_than_sold = current_programming_seat_obj.subsidiary_than_sold
        new_programming_seat_obj.subsidiary_who_puts_limit = current_programming_seat_obj.subsidiary_who_puts_limit
        new_programming_seat_obj.save()

        current_programming_seat_obj.status = '1'
        current_programming_seat_obj.subsidiary_than_sold = None
        current_programming_seat_obj.subsidiary_who_puts_limit = None
        current_programming_seat_obj.save()

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation

        subsidiary_associate_leader_obj = get_subsidiary_associate_leader(subsidiary_obj=subsidiary_obj)
        current_programming_progenitor_obj = get_programming_progenitor(current_programming_seat_obj.programming)
        new_programming_progenitor_obj = get_programming_progenitor(new_programming_seat_obj.programming)

        current_path_progenitor_obj = current_programming_progenitor_obj.path
        new_path_progenitor_obj = new_programming_progenitor_obj.path

        current_array_venues = tour_venues(current_path_progenitor_obj)
        new_array_venues = tour_venues(new_path_progenitor_obj)

        if len(current_array_venues) == len(new_array_venues):
            puts_seat_reassigned(
                programming_progenitor_of_new_programming_seat_obj=new_programming_progenitor_obj,
                programming_progenitor_of_old_programming_seat_obj=current_programming_progenitor_obj,
                new_programming_seat_obj=new_programming_seat_obj,
                old_programming_seat_obj=current_programming_seat_obj,
                subsidiary_obj=subsidiary_associate_leader_obj,
                array_venues=current_array_venues
            )

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'old_seats': get_progenitor_and_children(
                programming_seat_obj=current_programming_seat_obj,
                programming_progenitor_obj=current_programming_progenitor_obj),
            'new_seats': get_progenitor_and_children(
                programming_seat_obj=new_programming_seat_obj,
                programming_progenitor_obj=new_programming_progenitor_obj),
            'form': tpl.render(get_void_form_programming_seat(
                current_programming_seat_obj.programming, subsidiary_obj, company_rotation_obj), request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_programming_seat_of_programming(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        status = request.GET.get('recover_with_status', '')
        programming_obj = Programming.objects.get(id=pk)
        programming_seat_set = ProgrammingSeat.objects.filter(programming=programming_obj, status=status)
        # programming_seat_serialized_data = serializers.serialize('json', programming_seat_set)

        current_path_obj = programming_obj.path
        roads = current_path_obj.pathdetail_set.all()
        destinies = []
        for road in roads:
            for destiny in road.destiny_set.all():
                destinies.append(destiny)
        destinies_serialized = serializers.serialize('json', destinies)
        ps_set = [(
            ps.pk,
            ps.plan_detail.name,
            ps.status,
        ) for ps in programming_seat_set.order_by('plan_detail__name')]

        return JsonResponse({
            'success': True,
            'programming_seat_serialized': ps_set,
            'destinies_serialized': destinies_serialized,
        })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


# def get_data_programming_seat(programming_obj, programming_seat_obj=None, subsidiary_obj=None):
#     context = ({
#         'dictionary': truck_dictionary(programming_obj, programming_obj.truck.plan),
#         'serial': subsidiary_obj.serial_two,
#         'seat': programming_seat_obj,
#         'correlative': get_correlative_passenger(subsidiary_obj.serial_two, 'B'),
#     })
#     return context


def get_void_form_programming_seat(programming_obj=None, subsidiary_obj=None, company_rotation_obj=None):
    _serial = get_serial_subsidiary_company(subsidiary_obj=subsidiary_obj,
                                            company_rotation_obj=company_rotation_obj, type_document='T')
    _correlative = get_correlative_electronic_passenger(subsidiary_obj=subsidiary_obj, company_rotation_obj=company_rotation_obj, doc_type='T')

    context = ({
        'seat': None,
        'serial': _serial,
        'path_obj': programming_obj.path,
        'circles': programming_obj.path.pathdetail_set.count() + 1,
        'order_obj': None,
        'correlative': _correlative,
        'destinies': None,
        'programming_seat_obj': None,
        'passenger_obj': None,
        'passenger_type_obj': None,
        'passenger_age': '',
        'entity_obj': None,
        'entity_address_obj': None,
        'entity_type_obj': None
    })
    return context


def get_form_programming_seat(programming_seat_obj=None, subsidiary_obj=None, company_rotation_obj=None, type_document=None):
    programming_seat_obj = ProgrammingSeat.objects.get(id=programming_seat_obj.id)
    order_obj = None
    passenger_obj = None
    passenger_type_obj = None
    entity_obj = None
    entity_address_obj = None
    entity_type_obj = None
    passenger_age = None
    current_path_obj = None
    ps = None
    _serial = ''
    _correlative = ''
    _status = programming_seat_obj.status
    if _status in ['4', '7', '8']:  # red | gray | purple
        if _status == '4':  # red
            ps = programming_seat_obj
            current_path_obj = ps.programming.path

        elif _status == '7' or _status == '8':  # gray | purple
            ps = programming_seat_obj.parent
            current_path_obj = ps.programming.path

        order_obj = Order.objects.filter(programming_seat=ps).exclude(status='A').last()

        if order_obj is not None:
            _serial = order_obj.serial
            _correlative = order_obj.correlative_sale

            entity_set = order_obj.orderaction_set.filter(type='E')
            if entity_set.exists():
                passenger_obj = order_obj.orderaction_set.filter(type='P').first().client
                passenger_type_obj = ClientType.objects.filter(client=passenger_obj).last()
                entity_obj = entity_set.first().client
                entity_address_obj = ClientAddress.objects.filter(client=entity_obj).last()
                entity_type_obj = ClientType.objects.filter(client=entity_obj, document_type_id='06').last()
            else:
                passenger_obj = order_obj.client
                passenger_type_obj = ClientType.objects.filter(client=passenger_obj).last()

            # if passenger_obj.birthday is not None:
            #     passenger_age = calculate_age(passenger_obj.birthday)
    else:
        current_path_obj = programming_seat_obj.programming.path
        _serial = get_serial_subsidiary_company(subsidiary_obj=subsidiary_obj,
                                                company_rotation_obj=company_rotation_obj,
                                                type_document=type_document)
        _correlative = get_correlative_electronic_passenger(
            subsidiary_obj=subsidiary_obj,
            company_rotation_obj=company_rotation_obj,
            doc_type=type_document
        )

    destinies = []
    if _status in ['9', '10']:  # olive | ocher
        subsidiary_limit_obj = programming_seat_obj.subsidiary_who_puts_limit
        programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
        path_progenitor_obj = programming_progenitor_obj.path
        allowed = False
        for pd in path_progenitor_obj.pathdetail_set.all():
            if pd.get_origin() == subsidiary_obj:
                allowed = True
            elif pd.get_origin() == subsidiary_limit_obj:
                break
            if allowed:
                for destiny in pd.destiny_set.all():
                    destinies.append(destiny)
    else:
        roads = current_path_obj.pathdetail_set.all()
        for road in roads:
            for destiny in road.destiny_set.all():
                destinies.append(destiny)

    # Obtener todos los orígenes disponibles
    origins = Origin.objects.all()

    context = ({
        'seat': programming_seat_obj,
        'serial': _serial,
        'path_obj': programming_seat_obj.programming.path,
        'circles': programming_seat_obj.programming.path.pathdetail_set.count() + 1,
        'order_obj': order_obj,
        'correlative': _correlative,
        'destinies': destinies,
        'origins': origins,
        'subsidiary_obj': subsidiary_obj,
        'programming_seat_obj': programming_seat_obj,
        'passenger_obj': passenger_obj,
        'passenger_type_obj': passenger_type_obj,
        'passenger_age': passenger_age,
        'entity_obj': entity_obj,
        'entity_address_obj': entity_address_obj,
        'entity_type_obj': entity_type_obj
    })
    return context


def get_vouchers_by_subsidiary(subsidiary_obj=None, programming_obj=None):
    subsidiary_associated = None
    order_set = Order.objects.filter(subsidiary=subsidiary_obj, status__in=['P', 'C'],
                                     programming_seat__programming=programming_obj)
    if order_set:
        vouchers = []
        for order_obj in order_set:
            _voucher_type = 'T'
            _voucher_serial = order_obj.serial
            _voucher_number = str(order_obj.correlative_sale).zfill(6)
            item = {
                'date': order_obj.create_at,
                'voucher_type': _voucher_type,
                'voucher_serial': _voucher_serial,
                'voucher_number': _voucher_number,
                'passenger': order_obj.client.names,
                'destiny': order_obj.destiny.name,
                'price': order_obj.total,
                'paid': order_obj.paid,
                'turned': order_obj.turned,
                'seat': order_obj.programming_seat.plan_detail.name,
            }
            vouchers.append(item)
        subsidiary_associated = {
            'subsidiary': subsidiary_obj,
            'vouchers': vouchers,
        }
    return subsidiary_associated


def get_summary(totals=None):
    counter_dict = Counter(totals)
    sum_quantity = 0
    sum_product = 0
    values = []
    for total, quantity in counter_dict.items():
        item = {
            'quantity': quantity,
            'total': total,
            'product': total * quantity,
        }
        values.append(item)
        sum_quantity = sum_quantity + quantity
        sum_product = sum_product + total * quantity
    return {
        'sum_quantity': sum_quantity,
        'sum_product': sum_product,
        'values': values,
    }


def get_settlement_by_subsidiary(subsidiary_obj=None, programming_obj=None):
    subsidiary_associated = None
    order_set = Order.objects.filter(subsidiary=subsidiary_obj, status__in=['P', 'C'],
                                     programming_seat__programming=programming_obj)
    if order_set:
        totals = order_set.values_list('total', flat=True)
        totals = list(totals)
        context = get_summary(totals)
        subsidiary_associated = {
            'subsidiary': subsidiary_obj,
            'sum_quantity': context.get('sum_quantity'),
            'sum_product': context.get('sum_product'),
            'totals': totals,
            'values': context.get('values'),
        }
    return subsidiary_associated


def get_money_flows_by_subsidiary(subsidiary_obj=None, programming_obj=None):
    subsidiary_associated = None
    cash_flow_set = CashFlow.objects.filter(cash__subsidiary=subsidiary_obj, programming=programming_obj)
    if cash_flow_set:
        operations = cash_flow_set.values('transaction_date', 'description', 'type', 'total')
        subsidiary_associated = {
            'subsidiary': subsidiary_obj,
            'operations': operations,
        }
    return subsidiary_associated


def get_voucher_report(programming_obj=None, current_subsidiary_obj=None):
    subsidiary_associated_set = AssociateDetail.objects.filter(associate__subsidiary=programming_obj.subsidiary)
    vouchers_of_associated = []
    if subsidiary_associated_set:
        for sa in subsidiary_associated_set:
            subsidiary_associated = get_vouchers_by_subsidiary(subsidiary_obj=sa.subsidiary,
                                                               programming_obj=programming_obj)
            if subsidiary_associated:
                vouchers_of_associated.append(subsidiary_associated)

    subsidiary_associated = get_vouchers_by_subsidiary(subsidiary_obj=programming_obj.subsidiary,
                                                       programming_obj=programming_obj)
    if subsidiary_associated:
        vouchers_of_associated.append(subsidiary_associated)

    context = ({
        'programming_obj': programming_obj,
        'voucher_set': vouchers_of_associated,
    })
    return context


def get_score_programming_seat(programming_obj=None, current_subsidiary_obj=None):
    totals_summary = []
    programming_seat_set = ProgrammingSeat.objects.filter(programming=programming_obj)
    quantity_sold = programming_seat_set.filter(status='4').count()
    quantity_free = programming_seat_set.filter(status='1').count()
    quantity_reserved = programming_seat_set.filter(Q(status='5') | Q(status='6')).count()

    subsidiary_associated_set = AssociateDetail.objects.filter(associate__subsidiary=programming_obj.subsidiary)
    associated = []
    associated_with_operations = []
    if subsidiary_associated_set:
        for sa in subsidiary_associated_set:
            subsidiary_associated = get_settlement_by_subsidiary(
                subsidiary_obj=sa.subsidiary, programming_obj=programming_obj)
            if subsidiary_associated:
                associated.append(subsidiary_associated)
                totals_summary = totals_summary + subsidiary_associated.get('totals')

            subsidiary_associated_has_operations = get_money_flows_by_subsidiary(
                subsidiary_obj=sa.subsidiary, programming_obj=programming_obj)
            if subsidiary_associated_has_operations:
                associated_with_operations.append(subsidiary_associated_has_operations)

    subsidiary_associated = get_settlement_by_subsidiary(subsidiary_obj=programming_obj.subsidiary,
                                                         programming_obj=programming_obj)
    if subsidiary_associated:
        associated.append(subsidiary_associated)
        totals_summary = totals_summary + subsidiary_associated.get('totals')

    _summaries = get_summary(totals_summary)

    subsidiary_associated_has_operations = get_money_flows_by_subsidiary(
        subsidiary_obj=programming_obj.subsidiary, programming_obj=programming_obj)
    if subsidiary_associated_has_operations:
        associated_with_operations.append(subsidiary_associated_has_operations)

    context = ({
        'programming_obj': programming_obj,
        'quantity_sold': quantity_sold,
        'quantity_free': quantity_free,
        'quantity_reserved': quantity_reserved,
        'associated': associated,
        'associated_with_operations': associated_with_operations,
        'totals': _summaries,
    })
    return context


def tour_venues(path_obj):
    path_details = path_obj.pathdetail_set.all()
    points = []
    for pd in path_details:
        _point = pd.get_origin().id
        points.append(_point)
    points.append(path_obj.get_last_point().id)
    return points


def get_programming_progenitor(programming_obj=None):
    programming_progenitor = programming_obj
    if programming_obj.parent is not None:
        programming_progenitor = programming_obj.parent
    return programming_progenitor


def puts_seats_disabled(
        programming_progenitor_obj=None,
        subsidiary_than_sold_obj=None,
        programming_seat_sold_obj=None,
        subsidiary_predecessor_obj=None,
        points_arr=None
):
    allowed = False

    for i in reversed(range(len(points_arr))):
        if points_arr[i] == subsidiary_predecessor_obj.id:
            allowed = True
        if allowed:
            passing_subsidiary = Subsidiary.objects.get(id=points_arr[i])
            programming_of_predecessor = Programming.objects.filter(
                parent=programming_progenitor_obj, subsidiary=passing_subsidiary)
            if subsidiary_than_sold_obj == passing_subsidiary:
                break
            if programming_of_predecessor.exists():
                psp = ProgrammingSeat.objects.get(
                    programming=programming_of_predecessor.last(),
                    plan_detail=programming_seat_sold_obj.plan_detail)
                _status = psp.status
                if _status in ['1', '2', '8', '9', '10']:  # green | yellow | purple | olive | gray
                    psp.status = '7'  # gray
                    psp.subsidiary_than_sold = programming_seat_sold_obj.subsidiary_than_sold
                    psp.subsidiary_who_puts_limit = programming_seat_sold_obj.subsidiary_who_puts_limit
                    psp.save()


def puts_seats_with_destination_limit(
        programming_progenitor_obj=None,
        subsidiary_than_sold_obj=None,
        programming_seat_sold_obj=None,
        points_arr=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    allowed = False

    for i in reversed(range(len(points_arr))):
        if points_arr[i] == subsidiary_than_sold_obj.id:
            allowed = True
        if allowed:
            passing_subsidiary = Subsidiary.objects.get(id=points_arr[i])
            programming_of_predecessor = Programming.objects.filter(
                parent=programming_progenitor_obj, subsidiary=passing_subsidiary)
            if subsidiary_than_sold_obj == passing_subsidiary:
                continue
            if subsidiary_progenitor_obj == passing_subsidiary:
                programming_of_predecessor = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            if programming_of_predecessor.exists():
                psp = ProgrammingSeat.objects.get(
                    programming=programming_of_predecessor.last(),
                    plan_detail=programming_seat_sold_obj.plan_detail)
                _status = psp.status
                if _status in ['1', '2', '8', '9', '10']:  # green | yellow | purple | olive | ocher
                    psp.status = '9'  # olive
                    psp.subsidiary_than_sold = programming_seat_sold_obj.subsidiary_than_sold
                    psp.subsidiary_who_puts_limit = programming_seat_sold_obj.subsidiary_than_sold
                    psp.save()


def reserve_seats_of_successors(
        programming_progenitor_obj=None,
        programming_seat_reserved=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary

    if subsidiary_obj.id in array_venues:
        index_current = array_venues.index(subsidiary_obj.id)

        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])

            if subsidiary_progenitor_obj == passing_subsidiary:
                p = Programming.objects.filter(
                    id=programming_progenitor_obj.id, subsidiary=passing_subsidiary)
            else:
                p = Programming.objects.filter(
                    parent=programming_progenitor_obj, subsidiary=passing_subsidiary)
            if p.exists():
                pos = ProgrammingSeat.objects.get(
                    programming=p.last(),
                    plan_detail=programming_seat_reserved.plan_detail)
                if pos.status in ['1', '8', '9']:  # green | purple | olive
                    pos.status = programming_seat_reserved.status  # blue ! sky blue
                    pos.subsidiary_than_reserve = programming_seat_reserved.subsidiary_than_reserve
                    pos.description = programming_seat_reserved.description
                    pos.save()


def puts_seat_ready_to_be_released_in_next_successor(
        programming_progenitor_obj=None,
        programming_seat_predecessor_obj=None,
        subsidiary_successor_obj=None,
        subsidiary_obj=None,
        array_venues=None
):
    subsidiary_progenitor_obj = programming_progenitor_obj.subsidiary
    if subsidiary_obj.id in array_venues:
        for i in range(0, len(array_venues), 1):
            passing_subsidiary = Subsidiary.objects.get(id=array_venues[i])
            programming_of_successor = Programming.objects.filter(
                parent=programming_progenitor_obj, subsidiary=passing_subsidiary)
            if programming_of_successor.exists():
                pss = ProgrammingSeat.objects.get(
                    programming=programming_of_successor.last(),
                    plan_detail=programming_seat_predecessor_obj.plan_detail)
                _status = pss.status
                if _status in ['1', '2', '8']:  # green | yellow | purple
                    if subsidiary_successor_obj == passing_subsidiary:
                        pss.status = '8'  # purple
                        pss.subsidiary_than_sold = programming_seat_predecessor_obj.subsidiary_than_sold
                        pss.subsidiary_who_puts_limit = programming_seat_predecessor_obj.subsidiary_who_puts_limit
                        pss.save()
                    else:
                        pss.status = '1'  # green
                        pss.save()


def sell_seat(programming_seat_id=0, destiny_id=0, subsidiary_obj=None):
    destiny_obj = Destiny.objects.get(id=int(destiny_id))
    successor = destiny_obj.get_final_subsidiary()
    predecessor = destiny_obj.get_initial_subsidiary()

    # red
    programming_seat_obj = ProgrammingSeat.objects.get(pk=programming_seat_id)
    programming_seat_obj.status = '4'
    programming_seat_obj.subsidiary_who_puts_limit = successor
    programming_seat_obj.subsidiary_than_sold = subsidiary_obj
    programming_seat_obj.save()

    programming_progenitor_obj = get_programming_progenitor(programming_seat_obj.programming)
    path_progenitor_obj = programming_progenitor_obj.path
    points_arr = tour_venues(path_progenitor_obj)

    # purple
    puts_seat_ready_to_be_released_in_next_successor(
        programming_progenitor_obj=programming_progenitor_obj,
        programming_seat_predecessor_obj=programming_seat_obj,
        subsidiary_successor_obj=successor,
        subsidiary_obj=subsidiary_obj,
        array_venues=points_arr
    )
    # gray
    puts_seats_disabled(
        programming_progenitor_obj=programming_progenitor_obj,
        subsidiary_than_sold_obj=subsidiary_obj,
        programming_seat_sold_obj=programming_seat_obj,
        subsidiary_predecessor_obj=predecessor,
        points_arr=points_arr
    )
    # olive
    puts_seats_with_destination_limit(
        programming_progenitor_obj=programming_progenitor_obj,
        subsidiary_than_sold_obj=subsidiary_obj,
        programming_seat_sold_obj=programming_seat_obj,
        points_arr=points_arr
    )
    return programming_seat_obj


def create_order_passenger(request):
    if request.method == 'GET':
        orders_request = request.GET.get('data', '')
        data_orders = json.loads(orders_request)
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation
        client_obj = None
        client_nro_document_natural = str(data_orders["Client_Nro_document"]).strip()  # Document number passenger
        client_document_type = str(data_orders["Document_type_client"])  # type document passenger
        client_name1 = str(data_orders["Client_name"]).strip()  # Passenger Name

        client_nro_document_business = str(data_orders["Client_Nro_document_2"]).strip()

        client_document_type_obj = DocumentType.objects.get(id=client_document_type)
        phone = str(data_orders["Phone"]).strip()
        nationality = str(data_orders["Nationality"])

        # correlative = str(data_orders["Correlative"])
        _now = datetime.now()
        _year = _now.year
        _birthday = None
        nationality_obj = None

        if nationality != 'None':
            nationality_obj = Nationality.objects.get(id=nationality)

        client_set = Client.objects.filter(clienttype__document_number=client_nro_document_natural)

        if client_set.count() > 0:
            client_obj = client_set.first()
            if client_obj.names != client_name1:
                client_obj.names = client_name1
            client_obj.phone = phone
            client_obj.save()
        else:
            client_names_search = Client.objects.filter(names=client_name1.upper())
            if client_names_search.exists():
                data = {'error': "NOMBRE YA REGISTRADO EN LA BASE DE DATOS, INGRESE OTRO NOMBRE O AGREGUE UN APELLIDO MAS"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

            client_obj = Client(
                names=client_name1.upper(),
                phone=phone,
                nationality=nationality_obj,
            )
            client_obj.save()

            client_type_obj = ClientType(
                document_number=client_nro_document_natural,
                client=client_obj,
                document_type=client_document_type_obj
            )
            client_type_obj.save()

        if client_nro_document_business:
            client_business_obj = Client.objects.get(clienttype__document_number=client_nro_document_business)
        else:
            client_business_obj = ''

        serial = str(data_orders["Serial"])
        destiny = int(data_orders["Destiny"])
        origin = int(data_orders["Origin"]) if "Origin" in data_orders else None
        programming_seat_id = int(data_orders["Programming_seat_id"])
        amount = str(data_orders["Amount"])

        paid = 0
        turned = 0
        if 'Paid' in data_orders:
            paid = str(data_orders["Paid"])
        if 'Turned' in data_orders:
            turned = str(data_orders["Turned"])

        type_bill = str(data_orders["Type_bill"])
        is_demo = bool(int(data_orders["Demo"]))
        show_original_name = bool(int(data_orders["ShowOriginalName"]))

        destiny_obj = Destiny.objects.get(id=destiny)
        origin_obj = None
        if origin:
            origin_obj = Origin.objects.get(id=origin)

        programming_seat_obj = sell_seat(
            programming_seat_id=programming_seat_id,
            destiny_id=destiny,
            subsidiary_obj=subsidiary_obj
        )
        programming_obj = programming_seat_obj.programming
        programming_progenitor_obj = get_programming_progenitor(programming_obj)

        correlative = get_correlative_electronic_passenger(subsidiary_obj=subsidiary_obj, company_rotation_obj=programming_obj.company, doc_type=type_bill)

        traslate_date = programming_obj.departure_date
        msg_sunat = ''
        sunat_pdf = ''

        if is_demo:
            value_is_demo = 'D'
        else:
            value_is_demo = 'P'

        order_obj = Order(
            traslate_date=traslate_date,
            serial=serial,
            user=user_obj,
            client=client_obj,
            subsidiary=subsidiary_obj,
            correlative_sale=correlative,
            type_order='P',
            status='C',
            programming_seat=programming_seat_obj,
            destiny=destiny_obj,
            origin=origin_obj,
            total=amount,
            paid=paid,
            turned=turned,
            company=programming_obj.company,
            type_document=type_bill,
            show_original_name=show_original_name
        )
        order_obj.save()

        update_correlative_passenger(order_obj=order_obj)

        if client_nro_document_business:
            order_action_sender_obj = OrderAction(
                client=client_obj,
                order=order_obj,
                type='P'
            )
            order_action_sender_obj.save()

            order_action_addressee_obj = OrderAction(
                client=client_business_obj,
                order=order_obj,
                type='E'
            )
            order_action_addressee_obj.save()

        if type_bill == 'F':
            '''serie = order_obj.serial
            order_bill_obj = OrderBill(order=order_obj,
                                       serial='F' + serie[1:],
                                       type='1',
                                       # sunat_status=r.get('aceptada_por_sunat'),
                                       # sunat_description=r.get('sunat_description'),
                                       user=user_obj,
                                       # sunat_enlace_pdf=r.get('enlace_del_pdf'),
                                       # code_qr=r.get('cadena_para_codigo_qr'),
                                       # code_hash=r.get('codigo_hash'),
                                       n_receipt=int(order_obj.correlative_sale),
                                       status='E',
                                       created_at=order_obj.create_at,
                                       is_demo='D'
                                       )
            order_bill_obj.save()'''
            # r = send_bill_passenger(order_obj.id)
            # msg_sunat = r.get('sunat_description')
            # sunat_pdf = r.get('enlace_del_pdf')
            # codigo_hash = r.get('codigo_hash')
            # if codigo_hash:
            #     order_bill_obj = OrderBill(order=order_obj,
            #                                serial=r.get('serie'),
            #                                type=r.get('tipo_de_comprobante'),
            #                                sunat_status=r.get('aceptada_por_sunat'),
            #                                sunat_description=r.get('sunat_description'),
            #                                user=user_obj,
            #                                sunat_enlace_pdf=r.get('enlace_del_pdf'),
            #                                code_qr=r.get('cadena_para_codigo_qr'),
            #                                code_hash=r.get('codigo_hash'),
            #                                n_receipt=r.get('numero'),
            #                                status='E',
            #                                created_at=order_obj.create_at,
            #                                is_demo=value_is_demo
            #                                )
            #     order_bill_obj.save()
            r = send_bill_ticket_fact(request, order_obj.id)
            if r.get('success'):
                order_bill_obj = OrderBill(order=order_obj,
                                           serial=r.get('serie'),
                                           type=r.get('tipo_de_comprobante'),
                                           user=user_obj,
                                           n_receipt=r.get('numero'),
                                           status='E',
                                           created_at=order_obj.create_at,
                                           invoice_id=r.get('operationId'),
                                           company=order_obj.company
                                           )
                order_bill_obj.save()
            else:
                objects_to_delete = OrderDetail.objects.filter(order=order_obj)
                objects_to_delete.delete()
                order_obj.delete()
                if r.get('errors'):
                    data = {'error': str(r.get('errors'))}
                elif r.get('error'):
                    data = {'error': str(r.get('error'))}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        elif type_bill == 'B':
            '''serie = order_obj.serial
            order_bill_obj = OrderBill(order=order_obj,
                                       serial='B' + serie[1:],
                                       type='2',
                                       # sunat_status=r.get('aceptada_por_sunat'),
                                       # sunat_description=r.get('sunat_description'),
                                       user=user_obj,
                                       # sunat_enlace_pdf=r.get('enlace_del_pdf'),
                                       # code_qr='code',
                                       # code_hash=r.get('codigo_hash'),
                                       n_receipt=int(order_obj.correlative_sale),
                                       status='E',
                                       created_at=order_obj.create_at,
                                       is_demo='D'
                                       )
            order_bill_obj.save()'''
            # r = send_receipt_passenger(order_obj.id)
            # msg_sunat = r.get('sunat_description')
            # sunat_pdf = r.get('enlace_del_pdf')
            # codigo_hash = r.get('codigo_hash')
            # if codigo_hash:
            #     order_bill_obj = OrderBill(order=order_obj,
            #                                serial=r.get('serie'),
            #                                type=r.get('tipo_de_comprobante'),
            #                                sunat_status=r.get('aceptada_por_sunat'),
            #                                sunat_description=r.get('sunat_description'),
            #                                user=user_obj,
            #                                sunat_enlace_pdf=r.get('enlace_del_pdf'),
            #                                code_qr=r.get('cadena_para_codigo_qr'),
            #                                code_hash=r.get('codigo_hash'),
            #                                n_receipt=r.get('numero'),
            #                                status='E',
            #                                created_at=order_obj.create_at,
            #                                is_demo=value_is_demo
            #                                )
            #     order_bill_obj.save()
                # print_ticket_order_passenger(order_obj.id)
            r = send_receipt_passenger_fact(request, order_obj.id)
            if r.get('success'):
                order_bill_obj = OrderBill(order=order_obj,
                                           serial=r.get('serie'),
                                           type=r.get('tipo_de_comprobante'),
                                           user=user_obj,
                                           n_receipt=r.get('numero'),
                                           status='E',
                                           created_at=order_obj.create_at,
                                           invoice_id=r.get('operationId'),
                                           company=order_obj.company
                                           )
                order_bill_obj.save()
            else:
                objects_to_delete = OrderDetail.objects.filter(order=order_obj)
                objects_to_delete.delete()
                order_obj.delete()
                if r.get('errors'):
                    data = {'error': str(r.get('errors'))}
                elif r.get('error'):
                    data = {'error': str(r.get('error'))}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        register_in_cash_flow(
            order_obj=order_obj, subsidiary_obj=subsidiary_obj, user_obj=user_obj, programming_obj=programming_obj,
            type_bill=type_bill, amount=amount
        )

        user_subsidiary_subsidiary = None
        user_subsidiary_office = None
        user_subsidiary_printer = None
        user_subsidiary_set = UserSubsidiary.objects.filter(user=user_obj)
        if user_subsidiary_set.exists():
            user_subsidiary_obj = user_subsidiary_set.last()
            user_subsidiary_subsidiary = str(user_subsidiary_obj.subsidiary.id)
            user_subsidiary_office = user_subsidiary_obj.office
            user_subsidiary_printer = user_subsidiary_obj.printer

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'order_id': order_obj.id,
            'type_document': order_obj.type_document,
            'serial': order_obj.serial,
            'correlative': order_obj.correlative_sale,
            'userOffice': user_subsidiary_office,
            'userPrinter': user_subsidiary_printer,
            'userSubsidiary': user_subsidiary_subsidiary,
            'seats': get_progenitor_and_children(
                programming_seat_obj=programming_seat_obj, programming_progenitor_obj=programming_progenitor_obj),
            'form': tpl.render(get_void_form_programming_seat(programming_obj, subsidiary_obj, company_rotation_obj),
                               request),
        }, status=HTTPStatus.OK)

    return JsonResponse({
        'message': 'Se guardo el Bolete de Viaje Correctamente.',
    }, status=HTTPStatus.OK)


def register_in_cash_flow(order_obj=None, subsidiary_obj=None, user_obj=None, programming_obj=None, type_bill=None, amount=None):
    # GUARDANDO LA PASAJERO EN LA CAJA
    cash_obj = Cash.objects.filter(cash_type='B', subsidiary=subsidiary_obj).last()

    register_date = utc_to_local(order_obj.create_at)
    formatdate = register_date.strftime("%Y-%m-%d")

    cashflow_set = CashFlow.objects.filter(cash=cash_obj, transaction_date=formatdate, type='A')

    serial_description_cash = 'PAGO DEL BOLETO DE VIAJE {}-{}'.format(order_obj.serial,
                                                                      order_obj.correlative_sale.zfill(6))
    document_type_attached = 'T'
    if type_bill == 'F':
        document_type_attached = 'F'
    elif type_bill == 'B':
        document_type_attached = 'B'

    if not cashflow_set.exists():
        last_cash_flow_opening_set = CashFlow.objects.filter(cash=cash_obj, type='A').order_by('id')
        if last_cash_flow_opening_set:  # search last closing
            cash_flow_opening_obj = last_cash_flow_opening_set.last()
            last_cash_flow_is_closed = CashFlow.objects.filter(type='C', cash=cash_obj,
                                                               transaction_date=cash_flow_opening_obj.transaction_date)
            if not last_cash_flow_is_closed.exists():
                cash_flow_obj = CashFlow(
                    transaction_date=cash_flow_opening_obj.transaction_date,
                    cash=cash_obj,
                    description='CIERRE',
                    total=decimal.Decimal(cash_flow_opening_obj.return_balance()),
                    type='C')
                cash_flow_obj.save()

            current_balance = cash_obj.current_balance()
        else:  # create first opening record
            current_balance = cash_obj.initial

        cash_flow_obj = CashFlow(
            transaction_date=formatdate,
            cash=cash_obj,
            description='APERTURA',
            total=decimal.Decimal(current_balance),
            type='A')
        cash_flow_obj.save()

    save_cash_flow(
        cash_obj=cash_obj, order_obj=order_obj, user_obj=user_obj,
        cash_flow_transact_date=formatdate,
        cash_flow_description=str(serial_description_cash),
        cash_flow_type='E',
        cash_flow_programming=programming_obj,
        document_type_attached=document_type_attached,
        cash_flow_total=amount
    )


def get_create_legacy_programming_form(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        programming_obj = Programming.objects.get(id=int(pk))

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        path_obj = programming_obj.path
        take_path_detail = False
        subsidiary_destinies = []
        for pd in path_obj.pathdetail_set.all():
            if pd.get_origin() == subsidiary_obj:
                take_path_detail = True
            if take_path_detail:
                subsidiary_destinies.append(pd.get_destiny())

        t = loader.get_template('comercial/legacy_programming_modal_form.html')
        c = ({
            'programming_obj': programming_obj,
            'subsidiary_origin': subsidiary_obj,
            'subsidiary_destinies': subsidiary_destinies,
            'choices_turn': Programming._meta.get_field('turn').choices,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def create_path_legacy(subsidiary_origin_obj=None, subsidiary_destiny_obj=None, legacy_programming=None):
    if subsidiary_origin_obj.short_name is None:
        origin_short_name = subsidiary_origin_obj.name
    else:
        origin_short_name = subsidiary_origin_obj.short_name

    if subsidiary_destiny_obj.short_name is None:
        destiny_short_name = subsidiary_destiny_obj.name
    else:
        destiny_short_name = subsidiary_destiny_obj.short_name

    new_path_obj = Path(
        name=origin_short_name + ' - ' + destiny_short_name,
        subsidiary=subsidiary_origin_obj,
        type=legacy_programming.path.type
    )
    new_path_obj.save()
    lp_path = legacy_programming.path
    road_included = False
    counter_stopping = 1
    for path_detail in lp_path.pathdetail_set.all():
        if path_detail.get_origin() == subsidiary_origin_obj:
            road_included = True
        if road_included:
            new_path_detail_obj = PathDetail(path=new_path_obj, stopping=counter_stopping)
            new_path_detail_obj.save()
            counter_stopping = counter_stopping + 1
            new_path_subsidiary_origin_obj = PathSubsidiary(
                path_detail=new_path_detail_obj, subsidiary=path_detail.get_origin(), type='O'
            )
            new_path_subsidiary_origin_obj.save()
            new_path_subsidiary_destiny_obj = PathSubsidiary(
                path_detail=new_path_detail_obj, subsidiary=path_detail.get_destiny(), type='D'
            )
            new_path_subsidiary_destiny_obj.save()
            destiny_set = path_detail.destiny_set.all()
            for destiny in destiny_set:
                destiny_obj = Destiny(name=destiny.name, path_detail=new_path_detail_obj)
                destiny_obj.save()
        if path_detail.get_destiny() == subsidiary_destiny_obj:
            road_included = False
    return new_path_obj


def create_programming_from_legacy_programming(subsidiary_origin_obj=None, turn=None, path_obj=None,
                                               legacy_programming=None):
    new_programming_obj = Programming(
        departure_date=legacy_programming.departure_date,
        truck=legacy_programming.truck,
        towing=legacy_programming.towing,
        subsidiary=subsidiary_origin_obj,
        turn=turn,
        path=path_obj,
        status='P',
        parent=legacy_programming
    )
    new_programming_obj.save()
    set_employee_pilot_obj = SetEmployee(
        programming=new_programming_obj,
        employee=legacy_programming.get_pilot(),
        function='P',
    )
    set_employee_pilot_obj.save()

    if legacy_programming.get_copilot() is not None:
        set_employee_copilot_obj = SetEmployee(
            programming=new_programming_obj,
            employee=legacy_programming.get_copilot(),
            function='C',
        )
        set_employee_copilot_obj.save()
    return new_programming_obj


def new_legacy_programming(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        lp_id = request.POST.get('programming')
        new_turn = request.POST.get('turn', '')
        subsidiary_destiny_id = request.POST.get('subsidiary-destiny', '')
        subsidiary_destiny_obj = Subsidiary.objects.get(id=int(subsidiary_destiny_id))

        path_set = Path.objects.filter(subsidiary=subsidiary_obj)
        lp = Programming.objects.get(id=int(lp_id))

        if path_set:  # search path & create programming
            searched_path = None
            for p in path_set:
                if p.get_last_point() == subsidiary_destiny_obj:
                    searched_path = p
                    break
            if searched_path is None:
                searched_path = create_path_legacy(
                    subsidiary_origin_obj=subsidiary_obj,
                    subsidiary_destiny_obj=subsidiary_destiny_obj,
                    legacy_programming=lp
                )
            new_programming_obj = create_programming_from_legacy_programming(
                subsidiary_origin_obj=subsidiary_obj,
                turn=new_turn,
                path_obj=searched_path,
                legacy_programming=lp
            )

        else:  # create path & programming
            new_path = create_path_legacy(
                subsidiary_origin_obj=subsidiary_obj,
                subsidiary_destiny_obj=subsidiary_destiny_obj,
                legacy_programming=lp
            )
            new_programming_obj = create_programming_from_legacy_programming(
                subsidiary_origin_obj=subsidiary_obj,
                turn=new_turn,
                path_obj=new_path,
                legacy_programming=lp
            )

        return JsonResponse({
            'success': True,
            'programming_id': new_programming_obj.id,
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)


def get_postponements(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        postponement_set = Postponement.objects.all()
        return render(request, 'comercial/postponement_list.html', {
            'postponement_set': postponement_set,
            'formatdate': formatdate,
        })
    elif request.method == 'POST':
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        if start_date == end_date:
            postponement_set = Postponement.objects.filter(created_at__date=start_date, subsidiary=subsidiary_obj)
        else:
            postponement_set = Postponement.objects.filter(created_at__date__range=[start_date, end_date],
                                                           subsidiary=subsidiary_obj)

        if postponement_set:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        status = Postponement._meta.get_field('status').choices

        tpl = loader.get_template('comercial/postponement_grid_list.html')
        context = ({
            'postponement_set': postponement_set,
            'status': status,
            'subsidiary_obj': subsidiary_obj,
            'has_rows': has_rows
        })

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_reschedule_form(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        pk = request.GET.get('pk', '')
        postponement_obj = Postponement.objects.get(id=int(pk))
        programming_seat_obj = postponement_obj.get_detail_aborted().order.programming_seat
        order_obj = postponement_obj.get_detail_aborted().order
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        other_programming_set = Programming.objects.filter(subsidiary=subsidiary_obj,
                                                           departure_date__gte=formatdate,
                                                           status__in=['P', 'R'],
                                                           programmingseat__isnull=False,
                                                           ).exclude(id=programming_seat_obj.programming.id).distinct(
            'id')

        tpl = loader.get_template('comercial/reschedule_seat_form.html')
        context = ({
            'other_programming_set': other_programming_set,
            'postponement_obj': postponement_obj,
            'seat_obj': programming_seat_obj.plan_detail,
            'order_obj': order_obj,
            'programming_seat_obj': programming_seat_obj,
        })
        return JsonResponse({
            'form': tpl.render(context, request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def save_seat_rescheduled(request):
    if request.method == 'POST':
        id_postponement = int(request.POST.get('postponement'))
        id_destiny = int(request.POST.get('destiny'))
        amount = decimal.Decimal(request.POST.get('cost', 0).replace(',', '.'))
        is_demo = bool(int(request.POST.get('demo', 0)))
        id_new_programming_seat = int(request.POST.get('new-programming-seat'))

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        new_programming_seat_obj = ProgrammingSeat.objects.get(id=id_new_programming_seat)
        programming_obj = new_programming_seat_obj.programming
        postponement_obj = Postponement.objects.get(id=int(id_postponement))
        old_order_obj = postponement_obj.get_detail_aborted().order
        old_order_bill_obj = old_order_obj.orderbill
        order_bill_type = 'B'
        if old_order_bill_obj.type == '1':
            order_bill_type = 'F'
        destiny_obj = Destiny.objects.get(id=id_destiny)
        traslate_date = programming_obj.departure_date
        serial = subsidiary_obj.serial_two
        correlative = get_correlative_electronic_passenger(old_order_obj.subsidiary, old_order_obj.company, old_order_obj.type_document)

        order_obj = Order(
            traslate_date=traslate_date,
            serial=serial,
            user=user_obj,
            client=old_order_obj.client,
            subsidiary=subsidiary_obj,
            correlative_sale=correlative,
            type_order='P',
            status='C',
            programming_seat=new_programming_seat_obj,
            destiny=destiny_obj,
            total=amount
        )
        order_obj.save()

        msg_sunat = ''
        sunat_pdf = ''

        if is_demo:
            value_is_demo = 'D'
        else:
            value_is_demo = 'P'

        if order_bill_type == 'F':

            # Guardando el orden action
            order_action_passenger_obj = OrderAction(
                client=old_order_obj.orderaction_set.filter(type='P').first().client,
                order=order_obj,
                type='P'
            )
            order_action_passenger_obj.save()

            order_action_entity_obj = OrderAction(
                client=old_order_obj.orderaction_set.filter(type='E').first().client,
                order=order_obj,
                type='E'
            )
            order_action_entity_obj.save()

            r = send_bill_passenger(order_obj.id)
            msg_sunat = r.get('sunat_description')
            sunat_pdf = r.get('enlace_del_pdf')
            codigo_hash = r.get('codigo_hash')
            if codigo_hash:
                order_bill_obj = OrderBill(order=order_obj,
                                           serial=r.get('serie'),
                                           type=r.get('tipo_de_comprobante'),
                                           sunat_status=r.get('aceptada_por_sunat'),
                                           sunat_description=r.get('sunat_description'),
                                           user=user_obj,
                                           sunat_enlace_pdf=r.get('enlace_del_pdf'),
                                           code_qr=r.get('cadena_para_codigo_qr'),
                                           code_hash=r.get('codigo_hash'),
                                           n_receipt=r.get('numero'),
                                           status='E',
                                           created_at=order_obj.create_at,
                                           is_demo=value_is_demo
                                           )
                order_bill_obj.save()
            else:
                objects_to_delete = OrderDetail.objects.filter(order=order_obj)
                objects_to_delete.delete()
                order_obj.delete()
                if r.get('errors'):
                    data = {'error': str(r.get('errors'))}
                elif r.get('error'):
                    data = {'error': str(r.get('error'))}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        elif order_bill_type == 'B':
            r = send_receipt_passenger(order_obj.id, is_demo)
            msg_sunat = r.get('sunat_description')
            sunat_pdf = r.get('enlace_del_pdf')
            codigo_hash = r.get('codigo_hash')
            if codigo_hash:
                order_bill_obj = OrderBill(order=order_obj,
                                           serial=r.get('serie'),
                                           type=r.get('tipo_de_comprobante'),
                                           sunat_status=r.get('aceptada_por_sunat'),
                                           sunat_description=r.get('sunat_description'),
                                           user=user_obj,
                                           sunat_enlace_pdf=r.get('enlace_del_pdf'),
                                           code_qr=r.get('cadena_para_codigo_qr'),
                                           code_hash=r.get('codigo_hash'),
                                           n_receipt=r.get('numero'),
                                           status='E',
                                           created_at=order_obj.create_at,
                                           is_demo=value_is_demo
                                           )
                order_bill_obj.save()
                # print_ticket_order_passenger(order_obj.id)
            else:
                objects_to_delete = OrderDetail.objects.filter(order=order_obj)
                objects_to_delete.delete()
                order_obj.delete()
                if r.get('errors'):
                    data = {'error': str(r.get('errors'))}
                elif r.get('error'):
                    data = {'error': str(r.get('error'))}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        postponement_obj.status = 'C'
        postponement_obj.save()

        postponement_detail_obj = PostponementDetail(postponement=postponement_obj, order=order_obj, type='R')
        postponement_detail_obj.save()

        programming_seat_obj = sell_seat(
            programming_seat_id=id_new_programming_seat,
            destiny_id=id_destiny,
            subsidiary_obj=subsidiary_obj
        )

        start_date = str(request.POST.get('query-start-date'))
        end_date = str(request.POST.get('query-end-date'))
        if start_date == end_date:
            postponement_set = Postponement.objects.filter(created_at__date=start_date, subsidiary=subsidiary_obj)
        else:
            postponement_set = Postponement.objects.filter(created_at__date__range=[start_date, end_date],
                                                           subsidiary=subsidiary_obj)
        status = Postponement._meta.get_field('status').choices
        tpl = loader.get_template('comercial/postponement_grid_list.html')
        context = ({
            'postponement_set': postponement_set,
            'status': status,
        })

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'order_id': order_obj.id,
            'msg_sunat': msg_sunat,
            'sunat_pdf': sunat_pdf,
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_order_set_values(order_set=None):
    order_dict = []
    get_status_display = {'A': 'Anulado', 'C': 'Completado'}
    for o in order_set:
        client_type_set = ClientType.objects.filter(client_id=o['client__id']).values('document_number')
        _document_number = '$$'
        if client_type_set.exists():
            client_type_obj = client_type_set.first()
            _document_number = client_type_obj['document_number']
        user_obj = Worker.objects.filter(user_id=o['user_id']).values(
            'employee__names',
            'employee__paternal_last_name',
            'employee__maternal_last_name'
        ).last()

        order_item = {
            'id': o['id'],
            'programming_serial': o['programming_seat__programming__serial'],
            'programming_correlative': o['programming_seat__programming__correlative'],
            'serial': o['serial'],
            'correlative_sale': o['correlative_sale'],
            'create_at': o['create_at'],
            'client_type__document_number': _document_number,
            'client__names': o['client__names'],
            'destiny__name': o['destiny__name'],
            'get_status_display': get_status_display[o['status']],
            'subsidiary__name': o['subsidiary__name'],
            'user__full_name': '{} {} {}'.format(
                user_obj['employee__names'],
                user_obj['employee__paternal_last_name'],
                user_obj['employee__maternal_last_name']
            ),
            'total': o['total']
        }
        order_dict.append(order_item)
    return order_dict


def get_ticket_inquiry_list(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        subsidiary_set = Subsidiary.objects.all()

        return render(request, 'comercial/ticket_inquiry_list.html', {
            'formatdate': formatdate,
            'subsidiary_set': subsidiary_set
        })
    elif request.method == 'POST':
        id_subsidiary = int(request.POST.get('subsidiary'))
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation

        if start_date == end_date:
            order_set = Order.objects.filter(create_at__date=start_date,
                                             subsidiary__id=id_subsidiary,
                                             company=company_rotation_obj,
                                             type_order='P').values(
                'id',
                'programming_seat__programming__serial',
                'programming_seat__programming__correlative',
                'serial',
                'correlative_sale',
                'create_at',
                'client__id',
                'client__names',
                'destiny__name',
                'status',
                'subsidiary__name',
                'user_id',
                'total'
            )

        else:
            order_set = Order.objects.filter(create_at__date__range=[start_date, end_date],
                                             subsidiary__id=id_subsidiary,
                                             company=company_rotation_obj,
                                             type_order='P').values(
                'id',
                'programming_seat__programming__serial',
                'programming_seat__programming__correlative',
                'serial',
                'correlative_sale',
                'create_at',
                'client__id',
                'client__names',
                'destiny__name',
                'status',
                'subsidiary__name',
                'user_id',
                'total'
            )
        order_dict = get_order_set_values(order_set)

        if len(order_dict) > 0:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/ticket_inquiry_grid_list.html')
        context = (
            {'order_set': order_dict, 'subsidiary_obj': subsidiary_obj, 'has_rows': has_rows})

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_manifest_passenger_inquiry_list(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation

    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        subsidiary_set = Subsidiary.objects.all()
        serials = get_serial_subsidiary_company(
            subsidiary_obj=subsidiary_obj, company_rotation_obj=company_rotation_obj, type_document='T')

        return render(request, 'comercial/manifest_passenger_list.html', {
            'formatdate': formatdate,
            'subsidiary_set': subsidiary_set,
            'serial_manifest_passenger': serials,
        })
    elif request.method == 'POST':
        id_subsidiary = int(request.POST.get('subsidiary'))
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))

        if start_date == end_date:
            programming_set = Programming.objects.filter(
                departure_date=start_date,
                subsidiary__id=id_subsidiary,
                programmingseat__isnull=False,
                company=company_rotation_obj).distinct('id')
        else:
            programming_set = Programming.objects.filter(
                departure_date__range=[start_date, end_date],
                subsidiary__id=id_subsidiary,
                programmingseat__isnull=False,
                company=company_rotation_obj).distinct('id')

        programming_dict = []
        for p in programming_set:
            programming_item = {
                'id': p.id,
                'departure_date': p.departure_date,
                'license_plate': p.truck.license_plate,
                'serial': p.serial,
                'correlative': p.correlative,
                'status': p.get_status_display(),
                'total': str(p.get_total_sold()),
                'seats_sold': p.get_count_seats_sold(),
                'passengers': p.get_programming_seat_set()
            }
            if p.get_total_sold() > 0:
                programming_dict.append(programming_item)

        if programming_set:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/manifest_passenger_grid_list.html')
        context = ({
            'programming_dict': programming_dict,
            'programming_set': programming_set,
            'subsidiary_obj': subsidiary_obj,
            'has_rows': has_rows
        })

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)
