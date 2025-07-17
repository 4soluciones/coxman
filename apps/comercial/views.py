import decimal, math, os
from http import HTTPStatus

from django.db.models import Prefetch, F, ExpressionWrapper, fields, Value
from django.shortcuts import render
from django.views.generic import View, TemplateView, UpdateView, CreateView
from django.views.decorators.csrf import csrf_exempt
from reportlab import xrange

from .models import *
from apps.hrm.models import Subsidiary, Employee, Company
from django.http import JsonResponse
from .forms import *
from django.urls import reverse_lazy
from apps.sales.models import Product, SubsidiaryStore, ProductStore, ProductDetail, ProductRecipe, \
    ProductSubcategory, ProductSupplier, TransactionPayment, Order, OrderDetail, OrderBill, OrderRoute, OrderAction, \
    OrderProgramming, OrderAddressee
from apps.sales.views import kardex_ouput, kardex_input, kardex_initial, calculate_minimum_unit, Supplier, Client, \
    ClientType, ClientAddress, Manifest
from apps.sales.views_SUNAT import query_dni, send_bill_nubefact, send_receipt_nubefact, \
    send_receipt_passenger, query_apis_net_dni_ruc, query_api_free_optimize_dni, query_api_facturacioncloud, \
    query_api_amigo, \
    query_api_free_optimize_ruc
from apps.hrm.models import Subsidiary, DocumentType, Nationality, UserSubsidiary
from apps.accounting.views import TransactionAccount, LedgerEntry, get_account_cash, Cash, CashFlow, AccountingAccount, \
    save_cash_flow
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import ImageFieldFile
from django.template import loader
from datetime import datetime
from django.db import DatabaseError, IntegrityError
from django.core import serializers
from datetime import date, timedelta
import datetime as date_time
# Create your views here.
from ..hrm.views import get_subsidiary_by_user, CompanyUser
from apps.comercial.view_passenger import get_serial_subsidiary_company, get_serial_manifest_and_commodity, \
    get_serial_manifest
from apps.comercial.view_correlative import get_correlative_manifest, get_correlative_commodity, \
    update_correlative_manifest_passenger, update_correlative_commodity
from ..sales.api_FACT import send_bill_commodity_fact, send_receipt_commodity_fact
from ..sales.format_to_dates import utc_to_local


class Index(TemplateView):
    # template_name = 'dashboard.html'
    # template_name = 'vetstore/home.html'
    template_name = 'comercial/..get/../templates/main.html'


# ---------------------------------------Truck-----------------------------------
class TruckList(View):
    model = Truck
    form_class = FormTruck
    template_name = 'comercial/truck_list.html'

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = {
            'trucks': self.get_queryset(),
            'form': self.form_class,
            'employee_set': Employee.objects.all(),
        }
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


class TruckCreate(CreateView):
    model = Truck
    form_class = FormTruck
    template_name = 'comercial/truck_create.html'
    success_url = reverse_lazy('comercial:truck_list')

    def get_context_data(self, **kwargs):
        ctx = super(TruckCreate, self).get_context_data(**kwargs)
        ctx['brands'] = TruckBrand.objects.all()
        ctx['models'] = TruckModel.objects.all()
        return ctx


class TruckUpdate(UpdateView):
    model = Truck
    form_class = FormTruck
    template_name = 'comercial/truck_update.html'
    success_url = reverse_lazy('comercial:truck_list')

    def get_context_data(self, **kwargs):
        ctx = super(TruckUpdate, self).get_context_data(**kwargs)
        ctx['brands'] = TruckBrand.objects.all()
        ctx['models'] = TruckModel.objects.all()
        return ctx


# -------------------------------------- Towing -----------------------------------


class TowingList(View):
    model = Towing
    form_class = FormTowing
    template_name = 'comercial/towing_list.html'

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        contexto = {}
        contexto['towings'] = self.get_queryset()  # agregamos la consulta al contexto
        contexto['form'] = self.form_class
        return contexto

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


class TowingCreate(CreateView):
    model = Towing
    form_class = FormTowing
    template_name = 'comercial/towing_create.html'
    success_url = reverse_lazy('comercial:towing_list')

    def get_context_data(self, **kwargs):
        ctx = super(TowingCreate, self).get_context_data(**kwargs)
        ctx['brands'] = TowingBrand.objects.all()
        ctx['models'] = TowingModel.objects.all()
        return ctx


class TowingUpdate(UpdateView):
    model = Towing
    form_class = FormTowing
    template_name = 'comercial/towing_update.html'
    success_url = reverse_lazy('comercial:towing_list')

    def get_context_data(self, **kwargs):
        ctx = super(TowingUpdate, self).get_context_data(**kwargs)
        ctx['brands'] = TowingBrand.objects.all()
        ctx['models'] = TowingModel.objects.all()
        return ctx


# ----------------------------------------Programming-------------------------------


class ProgrammingCreate(CreateView):
    model = Programming
    form_class = FormProgramming
    template_name = 'comercial/programming_list.html'
    success_url = reverse_lazy('comercial:programming_list')


class ProgrammingList(View):
    model = Programming
    form_class = FormProgramming
    template_name = 'comercial/programming_create.html'

    def get_context_data(self, **kwargs):
        user_id = self.request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        company_obj = user_obj.companyuser.company_rotation
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        context = {
            'employees': Employee.objects.all(),
            'trucks': Truck.objects.filter(truckassociate__isnull=False, owner__ruc=company_obj.ruc),
            'path_set': Path.objects.filter(company__ruc=company_obj.ruc),
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
            'show_edit': True,
            'show_plan': True,
            'show_lp': False,
        }
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


@csrf_exempt
def new_programming(request):
    if request.method == 'POST':

        truck = request.POST.get('truck', '')
        departure_date = request.POST.get('departure_date')
        # turn = request.POST.get('turn', '')
        towing = request.POST.get('towing', '')
        path = request.POST.get('path', '')
        status = request.POST.get('status', '')
        # observation = request.POST.get('observation', '')

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_origin_obj = get_subsidiary_by_user(user_obj)

        pilot = request.POST.get('pilot', '')
        copilot = request.POST.get('copilot', '')

        company_rotation_obj = user_obj.companyuser.company_rotation
        serials = get_serial_manifest(subsidiary_obj=subsidiary_origin_obj,
                                      company_rotation_obj=company_rotation_obj)

        serial = serials.get('serial_manifest_passenger')
        correlative = get_correlative_manifest(subsidiary_obj=subsidiary_origin_obj,
                                               company_rotation_obj=company_rotation_obj)

        pilot_obj = Employee.objects.get(pk=int(pilot))

        if len(truck) > 0:
            truck_obj = Truck.objects.get(id=truck)
            company_obj = Company.objects.get(ruc=truck_obj.owner.ruc)
            towing_obj = None
            if len(towing) > 0:
                towing_obj = Towing.objects.get(id=towing)
            path_obj = Path.objects.get(id=path)
            data_programming = {
                'departure_date': departure_date,
                'truck': truck_obj,
                'towing': towing_obj,
                'subsidiary': subsidiary_origin_obj,
                # 'turn': turn,
                # 'observation': observation,
                'path': path_obj,
                'status': status,
                'serial': serial,
                'correlative': correlative,
                'company': company_obj
            }
            programming_obj = Programming.objects.create(**data_programming)
            programming_obj.save()

            update_correlative_manifest_passenger(programming_obj=programming_obj)

            set_employee_pilot_obj = SetEmployee(
                programming=programming_obj,
                employee=pilot_obj,
                function='P',
            )
            set_employee_pilot_obj.save()

            if copilot != '':
                copilot_obj = Employee.objects.get(pk=int(copilot))
                set_employee_copilot_obj = SetEmployee(
                    programming=programming_obj,
                    employee=copilot_obj,
                    function='C',
                )
                set_employee_copilot_obj.save()

            route_origin_obj = Route(
                programming=programming_obj,
                subsidiary=subsidiary_origin_obj,
                type='O',
            )
            route_origin_obj.save()

            route_destiny_obj = Route(
                programming=programming_obj,
                subsidiary=path_obj.get_last_point(),
                type='D',
            )
            route_destiny_obj.save()

            return JsonResponse({
                'success': True,
                'message': 'La Programacion se guardo correctamente.',
                'grid': get_programmings(
                    need_rendering=True,
                    subsidiary_obj=subsidiary_origin_obj,
                    company_obj=company_obj,
                    show_edit=True, show_plan=True),
            })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


