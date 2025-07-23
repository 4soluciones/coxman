import requests

from .format_to_dates import utc_to_local
from .models import *
from ..hrm.views import get_subsidiary_by_user

GRAPHQL_URL = "https://ng.tuf4ctur4.net.pe/graphql"

tokens = {
    "20612403083": "gAAAAABoeUnbvlFDG3JPddIKSh_QW3ucWdV_nOAoiWUy2mLen3DBxQNxZwnC-iIfZVA1pucRVViggSLTHL3Hzj0iYcLoCu4Tcw==",

}


def send_bill_commodity_fact(request, order_id):  # FACTURA DE ENCOMIENDA 4FACT
    order_obj = Order.objects.get(id=int(order_id))
    serial = order_obj.serial
    correlative = order_obj.correlative_sale
    details = OrderDetail.objects.filter(order=order_obj)
    client_obj_sender = Client.objects.filter(orderaction__order=order_obj, orderaction__type='R').first()
    client_obj_sender_name = str(client_obj_sender.names).replace('"', "'")
    client_first_address = client_obj_sender.clientaddress_set.first()
    client_first_address_address = str(client_first_address).replace('"', "'")
    client_document = client_obj_sender.clienttype_set.filter(document_type_id='06').first()
    register_date = utc_to_local(order_obj.create_at)
    formatdate = order_obj.traslate_date.strftime("%Y-%m-%d")
    hour_date = register_date.strftime("%H:%M:%S")

    items = []
    index = 1
    sub_total = 0
    total = 0
    igv_total = 0
    _base_total_v = 0
    _base_amount_v = 0
    _igv = 0
    for d in details:
        base_total = d.quantity * d.price_unit
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        _base_total_v = _base_total_v + base_total
        _base_amount_v = (_base_amount_v + base_amount) / d.quantity
        _igv = _base_total_v - _base_amount_v
        sub_total = sub_total + base_amount
        total = total + base_total
        igv_total = igv_total + igv

        item = {
            "index": str(index),
            "codigoUnidad": "ZZ",
            "codigoProducto": "0000",
            "codigoSunat": "10000000",
            "producto": "TRANSPORTE DE CARGA POR CARRETERA A NIVEL REGIONAL Y NACIONAL",
            "cantidad": float(d.quantity),
            "precioBase": float(round(_base_amount_v, 6)),
            "tipoIgvCodigo": "10"
        }
        items.append(item)

    items_graphql = ", ".join(
        f"""{{  
               producto: "{item['producto']}", 
               cantidad: {item['cantidad']}, 
               precioBase: {item['precioBase']}, 
               codigoSunat: "{item['codigoSunat']}",
               codigoProducto: "{item['codigoProducto']}",
               codigoUnidad: "{item['codigoUnidad']}",                                            
               tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
        }}"""
        for item in items
    )

    graphql_query = f"""
    mutation RegisterSale  {{
        registerSale(            
            cliente: {{
                razonSocialNombres: "{client_obj_sender_name}",
                numeroDocumento: "{client_document.document_number}",
                codigoTipoEntidad: 6,
                clienteDireccion: "{client_first_address_address}"
            }},
            venta: {{
                serie: "F{serial[1:]}",
                numero: "{int(correlative)}",
                fechaEmision: "{formatdate}",
                horaEmision: "{hour_date}",
                fechaVencimiento: "",
                monedaId: 1,                
                formaPagoId: 1,
                totalGravada: {float(sub_total)},
                totalDescuentoGlobalPorcentaje: 0,
                totalDescuentoGlobal: 0,
                totalIgv: {float(igv_total)},
                totalExonerada: 0,
                totalInafecta: 0,
                totalImporte: {float(round(total, 2))},
                totalAPagar: {float(round(total, 2))},
                tipoDocumentoCodigo: "01",
                nota: " "
            }},
            items: {items_graphql}
        ) {{
            message
            success
            operationId
        }}
    }}
    """
    # print(graphql_query)

    token = tokens.get(order_obj.company.ruc, "ID no encontrado")

    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }

    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()

        result = response.json()

        success = result.get("data", {}).get("registerSale", {}).get("success")

        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": order_obj.serial,
                "numero": order_obj.correlative_sale,
                "tipo_de_comprobante": "1",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa",
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def send_receipt_commodity_fact(request, order_id):  # BOLETA DE ENCOMIENDA 4FACT
    order_obj = Order.objects.get(id=int(order_id))
    subsidiary = order_obj.subsidiary
    subsidiary_id = subsidiary.id
    # serie = subsidiary.serial
    serial = order_obj.serial
    # n_receipt = get_correlative(order_obj, 'B')
    correlative = order_obj.correlative_sale
    details = OrderDetail.objects.filter(order=order_obj)
    client_first_address = ""
    client_obj_sender = Client.objects.filter(orderaction__order=order_obj, orderaction__type='R').first()
    if client_obj_sender.clientaddress_set.first():
        client_first_address = client_obj_sender.clientaddress_set.first()
    # client_document = client_obj_sender.clienttype_set.filter(document_type_id='01').first()
    client_document_type_obj = client_obj_sender.clienttype_set.all().first()
    client_document = client_document_type_obj.document_number
    register_date = utc_to_local(order_obj.create_at)
    formatdate = register_date.strftime("%Y-%m-%d")
    hour_date = register_date.strftime("%H:%M:%S")

    items = []
    index = 1
    sub_total = 0
    total = 0
    igv_total = 0
    _base_total_v = 0
    _base_amount_v = 0
    _igv = 0
    for d in details:
        base_total = d.quantity * d.price_unit
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        _base_total_v = _base_total_v + base_total
        _base_amount_v = (_base_amount_v + base_amount) / d.quantity
        _igv = _base_total_v - _base_amount_v
        sub_total = sub_total + base_amount
        total = total + base_total
        igv_total = igv_total + igv

        item = {
            "index": str(index),
            "codigoUnidad": "ZZ",
            "codigoProducto": "0000",
            "codigoSunat": "10000000",
            "producto": "TRANSPORTE DE CARGA POR CARRETERA A NIVEL REGIONAL Y NACIONAL",
            "cantidad": float(d.quantity),
            "precioBase": float(round(_base_amount_v, 6)),
            "tipoIgvCodigo": "10"
        }
        items.append(item)

    items_graphql = ", ".join(
        f"""{{                     
                codigoUnidad: "{item['codigoUnidad']}", 
                codigoProducto: "{item['codigoProducto']}", 
                codigoSunat: "{item['codigoSunat']}", 
                producto: "{item['producto']}", 
                cantidad: {item['cantidad']}, 
                precioBase: {item['precioBase']}, 
                tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
            }}"""
        for item in items
    )

    graphql_query = f"""
        mutation RegisterSale  {{
            registerSale(            
                cliente: {{
                    razonSocialNombres: "{client_obj_sender.names}",
                    numeroDocumento: "{client_document}",
                    codigoTipoEntidad: {int(client_document_type_obj.document_type.id)},
                    clienteDireccion: "{client_first_address}"
                }},
                venta: {{
                    serie: "B{serial[1:]}",
                    numero: "{int(correlative)}",
                    fechaEmision: "{formatdate}",
                    horaEmision: "{hour_date}",
                    fechaVencimiento: "",
                    monedaId: 1,                
                    formaPagoId: 1,
                    totalGravada: {float(sub_total)},
                    totalDescuentoGlobalPorcentaje: 0,
                    totalDescuentoGlobal: 0,
                    totalIgv: {float(igv_total)},
                    totalExonerada: 0,
                    totalInafecta: 0,
                    totalImporte: {float(round(total, 2))},
                    totalAPagar: {float(round(total, 2))},
                    tipoDocumentoCodigo: "03",
                    nota: " "
                }},
                items: {items_graphql}
            ) {{
                message
                success
                operationId
            }}
        }}
        """

    # print(graphql_query)

    token = tokens.get(order_obj.company.ruc, "ID no encontrado")

    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }

    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()

        result = response.json()

        success = result.get("data", {}).get("registerSale", {}).get("success")

        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": order_obj.serial,
                "numero": order_obj.correlative_sale,
                "tipo_de_comprobante": "2",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa",
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def send_bill_ticket_fact(request, order_id):  # FACTURA DE BOLETO DE VIAJE 4 FACT
    order_obj = Order.objects.get(id=int(order_id))
    serial = order_obj.serial
    correlative = order_obj.correlative_sale
    client_address_address = ""
    client_business_obj = Client.objects.filter(orderaction__order=order_obj, orderaction__type='E').first()
    client_passenger_obj = Client.objects.filter(orderaction__order=order_obj, orderaction__type='P').first()
    client_business_obj_names = str(client_business_obj.names).replace('"', "'")
    if client_business_obj.clientaddress_set.first():
        client_address = client_business_obj.clientaddress_set.first()
        client_address_address = str(client_address.address).replace('"', "'")
    client_document = client_business_obj.clienttype_set.filter(document_type_id='06').first()
    register_date = utc_to_local(order_obj.create_at)
    formatdate = register_date.strftime("%Y-%m-%d")
    hour_date = register_date.strftime("%H:%M:%S")
    items = []
    index = 1
    base_amount = order_obj.total / decimal.Decimal(1.1800)
    igv = order_obj.total - base_amount
    total = base_amount + igv

    user_obj = order_obj.user
    subsidiary_origin_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation

    # Validar si el origen es distinto a la sede
    if order_obj.origin and order_obj.origin.name != subsidiary_origin_obj.name:
        _short_name_origin = order_obj.origin.name.replace("SEDE ", "")
    else:
        subsidiary_company_origin_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_origin_obj,
                                                                         company=company_rotation_obj).last()
        _short_name_origin = subsidiary_company_origin_obj.short_name

    subsidiary_destiny_obj = order_obj.programming_seat.programming.path.get_last_point()
    subsidiary_company_destiny_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_destiny_obj,
                                                                      company=company_rotation_obj).last()

    _short_name_destiny = order_obj.destiny.name

    _observation = f"PASAJERO: {client_passenger_obj.names}"
    _observation_graph = f'"{_observation}"'

    # print(_observation_graph)
    item = {
        "index": str(index),
        "codigoUnidad": "ZZ",
        "codigoProducto": "0000",
        "codigoSunat": "10000000",
        "producto": 'SERVICIO DE TRANSPORTE',
        "description": 'RUTA: ' + _short_name_origin + ' - ' + _short_name_destiny + ' ASIENTO: ' + order_obj.programming_seat.plan_detail.name,
        "cantidad": 1,
        "precioBase": float(round(decimal.Decimal(total), 2)),
        "tipoIgvCodigo": "20"
    }
    items.append(item)

    items_graphql = ", ".join(
        f"""{{                     
               codigoUnidad: "{item['codigoUnidad']}", 
               codigoProducto: "{item['codigoProducto']}", 
               codigoSunat: "{item['codigoSunat']}", 
               producto: "{item['producto']}", 
               description: "{item['description']}", 
               cantidad: {item['cantidad']}, 
               precioBase: {item['precioBase']}, 
               tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
            }}"""
        for item in items
    )

    # item = {
    #     "item": index,
    #     "unidad_de_medida": 'ZZ',
    #     "codigo": "",
    #     "codigo_producto_sunat": "10000000",
    #     "descripcion": 'SERVICIO DE TRANSPORTE RUTA: ' + _short_name_origin + ' - ' + _short_name_destiny + ' ASIENTO: ' + order_obj.programming_seat.plan_detail.name,
    #     "cantidad": '1',
    #     "valor_unitario": str(round(decimal.Decimal(total), 2)),
    #     "precio_unitario": str(round(decimal.Decimal(total), 2)),
    #     "descuento": "",
    #     "subtotal": str(round(decimal.Decimal(total), 2)),
    #     "tipo_de_igv": 8,
    #     "igv": 0,
    #     "total": str(round(decimal.Decimal(total), 2)),
    #     "anticipo_regularizacion": 'false',
    #     "anticipo_documento_serie": "",
    #     "anticipo_documento_numero": "",
    # }
    # items.append(item)

    graphql_query = f"""
        mutation RegisterSale  {{
            registerSale(                
                cliente: {{
                    razonSocialNombres: "{client_business_obj_names}",
                    numeroDocumento: "{client_document.document_number}",
                    codigoTipoEntidad: 6,
                    clienteDireccion: "{client_address_address}"
                }},
                venta: {{
                    serie: "F{serial[1:]}",
                    numero: "{int(correlative)}",
                    fechaEmision: "{formatdate}",
                    horaEmision: "{hour_date}",
                    fechaVencimiento: "",
                    monedaId: 1,                
                    formaPagoId: 1,
                    totalGravada: 0,
                    totalDescuentoGlobalPorcentaje: 0,
                    totalDescuentoGlobal: 0,
                    totalIgv: 0,
                    totalExonerada: {float(total)},
                    totalInafecta: 0,
                    totalImporte: {float(total)},
                    totalAPagar: {float(total)},
                    tipoDocumentoCodigo: "01",
                    nota: {_observation_graph},
                }},
                items: {items_graphql}
            ) {{
                message
                success
                operationId
            }}
        }}
        """
    # print(graphql_query)

    # params = {
    #     "operacion": "generar_comprobante",
    #     "tipo_de_comprobante": 1,
    #     "serie": 'F' + serie[1:],
    #     "numero": n_receipt,
    #     "sunat_transaction": 1,
    #     "cliente_tipo_de_documento": 6,
    #     "cliente_numero_de_documento": client_document.document_number,
    #     "cliente_denominacion": client_business_obj.names,
    #     "cliente_direccion": client_address.address,
    #     "cliente_email": client_business_obj.email,
    #     "cliente_email_1": "",
    #     "cliente_email_2": "",
    #     "fecha_de_emision": formatdate,
    #     "fecha_de_vencimiento": "",
    #     "moneda": 1,
    #     "tipo_de_cambio": "",
    #     "porcentaje_de_igv": 18.00,
    #     "descuento_global": "",
    #     "total_descuento": "",
    #     "total_anticipo": "",
    #     "total_gravada": "",
    #     "total_inafecta": "",
    #     "total_exonerada": str(round(decimal.Decimal(total))),
    #     "total_igv": "",
    #     "total_gratuita": "",
    #     "total_otros_cargos": "",
    #     "total": str(round(decimal.Decimal(total))),
    #     "percepcion_tipo": "",
    #     "percepcion_base_imponible": "",
    #     "total_percepcion": "",
    #     "total_incluido_percepcion": "",
    #     "total_impuestos_bolsas": "",
    #     "detraccion": 'false',
    #     "observaciones": "PASAJERO: " + client_passenger_obj.names,
    #     "documento_que_se_modifica_tipo": "",
    #     "documento_que_se_modifica_serie": "",
    #     "documento_que_se_modifica_numero": "",
    #     "tipo_de_nota_de_credito": "",
    #     "tipo_de_nota_de_debito": "",
    #     "enviar_automaticamente_a_la_sunat": 'true',
    #     "enviar_automaticamente_al_cliente": 'false',
    #     "codigo_unico": "",
    #     "condiciones_de_pago": "",
    #     "medio_de_pago": "",
    #     "placa_vehiculo": "",
    #     "orden_compra_servicio": "",
    #     "tabla_personalizada_codigo": "",
    #     "formato_de_pdf": "",
    #     "items": items,
    # }

    # print(graphql_query)

    token = tokens.get(order_obj.company.ruc, "ID no encontrado")

    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }

    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()

        result = response.json()

        success = result.get("data", {}).get("registerSale", {}).get("success")

        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": order_obj.serial,
                "numero": order_obj.correlative_sale,
                "tipo_de_comprobante": "1",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa",
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def send_receipt_passenger_fact(request, order_id):  # BOLETA DE VENTA PASAJE DE VIAJE FACT
    order_obj = Order.objects.get(id=int(order_id))
    serial = order_obj.serial
    correlative = order_obj.correlative_sale
    client_first_address = ""
    client_passenger_obj = order_obj.client
    client_passenger_type_obj = client_passenger_obj.clienttype_set.all().first()
    if client_passenger_obj.clientaddress_set.first():
        client_first_address = client_passenger_obj.clientaddress_set.first()
    client_document = client_passenger_type_obj.document_number
    register_date = utc_to_local(order_obj.create_at)
    formatdate = register_date.strftime("%Y-%m-%d")
    hour_date = register_date.strftime("%H:%M:%S")

    items = []
    index = 1
    base_amount = order_obj.total / decimal.Decimal(1.1800)
    igv = order_obj.total - base_amount
    total = base_amount + igv

    user_obj = order_obj.user
    subsidiary_origin_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation

    # Validar si el origen es distinto a la sede
    if order_obj.origin and order_obj.origin.name != subsidiary_origin_obj.name:
        _short_name_origin = order_obj.origin.name.replace("SEDE ", "")
    else:
        subsidiary_company_origin_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_origin_obj,
                                                                         company=company_rotation_obj).last()
        _short_name_origin = subsidiary_company_origin_obj.short_name

    subsidiary_destiny_obj = order_obj.programming_seat.programming.path.get_last_point()
    subsidiary_company_destiny_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_destiny_obj,
                                                                      company=company_rotation_obj).last()

    _short_name_destiny = order_obj.destiny.name

    _observation = f"PASAJERO: {client_passenger_obj.names}"
    _observation_graph = f'"{_observation}"'

    item = {
        "index": str(index),
        "codigoUnidad": "ZZ",
        "codigoProducto": "0000",
        "codigoSunat": "10000000",
        "producto": 'SERVICIO DE TRANSPORTE',
        "description": 'RUTA: ' + _short_name_origin + ' - ' + _short_name_destiny + ' ASIENTO: ' + order_obj.programming_seat.plan_detail.name,
        "cantidad": 1,
        "precioBase": float(round(decimal.Decimal(total), 2)),
        "tipoIgvCodigo": "20"
    }
    items.append(item)

    items_graphql = ", ".join(
        f"""{{                     
               codigoUnidad: "{item['codigoUnidad']}", 
               codigoProducto: "{item['codigoProducto']}", 
               codigoSunat: "{item['codigoSunat']}", 
               producto: "{item['producto']}", 
               description: "{item['description']}", 
               cantidad: {item['cantidad']}, 
               precioBase: {item['precioBase']}, 
               tipoIgvCodigo: "{item['tipoIgvCodigo']}" 
            }}"""
        for item in items
    )

    # item = {
    #     "item": index,  # index para los detalles
    #     "unidad_de_medida": 'ZZ',  # NIU viene del nubefact NIU=PRODUCTO
    #     "codigo": "",  # codigo del producto opcional
    #     "codigo_producto_sunat": "10000000",  # codigo del producto excel-sunat
    #     "descripcion": 'SERVICIO DE TRANSPORTE RUTA: ' + _short_name_origin + ' - ' + _short_name_destiny + ' ASIENTO: ' + order_obj.programming_seat.plan_detail.name,
    #     # + d.description,
    #     "cantidad": '1',  # float(round(d.quantity)),
    #     "valor_unitario": float(round(base_amount, 2)),  # valor unitario sin IGV
    #     "precio_unitario": float(round(total, 2)),  # float(round(d.price_unit, 2)),
    #     "descuento": "",
    #     "subtotal": float(round(base_amount, 2)),  # resultado del valor unitario por la cantidad menos el descuento
    #     "tipo_de_igv": 8,  # operacion exonerada
    #     "igv": 0,
    #     "total": float(round(total, 2)),
    #     "anticipo_regularizacion": 'false',
    #     "anticipo_documento_serie": "",
    #     "anticipo_documento_numero": "",
    # }
    # items.append(item)

    graphql_query = f"""
        mutation RegisterSale  {{
            registerSale(                
                cliente: {{
                    razonSocialNombres: "{client_passenger_obj.names}",
                    numeroDocumento: "{client_document}",
                    codigoTipoEntidad: {int(int(client_passenger_type_obj.document_type.id))},
                    clienteDireccion: "{client_first_address}"
                }},
                venta: {{
                    serie: "B{serial[1:]}",
                    numero: "{int(correlative)}",
                    fechaEmision: "{formatdate}",
                    horaEmision: "{hour_date}",
                    fechaVencimiento: "",
                    monedaId: 1,                
                    formaPagoId: 1,
                    totalGravada: 0,
                    totalDescuentoGlobalPorcentaje: 0,
                    totalDescuentoGlobal: 0,
                    totalIgv: 0,
                    totalExonerada: {float(round(total, 2))},
                    totalInafecta: 0,
                    totalImporte: {float(round(total, 2))},
                    totalAPagar: {float(round(total, 2))},
                    tipoDocumentoCodigo: "03",
                    nota: {_observation_graph},
                }},
                items: {items_graphql}
            ) {{
                message
                success
                operationId
            }}
        }}
        """
    # print(graphql_query)

    # params = {
    #     "operacion": "generar_comprobante",
    #     "tipo_de_comprobante": 2,
    #     "serie": serie,
    #     "numero": n_receipt,
    #     "sunat_transaction": 1,
    #     "cliente_tipo_de_documento": int(client_passenger_type_obj.document_type.id),
    #     "cliente_numero_de_documento": client_document,
    #     "cliente_denominacion": client_passenger_obj.names,
    #     "cliente_direccion": client_first_address,
    #     "cliente_email": client_passenger_obj.email,
    #     "cliente_email_1": "",
    #     "cliente_email_2": "",
    #     "fecha_de_emision": formatdate,
    #     "fecha_de_vencimiento": "",
    #     "moneda": 1,
    #     "tipo_de_cambio": "",
    #     "porcentaje_de_igv": 18.00,
    #     "descuento_global": "",
    #     "total_descuento": "",
    #     "total_anticipo": "",
    #     "total_gravada": "",
    #     "total_inafecta": "",
    #     "total_exonerada": float(round(total, 2)),
    #     "total_igv": "",
    #     "total_gratuita": "",
    #     "total_otros_cargos": "",
    #     "total": float(round(total, 2)),
    #     "percepcion_tipo": "",
    #     "percepcion_base_imponible": "",
    #     "total_percepcion": "",
    #     "total_incluido_percepcion": "",
    #     "total_impuestos_bolsas": "",
    #     "detraccion": 'false',
    #     "observaciones": "",
    #     "documento_que_se_modifica_tipo": "",
    #     "documento_que_se_modifica_serie": "",
    #     "documento_que_se_modifica_numero": "",
    #     "tipo_de_nota_de_credito": "",
    #     "tipo_de_nota_de_debito": "",
    #     "enviar_automaticamente_a_la_sunat": 'true',
    #     "enviar_automaticamente_al_cliente": 'false',
    #     "codigo_unico": "",
    #     "condiciones_de_pago": "",
    #     "medio_de_pago": "",
    #     "placa_vehiculo": "",
    #     "orden_compra_servicio": "",
    #     "tabla_personalizada_codigo": "",
    #     "formato_de_pdf": "",
    #     "items": items,
    # }

    # print(graphql_query)

    token = tokens.get(order_obj.company.ruc, "ID no encontrado")

    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }

    try:
        response = requests.post(GRAPHQL_URL, json={"query": graphql_query}, headers=HEADERS)
        response.raise_for_status()

        result = response.json()

        success = result.get("data", {}).get("registerSale", {}).get("success")

        if success:
            return {
                "success": success,
                "message": result.get("data", {}).get("registerSale", {}).get("message"),
                "operationId": result.get("data", {}).get("registerSale", {}).get("operationId"),
                "serie": order_obj.serial,
                "numero": order_obj.correlative_sale,
                "tipo_de_comprobante": "2",
            }
        else:
            # Maneja el caso en que la operación no fue exitosa
            return {
                "success": False,
                "message": "La operación no fue exitosa",
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"error": "La respuesta no es un JSON válido"}


