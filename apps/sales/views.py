from django.shortcuts import render
from django.views.generic import TemplateView, View, CreateView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from http import HTTPStatus

from .models import *
from .forms import *
from apps.hrm.models import Subsidiary, District, DocumentType, Employee, Worker
from apps.comercial.models import DistributionMobil, Truck
from django.contrib.auth.models import User
from apps.hrm.views import get_subsidiary_by_user
from apps.accounting.views import TransactionAccount, LedgerEntry, get_account_cash, Cash, CashFlow, AccountingAccount
import json
import decimal
import math
import random
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import ImageFieldFile
from django.template import loader
from datetime import datetime
from django.db import DatabaseError, IntegrityError
from django.core import serializers
from apps.sales.views_SUNAT import send_bill_nubefact, send_receipt_nubefact, send_bill_passenger, \
    send_receipt_passenger
from apps.sales.models import OrderBill
from apps.sales.number_to_letters import numero_a_letras, numero_a_moneda
from django.db.models import Min, Sum, Prefetch


class Home(TemplateView):
    template_name = 'sales/home.html'


class ProductList(View):
    model = Product
    form_class = FormProduct
    template_name = 'sales/product_list.html'

    def get_queryset(self):
        return self.model.objects.filter(is_enabled=True)

    def get_context_data(self, **kwargs):
        user = self.request.user.id
        user_obj = User.objects.get(id=int(user))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        context = {
            'products': self.get_queryset(),
            'subsidiary': subsidiary_obj,
            'form': self.form_class
        }
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


class JsonProductList(View):
    def get(self, request):
        products = Product.objects.filter(is_enabled=True)
        user = self.request.user.id
        user_obj = User.objects.get(id=int(user))
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        t = loader.get_template('sales/product_grid_list.html')
        c = ({'products': products, 'subsidiary': subsidiary_obj})
        return JsonResponse({'result': t.render(c)})


class JsonProductCreate(CreateView):
    model = Product
    form_class = FormProduct
    template_name = 'sales/product_create.html'

    def post(self, request):
        data = dict()
        form = FormProduct(request.POST, request.FILES)

        if form.is_valid():
            print('isvalid()')
            product = form.save()
            # converting a database model to a dictionary...
            data['product'] = model_to_dict(product)
            # Encode into JSON formatted Data
            result = json.dumps(data, cls=ExtendedEncoder)
            # Para pasar cualquier otro objeto serializable JSON, debe establecer el parámetro seguro en False.
            response = JsonResponse(result, safe=False)
            # change status code in JsonResponse
            response.status_code = HTTPStatus.OK
        else:
            # use form.errors to add the error msg as a dictonary
            data['error'] = "form not valid!"
            data['form_invalid'] = form.errors
            # Por defecto, el primer parámetro de JsonResponse, debe ser una instancia dict.
            # Para pasar cualquier otro objeto serializable JSON, debe establecer el parámetro seguro en False.
            response = JsonResponse(data)
            # change status code in JsonResponse
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response


class JsonProductUpdate(UpdateView):
    model = Product
    form_class = FormProduct
    template_name = 'sales/product_update.html'

    def post(self, request, pk):
        data = dict()
        product = self.model.objects.get(pk=pk)
        # form = SnapForm(request.POST, request.FILES, instance=instance)
        form = self.form_class(instance=product, data=request.POST, files=request.FILES)
        if form.is_valid():
            product = form.save()
            data['product'] = model_to_dict(product)
            result = json.dumps(data, cls=ExtendedEncoder)
            response = JsonResponse(result, safe=False)
            response.status_code = HTTPStatus.OK
        else:
            data['error'] = "form not valid!"
            data['form_invalid'] = form.errors
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response


def get_product(request):
    data = dict()
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        try:
            product_obj = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            data['error'] = "producto no existe!"
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        subsidiaries = Subsidiary.objects.all()
        inventories = Kardex.objects.filter(product_store__product_id=pk)
        units = Unit.objects.all()
        user_id = request.user.id
        user_obj = User.objects.get(id=int(user_id))
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        unit_min_obj = None
        product_detail = ProductDetail.objects.filter(
            product=product_obj).annotate(Min('quantity_minimum'))

        if product_detail.count() > 0:
            unit_min_obj = product_detail.first().unit

        t = loader.get_template('sales/product_update_quantity_on_hand.html')
        c = ({'product': product_obj,
              'subsidiaries': subsidiaries,
              'inventories': inventories,
              'units': units,
              'unit_min': unit_min_obj,
              'own_subsidiary': subsidiary_obj,
              })

        return JsonResponse({
            'success': True,
            'form': t.render(c, request),
        })


def new_quantity_on_hand(request):
    if request.method == 'GET':
        store_request = request.GET.get('stores', '')
        data = json.loads(store_request)

        product_id = str(data['Product'])
        product = Product.objects.get(pk=int(product_id))

        for detail in data['Details']:
            if detail['Operation'] == 'create':
                subsidiary_store_id = str(detail['SubsidiaryStore'])
                subsidiary_store = SubsidiaryStore.objects.get(pk=int(subsidiary_store_id))

                new_stock = 0
                new_price_unit = 0

                if detail['Quantity']:
                    new_stock = decimal.Decimal(detail['Quantity'])

                    if detail['Price']:
                        new_price_unit = decimal.Decimal(detail['Price'])

                        if detail['Unit'] != '0':
                            unit_obj = Unit.objects.get(id=int(detail['Unit']))

                            search_product_detail_set = ProductDetail.objects.filter(
                                unit=unit_obj, product=product)

                            if search_product_detail_set.count == 0:
                                product_detail_obj = ProductDetail(
                                    product=product,
                                    price_sale=new_price_unit,
                                    unit=unit_obj,
                                    quantity_minimum=1
                                )
                                product_detail_obj.save()
                        # New product store
                        new_product_store = {
                            'product': product,
                            'subsidiary_store': subsidiary_store,
                            'stock': new_stock
                        }
                        product_store_obj = ProductStore.objects.create(**new_product_store)
                        product_store_obj.save()

                        kardex_initial(product_store_obj, new_stock, new_price_unit)

                    else:
                        data = {'error': "Precio no existe!"}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response
            # else:
            #     data = {'error': "Producto con inventario inicial ya registrado!"}
            #     response = JsonResponse(data)
            #     response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            #     return response
        return JsonResponse({
            'success': True,
        })


def get_recipe_by_product(request):
    if request.method == 'GET':
        store_request = request.GET.get('stores', '')
        data = json.loads(store_request)

        product_id = str(data['Product'])
        product = Product.objects.get(pk=int(product_id))

        for detail in data['Details']:
            if detail['Operation'] == 'create':
                subsidiary_store_id = str(detail['SubsidiaryStore'])
                subsidiary_store = SubsidiaryStore.objects.get(pk=int(subsidiary_store_id))

                new_stock = 0
                new_price_unit = 0

                if detail['Quantity']:
                    new_stock = decimal.Decimal(detail['Quantity'])

                    if detail['Price']:
                        new_price_unit = decimal.Decimal(detail['Price'])

                        if detail['Unit'] != '0':
                            unit_obj = Unit.objects.get(id=int(detail['Unit']))

                            product_detail_obj = ProductDetail(
                                product=product,
                                price_sale=new_price_unit,
                                unit=unit_obj,
                                quantity_minimum=1
                            )
                            product_detail_obj.save()

                        # New product store
                        new_product_store = {
                            'product': product,
                            'subsidiary_store': subsidiary_store,
                            'stock': new_stock
                        }
                        product_store_obj = ProductStore.objects.create(**new_product_store)
                        product_store_obj.save()

                        kardex_initial(product_store_obj, new_stock, new_price_unit)

                    else:
                        data = {'error': "Precio no existe!"}
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response
            else:
                data = {'error': "Producto con inventario inicial ya registrado!"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
        return JsonResponse({
            'success': True,
        })


def get_kardex_by_product(request):
    data = dict()
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            data['error'] = "producto no existe!"
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        products = Product.objects.all()
        subsidiaries = Subsidiary.objects.all()
        subsidiaries_stores = SubsidiaryStore.objects.all()
        # check product detail
        basic_product_detail = ProductDetail.objects.filter(
            product=product, quantity_minimum=1)
        # kardex = Kardex.objects.filter(product_id=pk)
        t = loader.get_template('sales/kardex.html')
        c = ({
            'product': product,
            'subsidiaries': subsidiaries,
            'basic_product_detail': basic_product_detail,
            'subsidiaries_stores': subsidiaries_stores,
            'products': products,
        })

        return JsonResponse({
            'success': True,
            'form': t.render(c, request),
        })


def get_list_kardex(request):
    data = dict()
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        pk_subsidiary_store = request.GET.get('subsidiary_store', '')

        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            data['error'] = "producto no existe!"
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        subsidiary_store = SubsidiaryStore.objects.get(id=pk_subsidiary_store)

        try:
            product_store = ProductStore.objects.filter(
                product_id=product.id).filter(subsidiary_store_id=subsidiary_store.id)

        except ProductStore.DoesNotExist:
            data['error'] = "almacen producto no existe!"
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        inventories = None
        if product_store.count() > 0:
            inventories = Kardex.objects.filter(product_store=product_store[0]).order_by('id')

        t = loader.get_template('sales/kardex_grid_list.html')
        c = ({'product': product, 'inventories': inventories})

        return JsonResponse({
            'success': True,
            'form': t.render(c),
        })


class ExtendedEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, ImageFieldFile):
            return str(o)
        else:
            return super().default(o)