def get_programming(request):
    if request.method == 'GET':
        id_programming = request.GET.get('programming', '')
        programming_obj = Programming.objects.get(id=int(id_programming))
        tpl = loader.get_template('comercial/programming_form.html')
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_ruc = user_obj.companyuser.company_rotation.ruc
        context = ({
            'programming_obj': programming_obj,
            'pilot': programming_obj.setemployee_set.filter(function='P').first(),
            'copilot': programming_obj.setemployee_set.filter(function='C').first(),
            'subsidiary_origin': subsidiary_obj,
            'employees': Employee.objects.all(),
            'trucks': Truck.objects.filter(truckassociate__isnull=False, owner__ruc=company_ruc),
            'path_set': Path.objects.filter(subsidiary=subsidiary_obj, company__ruc=company_ruc),
            'choices_status': Programming._meta.get_field('status').choices,
            # 'choices_turn': Programming._meta.get_field('turn').choices,
        })

        return JsonResponse({
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)


def update_programming(request):
    print(request.method)
    data = {}
    if request.method == 'POST':
        id_programming = request.POST.get('programming', '')
        programming_obj = Programming.objects.get(id=int(id_programming))

        id_subsidiary_origin = request.POST.get('origin', '')
        id_path = request.POST.get('path', '')
        id_pilot = request.POST.get('pilot', '')
        id_copilot = request.POST.get('copilot', '')
        id_truck = request.POST.get('truck', '')
        id_towing = request.POST.get('towing', '')
        departure_date = request.POST.get('departure_date', '')
        arrival_date = request.POST.get('arrival_date', '')
        status = request.POST.get('status', '')
        order = request.POST.get('order', '')
        km_initial = request.POST.get('km_initial', '')
        km_ending = request.POST.get('km_ending', '')
        weight = request.POST.get('weight', 0)
        # observation = request.POST.get('observation', '')
        # turn = request.POST.get('turn', '')

        set_employee_obj = SetEmployee.objects.filter(programming=programming_obj)
        old_pilot_obj = set_employee_obj.filter(function='P').first()
        old_copilot_obj = set_employee_obj.filter(function='C').first()

        new_pilot_obj = Employee.objects.get(pk=int(id_pilot))
        if new_pilot_obj != old_pilot_obj:
            set_employee_obj.filter(function='P').delete()
            SetEmployee(employee=new_pilot_obj, function='P', programming=programming_obj).save()

        if id_copilot != '':
            new_copilot_obj = Employee.objects.get(pk=int(id_copilot))
            if new_copilot_obj != old_copilot_obj:
                set_employee_obj.filter(function='C').delete()
                SetEmployee(employee=new_copilot_obj, function='C', programming=programming_obj).save()

        if len(id_truck) > 0:
            truck_obj = Truck.objects.get(id=int(id_truck))
            programming_obj.truck = truck_obj

        if len(id_towing) > 0:
            towing_obj = Towing.objects.get(id=int(id_towing))
            programming_obj.towing = towing_obj

        new_subsidiary_origin_obj = None
        new_subsidiary_destiny_obj = None

        if len(id_subsidiary_origin) > 0:
            new_subsidiary_origin_obj = Subsidiary.objects.get(pk=int(id_subsidiary_origin))
        if len(id_path) > 0:
            new_path_obj = Path.objects.get(pk=int(id_path))
            new_subsidiary_destiny_obj = new_path_obj.get_last_point()

        routes_obj = Route.objects.filter(programming=programming_obj)
        old_subsidiary_origin_obj = routes_obj.filter(type='O').first()
        old_subsidiary_destiny_obj = routes_obj.filter(type='D').first()

        if new_subsidiary_origin_obj != old_subsidiary_origin_obj:
            routes_obj.filter(type='O').delete()
            Route(subsidiary=new_subsidiary_origin_obj, type='O', programming=programming_obj).save()

        if new_subsidiary_destiny_obj != old_subsidiary_destiny_obj:
            routes_obj.filter(type='D').delete()
            Route(subsidiary=new_subsidiary_destiny_obj, type='D', programming=programming_obj).save()

        programming_obj.weight = float(weight)
        programming_obj.status = status
        programming_obj.departure_date = departure_date
        programming_obj.km_initial = km_initial
        programming_obj.km_ending = km_ending
        # programming_obj.turn = turn

        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = user_obj.companyuser.company_rotation

        if len(order) > 0:
            programming_obj.order = int(order)
        # programming_obj.observation = observation
        programming_obj.save()

        return JsonResponse({
            'success': True,
            'message': 'La Programacion se guardo correctamente.',
            'grid': get_programmings(
                need_rendering=True,
                subsidiary_obj=subsidiary_obj,
                company_obj=company_obj,
                show_edit=True,
                show_plan=True),
        })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


def get_programmings(need_rendering, subsidiary_obj=None, company_obj=None, show_edit=False, show_plan=False,
                     show_lp=False):
    my_date = datetime.now()
    formatdate = my_date.strftime("%Y-%m-%d")
    if subsidiary_obj is None:
        # programmings = Programming.objects.all().order_by('id')
        programmings = Programming.objects.filter(departure_date__gte=formatdate, truck__owner__ruc=company_obj.ruc,
                                                  status__in=['P', 'R']).order_by(
            'departure_date')
    else:
        # programmings = Programming.objects.filter(subsidiary=subsidiary_obj).order_by('id')
        _im_associated = AssociateDetail.objects.filter(subsidiary=subsidiary_obj)
        if _im_associated:
            associated = []
            for ad in _im_associated:
                _who = ad.associate.subsidiary
                associated.append(_who.id)
            associated.append(subsidiary_obj.id)
            programmings = Programming.objects.filter(subsidiary_id__in=associated, truck__owner__ruc=company_obj.ruc,
                                                      departure_date__gte=formatdate,
                                                      status__in=['P', 'R']).order_by('departure_date')
        else:
            programmings = Programming.objects.filter(subsidiary=subsidiary_obj, truck__owner__ruc=company_obj.ruc,
                                                      departure_date__gte=formatdate,
                                                      status__in=['P', 'R']).order_by('departure_date')

    # programmings = Programming.objects.filter(departure_date__gte=formatdate, status__in=['P', 'R']).order_by('id')
    if need_rendering:
        tpl = loader.get_template('comercial/programming_list.html')
        context = ({'programmings': programmings, 'show_edit': show_edit, 'show_plan': show_plan, 'show_lp': show_lp, })
        return tpl.render(context)
    return programmings


# ----------------------------------------Guide------------------------------------

def new_guide(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    company_obj = Company.objects.get(ruc='20612403083')
    company_user_set = CompanyUser.objects.filter(user=user_obj)
    user_subsidiary_set = UserSubsidiary.objects.filter(subsidiary=subsidiary_obj)

    if company_user_set.exists():
        company_user_obj = company_user_set.last()
        company_user_obj.company_rotation = company_obj
        company_user_obj.save()

    serial_commodity = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
                                                         company_rotation_obj=company_obj,
                                                         type_document='T')
    document_types = DocumentType.objects.all()
    mydate = datetime.now()
    formatdate = mydate.strftime("%Y-%m-%d")
    formattime = mydate.strftime("%H:%M")
    form_obj = FormGuide()
    # cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')
    # programmings = Programming.objects.filter(status__in=['P'], subsidiary=subsidiary_obj).order_by('id')
    destinys = Destiny.objects.all()
    unit = Unit.objects.all()
    programming_set = Programming.objects.filter(departure_date=formatdate, subsidiary=subsidiary_obj)
    date_now = datetime.now().strftime("%Y-%m-%d")
    order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=date_now,
                                     status='P').order_by('id')

    cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, cash_type='E')

    return render(request, 'comercial/guide.html', {
        'form': form_obj,
        'programming_set': programming_set,
        'document_types': document_types,
        'subsidiaries': Subsidiary.objects.all().order_by('id'),
        'choices_type_payments': Guide._meta.get_field('way_to_pay').choices,
        'choices_type_guide': Order._meta.get_field('type_guide').choices,
        'cash_set': cash_set,
        'date': formatdate,
        'time': formattime,
        'unit_set': unit,
        'serie': serial_commodity,
        'destinys': destinys,
        'order_set': order_set,
        'user_subsidiary_set': user_subsidiary_set,
        'correlative': get_correlative_commodity(subsidiary_obj=subsidiary_obj, company_rotation_obj=company_obj,
                                                 doc_type='T'),
    })


def get_programming_guide(request):
    if request.method == 'GET':
        id_programming = request.GET.get('programming', '')
        programming_obj = Programming.objects.get(id=int(id_programming))
        pilot = programming_obj.setemployee_set.filter(function='P').first().employee
        name = pilot.names + ' ' + pilot.paternal_last_name
        # print(programming_obj.route_set.filter(type='O').first().subsidiary.name)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='V').first()
        products = Product.objects.filter(productstore__subsidiary_store=subsidiary_store_obj)

        tpl = loader.get_template('comercial/detail_guide.html')
        context = ({
            'products': products,
            'unit_set': Unit.objects.all(),
        })
        return JsonResponse({
            'origin': programming_obj.route_set.filter(type='O').first().subsidiary.name,
            'destiny': programming_obj.route_set.filter(type='D').first().subsidiary.name,
            'pilot': name,
            'departure_date': programming_obj.departure_date,
            'product_grid': tpl.render(context),
            'license_plate': programming_obj.truck.license_plate,
            'truck_brand': programming_obj.truck.truck_model.truck_brand.name,
            # 'truck_serial': programming_obj.truck.serial,
            'license': programming_obj.setemployee_set.filter(function='P').first().employee.n_license,
            'license_type': programming_obj.setemployee_set.filter(
                function='P').first().employee.get_license_type_display(),

        }, status=HTTPStatus.OK)


def get_quantity_product(request):
    if request.method == 'GET':
        id_product = request.GET.get('pk', '')
        print(id_product)
        product_obj = Product.objects.get(pk=int(id_product))
        print(product_obj)
        user = request.user.id
        user_obj = User.objects.get(id=user)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        print(subsidiary_obj)
        subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='V').first()
        print(subsidiary_store_obj)
        product_store_obj = ProductStore.objects.get(product__id=id_product, subsidiary_store=subsidiary_store_obj)
        print(product_store_obj)
        units_obj = Unit.objects.filter(productdetail__product=product_obj)
        print(units_obj)
        serialized_units = serializers.serialize('json', units_obj)
        return JsonResponse({
            'quantity': product_store_obj.stock,
            'units': serialized_units,
            'id_product_store': product_store_obj.id
        }, status=HTTPStatus.OK)


