from django.contrib.auth.models import User
from django.shortcuts import render

from apps.comercial.models import Programming, ProgrammingSeat, Truck, Path, Postponement, PostponementDetail
from apps.comercial.view_correlative import get_correlative_electronic_passenger, get_correlative_manifest
from apps.comercial.view_passenger import get_serial_subsidiary_company, get_score_programming_seat, get_voucher_report, \
    get_subsidiary_associate_leader, get_serial_manifest_and_commodity, truck_dictionary, get_form_programming_seat, \
    get_void_form_programming_seat, get_serial_manifest
from apps.comercial.views import get_programmings
from apps.hrm.models import UserSubsidiary, Subsidiary, Employee
from apps.hrm.views import get_subsidiary_by_user
from apps.accounting.views import Cash, CashFlow
from datetime import datetime
from django.template import loader
from http import HTTPStatus
from django.http import JsonResponse
# Create your views here.
from apps.sales.models import Order


def programming_list(request):
    user_id = request.user.id
    user_obj = User.objects.get(pk=int(user_id))
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation
    company_obj = user_obj.companyuser.company_rotation
    serials = get_serial_manifest(subsidiary_obj=subsidiary_obj,
                                  company_rotation_obj=company_rotation_obj)
    serial_manifest = serials.get('serial_manifest_passenger')

    my_date = datetime.now()
    formatdate = my_date.strftime("%Y-%m-%d")
    return render(request, 'transport/programming_create.html', {
        'employees': Employee.objects.all(),
        'trucks': Truck.objects.filter(truckassociate__isnull=False, owner__ruc=company_obj.ruc, is_enabled=True),
        'path_set': Path.objects.filter(subsidiary=subsidiary_obj, company__ruc=company_obj.ruc),
        'choices_status': Programming._meta.get_field('status').choices,
        # 'choices_turn': Programming._meta.get_field('turn').choices,
        'current_date': formatdate,
        'subsidiary_origin': subsidiary_obj,
        'programmings': get_programmings(
            need_rendering=False,
            subsidiary_obj=subsidiary_obj,
            company_obj=company_obj,
            show_edit=False, show_plan=False, show_lp=False
        ),
        'mode': 'firebase',
        'show_edit': True,
        'show_plan': True,
        'show_lp': False,
        'serial': serial_manifest,
        'correlative': get_correlative_manifest(subsidiary_obj=subsidiary_obj,
                                                company_rotation_obj=company_rotation_obj),
    })


def truck_plan(request, pk):
    user_id = request.user.id
    user_obj = User.objects.get(pk=int(user_id))

    # company_rotation_obj =
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    programming_obj = None
    company_rotation_obj = None
    cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')
    printer_set = None
    dictionary = []
    plan_obj = None
    serials = None

    if pk:
        programming_obj = Programming.objects.get(id=pk)

        company_rotation_obj = programming_obj.company
        # printer_set = Printer.objects.filter(subsidiary_company__company=company_rotation_obj)
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
                # green | purple
                # olive | gray

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

    user_subsidiary_subsidiary = None
    user_subsidiary_office = None
    user_subsidiary_printer = None
    user_subsidiary_set = UserSubsidiary.objects.filter(user=user_obj)

    if user_subsidiary_set.exists():
        user_subsidiary_obj = user_subsidiary_set.last()
        user_subsidiary_subsidiary = str(user_subsidiary_obj.subsidiary.id)
        user_subsidiary_office = user_subsidiary_obj.office
        user_subsidiary_printer = user_subsidiary_obj.printer

    return render(request, 'transport/truck_plan.html', {
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
        'choices_account': cash_set,
        'printer_set': printer_set,
        'company_rotation_obj': company_rotation_obj,
        'userOffice': user_subsidiary_office,
        'userPrinter': user_subsidiary_printer,
        'userSubsidiary': user_subsidiary_subsidiary,
        'serial_manifest': programming_obj.serial.zfill(4),
        'serial_correlative': programming_obj.correlative.zfill(6),
    })


def go_processing_of_sale(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        type_document = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        programming_seat_obj.status = '2'  # yellow
        programming_seat_obj.save()

        company_rotation_obj = programming_seat_obj.programming.company

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=type_document),
                request),
            'type_document': type_document,
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def go_release_seat(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        _type = request.GET.get('type', '')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_seat_obj = ProgrammingSeat.objects.get(id=pk)
        company_rotation_obj = programming_seat_obj.programming.company

        programming_seat_obj.status = '1'
        programming_seat_obj.save()

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'form': tpl.render(get_form_programming_seat(
                programming_seat_obj,
                subsidiary_obj,
                company_rotation_obj,
                type_document=_type),
                request),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


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
        programming_seat_obj.status = '1'  # green
        programming_seat_obj.save()

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
                request)
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

        tpl = loader.get_template('transport/reassign_seat_form.html')
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

        tpl = loader.get_template('comercial/truck_plan_form.html')
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'subsidiaryID': subsidiary_obj.id,
            'currentProgramming': current_programming_seat_obj.programming.id,
            'newProgramming': new_programming_seat_obj.programming.id,
            'currentProgrammingSeat': id_current_programming_seat,
            'newProgrammingSeat': id_new_programming_seat,
            'form': tpl.render(get_void_form_programming_seat(
                current_programming_seat_obj.programming, subsidiary_obj, company_rotation_obj), request),
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
        programming_seat_obj.status = '5'
        programming_seat_obj.subsidiary_than_reserve = subsidiary_obj
        programming_seat_obj.save()

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


