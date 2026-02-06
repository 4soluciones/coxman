from apps.comercial.models import Programming
from apps.hrm.models import SubsidiaryCompany
from apps.sales.models import Order


# def get_correlative_passenger(subsidiary_obj=None, company_rotation_obj=None):
#     result = ''
#     search = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
#     if search.exists():
#         subsidiary_company_obj = search.last()
#         c_two = subsidiary_company_obj.correlative_serial_two
#         c_two = c_two + 1
#         result = str(c_two).zfill(6)
#     return result


def get_correlative_electronic_passenger(subsidiary_obj=None, company_rotation_obj=None, doc_type=None):
    result = ''
    search = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if search.exists():
        subsidiary_company_obj = search.last()
        if doc_type == 'B':
            get_voucher = subsidiary_company_obj.correlative_of_vouchers_to_passenger
            new_voucher = get_voucher + 1
            result = str(new_voucher).zfill(6)
        elif doc_type == 'F':
            get_invoice = subsidiary_company_obj.correlative_of_invoices_to_passenger
            new_invoice = get_invoice + 1
            result = str(new_invoice).zfill(6)
        elif doc_type == 'T':
            get_ticket = subsidiary_company_obj.correlative_serial_two
            new_ticket = get_ticket + 1
            result = str(new_ticket).zfill(6)
    return result


def get_correlative_manifest(subsidiary_obj=None, company_rotation_obj=None):
    result = ''
    # c_set = Programming.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    search = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if search.exists():
        subsidiary_company_obj = search.last()
        c_three = subsidiary_company_obj.correlative_serial_three
        c_three = c_three + 1
        result = str(c_three).zfill(6)
    return result


def get_correlative_commodity(subsidiary_obj=None, company_rotation_obj=None, doc_type=None):
    result = ''
    search = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_obj, company=company_rotation_obj)
    if search.exists():
        subsidiary_company_obj = search.last()
        if doc_type == 'B':
            get_voucher = subsidiary_company_obj.correlative_of_vouchers_to_commodity
            new_voucher = get_voucher + 1
            result = str(new_voucher).zfill(6)
        elif doc_type == 'F':
            get_invoice = subsidiary_company_obj.correlative_of_invoices_to_commodity
            new_invoice = get_invoice + 1
            result = str(new_invoice).zfill(6)
        elif doc_type == 'T':
            get_ticket = subsidiary_company_obj.correlative_serial
            new_ticket = get_ticket + 1
            result = str(new_ticket).zfill(6)
    return result


def update_correlative_commodity(order_obj=None):

    search = SubsidiaryCompany.objects.filter(subsidiary=order_obj.subsidiary, company=order_obj.company)
    subsidiary_company_obj = search.last()

    c = int(order_obj.correlative_sale)

    if order_obj.type_order == 'E' and order_obj.type_document == 'T':  # TICKET
        subsidiary_company_obj.correlative_serial = c
        subsidiary_company_obj.save()

    if order_obj.type_order == 'E' and order_obj.type_document == 'B':  # TICKET
        subsidiary_company_obj.correlative_of_vouchers_to_commodity = c
        subsidiary_company_obj.save()

    if order_obj.type_order == 'E' and order_obj.type_document == 'F':  # TICKET
        subsidiary_company_obj.correlative_of_invoices_to_commodity = c
        subsidiary_company_obj.save()


def update_correlative_passenger(order_obj=None):

    search = SubsidiaryCompany.objects.filter(subsidiary=order_obj.subsidiary, company=order_obj.company)
    subsidiary_company_obj = search.last()

    correlative = int(order_obj.correlative_sale)

    if order_obj.type_order == 'P' and order_obj.type_document == 'B':
        subsidiary_company_obj.correlative_of_vouchers_to_passenger = correlative

    elif order_obj.type_order == 'P' and order_obj.type_document == 'F':
        subsidiary_company_obj.correlative_of_invoices_to_passenger = correlative

    elif order_obj.type_order == 'P' and order_obj.type_document == 'T':
        subsidiary_company_obj.correlative_serial_two = correlative

    subsidiary_company_obj.save()


def update_correlative_manifest_passenger(programming_obj=None):

    search = SubsidiaryCompany.objects.filter(subsidiary=programming_obj.subsidiary, company=programming_obj.company)
    subsidiary_company_obj = search.last()
    c_three = int(programming_obj.correlative)
    subsidiary_company_obj.correlative_serial_three = c_three
    subsidiary_company_obj.save()

'''
def get_correlative_passenger(serial_two, doc_type='B'):
    serial = doc_type + serial_two[-3:]

    c = OrderBill.objects.filter(serial=serial)
    correlative = 1
    if doc_type == 'B':
        c = c.filter(type='2')
    elif doc_type == 'F':
        c = c.filter(type='1')
    if c:
        correlative = c.last().n_receipt
        correlative = correlative + 1
    return correlative
'''