def create_order(request):
    if request.method == 'GET':
        orders_request = request.GET.get('orders', '')
        data_orders = json.loads(orders_request)
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        _document_type = 'G'
        serial = str(data_orders["Serial"])
        correlative = str(data_orders["Correlative"])
        company_obj = Company.objects.get(ruc='20612403083')
        client_obj_addressee = None
        client_obj_sender = None
        client_obj_addressee_obj = None
        client_addressee_name = str(data_orders["Client_Address_Sender"])
        client_sender_name = str(data_orders["Client_Sender"])
        subsidiary_origin = str(data_orders["Subsidiary_origin"])
        subsidiary_origin_obj = Subsidiary.objects.get(id=subsidiary_origin)
        subsidiary_destiny = str(data_orders["Subsidiary_destiny"])
        subsidiary_destiny_obj = Subsidiary.objects.get(id=subsidiary_destiny)
        client_sender_nro_document = str(data_orders["Client_Sender_nro_document"])
        code = str(data_orders["Code"])
        type_document = str(data_orders["Type"])

        arrival_time = str(data_orders["Arrival_Time"])
        user = int(data_orders["User"])
        type_guide = str(data_orders["Type_Guide"])
        address_delivery = str(data_orders["Address_Delivery"])

        company_rotation_obj = user_obj.companyuser.company_rotation

        user_selected_obj = User.objects.get(pk=int(user))

        user_subsidiary_set = UserSubsidiary.objects.filter(user=user_selected_obj)

        user_subsidiary_subsidiary = None
        user_subsidiary_office = None
        user_subsidiary_printer = None
        if user_subsidiary_set.exists():
            user_subsidiary_obj = user_subsidiary_set.last()
            user_subsidiary_subsidiary = str(user_subsidiary_obj.subsidiary.id)
            user_subsidiary_office = user_subsidiary_obj.office
            user_subsidiary_printer = user_subsidiary_obj.printer

        new_correlative = get_correlative_commodity(subsidiary_obj=subsidiary_obj, company_rotation_obj=company_obj,
                                                    doc_type=type_document)

        search_commodity_set = Order.objects.filter(serial=serial, correlative_sale=new_correlative, type_order='E',
                                                    type_document=type_document)
        if search_commodity_set.exists():
            data = {'error': "Encomienda Registrada"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        client_sender_set = Client.objects.filter(clienttype__document_number=client_sender_nro_document)
        if client_sender_set:
            client_obj_sender = client_sender_set.first()
            if client_obj_sender.names != client_sender_name:
                client_obj_sender.names = client_sender_name
                client_obj_sender.save()
        else:
            client_sender_type = str(data_orders["Client_Sender_type"])
            nationality_obj = None
            if client_sender_type == '01':
                nationality = '9589'
                nationality_obj = Nationality.objects.get(id=nationality)
            client_obj_sender = Client(
                names=client_sender_name.upper(),
                nationality=nationality_obj
            )
            client_obj_sender.save()
            client_type_sender_obj = ClientType(
                client=client_obj_sender,
                document_number=client_sender_nro_document.upper(),
                document_type_id=client_sender_type
            )
            client_type_sender_obj.save()
            client_sender_address = str(data_orders["Client_Address_Sender"])
            if client_sender_address:
                clien_address_sender_obj = ClientAddress(
                    address=client_sender_address,
                    client=client_obj_sender,
                )
                clien_address_sender_obj.save()

        _type = str(data_orders["Type"])
        traslate_date = str(data_orders["Date_traslate"])
        way_to_pay = str(data_orders["Way_to_pay"])
        igv = str(data_orders["Igv"])
        sub_total = str(data_orders["Sub_total"])
        total = str(data_orders["Total"])
        is_demo = bool(int(data_orders["Demo"]))
        msg_sunat = ''
        sunat_pdf = ''

        value_is_demo = ''
        if is_demo:
            value_is_demo = 'D'
        else:
            value_is_demo = 'P'

        _dtg = ''
        if _type == 'T':
            _dtg = 'GE'
        else:
            _dtg = 'DE'

        # Guardando la cabecera Orden
        order_obj = Order(
            traslate_date=traslate_date,
            way_to_pay=way_to_pay,
            correlative_sale=new_correlative,
            serial=serial,
            user=user_selected_obj,
            subsidiary=subsidiary_obj,
            type_order='E',
            type_document=type_document,
            dtg=_dtg,
            total=total,
            addressee_name=client_addressee_name.upper(),
            company=company_rotation_obj,
            code=code,
            type_guide=type_guide,
            arrival_time=arrival_time,
            address_delivery=address_delivery
        )
        order_obj.save()

        update_correlative_commodity(order_obj=order_obj)

        for data_addressee in data_orders['Addressees']:
            document_type_addressee = str(data_addressee['DocumentType'])
            document_number_addressee = str(data_addressee['DocumentNumber'])
            name_addressee = str(data_addressee['Name'])
            phone_addressee = str(data_addressee['Phone'])
            if document_number_addressee:
                client_obj_addressee_set = Client.objects.filter(clienttype__document_number=document_number_addressee)
                if client_obj_addressee_set.exists():
                    client_obj_addressee_obj = client_obj_addressee_set.first()
                    if client_obj_addressee_obj.names != name_addressee:
                        client_obj_addressee_obj.names = name_addressee
                    # if client_obj_addressee.phone is None:
                    client_obj_addressee_obj.phone = phone_addressee
                    client_obj_addressee_obj.save()
                else:
                    nationality_obj = None
                    if document_type_addressee == '01':
                        nationality = '9589'
                        nationality_obj = Nationality.objects.get(id=nationality)
                    client_obj_addressee_obj = Client(
                        names=name_addressee.upper(),
                        nationality=nationality_obj,
                        phone=phone_addressee
                    )
                    client_obj_addressee_obj.save()
                    client_type_addressee_obj = ClientType(
                        client=client_obj_addressee_obj,
                        document_number=document_number_addressee.upper(),
                        document_type_id=document_type_addressee
                    )
                    client_type_addressee_obj.save()

                order_action_addressee_obj = OrderAction(
                    client=client_obj_addressee_obj,
                    order=order_obj,
                    type='D'
                )
                order_action_addressee_obj.save()

            else:
                client_addressee_obj = OrderAddressee(
                    names=name_addressee,
                    phone=phone_addressee
                )
                client_addressee_obj.save()

                order_action_addressee_obj = OrderAction(
                    order=order_obj,
                    type='D',
                    order_addressee=client_addressee_obj
                )
                order_action_addressee_obj.save()

        # Guardando la orden route
        order_route_origin_obj = OrderRoute(
            order=order_obj,
            subsidiary=subsidiary_origin_obj,
            type='O'
        )
        order_route_origin_obj.save()

        order_route_destiny_obj = OrderRoute(
            order=order_obj,
            subsidiary=subsidiary_destiny_obj,
            type='D'
        )
        order_route_destiny_obj.save()

        # Guardando el orden action
        order_action_sender_obj = OrderAction(
            client=client_obj_sender,
            order=order_obj,
            type='R'
        )
        order_action_sender_obj.save()

        # Guardando el detalle de la orden
        for detail in data_orders['Details']:
            quantity = decimal.Decimal(detail['Quantity'])
            price_unit = decimal.Decimal(detail['Price_unit'])
            description = str(detail['Description'])
            amount = decimal.Decimal(detail['Amount'])
            # weight = decimal.Decimal(detail['Weight'])
            unit = decimal.Decimal(detail['Unit'])
            unit_obj = Unit.objects.get(id=unit)

            new_item_order = OrderDetail(
                order=order_obj,
                quantity=quantity,
                price_unit=price_unit,
                description=description,
                amount=amount,
                # weight=weight,
                unit=unit_obj,
            )
            new_item_order.save()

        if _type == 'F':
            '''_document_type = 'F'
            serie = order_obj.serial
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
            # r = send_bill_nubefact(order_obj.id)
            # msg_sunat = r.get('sunat_description')
            # sunat_pdf = r.get('enlace_del_pdf')
            # codigo_hash = r.get('codigo_hash')
            # if codigo_hash:
            #     order_bill_obj = OrderBill(
            #         order=order_obj,
            #         serial=r.get('serie'),
            #         type=r.get('tipo_de_comprobante'),
            #         sunat_status=r.get('aceptada_por_sunat'),
            #         sunat_description=r.get('sunat_description'),
            #         user=user_obj,
            #         sunat_enlace_pdf=r.get('enlace_del_pdf'),
            #         code_qr=r.get('cadena_para_codigo_qr'),
            #         code_hash=r.get('codigo_hash'),
            #         n_receipt=r.get('numero'),
            #         status='E',
            #         created_at=order_obj.create_at,
            #         is_demo=value_is_demo
            #     )
            #     _document_type = 'F'
            #     order_bill_obj.save()
            # else:
            #     objects_to_delete = OrderDetail.objects.filter(order=order_obj)
            #     objects_to_delete.delete()
            #     order_obj.delete()
            #     if r.get('errors'):
            #         data = {'error': str(r.get('errors'))}
            #     elif r.get('error'):
            #         data = {'error': str(r.get('error'))}
            #     response = JsonResponse(data)
            #     response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            #     return response
            r = send_bill_commodity_fact(request, order_obj.id)
            _document_type = 'F'
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

        elif _type == 'B':
            '''_document_type = 'B'
            serie = order_obj.serial
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
            # r = send_receipt_nubefact(order_obj.id)
            # msg_sunat = r.get('sunat_description')
            # sunat_pdf = r.get('enlace_del_pdf')
            # codigo_hash = r.get('codigo_hash')
            # if codigo_hash:
            #     order_bill_obj = OrderBill(
            #         order=order_obj,
            #         serial=r.get('serie'),
            #         type=r.get('tipo_de_comprobante'),
            #         sunat_status=r.get('aceptada_por_sunat'),
            #         sunat_description=r.get('sunat_description'),
            #         user=user_obj,
            #         sunat_enlace_pdf=r.get('enlace_del_pdf'),
            #         code_qr=r.get('cadena_para_codigo_qr'),
            #         code_hash=r.get('codigo_hash'),
            #         n_receipt=r.get('numero'),
            #         status='E',
            #         created_at=order_obj.create_at,
            #         is_demo=value_is_demo
            #     )
            #     _document_type = 'B'
            #     order_bill_obj.save()
            r = send_receipt_commodity_fact(request, order_obj.id)
            _document_type = 'B'
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

        # GUARDANDO LA ENCOMIENDA EN LA CAJA

        register_in_cash_flow(
            order_obj=order_obj, subsidiary_obj=subsidiary_obj, user_obj=user_obj,
            type_bill=_type, amount=total
        )

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'msg_sunat': msg_sunat,
            'document_type': _document_type,
            'sunat_pdf': sunat_pdf,
            'order_id': order_obj.id,
            'serial': order_obj.serial,
            'correlative': order_obj.correlative_sale,
            'userSubsidiary': user_subsidiary_subsidiary,
            'userOffice': user_subsidiary_office,
            'userPrinter': user_subsidiary_printer,
        }, status=HTTPStatus.OK)

    return JsonResponse({
        'message': 'Se guardo la guia correctamente.',
    }, status=HTTPStatus.OK)


def register_in_cash_flow(order_obj=None, subsidiary_obj=None, user_obj=None, type_bill=None, amount=None):
    cash_obj = Cash.objects.filter(cash_type='E', subsidiary=subsidiary_obj).last()

    register_date = utc_to_local(order_obj.create_at)
    formatdate = register_date.strftime("%Y-%m-%d")

    cashflow_set = CashFlow.objects.filter(cash=cash_obj, transaction_date=formatdate, type='A')

    serial_description_cash = 'PAGO DE LA ENCOMIENDA {}-{}'.format(order_obj.serial,
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
        document_type_attached=document_type_attached,
        cash_flow_total=amount
    )


def guide_detail_list(request):
    # programmings = Programming.objects.filter(status__in=['P'], guide__isnull=False).order_by('id')
    return render(request, 'comercial/guide_detail_programming.html', {
        'programmings': None
    })


def guide_by_programming(request):
    if request.method == 'GET':
        id_programming = request.GET.get('programming', '')
        programming_obj = Programming.objects.get(id=int(id_programming))
        guide_obj = Guide.objects.filter(programming=programming_obj).first()
        details = GuideDetail.objects.filter(guide=guide_obj)
        # print(guide_obj)
        # print(details)

        tpl = loader.get_template('comercial/guide_detail_list.html')
        context = ({'guide': guide_obj, 'details': details})
        return JsonResponse({
            # 'message': 'guias recuperadas',
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)


def programmings_by_date(request):
    if request.method == 'GET':
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        programmings = Programming.objects.filter(status__in=['P'], departure_date__range=(start_date, end_date),
                                                  guide__isnull=False).order_by('id')

        tpl = loader.get_template('comercial/guide_detail_programming_list.html')
        context = ({'programmings': programmings})
        return JsonResponse({
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)


def programming_receive_by_sucursal(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        routes = Route.objects.filter(type='D', subsidiary=subsidiary_obj)
        # programmings = Programming.objects.filter(status__in=['P'], guide__isnull=False, route__in=routes).order_by('id')
        programmings = Programming.objects.filter(status__in=['P'], route__in=routes).order_by('id')

        status_obj = Programming._meta.get_field('status').choices
        return render(request, 'comercial/programming_receive.html', {
            'programmings': programmings,
            'choices_status': status_obj,

        })


def programming_receive_by_sucursal_detail_guide(request):
    if request.method == 'GET':
        id_programming = request.GET.get('programming', '')
        programming_obj = Programming.objects.get(id=int(id_programming))
        guide_obj = Guide.objects.filter(programming=programming_obj).first()
        details = GuideDetail.objects.filter(guide=guide_obj)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiaries_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj)
        # product_store_obj = ProductStore.objects.get(subsidiary_store=subsidiaries_store_obj)

        tpl = loader.get_template('comercial/programming_receive_detail.html')
        context = ({
            'guide': guide_obj,
            'details': details,
            'subsidiaries_store': subsidiaries_store_obj,

        })

        return JsonResponse({
            'message': 'guias recuperadas',
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)


def get_stock_by_store(request):
    if request.method == 'GET':
        id_product = request.GET.get('ip', '')
        id_subsidiary_store = request.GET.get('iss', '')
        print(id_product)
        print(id_subsidiary_store)
        product_obj = Product.objects.get(pk=int(id_product))
        print(product_obj)
        subsidiary_store_obj = SubsidiaryStore.objects.get(id=int(id_subsidiary_store))
        print(subsidiary_store_obj)

        quantity = ''
        id_product_store = 0
        product_store_obj = None
        try:
            product_store_obj = ProductStore.objects.get(product=product_obj, subsidiary_store=subsidiary_store_obj)
        except ProductStore.DoesNotExist:
            quantity = 'SP'
        if product_store_obj is not None:
            print(product_store_obj)
            quantity = str(product_store_obj.stock)
            id_product_store = product_store_obj.id

        return JsonResponse({
            'quantity': quantity,
            'id_product_store': id_product_store
        }, status=HTTPStatus.OK)


def update_stock_from_programming(request):
    if request.method == 'GET':
        programming_request = request.GET.get('programming', '')
        data_programming = json.loads(programming_request)
        programming = int(data_programming["id_programming"])
        programming_obj = Programming.objects.get(pk=programming)
        programming_obj.status = 'F'
        programming_obj.save()

        for detail in data_programming['Details']:
            quantity = decimal.Decimal((detail['Quantity']).replace(',', '.'))
            product_id = int(detail['Product'])
            detail_id = int(detail['detail_id'])
            product_obj = Product.objects.get(id=product_id)
            detail_guide_obj = GuideDetail.objects.get(id=detail_id)
            type = str(detail['Type'])
            unit = str(detail['Unit']).strip()
            unit_obj = Unit.objects.get(description=unit)
            # product_detail_obj = ProductDetail.objects.get(product=product_obj, unit=unit_obj)
            user = request.user.id
            user_obj = User.objects.get(id=user)
            subsidiary_obj = get_subsidiary_by_user(user_obj)
            if type == '1':
                subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='I').first()
                subcategory_obj = ProductSubcategory.objects.get(name='FIERRO', product_category__name='FIERRO')
                product_recipe_obj = ProductRecipe.objects.filter(product=product_obj,
                                                                  product_input__product_subcategory=subcategory_obj)
                product_obj = product_recipe_obj.first().product_input

            if type == '2':
                subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='V').first()

            if type == '3':
                subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='R').first()

            if type == '4':
                subsidiary_store_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='R').first()
                subcategory_obj = ProductSubcategory.objects.get(name='FIERRO', product_category__name='FIERRO')
                product_recipe_obj = ProductRecipe.objects.filter(product=product_obj,
                                                                  product_input__product_subcategory=subcategory_obj)
                product_obj = product_recipe_obj.first().product_input

            try:
                product_store_obj = ProductStore.objects.get(product__id=product_obj.id,
                                                             subsidiary_store=subsidiary_store_obj)
            except ProductStore.DoesNotExist:
                product_store_obj = None
                # unit_min_detail_product = ProductDetail.objects.get(product=product_obj, unit=unit_obj).quantity_minimum
            quantity_minimum_unit = calculate_minimum_unit(quantity, unit_obj, product_obj)

            if product_store_obj is None:
                new_product_store_obj = ProductStore(
                    product=product_obj,
                    subsidiary_store=subsidiary_store_obj,
                    stock=quantity_minimum_unit
                )
                new_product_store_obj.save()
                kardex_initial(new_product_store_obj, quantity_minimum_unit,
                               product_obj.calculate_minimum_price_sale(),
                               guide_detail_obj=detail_guide_obj)
            else:
                kardex_input(product_store_obj.id, quantity_minimum_unit,
                             product_obj.calculate_minimum_price_sale(),
                             guide_detail_obj=detail_guide_obj)
    return JsonResponse({
        'message': 'Se guardo la guia correctamente.',
    }, status=HTTPStatus.OK)