def get_clients_values():
    # clients_set = Client.objects.all().values('id',
    #                                           'names',
    #                                           'phone',
    #                                           'clienttype__document_type',
    #                                           'clienttype__document_number',
    #                                           'clientaddress__address',
    #                                           'clientaddress__district',
    #                                           'clientaddress__reference',
    #                                           'email'
    #                                           )

    client_set = Client.objects.prefetch_related(
        Prefetch(
            'clienttype_set', queryset=ClientType.objects.select_related('document_type')
        ),
        Prefetch(
            'clientaddress_set', queryset=ClientAddress.objects.select_related('district')
        ),
    ).all().values(
        'id',
        'names',
        'phone',
        'clienttype__document_type__description',
        'clienttype__document_number',
        'clientaddress__address',
        'clientaddress__district__description',
        'clientaddress__reference',
        'email'
    )[:10000]
    client_dict = {}
    # client_type = None
    # client_document_number = None
    # address = None
    # district = None
    # reference = None
    for c in client_set:
        # print(c)
        key = c['id']
        client_dict[key] = {
            'id': c['id'],
            'names': c['names'],
            'phone': c['phone'],
            'client_type': c['clienttype__document_type__description'],
            'client_document_number': c['clienttype__document_number'],
            'address': c['clientaddress__address'],
            'district': c['clientaddress__district__description'],
            'reference': ['clientaddress__reference'],
            'email': c['email'],
        }
    return client_dict


class ClientList(View):
    model = Client
    form_class = FormClient
    template_name = 'sales/client_list.html'

    def get_queryset(self):
        return self.model.objects.all().order_by('id')

    def get_context_data(self, **kwargs):
        contexto = {}
        contexto['clients'] = get_clients_values()
        # contexto['clients'] = self.get_queryset()  # agregamos la consulta al contexto
        contexto['form'] = self.form_class
        contexto['document_types'] = DocumentType.objects.all()
        contexto['districts'] = District.objects.all()
        return contexto

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


@csrf_exempt
def new_client(request):
    data = dict()
    print(request.method)
    if request.method == 'POST':

        names = request.POST.get('names')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        email = request.POST.get('email', '')
        document_number = request.POST.get('document_number', '')
        document_type_id = request.POST.get('document_type', '')
        id_district = request.POST.get('id_district', '')
        reference = request.POST.get('reference', '')
        operation = request.POST.get('operation', '')
        client_id = int(request.POST.get('client_id', ''))  # solo se usa al editar

        if operation == 'N':

            if len(names) > 0:

                data_client = {
                    'names': names,
                    'phone': phone,
                    'email': email,
                }

                client = Client.objects.create(**data_client)
                client.save()

                if len(document_number) > 0:

                    try:
                        document_type = DocumentType.objects.get(id=document_type_id)
                    except DocumentType.DoesNotExist:
                        data['error'] = "Documento no existe!"
                        response = JsonResponse(data)
                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                        return response

                    data_client_type = {
                        'client': client,
                        'document_type': document_type,
                        'document_number': document_number,
                    }
                    client_type = ClientType.objects.create(**data_client_type)
                    client_type.save()

                    if len(address) > 0:

                        try:
                            district = District.objects.get(id=id_district)
                        except District.DoesNotExist:
                            data['error'] = "Distrito no existe!"
                            response = JsonResponse(data)
                            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                            return response

                        data_client_address = {
                            'client': client,
                            'address': address,
                            'district': district,
                            'reference': reference,
                        }
                        client_address = ClientAddress.objects.create(**data_client_address)
                        client_address.save()
                return JsonResponse({'success': True, 'message': 'El cliente se registro correctamente.'})
        else:

            client_obj = Client.objects.get(pk=client_id)
            client_obj.names = names
            client_obj.phone = phone
            client_obj.email = email
            client_obj.save()
            district = District.objects.get(id=id_district)
            document_type = DocumentType.objects.get(id=document_type_id)

            client_address_set = ClientAddress.objects.filter(client_id=client_id)
            if client_address_set:
                client_address_obj = client_address_set.first()

                client_address_obj.address = address
                client_address_obj.district = district
                client_address_obj.reference = reference
                client_address_obj.save()
            else:
                data_client_address = {
                    'client': client_obj,
                    'address': address,
                    'district': district,
                    'reference': reference,
                }
                client_address = ClientAddress.objects.create(**data_client_address)
                client_address.save()

            client_type_set = ClientType.objects.filter(client_id=client_id)
            if client_type_set:
                client_type_obj = client_type_set.first()
                client_type_obj.document_type = document_type
                client_type_obj.document_number = document_number
                client_type_obj.save()
            else:
                data_client_type = {
                    'client': client_obj,
                    'document_type': document_type,
                    'document_number': document_number,
                }
                client_type = ClientType.objects.create(**data_client_type)
                client_type.save()

            return JsonResponse({'success': True, 'message': 'El cliente se actualizo correctamente.'})
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


class SalesList(View):
    template_name = 'sales/sales_list.html'

    def get_context_data(self, **kwargs):
        error = ""
        user_id = self.request.user.id
        user_obj = User.objects.get(pk=int(user_id))
        pk = self.kwargs.get('pk', None)
        letter = self.kwargs.get('letter', None)
        contexto = {}
        mydate = datetime.now()
        formatdate = mydate.strftime("%Y-%m-%d")
        # try:
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        sales_store = None
        if subsidiary_obj is None:
            error = "No tiene una sede definida."
        else:
            sales_store = SubsidiaryStore.objects.filter(
                subsidiary=subsidiary_obj, category='V').first()
        # except Subsidiary.DoesNotExist:
        #     subsidiary_obj = None
        #     sales_store = None
        #     employee = None
        #     products = None
        #     clients = None
        #
        # if subsidiary_obj != None:
        products = None
        if sales_store is None:
            error = "No tiene un almacen de ventas registrado, Favor de registrar un almacen primero."
        else:
            products = Product.objects.filter(is_enabled=True, productstore__subsidiary_store=sales_store).order_by(
                'id')
        worker_obj = Worker.objects.filter(user=user_obj).last()
        employee = Employee.objects.get(worker=worker_obj)

        clients = Client.objects.all()
        series_set = Truck.objects.all()

        contexto['employee'] = employee
        contexto['error'] = error
        contexto['sales_store'] = sales_store
        contexto['subsidiary'] = subsidiary_obj
        contexto['products'] = products
        contexto['clients'] = clients
        contexto['date'] = formatdate
        contexto['distribution'] = pk
        contexto['choices_payments'] = TransactionPayment._meta.get_field('type').choices
        contexto['electronic_invoice'] = letter
        contexto['series'] = series_set
        return contexto

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