def annul_invoice(order_id):
    order_bill_obj = OrderBill.objects.get(order_id=int(order_id))
    correlative = order_bill_obj.n_receipt
    serial = order_bill_obj.serial

    variables = {
        "correlative": correlative,
        "serial": serial
    }

    mutation = """
    mutation AnnulInvoice($correlative: Int!, $serial: String!) {
        annulInvoice(correlative: $correlative, serial: $serial) {
            message
            success
        }
    }
    """

    token = tokens.get(order_bill_obj.order.company.ruc, "ID no encontrado")

    HEADERS = {
        "Content-Type": "application/json",
        "token": token
    }

    # print("Enviando mutación GraphQL:")
    # print("Query:", mutation)
    # print("Variables:", variables)
    # print("Headers:", HEADERS)

    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": mutation, "variables": variables},
            headers=HEADERS
        )
        response.raise_for_status()

        result = response.json()

        data = result.get("data", {}).get("annulInvoice")

        if data and data.get("success"):
            return {
                "success": True,
                "message": data.get("message"),
            }
        else:
            return {
                "success": False,
                "message": data.get("message") if data else "No se obtuvo respuesta del servidor.",
            }

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error en la solicitud: {str(e)}"}
    except ValueError:
        return {"success": False, "message": "La respuesta no es un JSON válido"}


def get_sale_by_id(pk):

    HEADERS = {
        "Content-Type": "application/json",
    }

    query = """
    query GetSale($pk: ID!) {
      getSaleById(pk: $pk) {
        linkXml
        linkCdr
      }
    }
    """

    variables = {"pk": str(pk)}

    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=HEADERS
        )

        # print("Response:", response.status_code)
        # print("Response Text:", response.text)

        response.raise_for_status()

        result = response.json()

        data = result.get("data", {}).get("getSaleById")

        if data:
            return {
                "success": True,
                "linkXml": data.get("linkXml"),
                "linkCdr": data.get("linkCdr"),
            }
        else:
            return {
                "success": False,
                "message": "No se encontró información para el ID proporcionado.",
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Error de red o servidor: {str(e)}"
        }