def get_add_detail(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        tpl = loader.get_template('comercial/detail_guide.html')
        mydate = datetime.now()
        unit = Unit.objects.all()
        formatdate = mydate.strftime("%Y-%m-%d")
        context = ({
            'date': formatdate,
            'unit_set': unit
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_address_subsidiary_by_id(request):
    if request.method == 'GET':
        pk = request.GET.get('subsidiary_id', '')
        subsidiary_obj = Subsidiary.objects.get(id=pk)
        address_subsidiary = subsidiary_obj.address

        return JsonResponse({'address_subsidiary': address_subsidiary}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def calculate_age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age
    # # Driver code
    # print(calculateAge(date(1997, 2, 3)), "years")


def get_name_business(request):
    if request.method == 'GET':
        nro_document = request.GET.get('nro_document', '')
        type_document = str(request.GET.get('type', ''))
        result = ''
        address = ''
        age = ''
        phone = ''
        client_obj_search = Client.objects.filter(clienttype__document_number=nro_document)

        if client_obj_search.exists():
            if type_document == '01':
                names = client_obj_search.first().names
                birthday = client_obj_search.first().birthday
                phone = client_obj_search.first().phone
                if birthday is not None:
                    age = calculate_age(birthday)
                return JsonResponse({'result': names, 'address': address, 'age': age, 'phone': phone},
                                    status=HTTPStatus.OK)

            elif type_document == '06':
                address_search = ClientAddress.objects.get(client__clienttype__document_number=nro_document)
                names = client_obj_search.first().names
                return JsonResponse({'result': names, 'address': address_search.address}, status=HTTPStatus.OK)

            elif type_document == '04' or type_document == '07':
                names = client_obj_search.first().names
                nationality = client_obj_search.first().nationality.id
                phone = client_obj_search.first().phone
                return JsonResponse({'result': names, 'nationality': nationality, 'phone': phone}, status=HTTPStatus.OK)

            else:
                data = {
                    'error': 'PROBLEMAS CON LA CONSULTA A LA RENIEC, FAVOR DE INTENTAR MAS TARDE O REGISTRE MANUALMENTE'}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
        else:
            if type_document == '01':
                type_name = 'DNI'
                # r = query_api_free_optimize_dni(nro_document, type_name)

                r = query_apis_net_dni_ruc(nro_document, type_name)
                name = r.get('nombres')
                paternal_name = r.get('apellidoPaterno')
                maternal_name = r.get('apellidoMaterno')

                if paternal_name is not None and len(paternal_name) > 0:
                    print('client finded in query_apis_net_dni_ruc')
                    result = name + ' ' + paternal_name + ' ' + maternal_name

                    if len(result.strip()) != 0:
                        client_obj = Client(
                            names=result,
                        )
                        client_obj.save()

                        client_type_obj = ClientType(
                            document_number=nro_document,
                            client=client_obj,
                            document_type_id=type_document
                        )
                        client_type_obj.save()

                    else:
                        data = {'error': 'NO EXISTE DNI. REGISTRE MANUALMENTE'}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response

                else:

                    r = query_api_facturacioncloud(nro_document, type_name)

                    name = r.get('Nombre')
                    paternal_name = r.get('Paterno')
                    maternal_name = r.get('Materno')

                    if name is not None and r.get('statusMessage') != 'SERVICIO SE VENCIO' and 'errors' not in r:
                        print('client finded in facturacioncloud')

                        if paternal_name is not None and len(paternal_name) > 0:

                            result = name + ' ' + paternal_name + ' ' + maternal_name
                            nationality = '9589'
                            nationality_obj = Nationality.objects.get(id=nationality)

                            if len(result.strip()) != 0:
                                try:
                                    client_obj = Client(
                                        names=result,
                                        nationality=nationality_obj,
                                    )
                                    client_obj.save()

                                    client_type_obj = ClientType(
                                        document_number=nro_document,
                                        client=client_obj,
                                        document_type_id=type_document
                                    )
                                    client_type_obj.save()

                                except DatabaseError as e:
                                    data = {'error': 'Cliente ya registrado, vuelva a intentar.'}
                                    response = JsonResponse(data)
                                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                                    return response
                            else:
                                data = {'error': 'NO EXISTE DNI. REGISTRE MANUALMENTE'}
                                response = JsonResponse(data)
                                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                                return response
                    else:
                        data = {
                            'error': 'NO EXISTE DNI. REGISTRE MANUALMENTE / FALLO RENIEC'}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response

            elif type_document == '06':

                type_name = 'RUC'
                # r = query_api_free_optimize_ruc(nro_document, type_name)

                r = query_apis_net_dni_ruc(nro_document, type_name)

                if r.get('numeroDocumento') == nro_document:
                    business_name = r.get('nombre')
                    address_business = r.get('direccion')
                    result = business_name
                    address = address_business

                    client_obj = Client(
                        names=result,
                    )
                    client_obj.save()

                    client_type_obj = ClientType(
                        document_number=nro_document,
                        client=client_obj,
                        document_type_id=type_document
                    )
                    client_type_obj.save()

                    client_address_obj = ClientAddress(
                        address=address,
                        client=client_obj
                    )
                    client_address_obj.save()

                else:
                    r = query_api_facturacioncloud(nro_document, type_name)

                    if r.get('statusMessage') != 'SERVICIO SE VENCIO' and r.get('razonSocial') is not None:

                        if r.get('ruc') == nro_document:
                            business_name = r.get('razonSocial')
                            address_business = r.get('direccion')
                            result = business_name
                            address = address_business

                            client_obj = Client(
                                names=result,
                            )
                            client_obj.save()

                            client_type_obj = ClientType(
                                document_number=nro_document,
                                client=client_obj,
                                document_type_id=type_document
                            )
                            client_type_obj.save()

                            client_address_obj = ClientAddress(
                                address=address,
                                client=client_obj
                            )
                            client_address_obj.save()

                    else:

                        data = {'error': 'NO EXISTE RUC. REGISTRE MANUAL O CORREGIRLO'}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response
            else:
                data = {
                    'error': 'No esta registrado en la Base de Datos, favor de registrar manualmente'}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        return JsonResponse({'result': result, 'address': address, 'age': age}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_phone_number_by_name_addressee(request):
    if request.method == 'GET':
        name_addressee = str(request.GET.get('name_addressee', ''))
        client_obj_search = OrderAddressee.objects.filter(names=name_addressee)
        if client_obj_search.exists():
            phone = client_obj_search.first().phone
            return JsonResponse({'phone': phone},
                                status=HTTPStatus.OK)
        else:
            data = {
                'error': 'No tiene telefono registrado'}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_path_list(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation
    path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj).order_by('id')
    return render(request, 'comercial/path_list.html', {
        'subsidiary_obj': subsidiary_obj,
        'path_set': path_set
    })


def get_create_associate_subsidiary_form(request):
    if request.method == 'GET':
        # pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        other_subsidiary_set = Subsidiary.objects.exclude(id=subsidiary_obj.id, serial_two__isnull=True)

        t = loader.get_template('comercial/associate_subsidiary_modal_form.html')
        c = ({
            'subsidiary_set': other_subsidiary_set,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })


def new_associate_subsidiary(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        _associate = request.POST.get('associate')

        _associate_set = Associate.objects.filter(subsidiary=subsidiary_obj)
        _subsidiary_to_associate_obj = Subsidiary.objects.get(id=int(_associate))

        if _associate_set:
            associate_obj = _associate_set.last()
            _associate_detail_set = AssociateDetail.objects.filter(associate=associate_obj,
                                                                   subsidiary=_subsidiary_to_associate_obj)
            if _associate_detail_set:
                data = {'error': 'Sucursal ya asociada'}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
            else:
                associate_detail_obj = AssociateDetail(associate=associate_obj, subsidiary=_subsidiary_to_associate_obj)
                associate_detail_obj.save()
        else:
            associate_obj = Associate(subsidiary=subsidiary_obj)
            associate_obj.save()
            associate_detail_obj = AssociateDetail(associate=associate_obj, subsidiary=_subsidiary_to_associate_obj)
            associate_detail_obj.save()

        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'success': True,
            'grid': t.render(c),
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)


def get_associate_subsidiary(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        associate_detail_obj = AssociateDetail.objects.get(id=int(pk))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        other_subsidiary_set = Subsidiary.objects.exclude(id=subsidiary_obj.id)
        t = loader.get_template('comercial/associate_subsidiary_modal_form.html')
        c = ({
            'associate_detail_obj': associate_detail_obj,
            'subsidiary_set': other_subsidiary_set,
        })

        return JsonResponse({'grid': t.render(c, request)}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def delete_associate_subsidiary(request):
    if request.method == 'POST':
        _associate_detail = request.POST.get('associate-detail')
        _associate = request.POST.get('associate')

        associate_detail_obj = AssociateDetail.objects.get(id=int(_associate_detail))

        try:
            associate_detail_obj.delete()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_create_path_form(request):
    if request.method == 'GET':
        # pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        other_subsidiary_set = Subsidiary.objects.exclude(id=subsidiary_obj.id)

        t = loader.get_template('comercial/path_modal_form.html')
        c = ({
            'subsidiary_obj': subsidiary_obj,
            'subsidiary_set': other_subsidiary_set,
            'choices_types': Path._meta.get_field('type').choices,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })


def new_path(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = user_obj.companyuser.company_rotation
        _name = request.POST.get('name')
        _type = request.POST.get('type', '')
        _destiny = request.POST.get('destiny', '')
        _subsidiary_destiny_obj = Subsidiary.objects.get(id=int(_destiny))
        try:
            path_obj = Path(
                name=_name,
                subsidiary=subsidiary_obj,
                type=_type,
                company=company_obj
            )
            path_obj.save()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        if _type == 'O':
            path_detail_obj = PathDetail(path=path_obj, stopping=1)
            path_detail_obj.save()
            path_subsidiary_obj = PathSubsidiary(path_detail=path_detail_obj, type='O', subsidiary=subsidiary_obj)
            path_subsidiary_obj.save()
            path_subsidiary_destiny_obj = PathSubsidiary(path_detail=path_detail_obj, type='D',
                                                         subsidiary=_subsidiary_destiny_obj)
            path_subsidiary_destiny_obj.save()

        path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'success': True,
            'grid': t.render(c),
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)


def get_path(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        path_obj = Path.objects.get(id=pk)

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        other_subsidiary_set = Subsidiary.objects.exclude(id=subsidiary_obj.id)

        t = loader.get_template('comercial/path_modal_form.html')
        c = ({
            'path_obj': path_obj,
            'subsidiary_set': other_subsidiary_set,
            'choices_types': Path._meta.get_field('type').choices,
        })

        return JsonResponse({'grid': t.render(c, request)}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def delete_path(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        path_obj = Path.objects.get(id=pk)
        try:
            path_obj.delete()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'message': 'Eliminado con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def update_path(request):
    if request.method == 'POST':
        _path = request.POST.get('path')
        _name = request.POST.get('name')
        _destiny = request.POST.get('destiny', '')
        _subsidiary_destiny_obj = Subsidiary.objects.get(id=int(_destiny))
        _type = request.POST.get('type', '')

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = user_obj.companyuser.company_rotation

        path_obj = Path.objects.get(id=_path)
        path_obj.name = _name
        path_obj.type = _type
        path_obj.company = company_obj
        path_obj.save()

        if _type == 'O':
            path_detail_obj = PathDetail(path=path_obj, stopping=1)
            path_detail_obj.save()
            path_subsidiary_obj = PathSubsidiary(path_detail=path_detail_obj, type='O', subsidiary=subsidiary_obj)
            path_subsidiary_obj.save()
            path_subsidiary_destiny_obj = PathSubsidiary(path_detail=path_detail_obj, type='D',
                                                         subsidiary=_subsidiary_destiny_obj)
            path_subsidiary_destiny_obj.save()

        path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_create_road_form(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_set = Subsidiary.objects.all()
        path_obj = Path.objects.get(id=pk)

        t = loader.get_template('comercial/road_modal_form.html')
        c = ({
            'path_obj': path_obj,
            'subsidiary_set': subsidiary_set,
            'choices_types': Path._meta.get_field('type').choices,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })


def new_road(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        company_obj = user_obj.companyuser.company_rotation
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        _path = request.POST.get('path')
        _origin = request.POST.get('origin')
        _destiny = request.POST.get('destiny')
        _stopping = request.POST.get('stopping', '')

        path_obj = Path.objects.get(id=_path)
        subsidiary_origin_obj = Subsidiary.objects.get(id=_origin)
        subsidiary_destiny_obj = Subsidiary.objects.get(id=_destiny)

        try:
            path_detail_obj = PathDetail(path=path_obj, stopping=_stopping)
            path_detail_obj.save()

            path_detail_origin_obj = PathSubsidiary(path_detail=path_detail_obj, subsidiary=subsidiary_origin_obj,
                                                    type='O')
            path_detail_origin_obj.save()

            path_detail_destiny_obj = PathSubsidiary(path_detail=path_detail_obj, subsidiary=subsidiary_destiny_obj,
                                                     type='D')
            path_detail_destiny_obj.save()

        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_obj).order_by('id')
        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'success': True,
            'grid': t.render(c),
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_road(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        path_detail_obj = PathDetail.objects.get(id=pk)
        path_obj = path_detail_obj.path
        subsidiary_set = Subsidiary.objects.all()

        t = loader.get_template('comercial/road_modal_form.html')
        c = ({
            'path_detail_obj': path_detail_obj,
            'path_obj': path_obj,
            'subsidiary_set': subsidiary_set,
            'choices_types': Path._meta.get_field('type').choices,
        })

        return JsonResponse({'grid': t.render(c, request)}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def update_road(request):
    if request.method == 'POST':
        _path = request.POST.get('path')
        _path_detail = request.POST.get('path-detail')
        _origin = request.POST.get('origin')
        _destiny = request.POST.get('destiny')
        _stopping = request.POST.get('stopping')
        subsidiary_origin_obj = Subsidiary.objects.get(id=_origin)
        subsidiary_destiny_obj = Subsidiary.objects.get(id=_destiny)

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        company_obj = user_obj.companyuser.company_rotation
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        path_detail_obj = PathDetail.objects.get(id=_path_detail)
        path_detail_obj._stopping = int(_stopping)
        path_detail_obj.save()

        path_subsidiary_origin_obj = PathSubsidiary.objects.get(type='O', path_detail=path_detail_obj)
        path_subsidiary_origin_obj.subsidiary = subsidiary_origin_obj
        path_subsidiary_origin_obj.save()

        path_subsidiary_destiny_obj = PathSubsidiary.objects.get(type='D', path_detail=path_detail_obj)
        path_subsidiary_destiny_obj.subsidiary = subsidiary_destiny_obj
        path_subsidiary_destiny_obj.save()

        path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_obj).order_by('id')
        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def delete_road(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        path_detail_obj = PathDetail.objects.get(id=pk)
        try:
            path_detail_obj.delete()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'message': 'Eliminado con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_create_destiny_form(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_set = Subsidiary.objects.all()
        path_detail_obj = PathDetail.objects.get(id=pk)

        t = loader.get_template('comercial/destiny_modal_form.html')
        c = ({
            'path_detail_obj': path_detail_obj,
            'subsidiary_set': subsidiary_set,
        })
        return JsonResponse({
            'success': True,
            'grid': t.render(c, request),
        })
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_destiny(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = user_obj.companyuser.company_rotation
        _path_detail = request.POST.get('path-detail')
        _destiny = request.POST.get('name')
        path_detail_obj = PathDetail.objects.get(id=_path_detail)

        try:
            destiny_obj = Destiny(path_detail=path_detail_obj, name=_destiny)
            destiny_obj.save()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        path_set = Path.objects.filter(subsidiary=subsidiary_obj, company=company_obj).order_by('id')
        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'success': True,
            'grid': t.render(c),
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_destiny(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        destiny_obj = Destiny.objects.get(id=pk)
        subsidiary_set = Subsidiary.objects.all()

        t = loader.get_template('comercial/destiny_modal_form.html')
        c = ({
            'destiny_obj': destiny_obj,
            'subsidiary_set': subsidiary_set,
            'choices_types': Path._meta.get_field('type').choices,
        })

        return JsonResponse({'grid': t.render(c, request)}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def update_destiny(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        _destiny = request.POST.get('destiny')
        _name = request.POST.get('name')
        destiny_obj = Destiny.objects.get(id=_destiny)
        destiny_obj.name = _name
        destiny_obj.save()
        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')
        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })
        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def delete_destiny(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        destiny_obj = Destiny.objects.get(id=pk)
        try:
            destiny_obj.delete()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        path_set = Path.objects.filter(subsidiary=subsidiary_obj).order_by('id')

        t = loader.get_template('comercial/path_list_grid.html')
        c = ({
            'path_set': path_set,
        })

        return JsonResponse({
            'message': 'Eliminado con exito.',
            'grid': t.render(c),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def manifest_comodity_list(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        company_rotation_obj = user_obj.companyuser.company_rotation
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = Company.objects.get(ruc='20612403083')
        company_user_set = CompanyUser.objects.filter(user=user_obj)
        if company_user_set.exists():
            company_user_obj = company_user_set.last()
            company_user_obj.company_rotation = company_obj
            company_user_obj.save()
        serials = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
                                                    company_rotation_obj=company_rotation_obj)
        # serial_commodity = serials.get('serial_commodity')
        serial_commodity = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
                                                             company_rotation_obj=company_obj,
                                                             type_document='T')
        date_now = datetime.now().strftime("%Y-%m-%d")
        programmings = get_programmings(False, subsidiary_obj=subsidiary_obj, company_obj=company_rotation_obj)
        date_now = datetime.now().strftime("%Y-%m-%d")
        # programmings = Programming.objects.filter(status__in=['P'], subsidiary=subsidiary_obj, departure_date=date_now).order_by('id')
        programming_set = Programming.objects.filter(departure_date=date_now, subsidiary=subsidiary_obj)

        return render(request, 'comercial/manifest_assign_list.html', {
            'date_now': date_now,
            'programmings': programmings,
            'serial': serial_commodity,
            'programming_set': programming_set
        })

    elif request.method == 'POST':
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        if start_date == end_date:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=start_date,
                                             status='P').order_by('id')
        else:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', status='P',
                                             traslate_date__range=[start_date, end_date]).order_by('id')
        has_rows = False
        if order_set:
            has_rows = True
        else:
            data = {'error': "No hay encomiendas registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/manifest_grid_list.html')
        context = ({
            'order_set': order_set,
            'has_rows': has_rows,

        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_programming_manifest(request):
    if request.method == 'GET':
        id_programming = request.GET.get('programming', '')
        type_programming = str(request.GET.get('type_programming', ''))
        programming_obj = Programming.objects.get(id=int(id_programming))
        pilot = programming_obj.setemployee_set.filter(function='P').first().employee.full_name()
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj).order_by(
            'order_id')
        subsidiary_company_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj,
                                                                  company=programming_obj.company).last()
        serial_manifest = subsidiary_company_obj.serial_fourth

        tpl = loader.get_template('comercial/guide_programming_assign_list.html')
        context = ({
            'programming_orders_set': programming_orders_set,
            'type': type_programming
        })

        # tpl = loader.get_template('comercial/manifest_programming_grid.html')
        # context = ({
        #     'programming_orders_set': programming_orders_set,
        # })
        turn = '-'
        if turn == '':
            turn = programming_obj.truck_exit.strftime("%H:%M%p")
        else:
            turn = '-'

        return JsonResponse({
            'license_plate': programming_obj.truck.license_plate,
            'serial_manifest': serial_manifest,
            # 'turn': programming_obj.get_turn_display()[0:8],
            'turn': turn,
            'pilot': pilot,
            'origin': programming_obj.path.get_first_point().short_name,
            'destiny': programming_obj.path.get_last_point().short_name,
            'departure_date': programming_obj.departure_date,
            'driver_type': programming_obj.truck.get_drive_type_display(),
            'license': programming_obj.setemployee_set.filter(function='P').first().employee.n_license,
            'license_type': programming_obj.setemployee_set.filter(
                function='P').first().employee.get_license_type_display(),
            'grid': tpl.render(context, request),

        }, status=HTTPStatus.OK)


def get_programming_order(request):
    if request.method == 'GET':
        programming_id = request.GET.get('programming_id', '')

        programming_obj = Programming.objects.get(id=programming_id)
        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj)
        tpl = loader.get_template('comercial/programming_list.html')
        context = ({'programming_orders_set': programming_orders_set})

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def add_order_to_order_programming(request):
    if request.method == 'GET':
        orders = request.GET.get('orders', '')
        programming_id = request.GET.get('programming_id', '')
        start_date = request.GET.get('start-date', '')
        end_date = request.GET.get('end-date', '')
        _type_programming = request.GET.get('_type_programming', '')
        list_orders = orders.split(",")
        programming_obj = Programming.objects.get(id=programming_id)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        for i in list_orders:
            order_obj = Order.objects.get(pk=int(i))
            order_programing_obj = OrderProgramming(
                order=order_obj,
                programming=programming_obj,
                shipping_type='B',
                shipping_condition='C'
            )

            order_programing_obj.save()
            order_obj.status = 'C'
            order_obj.save()
        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj, manifest=None).order_by(
            'order_id')
        if start_date == end_date:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=start_date,
                                             status='P').order_by('id')
        else:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', status='P',
                                             traslate_date__range=[start_date, end_date]).order_by('id')

        tpl = loader.get_template('comercial/manifest_programming_grid.html')
        context = ({'programming_orders_set': programming_orders_set, 'type': _type_programming})

        tpl2 = loader.get_template('comercial/manifest_grid_list.html')
        context2 = ({'order_set': order_set})

        return JsonResponse({
            'message': 'Encomiendas asignadas correctamente',
            'grid': tpl.render(context, request),
            'grid2': tpl2.render(context2, request),
            'programming_id': programming_obj.id
        }, status=HTTPStatus.OK)


def remove_order_to_order_programming(request):
    if request.method == 'GET':
        orders = request.GET.get('orders', '')
        programming_id = request.GET.get('programming_id', '')
        start_date = request.GET.get('start-date', '')
        end_date = request.GET.get('end-date', '')
        list_orders = orders.split(",")
        programming_obj = Programming.objects.get(id=programming_id)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        for i in list_orders:
            if i != '':
                order_obj = Order.objects.get(pk=int(i))
                order_programing_obj = OrderProgramming.objects.get(order=order_obj)
                order_programing_obj.delete()
                order_obj.status = 'P'
                order_obj.save()
        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj, manifest=None).order_by(
            'order_id')
        if start_date == end_date:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=start_date,
                                             status='P').order_by('id')
        else:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', status='P',
                                             traslate_date__range=[start_date, end_date]).order_by('id')

        tpl = loader.get_template('comercial/manifest_programming_grid.html')
        context = ({'programming_orders_set': programming_orders_set})

        tpl2 = loader.get_template('comercial/manifest_grid_list.html')
        context2 = ({'order_set': order_set})

        return JsonResponse({
            'message': 'Encomiendas asignadas correctamente',
            'grid': tpl.render(context, request),
            'grid2': tpl2.render(context2, request),
        }, status=HTTPStatus.OK)


def get_programming_query_list(request):
    if request.method == 'GET':
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        subsidiary_set = Subsidiary.objects.all()

        return render(request, 'comercial/programming_query_list.html', {
            'formatdate': formatdate,
            'subsidiary_set': subsidiary_set
        })
    elif request.method == 'POST':
        id_subsidiary = int(request.POST.get('subsidiary'))
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))

        if start_date == end_date:
            programming_set = Programming.objects.filter(departure_date=start_date,
                                                         subsidiary__id=id_subsidiary).order_by('truck_exit')
        else:
            programming_set = Programming.objects.filter(departure_date__range=[start_date, end_date],
                                                         subsidiary__id=id_subsidiary).order_by('truck_exit')

        if programming_set:
            has_rows = True
        else:
            data = {'error': "No hay operaciones registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        tpl = loader.get_template('comercial/programming_list.html')
        context = (
            {'programmings': programming_set, 'show_plan': True, 'show_lp': True, 'subsidiary_obj': subsidiary_obj})

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def generate_manifest(request):
    programming_id = request.GET.get('programming', '')
    programming_obj = Programming.objects.get(id=programming_id)
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    subsidiary_company_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj,
                                                              company=programming_obj.company).last()
    serial_manifest = subsidiary_company_obj.serial_fourth
    company_rotation_obj = user_obj.companyuser.company_rotation

    orders = request.GET.get('orders', '')
    list_orders = orders.split(",")

    manifest_obj = Manifest(
        serial=serial_manifest,
        user=user_obj,
        subsidiary=subsidiary_obj,
        company=company_rotation_obj
    )
    manifest_obj.save()

    for i in list_orders:
        order_obj = Order.objects.get(pk=int(i))
        order_programing_obj = OrderProgramming.objects.get(order=order_obj)
        order_programing_obj.manifest = manifest_obj
        order_programing_obj.save()

    programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj, manifest=None).order_by(
        'order_id')

    tpl = loader.get_template('comercial/manifest_programming_grid.html')
    context = ({'programming_orders_set': programming_orders_set})

    return JsonResponse({
        'grid': tpl.render(context, request),
        'manifest': manifest_obj.id
    }, status=HTTPStatus.OK)


def generate_guide(request):
    order_id = request.GET.get('order_id', '')
    serie_guide = str(int(request.GET.get('serie_guide', ''))).zfill(4)
    nro_guide = str(int(request.GET.get('nro_guide', ''))).zfill(6)
    order_obj = Order.objects.get(id=order_id)

    order_programing_obj = OrderProgramming.objects.get(order=order_obj)
    programming_obj = order_programing_obj.programming
    order_programing_obj.guide_serial = serie_guide
    order_programing_obj.guide_code = nro_guide
    order_programing_obj.save()

    programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj, manifest=None).order_by(
        'order_id')

    tpl = loader.get_template('comercial/manifest_programming_grid.html')
    context = ({'programming_orders_set': programming_orders_set, 'type': 'S'})

    return JsonResponse({
        'grid': tpl.render(context, request),
        'message': 'GUÍA GENERADA CORRECTAMENTE',
        'order_programming_id': order_programing_obj.order.id
    }, status=HTTPStatus.OK)


def report_comodity_grid(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation
        date_now = datetime.now().strftime("%Y-%m-%d")
        programmings = get_programmings(False, subsidiary_obj=subsidiary_obj, company_obj=company_rotation_obj)
        # serials = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
        #                                             company_rotation_obj=company_rotation_obj)
        subsidiaries_set = Subsidiary.objects.all().exclude(id=subsidiary_obj.id)
        # serial_commodity = serials.get('serial_commodity')
        company_obj = Company.objects.get(ruc='20612403083')
        company_user_set = CompanyUser.objects.filter(user=user_obj)
        if company_user_set.exists():
            company_user_obj = company_user_set.last()
            company_user_obj.company_rotation = company_obj
            company_user_obj.save()

        serial_commodity = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
                                                             company_rotation_obj=company_obj,
                                                             type_document='T')

        # programmings = Programming.objects.filter(status__in=['P'], subsidiary=subsidiary_obj, departure_date=date_now).order_by('id')
        return render(request, 'comercial/report_comodity.html', {
            'date_now': date_now,
            'programmings': programmings,
            'serial': serial_commodity,
            'subsidiaries_set': subsidiaries_set
        })

    elif request.method == 'POST':
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))
        user_type = int(request.POST.get('user'))
        way_to_pay = str(request.POST.get('way_to_pay'))
        destiny = request.POST.get('destiny')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        cont_counted = 0
        cont_destination_payment = 0
        order_route_set = ''

        if destiny == 'T' and way_to_pay == 'T':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            order__traslate_date__range=[start_date,
                                                                                         end_date]).order_by(
                    'order__id').distinct('order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            order__traslate_date__range=[start_date,
                                                                                         end_date]).order_by(
                    'order__id').distinct('order__id')
        if destiny == 'T' and way_to_pay == 'C':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='C').order_by('order__id').distinct(
                    'order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='C').order_by('order__id').distinct(
                    'order__id')
        if destiny == 'T' and way_to_pay == 'D':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='D').order_by('order__id').distinct(
                    'order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='D').order_by('order__id').distinct(
                    'order__id')

        if destiny != 'T' and way_to_pay == 'T':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date,
                                                                                         end_date]).order_by(
                    'order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date,
                                                                                         end_date]).order_by(
                    'order__id')
        if destiny != 'T' and way_to_pay == 'C':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='C').order_by('order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='C').order_by('order__id')
        if destiny != 'T' and way_to_pay == 'D':
            if user_type == 1:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E',
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='D').order_by('order__id')
            elif user_type == 2:
                order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                            order__type_order='E', order__user=user_obj,
                                                            type='D',
                                                            subsidiary__id=destiny,
                                                            order__traslate_date__range=[start_date, end_date],
                                                            order__way_to_pay='D').order_by('order__id')

        order_dict = get_order_comodity_values(order_route_set=order_route_set)

        if order_route_set.count() > 0:
            for o in order_route_set:
                if o.order.status != 'A':
                    if o.order.way_to_pay == 'C':
                        cont_counted = cont_counted + o.order.total
                    elif o.order.way_to_pay == 'D':
                        cont_destination_payment = cont_destination_payment + o.order.total

        has_rows = False
        if order_route_set:
            has_rows = True
        else:
            data = {'error': "No hay encomiendas registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/report_comodity_grid.html')
        context = ({
            'order_set': order_dict,
            'sum_counted': cont_counted,
            'sum_destination_payment': cont_destination_payment,
            'has_rows': has_rows,
            'subsidiary': subsidiary_obj,
            'f1': start_date,
            'f2': end_date,
            't': user_type,
            'w': way_to_pay,
            'd': destiny,
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_order_comodity_values(order_route_set=None):
    order_dict = []
    get_status_display = {'A': 'Anulado', 'C': 'Completado'}
    cont_counted = 0
    for o in order_route_set:
        item_detail_order = []
        item_route_origin = []
        item_route_destiny = []
        item_action_addressee = []
        item_action_sender = []
        item_order_programming = []
        item_set_employee = []

        order_detail_set = OrderDetail.objects.filter(order__id=o.order.id).values(
            'id',
            'quantity',
            'unit_id',
            'unit__description',
            'weight',
        )
        order_route_origin_set = OrderRoute.objects.filter(order_id=o.order.id, type='O').values(
            'id',
            'type',
            'subsidiary__name',
        )
        order_route_destiny_set = OrderRoute.objects.filter(order_id=o.order.id, type='D').values(
            'id',
            'type',
            'subsidiary__id',
            'subsidiary__name',
        )
        order_action_addressee_set = OrderAction.objects.filter(order__id=o.order.id, type='D').values(
            'id',
            'client__names',
            'order_addressee__names'
        )
        order_action_sender_set = OrderAction.objects.filter(order__id=o.order.id, type='R').values(
            'id',
            'client__names',
        )

        order_programming_set = OrderProgramming.objects.filter(order__id=o.order.id).values(
            'programming__truck_exit',
            'programming__id'
        )

        if order_programming_set.exists():
            order_programming_obj = order_programming_set.first()

            item_order_programming_o = {
                'hour_exit': order_programming_obj['programming__truck_exit'],
                'programming__id': order_programming_obj['programming__id']
            }
            item_order_programming.append(item_order_programming_o)

            set_employee_set = SetEmployee.objects.filter(function='P',
                                                          programming__id=order_programming_obj[
                                                              'programming__id']).values(
                'id',
                'employee__names',
                'employee__paternal_last_name',
                'employee__maternal_last_name',
            )
            if set_employee_set.exists():
                set_employee_obj = set_employee_set.first()
                names = ''
                paternal_name = ''
                maternal_name = ''
                if set_employee_obj['employee__names'] is not None:
                    names = set_employee_obj['employee__names']
                if set_employee_obj['employee__paternal_last_name'] is not None:
                    paternal_name = set_employee_obj['employee__paternal_last_name']
                if set_employee_obj['employee__maternal_last_name'] is not None:
                    maternal_name = set_employee_obj['employee__maternal_last_name']

                item_set_employee_o = {
                    'id': set_employee_obj['id'],
                    'names': names + ' ' + paternal_name + ' ' + maternal_name
                }
                item_set_employee.append(item_set_employee_o)

        if order_route_origin_set.exists():
            order_route_origin_obj = order_route_origin_set.first()

            item_route_o = {
                'id': order_route_origin_obj['id'],
                'type': order_route_origin_obj['type'],
                'subsidiary': order_route_origin_obj['subsidiary__name']
            }
            item_route_origin.append(item_route_o)

        if order_route_destiny_set.exists():
            order_route_destiny_obj = order_route_destiny_set.first()

            item_route_d = {
                'id': order_route_destiny_obj['id'],
                'type': order_route_destiny_obj['type'],
                'subsidiary': order_route_destiny_obj['subsidiary__name']
            }
            item_route_destiny.append(item_route_d)

        if order_action_sender_set.exists():
            order_action_sender_obj = order_action_sender_set.first()

            item_action_s = {
                'id': order_action_sender_obj['id'],
                'client_names': order_action_sender_obj['client__names'],
            }
            item_action_sender.append(item_action_s)

        for d in order_detail_set:
            item_detail = {
                'id': d['id'],
                'quantity': d['quantity'],
                'unit_id': d['unit_id'],
                'weight': d['weight'],
                'unit_description': d['unit__description']
            }
            item_detail_order.append(item_detail)

        for oa in order_action_addressee_set:
            _client_names = ''
            if oa['client__names'] is None:
                _client_names = oa['order_addressee__names']
            else:
                _client_names = oa['client__names']
            item_action_a = {
                'id': oa['id'],
                'client_names': _client_names
            }
            item_action_addressee.append(item_action_a)

        if o.order.way_to_pay == 'C':
            cont_counted = cont_counted + o.order.total

        order_item = {
            'id': o.order.id,
            'traslate_date': o.order.traslate_date,
            'type_document': o.order.type_document,
            'serial': o.order.serial,
            'correlative_sale': o.order.correlative_sale,
            'total': o.order.total,
            'way_to_pay': o.order.way_to_pay,
            'status': o.order.status,
            'user': o.order.user.worker_set.last().employee.names,
            'sum_counted': cont_counted,
            'item_detail_order': item_detail_order,
            'item_route_origin': item_route_origin,
            'item_route_destiny': item_route_destiny,
            'item_action_addressee': item_action_addressee,
            'item_action_sender': item_action_sender,
            'item_set_employee': item_set_employee,
            'item_order_programming': item_order_programming,
        }
        order_dict.append(order_item)

    return order_dict


def report_manifest_grid(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_rotation_obj = user_obj.companyuser.company_rotation
        date_now = datetime.now().strftime("%Y-%m-%d")
        serials = get_serial_subsidiary_company(subsidiary_obj=subsidiary_obj,
                                                company_rotation_obj=company_rotation_obj)
        serial_commodity = serials.get('serial_commodity')
        programmings = get_programmings(False, subsidiary_obj=subsidiary_obj, company_obj=company_rotation_obj)
        # programmings = Programming.objects.filter(status__in=['P'], subsidiary=subsidiary_obj, departure_date=date_now).order_by('id')
        return render(request, 'comercial/report_manifest.html', {
            'date_now': date_now,
            'programmings': programmings,
            'serial': serial_commodity
        })

    elif request.method == 'POST':
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        if start_date == end_date:
            # op_set = OrderProgramming.objects.filter(manifest__subsidiary=subsidiary_obj, manifest__created_at__date=start_date, manifest__isnull=False).annotate(Sum('manifest_id')).first()
            manifest_set = Manifest.objects.filter(subsidiary=subsidiary_obj, created_at__date=start_date)
        else:
            manifest_set = Manifest.objects.filter(subsidiary=subsidiary_obj,
                                                   created_at__date__range=[start_date, end_date])
            # op_set = OrderProgramming.objects.filter(manifest__subsidiary=subsidiary_obj, manifest__created_at__date__range=[start_date, end_date], manifest__isnull=False).annotate(Sum('manifest_id')).first()

        has_rows = False
        if manifest_set:
            has_rows = True
        else:
            data = {'error': "No hay manifiestos registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/report_manifest_grid.html')
        context = ({
            'manifest_set': manifest_set,
            'has_rows': has_rows
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_truck(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')

        truck_set = Truck.objects.filter(id=pk)
        truck_serialized_data = serializers.serialize('json', truck_set)
        return JsonResponse({
            'success': True,
            'truck_serialized': truck_serialized_data,
        })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


def new_pilot_associate(request):
    data = dict()
    if request.method == 'GET':

        id = request.GET.get('truck_id')
        license_plate = request.GET.get('license_plate')
        associates = request.GET.get('associates', '')
        _arr = []
        if associates != '[]':
            str1 = associates.replace(']', '').replace('[', '')
            _arr = str1.replace('"', '').split(",")
            truck_obj = Truck.objects.get(id=int(id))
            associated_set = TruckAssociate.objects.filter(truck=truck_obj)
            associated_set.delete()
            for a in _arr:
                employee_obj = Employee.objects.get(id=int(a))
                truck_associate_obj = TruckAssociate(truck=truck_obj, employee=employee_obj)
                truck_associate_obj.save()
        else:
            data['error'] = "Ingrese valores validos."
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        return JsonResponse({'success': True, 'message': 'El conductor se asocio correctamente.'})
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


def get_pilots_associated(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        truck_obj = Truck.objects.get(id=pk)
        associated_set = TruckAssociate.objects.filter(truck=truck_obj).values('employee_id', 'employee__names',
                                                                               'employee__paternal_last_name',
                                                                               'employee__maternal_last_name')
        # associated_serialized = serializers.serialize('json', associated_set)
        return JsonResponse({
            'success': True,
            'associated': list(associated_set),
        })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


def receive_manifests(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        company_rotation_obj = user_obj.companyuser.company_rotation
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        company_obj = Company.objects.get(ruc='20612403083')
        company_user_set = CompanyUser.objects.filter(user=user_obj)
        if company_user_set.exists():
            company_user_obj = company_user_set.last()
            company_user_obj.company_rotation = company_obj
            company_user_obj.save()
        serial_commodity = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
                                                             company_rotation_obj=company_obj,
                                                             type_document='T')

        # serials = get_serial_manifest_and_commodity(subsidiary_obj=subsidiary_obj,
        #                                             company_rotation_obj=company_rotation_obj)
        # serial_commodity = serials.get('serial_commodity')
        date_now = datetime.now().strftime("%Y-%m-%d")
        programmings = get_programmings(False, subsidiary_obj=subsidiary_obj, company_obj=company_rotation_obj)
        return render(request, 'comercial/receive_manifest.html', {
            'date_now': date_now,
            'programmings': programmings,
            'serial': serial_commodity,
        })

    elif request.method == 'POST':
        start_date = str(request.POST.get('start-date'))
        end_date = str(request.POST.get('end-date'))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, cash_type='E')
        subsidiary_set = Subsidiary.objects.all()
        # subsidiary_obj_mejia = Subsidiary.objects.get(name='SEDE MEJIA')
        # subsidiary_obj_matarani = Subsidiary.objects.get(name='SEDE MATARANI')
        # cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')

        # if subsidiary_obj.name == 'SEDE CAMANA':
        #     orders_set = OrderProgramming.objects.filter(
        #         order__orderroute__subsidiary__id__in=[subsidiary_obj.id, subsidiary_obj_matarani.id,
        #                                                subsidiary_obj_mejia.id],
        #         order__orderroute__type='D',
        #         order__traslate_date__range=[start_date, end_date]).order_by('order_id')
        # else:
        #     orders_set = OrderProgramming.objects.filter(order__orderroute__subsidiary=subsidiary_obj,
        #                                                  order__orderroute__type='D',
        #                                                  order__traslate_date__range=[start_date,
        #                                                                               end_date]).order_by('order_id')
        orders_set = OrderProgramming.objects.filter(order__orderroute__subsidiary=subsidiary_obj,
                                                     order__orderroute__type='D',
                                                     order__traslate_date__range=[start_date,
                                                                                  end_date]).order_by('order_id')
        order_dict = get_order_receive_values(orders_set)

        has_rows = False
        if orders_set:
            has_rows = True
        else:
            data = {'error': "No existen encomiendas en el rango de fechas seleccionado"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/receive_manifests_grid.html')
        context = ({
            'orders_set': order_dict,
            'has_rows': has_rows,
            'cash_set': cash_set,
            'subsidiary': subsidiary_obj,
            'subsidiaries': subsidiary_set,
            'f1': start_date,
            'f2': end_date,
            'type_commodity': Order._meta.get_field('type_commodity').choices

        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_order_receive_values(order_set=None):
    order_dict = []
    cont_counted = 0
    for o in order_set:
        item_detail_order = []
        item_route_origin = []
        item_route_destiny = []
        item_action_addressee = []
        item_action_sender = []
        item_order_programming = []
        item_set_employee = []

        order_detail_set = OrderDetail.objects.filter(order__id=o.order.id).values(
            'id',
            'quantity',
            'unit_id',
            'unit__description',
            'weight',
        )
        order_route_origin_set = OrderRoute.objects.filter(order_id=o.order.id, type='O').values(
            'id',
            'type',
            'subsidiary__name',
        )
        order_route_destiny_set = OrderRoute.objects.filter(order_id=o.order.id, type='D').values(
            'id',
            'type',
            'subsidiary__name',
        )
        order_action_addressee_set = OrderAction.objects.filter(order__id=o.order.id, type='D').values(
            'id',
            'client__names',
            'order_addressee__names'
        )
        order_action_sender_set = OrderAction.objects.filter(order__id=o.order.id, type='R').values(
            'id',
            'client__names',
        )
        order_programming_set = OrderProgramming.objects.filter(order__id=o.order.id).values(
            'programming__truck_exit',
            'programming__id'
        )

        if order_programming_set.exists():
            order_programming_obj = order_programming_set.first()

            item_order_programming_o = {
                'hour_exit': order_programming_obj['programming__truck_exit'],
                'programming__id': order_programming_obj['programming__id']
            }
            item_order_programming.append(item_order_programming_o)

            set_employee_set = SetEmployee.objects.filter(function='P',
                                                          programming__id=order_programming_obj[
                                                              'programming__id']).values(
                'id',
                'employee__names',
                'employee__paternal_last_name',
                'employee__maternal_last_name',
            )
            if set_employee_set.exists():
                set_employee_obj = set_employee_set.first()
                names = ''
                paternal_name = ''
                maternal_name = ''
                if set_employee_obj['employee__names'] is not None:
                    names = set_employee_obj['employee__names']
                if set_employee_obj['employee__paternal_last_name'] is not None:
                    paternal_name = set_employee_obj['employee__paternal_last_name']
                if set_employee_obj['employee__maternal_last_name'] is not None:
                    maternal_name = set_employee_obj['employee__maternal_last_name']

                item_set_employee_o = {
                    'id': set_employee_obj['id'],
                    'names': names + ' ' + paternal_name + ' ' + maternal_name
                }
                item_set_employee.append(item_set_employee_o)

        if order_route_origin_set.exists():
            order_route_origin_obj = order_route_origin_set.first()

            item_route_o = {
                'id': order_route_origin_obj['id'],
                'type': order_route_origin_obj['type'],
                'subsidiary': order_route_origin_obj['subsidiary__name']
            }
            item_route_origin.append(item_route_o)

        if order_route_destiny_set.exists():
            order_route_destiny_obj = order_route_destiny_set.first()

            item_route_d = {
                'id': order_route_destiny_obj['id'],
                'type': order_route_destiny_obj['type'],
                'subsidiary': order_route_destiny_obj['subsidiary__name']
            }
            item_route_destiny.append(item_route_d)

        if order_action_sender_set.exists():
            order_action_sender_obj = order_action_sender_set.first()

            item_action_s = {
                'id': order_action_sender_obj['id'],
                'client_names': order_action_sender_obj['client__names'],
            }
            item_action_sender.append(item_action_s)

        for d in order_detail_set:
            item_detail = {
                'id': d['id'],
                'quantity': d['quantity'],
                'unit_id': d['unit_id'],
                'weight': d['weight'],
                'unit_description': d['unit__description']
            }
            item_detail_order.append(item_detail)

        for oa in order_action_addressee_set:
            _client_names = ''
            if oa['client__names'] is None:
                _client_names = oa['order_addressee__names']
            else:
                _client_names = oa['client__names']
            item_action_a = {
                'id': oa['id'],
                'client_names': _client_names
            }
            item_action_addressee.append(item_action_a)

        order_item = {
            'id': o.order.id,
            'traslate_date': o.order.traslate_date,
            'serial': o.order.serial,
            'correlative_sale': o.order.correlative_sale,
            'total': o.order.total,
            'way_to_pay': o.order.way_to_pay,
            'get_way_to_pay_display': o.order.get_way_to_pay_display(),
            'status': o.order.status,
            'type_commodity': o.order.type_commodity,
            'user': o.order.user.worker_set.last().employee.names,
            'sum_counted': cont_counted,
            'item_detail_order': item_detail_order,
            'item_route_origin': item_route_origin,
            'item_route_destiny': item_route_destiny,
            'item_action_addressee': item_action_addressee,
            'item_action_sender': item_action_sender,
            'item_set_employee': item_set_employee,
            'item_order_programming': item_order_programming,
        }
        order_dict.append(order_item)

    return order_dict


def change_type_commodity(request):
    if request.method == 'GET':
        type_commodity = str(request.GET.get('type_commodity', ''))
        way_to_pay = str(request.GET.get('way_to_pay', ''))
        total = decimal.Decimal(str(request.GET.get('total', '')).replace(',', '.'))
        cash_id = int(request.GET.get('cash', ''))
        cash_obj = Cash.objects.get(id=cash_id)
        order_id = request.GET.get('order_id', '')
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        order_obj = Order.objects.get(pk=order_id)
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        cashflow_set = CashFlow.objects.filter(cash_id=cash_id, transaction_date=formatdate, type='A')

        serial_description_cash = 'PAGO DE LA ENCOMIENDA PAGO DESTINO G{}-{}'.format(order_obj.serial,
                                                                                     order_obj.correlative_sale.zfill(
                                                                                         6))
        if way_to_pay == 'PAGO DESTINO':
            if cashflow_set.count() > 0:
                save_cash_flow(cash_obj=cash_obj, order_obj=order_obj, user_obj=user_obj,
                               cash_flow_transact_date=formatdate,
                               cash_flow_description=str(serial_description_cash),
                               cash_flow_type='E',
                               cash_flow_total=total)
            else:
                data = {'error': "No existe una Apertura de Caja, Favor de Aperturar la caja de Encomiendas"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        order_obj.type_commodity = type_commodity
        order_obj.save()

        return JsonResponse({
            'success': True,
            'message': 'Se actualizo la encomienda correctamente.'
        })
    return JsonResponse({'error': True, 'message': 'Error de petición, contactar con sistemas.'})


def cancel_commodity(request):
    if request.method == 'GET':
        start_date = str(request.GET.get('start-date'))
        end_date = str(request.GET.get('end-date'))
        order_id = int(request.GET.get('pk', ''))
        order_obj = Order.objects.get(pk=order_id)
        order_obj.status = 'A'
        order_obj.save()
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        cash_obj = CashFlow.objects.filter(order=order_obj)
        cash_obj.delete()

        if start_date == end_date:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', status__in=['P', 'C'],
                                             traslate_date=start_date).order_by('id')
        else:
            order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', status__in=['P', 'C'],
                                             traslate_date__range=[start_date, end_date]).order_by('id')
        has_rows = False
        if order_set:
            has_rows = True
        else:
            data = {'error': "No hay encomiendas registradas"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        tpl = loader.get_template('comercial/report_comodity_grid.html')
        context = ({
            'order_set': order_set,
            'has_rows': has_rows
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def add_order_to_order_programming_guide(request):
    if request.method == 'GET':
        orders = request.GET.get('orders', '')
        programming_id = request.GET.get('programming_id', '')
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        # start_date = request.GET.get('start-date', '')
        # end_date = request.GET.get('end-date', '')
        _type_programming = request.GET.get('_type_programming', '')
        list_orders = orders.split(",")
        programming_obj = Programming.objects.get(id=programming_id)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        for i in list_orders:
            order_obj = Order.objects.get(pk=int(i))
            order_programing_obj = OrderProgramming(
                order=order_obj,
                programming=programming_obj,
                shipping_type='B',
                shipping_condition='C'
            )
            order_programing_obj.save()
            order_obj.status = 'C'
            order_obj.save()

        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj).order_by(
            'order_id')
        order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=formatdate,
                                         status='P').order_by('id')

        # tpl = loader.get_template('comercial/manifest_programming_grid.html')
        # context = ({'programming_orders_set': programming_orders_set, 'type': _type_programming})
        #
        # tpl2 = loader.get_template('comercial/manifest_grid_list.html')
        # context2 = ({'order_set': order_set})

        tpl = loader.get_template('comercial/guide_programming_assign_list.html')
        context = ({'programming_orders_set': programming_orders_set, 'type': _type_programming})

        tpl2 = loader.get_template('comercial/guide_programming_unassign_list.html')
        context2 = ({'order_set': order_set})

        return JsonResponse({
            'message': 'Encomiendas asignadas correctamente',
            'grid': tpl.render(context, request),
            'grid2': tpl2.render(context2, request),
            'programming_id': programming_obj.id
        }, status=HTTPStatus.OK)


def remove_order_to_order_programming_guide(request):
    if request.method == 'GET':
        orders = request.GET.get('orders', '')
        programming_id = request.GET.get('programming_id', '')
        # start_date = request.GET.get('start-date', '')
        # end_date = request.GET.get('end-date', '')
        my_date = datetime.now()
        formatdate = my_date.strftime("%Y-%m-%d")
        list_orders = orders.split(",")
        programming_obj = Programming.objects.get(id=programming_id)
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        for i in list_orders:
            if i != '':
                order_obj = Order.objects.get(pk=int(i))
                order_programing_obj = OrderProgramming.objects.get(order=order_obj)
                order_programing_obj.delete()
                order_obj.status = 'P'
                order_obj.save()
        programming_orders_set = OrderProgramming.objects.filter(programming=programming_obj, manifest=None).order_by(
            'order_id')

        order_set = Order.objects.filter(subsidiary=subsidiary_obj, type_order='E', traslate_date=formatdate,
                                         status='P').order_by('id')

        tpl = loader.get_template('comercial/guide_programming_assign_list.html')
        context = ({'programming_orders_set': programming_orders_set})

        tpl2 = loader.get_template('comercial/guide_programming_unassign_list.html')
        context2 = ({'order_set': order_set})

        return JsonResponse({
            'message': 'Encomiendas asignadas correctamente',
            'grid': tpl.render(context, request),
            'grid2': tpl2.render(context2, request),
        }, status=HTTPStatus.OK)


def get_modal_change(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        _subsidiary_origin = request.GET.get('_subsidiary_origin', '')
        _order_id = request.GET.get('_order_id', '')
        tpl = loader.get_template('comercial/new_destiny_comodity.html')
        subsidiary_set = ''
        if subsidiary_obj.id == 1:
            subsidiary_set = Subsidiary.objects.all().exclude(id=subsidiary_obj.id)

        context = ({
            'subsidiary_set': subsidiary_set,
            'subsidiary_origin': _subsidiary_origin,
            'order_id': _order_id,
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def change_destiny(request):
    if request.method == 'POST':
        order_id = request.POST.get('orden', '')
        new_destiny = int(request.POST.get('new_destiny', ''))
        new_subsidiary_destiny_obj = Subsidiary.objects.get(id=new_destiny)
        order_obj = Order.objects.get(id=int(order_id))
        order_route_obj = OrderRoute.objects.filter(order=order_obj, type='D').first()
        order_route_obj.subsidiary = new_subsidiary_destiny_obj
        order_route_obj.save()
        # serialized_new_subsidiary_destiny = serializers.serialize('json', new_subsidiary_destiny_obj)

        return JsonResponse({
            'message': 'Sucursal actualizada correctamente',
            'destiny': new_subsidiary_destiny_obj.name,
        }, status=HTTPStatus.OK)


def get_modal_way_pay(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        way_to_pay = request.GET.get('way_to_pay', '')
        _order_id = request.GET.get('_order_id', '')
        tpl = loader.get_template('comercial/new_way_to_pay_modal.html')

        context = ({
            'choices_type_payments': Guide._meta.get_field('way_to_pay').choices,
            'order_id': _order_id,
        })
        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def change_way_to_pay(request):
    if request.method == 'POST':
        order_id = request.POST.get('orden', '')
        way_to_pay = str(request.POST.get('way_to_pay', ''))
        order_obj = Order.objects.get(id=int(order_id))
        order_obj.way_to_pay = way_to_pay
        order_obj.save()
        return JsonResponse({
            'message': 'Cambio actualizado correctamente',
            'way_to_pay': way_to_pay,
            'total': order_obj.total,
        }, status=HTTPStatus.OK)


def departures_of_month(request):
    my_date = datetime.now()
    departure_set = Departure.objects.filter(month=my_date.month).prefetch_related(
        Prefetch('departuredetail_set')
    ).select_related('truck__owner')

    first_day_of_the_month = datetime.today().replace(day=1)
    last_day_of_the_month = last_day_of_month(my_date.date())
    print(first_day_of_the_month)
    print(last_day_of_the_month)

    days_of_month_choices = []
    weekday = ['DOM', 'LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB']
    for i in range(1, last_day_of_the_month.day + 1):
        w = date_time.datetime(my_date.year, my_date.month, i).strftime('%w')
        days_of_month_choices.append((i, weekday[int(w)]))

    return render(request, 'comercial/departures_of_month_list.html', {
        'departure_set': departure_set,
        'days_of_month_choices': days_of_month_choices,
    })


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def report_expiration_soat_and_technical(request):
    my_date = datetime.now().date()
    truck_associate_set = TruckAssociate.objects.all().annotate(
        difference_soat_date=ExpressionWrapper(
            F('truck__soat_expiration_date') - Value(my_date), output_field=fields.DurationField()
        )
    ).annotate(
        difference_technical_date=ExpressionWrapper(
            F('truck__technical_review_expiration_date') - Value(my_date), output_field=fields.DurationField()
        )
    ).values(
        'id',
        'truck__id',
        'truck__license_plate',
        'truck__truck_model__truck_brand__name',
        'truck__truck_model__name',
        'truck__owner__name',
        'difference_soat_date',
        'difference_technical_date',
        'truck__soat_expiration_date',
        'truck__technical_review_expiration_date',
    )
    return render(request, 'comercial/report_expiration_soat_and_technical.html', {
        'truck_associate_set': truck_associate_set,
    })


def save_delivery_code(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        code_request = request.GET.get('code_request', '')
        order_id = request.GET.get('order_id', '')
        order_obj = Order.objects.get(id=order_id)

        if code_request == order_obj.code:
            order_obj.type_commodity = 'E'
            order_obj.save()
        else:
            data = {'error': "El codigo ingresado no es el correcto, intente nuevamente"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        return JsonResponse({
            'success': True,
            'message': 'Se actualizo la encomienda correctamente.'
        })
    return JsonResponse({'error': True, 'message': 'Error de petición, contactar con sistemas.'})