def get_client(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        client_set = Client.objects.filter(id=pk)
        client_address_set = ClientAddress.objects.filter(client_id=pk)
        client_type_set = ClientType.objects.filter(client_id=pk)
        client_bill_set = OrderBill.objects.filter(order__client__id=client_set.first().id)
        client_serialized_data = serializers.serialize('json', client_set)
        client_serialized_data_address = serializers.serialize('json', client_address_set)
        client_serialized_data_type = serializers.serialize('json', client_type_set)
        client_bill = serializers.serialize('json', client_bill_set)

        return JsonResponse({
            'success': True,
            'client_names': client_set.first().names,
            'client_serialized': client_serialized_data,
            'client_serialized_data_address': client_serialized_data_address,
            'client_serialized_data_type': client_serialized_data_type,
            'client_bill': client_bill,
        })
    return JsonResponse({'error': True, 'message': 'Error de peticion.'})


# @csrf_exempt
def set_product_detail(request):
    data = {}
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        try:
            product_obj = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            data['error'] = "producto no existe!"
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        products = Product.objects.all()
        units = Unit.objects.all()
        t = loader.get_template('sales/product_detail.html')
        c = ({
            'product': product_obj,
            'units': units,
            'products': products,
        })

        product_details = ProductDetail.objects.filter(product=product_obj).order_by('id')
        tpl2 = loader.get_template('sales/product_detail_grid_list.html')
        context2 = ({'product_details': product_details, })
        serialized_data = serializers.serialize('json', product_details)
        return JsonResponse({
            'success': True,
            'form': t.render(c, request),
            'grid': tpl2.render(context2),
            'serialized_data': serialized_data,
            # 'form': t.render(c),
        }, status=HTTPStatus.OK)
    else:
        if request.method == 'POST':
            id_product = request.POST.get('product', '')
            price_sale = request.POST.get('price_sale', '')
            id_unit = request.POST.get('unit', '')
            quantity_minimum = request.POST.get('quantity_minimum', '')

            if decimal.Decimal(price_sale) == 0 or decimal.Decimal(quantity_minimum) == 0:
                data['error'] = "Ingrese valores validos."
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

            product_obj = Product.objects.get(id=int(id_product))
            unit_obj = Unit.objects.get(id=int(id_unit))

            try:
                product_detail_obj = ProductDetail(
                    product=product_obj,
                    price_sale=decimal.Decimal(price_sale),
                    unit=unit_obj,
                    quantity_minimum=decimal.Decimal(quantity_minimum),
                )
                product_detail_obj.save()
            except DatabaseError as e:
                data['error'] = str(e)
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
            except IntegrityError as e:
                data['error'] = str(e)
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

            product_details = ProductDetail.objects.filter(product=product_obj).order_by('id')
            tpl2 = loader.get_template('sales/product_detail_grid_list.html')
            context2 = ({'product_details': product_details, })

            return JsonResponse({
                'message': 'Guardado con exito.',
                'grid': tpl2.render(context2),
            }, status=HTTPStatus.OK)


def get_product_detail(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        product_detail_obj = ProductDetail.objects.filter(id=pk)
        serialized_obj = serializers.serialize('json', product_detail_obj)
        return JsonResponse({'obj': serialized_obj}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def toogle_status_product_detail(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        text_status = request.GET.get('status', '')
        status = False
        if text_status == 'True':
            status = True
        product_detail_obj = ProductDetail.objects.get(id=pk)
        product_detail_obj.is_enabled = status
        product_detail_obj.save()

        return JsonResponse({'message': 'Cambios guardados con exito.'}, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def update_product_detail(request):
    data = dict()
    if request.method == 'POST':
        id_product_detail = request.POST.get('product_detail', '')
        id_product = request.POST.get('product', '')
        price_sale = request.POST.get('price_sale', '')
        id_unit = request.POST.get('unit', '')
        quantity_minimum = request.POST.get('quantity_minimum', '')

        if decimal.Decimal(price_sale) == 0 or decimal.Decimal(quantity_minimum) == 0:
            data['error'] = "Ingrese valores validos."
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response
        product_obj = Product.objects.get(id=int(id_product))
        unit_obj = Unit.objects.get(id=int(id_unit))

        product_detail_obj = ProductDetail.objects.get(id=int(id_product_detail))
        product_detail_obj.quantity_minimum = quantity_minimum
        product_detail_obj.price_sale = price_sale
        product_detail_obj.product = product_obj
        product_detail_obj.unit = unit_obj
        product_detail_obj.save()

        product_details = ProductDetail.objects.filter(product=product_obj).order_by('id')
        tpl2 = loader.get_template('sales/product_detail_grid_list.html')
        context2 = ({'product_details': product_details, })

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': tpl2.render(context2),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def get_rate_product(request):
    if request.method == 'GET':
        id_product = request.GET.get('product', '')
        id_distribution = request.GET.get('distribution')
        distribution_obj = None
        if id_distribution != '0':
            distribution_obj = DistributionMobil.objects.get(pk=int(id_distribution))

        product_obj = Product.objects.get(id=int(id_product))
        product_details = ProductDetail.objects.filter(product=product_obj)
        subsidiaries_stores = SubsidiaryStore.objects.filter(stores__product=product_obj)
        user_id = request.user.id
        user_obj = User.objects.get(pk=int(user_id))

        product_stores = ProductStore.objects.filter(product=product_obj)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        store = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='V').first()

        serialized_obj1 = serializers.serialize('json', product_details)
        serialized_obj2 = serializers.serialize('json', product_stores)
        print(subsidiaries_stores)

        tpl = loader.get_template('sales/sales_rates.html')

        context = ({

            'store': store,
            'product_obj': product_obj,
            'subsidiaries_stores': subsidiaries_stores,
            'product_stores': product_stores,
            'product_details': product_details,
            'distribution_obj': distribution_obj,
        })

        return JsonResponse({
            'serialized_obj2': serialized_obj2,
            'grid': tpl.render(context),
        }, status=HTTPStatus.OK)


# create by Jhon por siacaso----------------------------------

def create_order_detail(request):
    if request.method == 'GET':
        sale_request = request.GET.get('sales', '')
        data_sale = json.loads(sale_request)
        distribution_obj = None
        serie_obj = None
        truck_obj = None
        client_id = str(data_sale["Client"])
        client_obj = Client.objects.get(pk=int(client_id))
        sale_total = decimal.Decimal(data_sale["SaleTotal"])
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_store_sales_obj = SubsidiaryStore.objects.get(
            subsidiary=subsidiary_obj, category='V')
        # order_id = str(data_sale["Orden"])
        distribution_id = str(data_sale["Distribution"])
        serie = str(data_sale["Serie"])
        _type = str(data_sale["Type"])
        _bill_type = str(data_sale["BillType"])
        msg_sunat = ''
        sunat_pdf = ''
        _date = str(data_sale["Date"])
        is_demo = bool(int(data_sale["Demo"]))
        value_is_demo = ''
        if is_demo:
            value_is_demo = 'D'
        else:
            value_is_demo = 'P'

        if distribution_id != '0':
            distribution_obj = DistributionMobil.objects.get(pk=int(distribution_id))

        if serie != '0':
            truck_obj = Truck.objects.get(id=int(serie))
            truck_obj_id = truck_obj.id
            serie_obj = truck_obj.serial

        new_order_sale = {
            'type': _type,
            'client': client_obj,
            'user': user_obj,
            'total': sale_total,
            'distribution_mobil': distribution_obj,
            'subsidiary_store': subsidiary_store_sales_obj,
            'truck': truck_obj,
            'create_at': _date
            # 'correlative_sale': order_id,
        }
        order_sale_obj = Order.objects.create(**new_order_sale)
        order_sale_obj.save()
        new_detail_order = None
        for detail in data_sale['Details']:
            quantity = decimal.Decimal(detail['Quantity'])
            price = decimal.Decimal(detail['Price'])
            total = decimal.Decimal(detail['DetailTotal'])

            # recuperamos del producto
            product_id = int(detail['Product'])
            product_obj = Product.objects.get(id=product_id)

            # recuperamos la unidad
            unit_id = int(detail['Unit'])
            unit_obj = Unit.objects.get(id=unit_id)

            item_with_unit_g = None
            item_with_unit_b = None
            new_detail_order_obj = None

            if unit_obj.name == 'BG':
                search_item_with_unit_g_set = OrderDetail.objects.filter(
                    unit__name='G', order=order_sale_obj)

                if search_item_with_unit_g_set.count() > 0:
                    item_with_unit_g = search_item_with_unit_g_set.last()
                    item_with_unit_g.quantity_sold = item_with_unit_g.quantity_sold + quantity
                    item_with_unit_g.save()
                else:
                    product_detail_g = ProductDetail.objects.get(
                        product=product_obj, unit__name='G')
                    new_item_with_unit_g = {
                        'order': order_sale_obj,
                        'product': product_obj,
                        'quantity_sold': quantity,
                        'price_unit': product_detail_g.price_sale,
                        'unit': product_detail_g.unit,
                        'status': 'V'
                    }
                    item_with_unit_g = OrderDetail.objects.create(**new_item_with_unit_g)
                    item_with_unit_g.save()

                product_detail_b = ProductDetail.objects.get(product=product_obj, unit__name='B')
                price_g = item_with_unit_g.price_unit
                price_bg = price
                price_b = price_bg - price_g

                new_item_with_unit_b = {
                    'order': order_sale_obj,
                    'product': product_obj,
                    'quantity_sold': quantity,
                    'price_unit': price_b,
                    'unit': product_detail_b.unit,
                    'status': 'V'
                }
                item_with_unit_b = OrderDetail.objects.create(**new_item_with_unit_b)
                item_with_unit_b.save()
            else:
                if unit_obj.name == 'BCG':
                    search_item_with_unit_g_set = OrderDetail.objects.filter(
                        unit__name='G', order=order_sale_obj)

                    if search_item_with_unit_g_set.count() > 0:
                        item_with_unit_g = search_item_with_unit_g_set.last()
                        item_with_unit_g.quantity_sold = item_with_unit_g.quantity_sold + quantity
                        item_with_unit_g.save()
                    else:
                        product_detail_g = ProductDetail.objects.get(
                            product=product_obj, unit__name='G')
                        new_item_with_unit_g = {
                            'order': order_sale_obj,
                            'product': product_obj,
                            'quantity_sold': quantity,
                            'price_unit': product_detail_g.price_sale,
                            'unit': product_detail_g.unit,
                            'status': 'V'
                        }
                        item_with_unit_g = OrderDetail.objects.create(**new_item_with_unit_g)
                        item_with_unit_g.save()
                else:
                    new_detail_order = {
                        'order': order_sale_obj,
                        'product': product_obj,
                        'quantity_sold': quantity,
                        'price_unit': price,
                        'unit': unit_obj,
                        'status': 'V'
                    }
                    new_detail_order_obj = OrderDetail.objects.create(**new_detail_order)
                    new_detail_order_obj.save()

            store_product_id = int(detail['Store'])

            if _type == 'V':
                if unit_obj.name == 'G':

                    # output sales
                    kardex_ouput(store_product_id, quantity, order_detail_obj=new_detail_order_obj)
                    # get iron supply
                    product_supply_obj = get_iron_man(product_id)
                    subsidiary_store_supply_obj = SubsidiaryStore.objects.get(subsidiary=subsidiary_obj,
                                                                              category='I')

                    try:
                        product_store_supply_obj = ProductStore.objects.get(product=product_supply_obj,
                                                                            subsidiary_store=subsidiary_store_supply_obj)
                    except ProductStore.DoesNotExist:
                        product_store_supply_obj = None

                    if product_store_supply_obj is None:
                        product_store_supply_obj = ProductStore(
                            product=product_supply_obj,
                            subsidiary_store=subsidiary_store_supply_obj,
                            stock=quantity
                        )
                        product_store_supply_obj.save()
                        kardex_initial(product_store_supply_obj, quantity,
                                       product_supply_obj.calculate_minimum_price_sale(),
                                       order_detail_obj=new_detail_order_obj)
                    else:
                        # input supplies
                        kardex_input(product_store_supply_obj.id, quantity,
                                     product_supply_obj.calculate_minimum_price_sale(),
                                     order_detail_obj=new_detail_order_obj)
                elif unit_obj.name == 'BG':
                    # output sales
                    kardex_ouput(store_product_id, quantity, order_detail_obj=item_with_unit_b)
                elif unit_obj.name == 'BCG':
                    # output sales
                    kardex_ouput(store_product_id, quantity, order_detail_obj=item_with_unit_g)
                else:
                    kardex_ouput(store_product_id, quantity, order_detail_obj=new_detail_order_obj)

        if _type == 'E':
            if _bill_type == 'F':
                r = send_bill_nubefact(order_sale_obj.id, is_demo)
                msg_sunat = r.get('sunat_description')
                sunat_pdf = r.get('enlace_del_pdf')
                codigo_hash = r.get('codigo_hash')
                if codigo_hash:
                    order_bill_obj = OrderBill(order=order_sale_obj,
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
                                               created_at=order_sale_obj.create_at,
                                               is_demo=value_is_demo
                                               )
                    order_bill_obj.save()
                else:
                    objects_to_delete = OrderDetail.objects.filter(order=order_sale_obj)
                    objects_to_delete.delete()
                    order_sale_obj.delete()
                    if r.get('errors'):
                        data = {'error': str(r.get('errors'))}
                    elif r.get('error'):
                        data = {'error': str(r.get('error'))}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response

            elif _bill_type == 'B':
                r = send_receipt_nubefact(order_sale_obj.id, is_demo)
                msg_sunat = r.get('sunat_description')
                sunat_pdf = r.get('enlace_del_pdf')
                codigo_hash = r.get('codigo_hash')
                if codigo_hash:
                    order_bill_obj = OrderBill(order=order_sale_obj,
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
                                               created_at=order_sale_obj.create_at,
                                               is_demo=value_is_demo
                                               )
                    order_bill_obj.save()
                else:
                    objects_to_delete = OrderDetail.objects.filter(order=order_sale_obj)
                    objects_to_delete.delete()
                    order_sale_obj.delete()
                    if r.get('errors'):
                        data = {'error': str(r.get('errors'))}
                    elif r.get('error'):
                        data = {'error': str(r.get('error'))}
                    response = JsonResponse(data)
                    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    return response

        # subsidiary_obj = get_subsidiary_by_user(user_obj)
        # sales_store = SubsidiaryStore.objects.filter(
        #     subsidiary=subsidiary_obj, category='V').first()

        # products = Product.objects.all().order_by('id')
        # products = Product.objects.filter(productstore__subsidiary_store=sales_store).order_by('id')

        # tpl = loader.get_template('sales/sales_grid_tab2.html')
        # context = ({'products': products, 'sales_store': sales_store, 'is_render': True, })

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'msg_sunat': msg_sunat,
            'sunat_pdf': sunat_pdf,
            # 'grid': tpl.render(context),
        }, status=HTTPStatus.OK)

    return JsonResponse({
        'message': 'La Venta se Realizo correctamente.',
    }, status=HTTPStatus.OK)


@csrf_exempt
def generate_receipt_random(request):
    if request.method == 'POST':
        product = request.POST.get('create_product')
        truck = request.POST.get('id_truck')
        client = request.POST.get('id_client_name')
        date = request.POST.get('date')
        is_demo = False
        value_is_demo = 'P'
        if request.POST.get('demo') == '0':
            is_demo = True
            value_is_demo = 'D'

        price = decimal.Decimal(request.POST.get('price'))
        truck_obj = Truck.objects.get(id=int(truck))
        client_obj = Client.objects.get(pk=int(client))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        product_obj = Product.objects.get(id=int(product))
        unit = product_obj.calculate_minimum_unit_id()
        unit_obj = Unit.objects.get(id=unit)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_store_sales_obj = SubsidiaryStore.objects.get(
            subsidiary=subsidiary_obj, category='V')

        counter = int(request.POST.get('counter')) + 1
        quantity_min = 1
        limit = 100
        quantity_max = math.floor(limit / price)
        for x in range(1, counter, 1):
            quantity = random.randint(quantity_min, quantity_max)
            total = decimal.Decimal(quantity * price)

            order_obj = Order(type='E',
                              client=client_obj,
                              user=user_obj,
                              total=total,
                              subsidiary_store=subsidiary_store_sales_obj,
                              truck=truck_obj,
                              create_at=date)
            order_obj.save()
            detail_order_obj = OrderDetail(order=order_obj,
                                           product=product_obj,
                                           quantity_sold=quantity,
                                           price_unit=price,
                                           unit=unit_obj,
                                           status='V')
            detail_order_obj.save()
            r = send_receipt_nubefact(order_obj.id, is_demo)
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

        return JsonResponse({
            'msg_sunat': 'Boletas enviadas correctamente',
        }, status=HTTPStatus.OK)


def calculate_minimum_unit(quantity, unit_obj, product_obj):
    product_detail = ProductDetail.objects.filter(
        product=product_obj).annotate(Min('quantity_minimum')).first()
    product_detail_sent = ProductDetail.objects.get(product=product_obj, unit=unit_obj)
    if product_detail.quantity_minimum > 1:
        new_quantity = quantity * product_detail.quantity_minimum
    else:
        new_quantity = quantity * product_detail.quantity_minimum * product_detail_sent.quantity_minimum
    return new_quantity


def kardex_initial(
        product_store_obj,
        stock,
        price_unit,
        purchase_detail_obj=None,
        requirement_detail_obj=None,
        programming_invoice_obj=None,
        manufacture_detail_obj=None,
        guide_detail_obj=None,
        distribution_detail_obj=None,
        order_detail_obj=None,
        loan_payment_obj=None,
        ball_change_obj=None,
):
    new_kardex = {
        'operation': 'C',
        'quantity': 0,
        'price_unit': 0,
        'price_total': 0,
        'remaining_quantity': decimal.Decimal(stock),
        'remaining_price': decimal.Decimal(price_unit),
        'remaining_price_total': decimal.Decimal(stock) * decimal.Decimal(price_unit),
        'product_store': product_store_obj,
        'purchase_detail': purchase_detail_obj,
        'requirement_detail': requirement_detail_obj,
        'programming_invoice': programming_invoice_obj,
        'manufacture_detail': manufacture_detail_obj,
        'guide_detail': guide_detail_obj,
        'distribution_detail': distribution_detail_obj,
        'order_detail': order_detail_obj,
        'loan_payment': loan_payment_obj,
        'ball_change': ball_change_obj,
    }
    kardex = Kardex.objects.create(**new_kardex)
    kardex.save()


def kardex_input(
        product_store_id,
        quantity_purchased,
        price_unit,
        purchase_detail_obj=None,
        requirement_detail_obj=None,
        programming_invoice_obj=None,
        manufacture_detail_obj=None,
        guide_detail_obj=None,
        distribution_detail_obj=None,
        order_detail_obj=None,
        loan_payment_obj=None,
        ball_change_obj=None,
):
    product_store = ProductStore.objects.get(pk=int(product_store_id))

    old_stock = product_store.stock
    new_quantity = decimal.Decimal(quantity_purchased)
    new_stock = old_stock + new_quantity  # Cantidad nueva de stock
    new_price_unit = decimal.Decimal(price_unit)
    new_price_total = new_quantity * new_price_unit

    last_kardex = Kardex.objects.filter(product_store_id=product_store.id).last()
    last_remaining_quantity = last_kardex.remaining_quantity
    last_remaining_price_total = last_kardex.remaining_price_total

    new_remaining_quantity = last_remaining_quantity + new_quantity
    new_remaining_price = (decimal.Decimal(last_remaining_price_total) +
                           new_price_total) / new_remaining_quantity
    new_remaining_price_total = new_remaining_quantity * new_remaining_price

    new_kardex = {
        'operation': 'E',
        'quantity': new_quantity,
        'price_unit': new_price_unit,
        'price_total': new_price_total,
        'remaining_quantity': new_remaining_quantity,
        'remaining_price': new_remaining_price,
        'remaining_price_total': new_remaining_price_total,
        'product_store': product_store,
        'purchase_detail': purchase_detail_obj,
        'requirement_detail': requirement_detail_obj,
        'programming_invoice': programming_invoice_obj,
        'manufacture_detail': manufacture_detail_obj,
        'guide_detail': guide_detail_obj,
        'distribution_detail': distribution_detail_obj,
        'order_detail': order_detail_obj,
        'loan_payment': loan_payment_obj,
        'ball_change': ball_change_obj,
    }
    kardex = Kardex.objects.create(**new_kardex)
    kardex.save()

    product_store.stock = new_stock
    product_store.save()


def kardex_ouput(
        product_store_id,
        quantity_sold,
        order_detail_obj=None,
        programming_invoice_obj=None,
        manufacture_recipe_obj=None,
        guide_detail_obj=None,
        distribution_detail_obj=None,
        loan_payment_obj=None,
        ball_change_obj=None,
):
    product_store = ProductStore.objects.get(pk=int(product_store_id))

    old_stock = product_store.stock
    new_stock = old_stock - decimal.Decimal(quantity_sold)
    new_quantity = decimal.Decimal(quantity_sold)

    last_kardex = Kardex.objects.filter(product_store_id=product_store.id).last()
    last_remaining_quantity = last_kardex.remaining_quantity
    old_price_unit = last_kardex.remaining_price

    new_price_total = old_price_unit * new_quantity

    new_remaining_quantity = last_remaining_quantity - new_quantity
    new_remaining_price = old_price_unit
    new_remaining_price_total = new_remaining_quantity * new_remaining_price
    new_kardex = {
        'operation': 'S',
        'quantity': new_quantity,
        'price_unit': old_price_unit,
        'price_total': new_price_total,
        'remaining_quantity': new_remaining_quantity,
        'remaining_price': new_remaining_price,
        'remaining_price_total': new_remaining_price_total,
        'product_store': product_store,
        'programming_invoice': programming_invoice_obj,
        'manufacture_recipe': manufacture_recipe_obj,
        'order_detail': order_detail_obj,
        'guide_detail': guide_detail_obj,
        'distribution_detail': distribution_detail_obj,
        'loan_payment': loan_payment_obj,
        'ball_change': ball_change_obj,
    }
    kardex = Kardex.objects.create(**new_kardex)
    kardex.save()

    product_store.stock = new_stock
    product_store.save()


def generate_invoice(request):
    if request.method == 'GET':
        id_order = request.GET.get('order', '')

        # print(numero_a_letras(145))

        r = send_bill_nubefact(id_order)

        return JsonResponse({
            'success': True,
            'msg': r.get('errors'),
            # 'numero_a_letras': numero_a_letras(decimal.Decimal(id_order)),
            'numero_a_moneda': numero_a_moneda(decimal.Decimal(id_order)),

            'parameters': r.get('params'),
        }, status=HTTPStatus.OK)


def get_sales_by_subsidiary_store(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    orders = None

    if subsidiary_obj is not None:
        subsidiary_store_obj = SubsidiaryStore.objects.get(subsidiary=subsidiary_obj, category='V')
        orders = Order.objects.filter(subsidiary_store=subsidiary_store_obj)

    return render(request, 'sales/order_sales_list.html', {'orders': orders})


def get_products_by_subsidiary(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary = get_subsidiary_by_user(user_obj)
    subsidiary_stores = SubsidiaryStore.objects.filter(subsidiary=subsidiary)
    form_subsidiary_store = FormSubsidiaryStore()

    return render(request, 'sales/product_by_subsidiary.html', {
        'form': form_subsidiary_store,
        'subsidiary_stores': subsidiary_stores
    })


def new_subsidiary_store(request):
    if request.method == 'POST':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        name = request.POST.get('name')
        category = request.POST.get('category', '')

        try:
            subsidiary_store_obj = SubsidiaryStore(
                subsidiary=subsidiary_obj,
                name=name,
                category=category
            )
            subsidiary_store_obj.save()
        except DatabaseError as e:
            data = {'error': str(e)}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        return JsonResponse({
            'success': True,
            'message': 'Registrado con exito.',
        }, status=HTTPStatus.OK)


def get_recipe(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)

    products = Product.objects.filter(is_manufactured=True)
    products_insume = Product.objects.filter(is_supply=True)

    return render(request, 'sales/product_recipe.html', {
        'products': products,
        'products_insume': products_insume,
    })


def get_manufacture(request):
    products_insume = Product.objects.filter(
        is_manufactured=True, recipes__isnull=False).distinct('name')
    inputs = Product.objects.filter(is_supply=True)
    mydate = datetime.now()
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    my_subsidiary_store_obj = SubsidiaryStore.objects.get(subsidiary=subsidiary_obj, category='I')
    formatdate = mydate.strftime("%Y-%m-%d %H:%M:%S")
    return render(request, 'sales/recipe_list.html', {
        'products_insume': products_insume,
        'my_subsidiary_store': my_subsidiary_store_obj,
        'date': formatdate,
        'context': validate_manufacture_pendient(subsidiary_obj),
        'inputs': inputs
    })


def get_unit_by_product(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        units = Unit.objects.filter(productdetail__product__id=pk)
        serialized_obj = serializers.serialize('json', units)

    return JsonResponse({'units_serial': serialized_obj})


def get_price_by_product(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        product_detail_obj = ProductDetail.objects.filter(product_id=int(pk)).first()
        price = product_detail_obj.price_sale

    return JsonResponse({'price_unit': price})


def create_recipe(request):
    if request.method == 'GET':
        recipe_request = request.GET.get('recipe_dic', '')
        data_recipe = json.loads(recipe_request)

        for detail in data_recipe['Details']:
            product_create_id = str(detail["ProductCreate"])
            product_create_obj = Product.objects.get(id=product_create_id)

            product_insume_id = str(detail["ProductoInsume"])
            product_insume_obj = Product.objects.get(id=product_insume_id)

            quantity = decimal.Decimal(detail["Quantity"])

            unit_id = str(detail["Unit"])
            unit_obj = Unit.objects.get(id=unit_id)

            price = decimal.Decimal(detail["Price"])

            recipe_product = {
                'product': product_create_obj,
                'product_input': product_insume_obj,
                'quantity': quantity,
                'unit': unit_obj,
                'price': price

            }
            new_recipe_obj = ProductRecipe.objects.create(**recipe_product)
            new_recipe_obj.save()

        return JsonResponse({
            'message': 'La operaciòn se Realizo correctamente.',
        }, status=HTTPStatus.OK)


def get_price_and_total_by_product_recipe(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        product_recipe_obj = ProductRecipe.objects.filter(product__id=int(pk)).first()
        quantity = decimal.Decimal(request.GET.get('quantity', ''))
        price_unit = product_recipe_obj.price
        total = quantity * price_unit

    return JsonResponse({'price_unit': price_unit, 'total': total})


def get_stock_insume_by_product_recipe(request):
    if request.method == 'GET':
        pk = request.GET.get('pk', '')
        quantity_request = decimal.Decimal(request.GET.get('quantity'))
        status = request.GET.get('status', '')
        product_recipe_set = ProductRecipe.objects.filter(product__id=int(pk))
        product_create_obj = Product.objects.get(id=int(pk))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        subsidiary_store_supplies_obj = SubsidiaryStore.objects.get(
            subsidiary=subsidiary_obj, category='I')
        dictionary = []

        for i in product_recipe_set.all():
            current_stock_of_supply = i.product_input.productstore_set.filter(
                subsidiary_store=subsidiary_store_supplies_obj).first().stock
            total_quantity_request = i.quantity * quantity_request
            total_quantity_remaining = current_stock_of_supply - total_quantity_request
            detail = {
                'id': i.product_input.id,
                'name': i.product_input.name,
                'unit': Unit.objects.get(id=i.product_input.calculate_minimum_unit_id()),
                'quantity_supply': i.quantity,
                'current_stock': current_stock_of_supply,
                'total_quantity_request': total_quantity_request,
                'quantity_remaining_in_stock': total_quantity_remaining,
            }
            dictionary.append(detail)

        tpl = loader.get_template('sales/detail_product_recipe.html')
        context = ({
            'product_details': dictionary,
            'rowspan': len(dictionary) + 1,
            'quantity': quantity_request,
            'status': status,
            'subsidiary_store_insume': subsidiary_store_supplies_obj,
            'product_create': product_create_obj,
        })
        # serialized_data = serializers.serialize('json', product_recipe_set)
        return JsonResponse({
            'success': True,
            # 'form': t.render(c, request),
            'grid': tpl.render(context),
            # 'serialized_data': serialized_data,
            # 'form': t.render(c),
        }, status=HTTPStatus.OK)


def get_context_kardex_glp(subsidiary_obj, pk, is_pdf=False, get_context=False):
    other_subsidiary_store_obj = SubsidiaryStore.objects.get(id=int(pk))  # otro almacen insumos
    my_subsidiary_store_glp_obj = SubsidiaryStore.objects.get(
        subsidiary=subsidiary_obj, category='G')  # pluspetrol
    my_subsidiary_store_insume_obj = SubsidiaryStore.objects.get(subsidiary=subsidiary_obj,
                                                                 category='I')  # tu almacen insumos

    product_obj = Product.objects.get(is_approved_by_osinergmin=True, name__exact='GLP')
    product_store_obj = ProductStore.objects.get(
        subsidiary_store=my_subsidiary_store_glp_obj, product=product_obj)

    kardex_set = Kardex.objects.filter(product_store=product_store_obj)

    tpl = loader.get_template('sales/kardex_glp_grid.html')
    context = ({
        'is_pdf': is_pdf,
        'kardex_set': kardex_set,
        'my_subsidiary_store_insume': my_subsidiary_store_insume_obj,
        'other_subsidiary_store': other_subsidiary_store_obj,
    })
    if get_context:
        return context
    else:
        return tpl.render(context)


def get_kardex_glp(request):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    if request.method == 'GET':
        pk = request.GET.get('subsidiary_store_id', '')
        if pk != '':

            return JsonResponse({
                'success': True,
                'grid': get_context_kardex_glp(subsidiary_obj, pk),
            }, status=HTTPStatus.OK)
        else:
            subsidiary_store_set = SubsidiaryStore.objects.exclude(
                subsidiary=subsidiary_obj).filter(category='I')
            mydate = datetime.now()
            formatdate = mydate.strftime("%Y-%m-%d %H:%M:%S")
            return render(request, 'sales/kardex_glp.html', {
                'subsidiary_stores': subsidiary_store_set,
                'date': formatdate
            })


def get_only_grid_kardex_glp(request, pk):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    return render(request, 'sales/kardex_glp_grid.html', get_context_kardex_glp(subsidiary_obj, pk, get_context=True))


def create_order_manufacture(request):
    if request.method == 'GET':
        production_request = request.GET.get('production')
        data_production = json.loads(production_request)

        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        manufacture_obj_val = ManufactureAction.objects.filter(
            status="1", manufacture__subsidiary=subsidiary_obj)

        # ---Cabecera de Manufacturee---
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        code = str(data_production["Code"])
        total = decimal.Decimal((data_production["Total"]).replace(',', '.'))

        new_manufacture_obj = Manufacture(subsidiary=subsidiary_obj, code=code, total=total)
        new_manufacture_obj.save()

        # --Save ManufactureAction--
        new_manufacture_action_obj = ManufactureAction(
            user=user_obj, manufacture=new_manufacture_obj, status="1")
        new_manufacture_action_obj.save()

        # --Save Manufacturedetail--
        for details in data_production['Details']:

            product_create_id = str(details["Product"])
            product_create_obj = Product.objects.get(id=product_create_id)

            quantity_request = decimal.Decimal(details["Quantity"])
            price = decimal.Decimal(details["Price"])

            new_manufacture_detail_obj = ManufactureDetail(manufacture=new_manufacture_obj,
                                                           product_manufacture=product_create_obj,
                                                           quantity=quantity_request, price=price)
            new_manufacture_detail_obj.save()

            for insume in ProductRecipe.objects.filter(product=product_create_obj):
                new_manufacture_recipe_obj = ManufactureRecipe(manufacture_detail=new_manufacture_detail_obj,
                                                               product_input=insume.product_input,
                                                               quantity=insume.quantity * quantity_request)
                new_manufacture_recipe_obj.save()

        return JsonResponse({
            'message': 'La operaciòn se Realizo correctamente.',
        }, status=HTTPStatus.OK)

    else:
        return JsonResponse({
            'error': 'No se puede guardar, existe una Orden pendiente'
        }, status=HTTPStatus.OK)


def orders_manufacture(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        manufactures = Manufacture.objects.filter(subsidiary=subsidiary_obj)
        status = ManufactureAction._meta.get_field('status').choices

        return render(request, 'sales/manufacture_list.html', {
            'manufactures': manufactures,
            'status': status
        })


# Aqui tambien se guardan los productos creados
def update_manufacture_by_id(request):
    if request.method == 'GET':
        manufacture_id = request.GET.get('pk', '')
        status_id = request.GET.get('status', '')
        manufacture_obj = Manufacture.objects.get(id=int(manufacture_id))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)

        if status_id == '2':  # aprobado
            subsidiary_store_set_obj = SubsidiaryStore.objects.get(
                subsidiary=subsidiary_obj, category='I')
            manufacture_details_set = ManufactureDetail.objects.filter(
                manufacture_id=int(manufacture_id))
            if validate_stock_insume(subsidiary_store_set_obj, manufacture_id):
                for d in manufacture_details_set.all():
                    inputs_set = ManufactureRecipe.objects.filter(manufacture_detail=d)
                    for i in inputs_set:
                        product_store_inputs_obj = ProductStore.objects.get(subsidiary_store=subsidiary_store_set_obj,
                                                                            product=i.product_input)
                        kardex_ouput(product_store_inputs_obj.id,
                                     i.quantity,
                                     manufacture_recipe_obj=i)  # i.quantity = LA CANTIDAD QUE SE DESCONTARA DEL STOCK DEL INSUMO

                new_manufacture_action_obj = ManufactureAction(user=user_obj, date=datetime.now(),
                                                               manufacture=manufacture_obj, status=status_id)
                new_manufacture_action_obj.save()
            else:
                data = {'error': 'No se pudo Aprobar la solicitud por falta de stock de un insumo'}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

        elif status_id == '3':  # produccion
            new_manufacture_action_obj = ManufactureAction(user=user_obj, date=datetime.now(),
                                                           manufacture=manufacture_obj, status=status_id)
            new_manufacture_action_obj.save()

        elif status_id == '4':
            subsidiary_store_set_obj = SubsidiaryStore.objects.get(
                subsidiary=subsidiary_obj, category='V')
            manufacture_details_set = ManufactureDetail.objects.filter(
                manufacture_id=int(manufacture_id))
            for d in manufacture_details_set.all():
                price_unit = d.price / d.quantity
                try:
                    product_store_create = ProductStore.objects.get(subsidiary_store=subsidiary_store_set_obj,
                                                                    product=d.product_manufacture)
                except ProductStore.DoesNotExist:
                    product_store_create = None

                if product_store_create is None:
                    product_store_create = ProductStore(product=d.product_manufacture, stock=d.quantity,
                                                        subsidiary_store=subsidiary_store_set_obj)
                    product_store_create.save()
                    kardex_initial(product_store_create, d.quantity,
                                   price_unit, manufacture_detail_obj=d)
                else:
                    kardex_input(product_store_create.id, d.quantity,
                                 price_unit, manufacture_detail_obj=d)

            new_manufacture_action_obj = ManufactureAction(user=user_obj, date=datetime.now(),
                                                           manufacture=manufacture_obj, status=status_id)
            new_manufacture_action_obj.save()

        elif status_id == '5':
            new_manufacture_action_obj = ManufactureAction(user=user_obj, date=datetime.now(),
                                                           manufacture=manufacture_obj, status=status_id)
            new_manufacture_action_obj.save()

        return JsonResponse({
            'message': 'Se cambio el estado correctamente.',
        }, status=HTTPStatus.OK)


def validate_stock_insume(subsidiary_store, manufacture_id):
    manufacture_details_set = ManufactureDetail.objects.filter(manufacture_id=int(manufacture_id))
    for d in manufacture_details_set.all():
        inputs_set = ManufactureRecipe.objects.filter(manufacture_detail=d)
        for i in inputs_set:
            product_store_inputs_obj = ProductStore.objects.get(subsidiary_store=subsidiary_store,
                                                                product=i.product_input)
            if product_store_inputs_obj.stock < i.quantity:
                return False
    return True


def validate_manufacture_pendient(subsidiary_obj):
    for m in Manufacture.objects.filter(subsidiary=subsidiary_obj):
        last_action = ManufactureAction.objects.filter(manufacture=m).last()
        if last_action.status == '1':
            context = ({
                'code': last_action.manufacture.code,
                'flag': False,
            })
            return context
    return {'flag': True}


def order_list(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        clients = Client.objects.all()
        orders = Order.objects.all()

        return render(request, 'sales/account_status_list.html', {
            'orders': orders,
            'clients': clients,
        })


def get_dict_orders(order_set, client_obj=None, is_pdf=False):
    dictionary = []

    for o in order_set:
        if o.orderdetail_set.count() > 0:
            new = {
                'id': o.id,
                'type': o.get_type_display(),
                'client': o.client.names,
                'date': o.create_at,
                'distribution_mobil': [],
                'order_detail_set': [],
                'status': o.get_status_display(),
                'total': o.total,
                'total_repay_loan': o.total_repay_loan(),
                'total_repay_loan_with_vouchers': o.total_repay_loan_with_vouchers(),
                'total_return_loan': o.total_return_loan(),
                'total_remaining_repay_loan': o.total_remaining_repay_loan(),
                'total_remaining_repay_loan_ball': o.total_remaining_repay_loan_ball(),
                'total_remaining_return_loan': o.total_remaining_return_loan(),
                'total_ball_changes': o.total_ball_changes(),
                'total_spending': o.total_cash_flow_spending(),
                'details_count': o.orderdetail_set.count(),
                'rowspan': 0,
                'has_loans': False
            }
            license_plate = '-'
            pilot = '-'
            if o.distribution_mobil:
                license_plate = o.distribution_mobil.truck.license_plate
                pilot = o.distribution_mobil.pilot.full_name
            distribution_mobil = {
                'license_plate': license_plate,
                'pilot': pilot,
            }
            new.get('distribution_mobil').append(distribution_mobil)

            for d in OrderDetail.objects.filter(order=o):
                _type = '-'
                if d.unit.name == 'G':
                    _type = 'CANJEADO'
                elif d.unit.name == 'B':
                    _type = 'PRESTADO'

                loan_payment_set = []
                for lp in d.loanpayment_set.all():
                    _payment_type = '-'
                    _number_of_vouchers = 0
                    transaction_payment_set = lp.transactionpayment_set
                    if transaction_payment_set.count() > 0:
                        transaction_payment = transaction_payment_set.first()
                        _payment_type = transaction_payment.get_type_display()
                        _number_of_vouchers = transaction_payment.number_of_vouchers

                    loan_payment = {
                        'id': lp.id,
                        'quantity': lp.quantity,
                        'number_of_vouchers': _number_of_vouchers,
                        'date': lp.create_at,
                        'price': lp.price,
                        'type': _payment_type,
                    }
                    loan_payment_set.append(loan_payment)

                loans_count = d.loanpayment_set.count()

                if loans_count == 0:
                    rowspan = 1
                else:
                    rowspan = loans_count
                    if not new['has_loans']:
                        new['has_loans'] = True

                order_detail = {
                    'id': d.id,
                    'product': d.product.name,
                    'unit': d.unit.name,
                    'type': _type,
                    'quantity_sold': d.quantity_sold,
                    'price_unit': d.price_unit,
                    'multiply': d.multiply,
                    'return_loan': d.return_loan(),
                    'repay_loan': d.repay_loan(),
                    'repay_loan_ball': d.repay_loan_ball(),
                    'repay_loan_with_vouchers': d.repay_loan_with_vouchers(),
                    'ball_changes': d.ball_changes(),
                    'loan_payment_set': loan_payment_set,
                    'loans_count': loans_count,
                    'rowspan': rowspan,
                    'has_spending': False
                }
                new.get('order_detail_set').append(order_detail)
                new['rowspan'] = new['rowspan'] + rowspan

                if d.unit.name == 'G' and o.distribution_mobil:
                    order_detail['has_spending'] = True
                else:
                    order_detail['has_spending'] = False

            dictionary.append(new)

    sum_total = 0
    sum_total_repay_loan = 0
    sum_total_repay_loan_with_vouchers = 0
    sum_total_return_loan = 0
    sum_total_remaining_repay_loan = 0
    sum_total_remaining_return_loan = 0
    sum_total_remaining_repay_loan_ball = 0
    sum_total_ball_changes = 0
    sum_total_cash_flow_spending = 0
    if order_set.count() > 0:
        for o in order_set:
            sum_total_repay_loan = sum_total_repay_loan + o.total_repay_loan()
            sum_total_repay_loan_with_vouchers = sum_total_repay_loan_with_vouchers + o.total_repay_loan_with_vouchers()
            sum_total_return_loan = sum_total_return_loan + o.total_return_loan()
            sum_total_remaining_repay_loan = sum_total_remaining_repay_loan + o.total_remaining_repay_loan()
            sum_total_remaining_return_loan = sum_total_remaining_return_loan + o.total_remaining_return_loan()
            sum_total_remaining_repay_loan_ball = sum_total_remaining_repay_loan_ball + o.total_remaining_repay_loan_ball()
            sum_total_ball_changes = sum_total_ball_changes + o.total_ball_changes()
            sum_total_cash_flow_spending = sum_total_cash_flow_spending + o.total_cash_flow_spending()
        total_set = order_set.values('client').annotate(totals=Sum('total'))
        sum_total = total_set[0].get('totals')
    tpl = loader.get_template('sales/account_order_list.html')
    context = ({
        'dictionary': dictionary,
        'sum_total': sum_total,
        'sum_total_repay_loan': sum_total_repay_loan,
        'sum_total_repay_loan_with_vouchers': sum_total_repay_loan_with_vouchers,
        'sum_total_return_loan': sum_total_return_loan,
        'sum_total_remaining_repay_loan': sum_total_remaining_repay_loan,
        'sum_total_remaining_repay_loan_ball': sum_total_remaining_repay_loan_ball,
        'sum_total_remaining_return_loan': sum_total_remaining_return_loan,
        'sum_total_ball_changes': sum_total_ball_changes,
        'sum_total_cash_flow_spending': sum_total_cash_flow_spending,
        'is_pdf': is_pdf,
        'client_obj': client_obj,
    })

    return tpl.render(context)


def get_orders_by_client(request):
    if request.method == 'GET':
        client_id = request.GET.get('client_id', '')
        client_obj = Client.objects.get(pk=int(client_id))
        order_set = Order.objects.filter(client=client_obj).exclude(type='E').order_by('id')

    return JsonResponse({
        'grid': get_dict_orders(order_set, client_obj=client_obj, is_pdf=False),
    }, status=HTTPStatus.OK)


def get_iron_man(product_id):
    # user_id = self.request.user.id
    # user_obj = User.objects.get(id=user_id)
    # subsidiary_obj = get_subsidiary_by_user(user_obj)
    product_obj = Product.objects.get(id=product_id)
    subcategory_obj = ProductSubcategory.objects.get(name='FIERRO', product_category__name='FIERRO')
    product_insume_set = ProductRecipe.objects.filter(product=product_obj,
                                                      product_input__product_subcategory=subcategory_obj)
    product_insume_obj = product_insume_set.first().product_input
    return product_insume_obj


def get_order_detail_for_pay(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        detail_id = request.GET.get('detail_id', '')
        detail_obj = OrderDetail.objects.get(id=int(detail_id))
        order_obj = Order.objects.get(orderdetail=detail_obj)
        cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')
        cash_deposit_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='104')
        mydate = datetime.now()
        formatdate = mydate.strftime("%Y-%m-%d")
        tpl = loader.get_template('sales/new_payment_from_lending.html')
        context = ({
            'choices_payments': TransactionPayment._meta.get_field('type').choices,
            'detail': detail_obj,
            'order': order_obj,
            'choices_account': cash_set,
            'choices_account_bank': cash_deposit_set,
            'date': formatdate
        })

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def get_expenses(request):
    if request.method == 'GET':
        transactionaccount_obj = TransactionAccount.objects.all()
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        tpl = loader.get_template('sales/new_expense.html')
        cash_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='101')
        cash_deposit_set = Cash.objects.filter(subsidiary=subsidiary_obj, accounting_account__code__startswith='104')
        mydate = datetime.now()
        formatdate = mydate.strftime("%Y-%m-%d")

        context = ({
            'choices_document': TransactionAccount._meta.get_field('document_type_attached').choices,
            'transactionaccount': transactionaccount_obj,
            'choices_account': cash_set,
            'choices_account_bank': cash_deposit_set,
            'date': formatdate
        })

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def new_expense(request):
    if request.method == 'POST':
        transaction_date = str(request.POST.get('id_date'))
        type_document = str(request.POST.get('id_transaction_document_type'))
        serie = str(request.POST.get('id_serie'))
        nro = str(request.POST.get('id_nro'))
        total_pay = str(request.POST.get('pay-loan')).replace(',', '.')
        order = int(request.POST.get('id_order'))
        order_obj = Order.objects.get(id=order)
        subtotal = str(request.POST.get('id_subtotal'))
        igv = str(request.POST.get('igv'))
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        serie_obj = None
        nro_obj = None
        if serie:
            serie_obj = serie
        if nro:
            nro_obj = nro
        description_expense = str(request.POST.get('id_description'))
        total = str(request.POST.get('id_amount'))
        _account = str(request.POST.get('id_cash'))
        cashflow_set = CashFlow.objects.filter(cash_id=_account, transaction_date__date=transaction_date, type='A')

        if cashflow_set.count() > 0:
            cash_obj = cashflow_set.first().cash

            if decimal.Decimal(total) > decimal.Decimal(total_pay):
                data = {
                    'error': "El monto excede al total de la deuda"}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response
        else:
            data = {'error': "No existe una Apertura de Caja"}
            response = JsonResponse(data)
            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            return response

        cashflow_obj = CashFlow(
            transaction_date=transaction_date,
            document_type_attached=type_document,
            serial=serie_obj,
            n_receipt=nro_obj,
            description=description_expense,
            subtotal=subtotal,
            igv=igv,
            total=total,
            order=order_obj,
            type='S',
            cash=cash_obj,
            user=user_obj
        )
        cashflow_obj.save()

        order_set = Order.objects.filter(
            client=order_obj.client).exclude(type='E').order_by('id')

        return JsonResponse({
            'message': 'Registro guardado correctamente.',
            'grid': get_dict_orders(order_set, client_obj=order_obj.client, is_pdf=False)
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def new_loan_payment(request):
    data = dict()
    if request.method == 'POST':

        id_detail = int(request.POST.get('detail'))
        detail_obj = OrderDetail.objects.get(id=id_detail)
        option = str(request.POST.get('radio'))  # G or B or P
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)

        payment = 0
        quantity = 0

        if option == 'G':

            if len(request.POST.get('loan_payment', '')) > 0:
                val = decimal.Decimal(request.POST.get('loan_payment'))
                if 0 < val <= detail_obj.order.total_remaining_repay_loan():
                    transaction_payment_type = str(request.POST.get('transaction_payment_type'))
                    number_of_vouchers = decimal.Decimal(
                        request.POST.get('number_of_vouchers', '0'))
                    code_operation = str(request.POST.get('code_operation'))

                    payment = val

                    if transaction_payment_type == 'D':
                        cash_flow_description = str(request.POST.get('description_deposit'))
                        cash_flow_transact_date_deposit = str(request.POST.get('id_date_deposit'))
                        cash_id = str(request.POST.get('id_cash_deposit'))
                        cash_obj = Cash.objects.get(id=cash_id)
                        order_obj = detail_obj.order

                        cashflow_obj = CashFlow(
                            transaction_date=cash_flow_transact_date_deposit,
                            document_type_attached='O',
                            description=cash_flow_description,
                            order=order_obj,
                            type='D',
                            operation_code=code_operation,
                            total=payment,
                            cash=cash_obj,
                            user=user_obj
                        )
                        cashflow_obj.save()

                        loan_payment_obj = LoanPayment(
                            price=payment,
                            quantity=quantity,
                            product=detail_obj.product,
                            order_detail=detail_obj,
                        )
                        loan_payment_obj.save()

                        transaction_payment_obj = TransactionPayment(
                            payment=payment,
                            number_of_vouchers=number_of_vouchers,
                            type=transaction_payment_type,
                            operation_code=code_operation,
                            loan_payment=loan_payment_obj
                        )
                        transaction_payment_obj.save()

                    if transaction_payment_type == 'E':

                        cash_flow_transact_date = str(request.POST.get('id_date'))
                        cash_flow_description = str(request.POST.get('id_description'))
                        cash_id = str(request.POST.get('id_cash_efectivo'))
                        cash_obj = Cash.objects.get(id=cash_id)
                        order_obj = detail_obj.order
                        cashflow_set = CashFlow.objects.filter(cash_id=cash_id,
                                                               transaction_date__date=cash_flow_transact_date, type='A')
                        if cashflow_set.count() > 0:
                            cash_obj = cashflow_set.first().cash
                        else:
                            data = {'error': "No existe una Apertura de Caja, Favor de revisar las Control de Cajas"}
                            response = JsonResponse(data)
                            response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                            return response

                        cashflow_obj = CashFlow(
                            transaction_date=cash_flow_transact_date,
                            document_type_attached='O',
                            description=cash_flow_description,
                            order=order_obj,
                            type='E',
                            total=payment,
                            cash=cash_obj,
                            user=user_obj
                        )
                        cashflow_obj.save()

                        loan_payment_obj = LoanPayment(
                            price=payment,
                            quantity=quantity,
                            product=detail_obj.product,
                            order_detail=detail_obj,
                        )
                        loan_payment_obj.save()

                        transaction_payment_obj = TransactionPayment(
                            payment=payment,
                            number_of_vouchers=number_of_vouchers,
                            type=transaction_payment_type,
                            operation_code=code_operation,
                            loan_payment=loan_payment_obj
                        )
                        transaction_payment_obj.save()

                    if transaction_payment_type == 'F':
                        cash_flow_description = str(request.POST.get('id_description_deposit_fise'))
                        cash_flow_transact_date_deposit = str(request.POST.get('id_date_desposit_fise'))
                        cash_id = str(request.POST.get('id_cash_deposit_fise'))
                        cash_obj = Cash.objects.get(id=cash_id)
                        order_obj = detail_obj.order

                        cashflow_obj = CashFlow(
                            transaction_date=cash_flow_transact_date_deposit,
                            document_type_attached='O',
                            description=cash_flow_description,
                            order=order_obj,
                            type='D',
                            operation_code=code_operation,
                            total=payment,
                            cash=cash_obj,
                            user=user_obj
                        )
                        cashflow_obj.save()

                        loan_payment_obj = LoanPayment(
                            price=payment,
                            quantity=quantity,
                            product=detail_obj.product,
                            order_detail=detail_obj,
                        )
                        loan_payment_obj.save()

                        transaction_payment_obj = TransactionPayment(
                            payment=payment,
                            number_of_vouchers=number_of_vouchers,
                            type=transaction_payment_type,
                            operation_code=code_operation,
                            loan_payment=loan_payment_obj
                        )
                        transaction_payment_obj.save()

        else:
            if option == 'B':

                if len(request.POST.get('loan_quantity', '')) > 0:
                    val = decimal.Decimal(request.POST.get('loan_quantity'))
                    if 0 < val <= detail_obj.quantity_sold:
                        quantity = val
                        loan_payment_obj = LoanPayment(
                            price=detail_obj.price_unit,
                            quantity=quantity,
                            product=detail_obj.product,
                            order_detail=detail_obj,
                        )
                        loan_payment_obj.save()
                        if detail_obj.order.type == 'V':
                            if detail_obj.unit.name == 'B':
                                product_supply_obj = get_iron_man(detail_obj.product.id)
                                subsidiary_store_supply_obj = SubsidiaryStore.objects.get(
                                    subsidiary=detail_obj.order.subsidiary_store.subsidiary, category='I')
                                try:
                                    product_store_supply_obj = ProductStore.objects.get(product=product_supply_obj,
                                                                                        subsidiary_store=subsidiary_store_supply_obj)
                                    kardex_input(product_store_supply_obj.id, quantity,
                                                 product_supply_obj.calculate_minimum_price_sale(),
                                                 loan_payment_obj=loan_payment_obj)
                                except ProductStore.DoesNotExist:
                                    product_store_supply_obj = ProductStore(
                                        product=product_supply_obj,
                                        subsidiary_store=subsidiary_store_supply_obj,
                                        stock=quantity
                                    )
                                    product_store_supply_obj.save()
                                    kardex_initial(product_store_supply_obj, quantity,
                                                   product_supply_obj.calculate_minimum_price_sale(),
                                                   loan_payment_obj=loan_payment_obj)

            elif option == 'P':

                if len(request.POST.get('loan_quantity2', '')) > 0:
                    val = decimal.Decimal(request.POST.get('loan_quantity2'))

                    if 0 < val <= detail_obj.quantity_sold:
                        quantity = val
                        if len(request.POST.get('loan_payment2', '')) > 0:
                            val2 = decimal.Decimal(request.POST.get('loan_payment2'))
                            if 0 < val2 <= detail_obj.multiply():
                                transaction_payment_type = str(
                                    request.POST.get('transaction_payment_type2'))
                                code_operation = str(request.POST.get('code_operation2'))
                                payment = val2
                                unit_price_with_discount = payment / quantity
                                product_detail_obj = ProductDetail.objects.get(product=detail_obj.product,
                                                                               unit=detail_obj.unit)
                                unit_price = product_detail_obj.price_sale
                                _discount = unit_price - unit_price_with_discount

                                if transaction_payment_type == 'D':
                                    cash_flow_transact_date = str(request.POST.get('id_date_desposit2'))
                                    cash_flow_description = str(request.POST.get('description_deposit2'))
                                    cash_id = str(request.POST.get('id_cash_deposit2'))
                                    cash_obj = Cash.objects.get(id=cash_id)
                                    order_obj = detail_obj.order

                                    cashflow_obj = CashFlow(
                                        transaction_date=cash_flow_transact_date,
                                        document_type_attached='O',
                                        description=cash_flow_description,
                                        order=order_obj,
                                        type='D',
                                        operation_code=code_operation,
                                        total=payment,
                                        cash=cash_obj,
                                        user=user_obj
                                    )
                                    cashflow_obj.save()

                                    loan_payment_obj = LoanPayment(
                                        price=unit_price_with_discount,
                                        quantity=quantity,
                                        discount=_discount,
                                        product=detail_obj.product,
                                        order_detail=detail_obj
                                    )
                                    loan_payment_obj.save()

                                    transaction_payment_obj = TransactionPayment(
                                        payment=payment,
                                        type=transaction_payment_type,
                                        operation_code=code_operation,
                                        loan_payment=loan_payment_obj
                                    )
                                    transaction_payment_obj.save()

                                if transaction_payment_type == 'E':

                                    cash_flow_transact_date = str(request.POST.get('id_date2'))
                                    cash_flow_description = str(request.POST.get('id_description2'))
                                    cash_id = str(request.POST.get('id_cash_efectivo2'))
                                    cash_obj = Cash.objects.get(id=cash_id)
                                    order_obj = detail_obj.order
                                    cashflow_set = CashFlow.objects.filter(cash_id=cash_id,
                                                                           transaction_date__date=cash_flow_transact_date,
                                                                           type='A')
                                    if cashflow_set.count() > 0:
                                        cash_obj = cashflow_set.first().cash
                                    else:
                                        data = {
                                            'error': "No existe una Apertura de Caja, Favor de revisar las Control de Cajas"}
                                        response = JsonResponse(data)
                                        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                                        return response

                                    cashflow_obj = CashFlow(
                                        transaction_date=cash_flow_transact_date,
                                        document_type_attached='O',
                                        description=cash_flow_description,
                                        order=order_obj,
                                        type='E',
                                        total=payment,
                                        cash=cash_obj,
                                        user=user_obj
                                    )
                                    cashflow_obj.save()

                                    loan_payment_obj = LoanPayment(
                                        price=unit_price_with_discount,
                                        quantity=quantity,
                                        discount=_discount,
                                        product=detail_obj.product,
                                        order_detail=detail_obj
                                    )
                                    loan_payment_obj.save()

                                    transaction_payment_obj = TransactionPayment(
                                        payment=payment,
                                        type=transaction_payment_type,
                                        operation_code=code_operation,
                                        loan_payment=loan_payment_obj
                                    )
                                    transaction_payment_obj.save()

        order_set = Order.objects.filter(
            client=detail_obj.order.client).exclude(type='E').order_by('id')

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': get_dict_orders(order_set, client_obj=detail_obj.order.client, is_pdf=False),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def open_loan_account(order_detail_obj, payment=0, quantity=0):
    new_quantity = decimal.Decimal(quantity)
    new_price_unit = decimal.Decimal(payment)
    new_price_total = new_quantity * new_price_unit
    new_remaining_quantity = new_quantity
    new_remaining_price = new_price_unit
    new_remaining_price_total = new_remaining_quantity * new_remaining_price

    new_loan_account = LoanAccount(
        operation='L',
        quantity=new_quantity,
        price_unit=new_price_unit,
        price_total=new_price_total,
        remaining_quantity=new_remaining_quantity,
        remaining_price=new_remaining_price,
        remaining_price_total=new_remaining_price_total,
        product=order_detail_obj.product,
        order_detail=order_detail_obj,
    )
    new_loan_account.save()


def return_loan_account(order_detail_obj, payment=0, quantity=0):
    new_quantity = decimal.Decimal(quantity)
    new_price_unit = decimal.Decimal(payment)
    new_price_total = new_quantity * new_price_unit

    loan_account_set = LoanAccount.objects.filter(
        client=order_detail_obj.order.client, product=order_detail_obj.product)

    if loan_account_set.count > 0:
        last_loan_account = loan_account_set.last()
        last_remaining_quantity = last_loan_account.remaining_quantity
        last_remaining_price_total = last_loan_account.remaining_price_total

        new_remaining_quantity = last_remaining_quantity + new_quantity
        new_remaining_price = (decimal.Decimal(last_remaining_price_total) +
                               new_price_total) / new_remaining_quantity
        new_remaining_price_total = new_remaining_quantity * new_remaining_price

        new_loan_account = LoanAccount(
            operation='P',
            quantity=new_quantity,
            price_unit=new_price_unit,
            price_total=new_price_total,
            remaining_quantity=new_remaining_quantity,
            remaining_price=new_remaining_price,
            remaining_price_total=new_remaining_price_total,
            product=order_detail_obj.product,
            order_detail=order_detail_obj,
        )
        new_loan_account.save()


def get_order_detail_for_ball_change(request):
    if request.method == 'GET':
        detail_id = request.GET.get('detail_id', '')
        detail_obj = OrderDetail.objects.get(id=int(detail_id))
        tpl = loader.get_template('sales/new_ball_change.html')
        context = ({
            'choices_status': BallChange._meta.get_field('status').choices,
            'detail': detail_obj,
        })

        return JsonResponse({
            'grid': tpl.render(context, request),
        }, status=HTTPStatus.OK)


def new_ball_change(request):
    if request.method == 'POST':

        id_detail = int(request.POST.get('detail'))
        detail_obj = OrderDetail.objects.get(id=id_detail)

        quantity = 0
        ball_change_obj = None

        if len(request.POST.get('quantity', '')) > 0:
            val = decimal.Decimal(request.POST.get('quantity'))
            if 0 < val <= detail_obj.quantity_sold:
                status = str(request.POST.get('status'))
                observation = str(request.POST.get('observation'))
                quantity = val

                ball_change_obj = BallChange(
                    status=status,
                    observation=observation,
                    quantity=quantity,
                    product=detail_obj.product,
                    order_detail=detail_obj,
                )
                ball_change_obj.save()

        if detail_obj.order.type == 'V':

            # OUTPUT SALES
            subsidiary_store_sales_obj = detail_obj.order.subsidiary_store
            product_store_sales_obj = ProductStore.objects.get(product=detail_obj.product,
                                                               subsidiary_store=subsidiary_store_sales_obj)
            kardex_ouput(product_store_sales_obj.id, quantity, ball_change_obj=ball_change_obj)

            # INPUT MAINTENANCE
            try:
                subsidiary_store_maintenance_obj = SubsidiaryStore.objects.get(
                    subsidiary=detail_obj.order.subsidiary_store.subsidiary, category='R')
            except SubsidiaryStore.DoesNotExist:
                data = {'error': 'No se encontro el almacen de mantenimiento.'}
                response = JsonResponse(data)
                response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                return response

            try:
                product_store_maintenance_obj = ProductStore.objects.get(product=detail_obj.product,
                                                                         subsidiary_store=subsidiary_store_maintenance_obj)
                kardex_input(product_store_maintenance_obj.id, quantity,
                             detail_obj.product.calculate_minimum_price_sale(),
                             ball_change_obj=ball_change_obj)
            except ProductStore.DoesNotExist:
                product_store_maintenance_obj = ProductStore(
                    product=detail_obj.product,
                    subsidiary_store=subsidiary_store_maintenance_obj,
                    stock=quantity
                )
                product_store_maintenance_obj.save()
                kardex_initial(product_store_maintenance_obj, quantity,
                               detail_obj.product.calculate_minimum_price_sale(),
                               ball_change_obj=ball_change_obj)

        order_set = Order.objects.filter(
            client=detail_obj.order.client).exclude(type='E').order_by('id')

        return JsonResponse({
            'message': 'Cambios guardados con exito.',
            'grid': get_dict_orders(order_set, client_obj=detail_obj.order.client, is_pdf=False),
        }, status=HTTPStatus.OK)
    return JsonResponse({'message': 'Error de peticion.'}, status=HTTPStatus.BAD_REQUEST)


def generate_receipt(request):
    truck_set = Truck.objects.exclude(truck_model__name__in=['INTER', 'VOLVO'])
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    SubsidiaryStore_obj = SubsidiaryStore.objects.filter(subsidiary=subsidiary_obj, category='V').first()
    product_store_set = ProductStore.objects.filter(subsidiary_store=SubsidiaryStore_obj)
    products_set = Product.objects.filter(productstore__in=product_store_set)
    clients = Client.objects.all()

    return render(request, 'sales/receipt_random.html', {
        'trucks': truck_set,
        'products_set': products_set,
        'clients': clients
    })


def PerceptronList(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        subsidiary_obj = get_subsidiary_by_user(user_obj)
        clients_set = Client.objects.filter(clienttype__document_type='06')
        orders = Order.objects.all()
        mydate = datetime.now()
        formatdate = mydate.strftime("%Y-%m-%d %H:%M:%S")
        truck_Set = Truck.objects.all()

        return render(request, 'sales/new_perceptron.html', {
            'orders': orders,
            'clients': clients_set,
            'date': formatdate
        })


def send_invoices_sunat(request):
    if request.method == 'GET':
        date = '2023-07-17'
        order_bill_set = OrderBill.objects.filter(created_at__date=date, is_demo='D').order_by('created_at', 'n_receipt')
        for o in order_bill_set:
            order_id = o.order.id
            if o.order.type_order == 'E':
                if o.type == '1':
                    r = send_bill_nubefact(order_id)
                    if r.get('serie'):
                        print(str(r.get('serie')) + '-' + str(r.get("numero")))
                elif o.type == '2':
                    r = send_receipt_nubefact(order_id)
                    if r.get('serie'):
                        print(str(r.get('serie')) + '-' + str(r.get("numero")))
                o.is_demo = 'P'
                o.save()
            elif o.order.type_order == 'P':
                if o.type == '1':
                    r = send_bill_passenger(order_id)
                    if r.get('serie'):
                        print(str(r.get('serie')) + '-' + str(r.get("numero")))
                elif o.type == '2':
                    r = send_receipt_passenger(order_id)
                    if r.get('serie'):
                        print(str(r.get('serie')) + '-' + str(r.get("numero")))
                o.is_demo = 'P'
                o.save()
        print('end_send')
        return JsonResponse({
            'message': 'Enviado.',
        }, status=HTTPStatus.OK)