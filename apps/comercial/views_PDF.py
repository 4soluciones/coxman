import decimal
import time
# import pywintypes
import reportlab
# import cgi
# import tempfile
# import win32api
# import win32con
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A5, portrait, A6, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, Image
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.rl_settings import defaultPageSize
from coxman import settings
from apps.sales.format_to_dates import utc_to_local
from .models import Programming, ProgrammingSeat, Departure, DepartureDetail
from apps.sales.number_to_letters import numero_a_moneda
from apps.sales.models import Order, OrderAction, OrderBill, OrderProgramming, Manifest, OrderRoute
import io
from .views import calculate_age
import datetime
from datetime import datetime, timedelta
# import win32
# import win32api
# import os, sys
# import win32print
from ..hrm.models import SubsidiaryCompany, Subsidiary
from ..hrm.views import get_subsidiary_by_user, User

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='JustifySquare', alignment=TA_JUSTIFY, leading=12, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='LeftSquare', alignment=TA_LEFT, leading=12, fontName='Square', fontSize=13))
styles.add(ParagraphStyle(name='LeftSquareSmall', alignment=TA_LEFT, leading=9, fontName='Square', fontSize=10))
styles.add(ParagraphStyle(name='LeftSquareSmall2', alignment=TA_LEFT, leading=9, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Justify-Dotcirful', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
                          fontSize=10))
styles.add(
    ParagraphStyle(name='Justify-Dotcirful-table', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
                   fontSize=7))
styles.add(ParagraphStyle(name='Justify_Bold', alignment=TA_JUSTIFY, leading=8, fontName='Square-Bold', fontSize=8))
styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Center4', alignment=TA_CENTER, leading=10, fontName='Square-Bold',
                          fontSize=10, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center5', alignment=TA_LEFT, leading=15, fontName='ticketing.regular',
                          fontSize=12))
styles.add(
    ParagraphStyle(name='Center-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular', fontSize=10))
styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=8))
styles.add(ParagraphStyle(name='CenterTitle-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular',
                          fontSize=10))
styles.add(ParagraphStyle(name='CenterTitle2', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=12))
styles.add(ParagraphStyle(name='Center_Regular', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=10))
styles.add(ParagraphStyle(name='Center_Bold', alignment=TA_CENTER,
                          leading=8, fontName='Square-Bold', fontSize=12, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center_Bold_title', alignment=TA_CENTER,
                          leading=12, fontName='Square-Bold', fontSize=12, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='ticketing.regular', alignment=TA_CENTER,
                          leading=8, fontName='ticketing.regular', fontSize=14, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center2', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=8))
styles.add(ParagraphStyle(name='Center3', alignment=TA_JUSTIFY, leading=8, fontName='Ticketing', fontSize=6))

styles.add(ParagraphStyle(name='Square_left', alignment=TA_LEFT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Square_bold_left', alignment=TA_LEFT, leading=8, fontName='Square-Bold', fontSize=8))

style = styles["Normal"]

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/static/fonts')
pdfmetrics.registerFont(TTFont('Square', 'square-721-condensed-bt.ttf'))
pdfmetrics.registerFont(TTFont('Square-Bold', 'sqr721bc.ttf'))
pdfmetrics.registerFont(TTFont('Newgot', 'newgotbc.ttf'))
pdfmetrics.registerFont(TTFont('Ticketing', 'ticketing.regular.ttf'))
pdfmetrics.registerFont(TTFont('Lucida-Console', 'lucida-console.ttf'))
pdfmetrics.registerFont(TTFont('Square-Dot', 'square_dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Serif-Dot', 'serif_dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Enhanced-Dot-Digital', 'enhanced-dot-digital-7.regular.ttf'))
pdfmetrics.registerFont(TTFont('Merchant-Copy-Wide', 'MerchantCopyWide.ttf'))
pdfmetrics.registerFont(TTFont('Dot-Digital', 'dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Raleway-Dots-Regular', 'RalewayDotsRegular.ttf'))
pdfmetrics.registerFont(TTFont('Ordre-Depart', 'Ordre-de-Depart.ttf'))
pdfmetrics.registerFont(TTFont('Dotcirful-Regular', 'DotcirfulRegular.otf'))
pdfmetrics.registerFont(TTFont('Nationfd', 'Nationfd.ttf'))
pdfmetrics.registerFont(TTFont('Kg-Primary-Dots', 'KgPrimaryDots-Pl0E.ttf'))
pdfmetrics.registerFont(TTFont('Dot-line', 'Dotline-LA7g.ttf'))
pdfmetrics.registerFont(TTFont('Dot-line-Light', 'DotlineLight-XXeo.ttf'))
pdfmetrics.registerFont(TTFont('Jd-Lcd-Rounded', 'JdLcdRoundedRegular-vXwE.ttf'))
pdfmetrics.registerFont(TTFont('ticketing.regular', 'ticketing.regular.ttf'))
pdfmetrics.registerFont(TTFont('allerta_medium', 'allerta_medium.ttf'))
# pdfmetrics.registerFont(TTFont('Romanesque_Serif', 'Romanesque Serif.ttf'))

logo = "apps/sales/static/assets/logo_turnee.jpg"


def print_ticket_order_commodity(request, pk=None):  # Ticket/Guia de encomienda

    tbh_business_name_address = ''

    # _wt = 2.57 * inch - 5 * 0.05 * inch  #  TIKETERRA
    # _wt = 2.55 * inch - 4 * 0.05 * inch  # ticket normal
    _wt = 2.83 * inch - 4 * 0.05 * inch  # termical
    # _wt = 3.11 * inch

    order_obj = Order.objects.get(pk=pk)
    order_action_sender_obj = OrderAction.objects.get(order=order_obj, type='R')

    subsidiary_aqp = Subsidiary.objects.filter(name='SEDE AREQUIPA').first()
    phone_aqp = subsidiary_aqp.phone

    # subsidiary_pedregal = Subsidiary.objects.filter(name='SEDE PEDREGAL AV AREQUIPA').first()
    # phone_pedregal = subsidiary_pedregal.phone

    subsidiary_camana = Subsidiary.objects.filter(name='SEDE CAMANA').first()
    phone_camana = subsidiary_camana.phone

    if order_obj.company.id == 1:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '
    elif order_obj.company.id == 2:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '
    elif order_obj.company.id == 3:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '

    line = '-----------------------------------------------------'
    name_document = 'GUÍA DE ENCOMIENDA'
    data_title = 'DATOS DE ENVÍO'
    serie = 'SERIE: ' + order_obj.serial
    # colwiths_table = [2.57 / 2.2 * inch, 2.57 / 2.2 * inch]
    colwiths_table = [_wt * 50 / 100, _wt * 50 / 100]
    correlative = order_obj.correlative_sale

    # I = Image(logo)
    # I.drawHeight = 1.95 * inch / 2.9
    # I.drawWidth = 7.4 * inch / 2.9
    date = order_obj.create_at.date()
    _date_convert_zone = utc_to_local(order_obj.create_at)
    date_hour = _date_convert_zone.time()
    _formatdate = _date_convert_zone.strftime("%d/%m/%Y")
    _formattime = date_hour.strftime("%I:%M:%S %p")

    td_date = ('FECHA EMISIÓN: ' + str(_formatdate), 'HORA: ' + str(_formattime))
    td_user = ('ATENDIDO POR: ' + order_obj.user.username.upper(), order_obj.subsidiary.name)
    ana_c1 = Table([td_date] + [td_user], colWidths=colwiths_table)
    my_style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        # ('FONTNAME', (0, 1), (0, -1), 'Newgot'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        ('ALIGNMENT', (1, 1), (1, 1), 'RIGHT'),
        ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        # ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]

    my_style_table_recipients = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('FONTNAME', (1, 3), (1, 3), 'allerta_medium'),
        # ('FONTNAME', (1, -2), (-2, -1), 'allerta_medium'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (1, 1), (1, 1), 10),
        ('FONTNAME', (1, 1), (1, 1), 'Square-Bold'),
        # ('ALIGNMENT', (1, 0), (1, -1), 'CENTER'),
        # ('ALIGNMENT', (0, 1), (0, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('LEFTPADDING', (1, 0), (1, -1), 0.3),  # second column
        # ('LEFTPADDING', (2, 0), (2, -1), 1.3),  # third column
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # ('BACKGROUND', (1, 1), (1, 1), colors.lightgrey),
        # ('FONTSIZE', (1, 2), (1, 2), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -4),
    ]
    my_style_table2 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        ('FONTNAME', (1, 3), (1, 3), 'allerta_medium'),
        ('FONTNAME', (1, 2), (1, 2), 'allerta_medium'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),
        # ('BACKGROUND', (1, 2), (1, 2), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    my_style_code = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square-Bold'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        # ('BACKGROUND', (1, 2), (1, 2), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    my_style_table3 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGNMENT', (2, 0), (2, -1), 'CENTER'),  # third column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        ('TOPPADDING', (0, 0), (-1, -1), -1),
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.5),  # four column
    ]
    my_style_table4 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        # ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('ALIGNMENT', (1, 0), (1, -1), 'CENTER'),  # second column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGNMENT', (2, 0), (2, -1), 'CENTER'),  # third column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.5),  # four column
    ]
    my_style_table5 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (3, 2), (3, -1), 10),
        ('FONTNAME', (3, 2), (3, -1), 'Square-Bold'),
        ('RIGHTPADDING', (2, 0), (2, -1), 0),  # third column
        ('ALIGNMENT', (2, 0), (2, -1), 'RIGHT'),  # third column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.3),  # four column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        # ('BACKGROUND', (3, 2), (3, -1), colors.lightgrey),
    ]

    ana_c1.setStyle(TableStyle(my_style_table))

    document_sender = str(order_action_sender_obj.client.clienttype_set.first().document_type.short_description)

    td_client = ('NOMBRES: ' + str(order_action_sender_obj.client.names), '')
    td_client_nro_documento = (
        document_sender + ': ' + str(order_action_sender_obj.client.clienttype_set.first().document_number), '')
    ana_c2 = Table([td_client] + [td_client_nro_documento], colWidths=colwiths_table)
    ana_c2.setStyle(TableStyle(my_style_table))

    td_code = ('CÓDIGO DE RECOJO: ' + str(order_obj.code), '')

    ana_code = Table([td_code], colWidths=colwiths_table)
    ana_code.setStyle(TableStyle(my_style_code))

    td_sender = ('REMITENTE: ' + str(order_action_sender_obj.client.names), '')

    if order_action_sender_obj.client.phone:
        td_sender_document = (
            document_sender + ': ' + str(order_action_sender_obj.client.clienttype_set.first().document_number),
            'TELEFONO: ' + str(order_action_sender_obj.client.phone))
        ana_c3 = Table([td_sender] + [td_sender_document], colWidths=colwiths_table)
        ana_c3.setStyle(TableStyle(my_style_table))
    else:
        td_sender_document = (
            document_sender + ': ' + str(order_action_sender_obj.client.clienttype_set.first().document_number), '')
        ana_c3 = Table([td_sender] + [td_sender_document], colWidths=colwiths_table)
        ana_c3.setStyle(TableStyle(my_style_table))

    recipients = OrderAction.objects.filter(order=order_obj, type='D')
    _rows = []
    for d in recipients:
        _phone = ''
        if d.client is None:
            _names = Paragraph(d.order_addressee.names.upper(), styles["Center5"])
            _phone = d.order_addressee.phone
            _rows.append(['NOMBRES :', _names, ''])
            _rows.append(['CEL : ' + _phone, '', ''])
        else:
            if d.client.phone is not None:
                _phone = d.client.phone
            _names = Paragraph(d.client.names.upper(), styles["Center5"])
            _rows.append([str(d.client.clienttype_set.first().document_type.short_description) + ':' + str(
                d.client.clienttype_set.first().document_number), '       CEL :' + _phone, ''])
            _rows.append(['NOMBRES :', _names, ''])

    colwiths_table_recipients = [_wt * 22 / 100, _wt * 73 / 100, _wt * 5 / 100]

    ana_c4 = Table([('DESTINATARIO(S):', '', '')] + _rows, colWidths=colwiths_table_recipients)

    ana_c4.setStyle(TableStyle(my_style_table_recipients))

    address_delivery = '-'

    if order_obj.address_delivery:
        address_delivery = Paragraph(str(order_obj.address_delivery.upper()), styles["Justify"])

    td_type = ('TIPO', ': ENCOMIENDA')
    td_origin = ('ORIGEN', ': ' + str(order_obj.orderroute_set.filter(type='O').first().subsidiary))
    td_destiny = ('DESTINO', ': ' + str(order_obj.orderroute_set.filter(type='D').first().subsidiary))
    td_way_to_pay = ('COND. PAGO', ': ' + str(order_obj.get_way_to_pay_display()))
    td_service = ('SERVICIO', ': ' + str(order_obj.get_type_guide_display()))
    td_address_delivery = ('DIRECCIÓN REPARTO ' + ' :', address_delivery)
    # ana_c5 = Table([td_type] + [td_origin] + [td_destiny] + [td_way_to_pay] + [td_service],
    #                colWidths=[_wt * 25 / 100, _wt * 75 / 100])
    # ana_c5.setStyle(TableStyle(my_style_table2))

    if order_obj.address_delivery:
        ana_c5 = Table(
            [td_type] + [td_origin] + [td_destiny] + [td_way_to_pay] + [td_service] + [td_address_delivery],
            colWidths=[_wt * 33 / 100, _wt * 67 / 100])

    else:
        ana_c5 = Table([td_type] + [td_origin] + [td_destiny] + [td_way_to_pay] + [td_service],
                       colWidths=[_wt * 33 / 100, _wt * 67 / 100])
    ana_c5.setStyle(TableStyle(my_style_table2))

    td_description = ('DESCRIPCIÓN', 'U.M.', 'CANT.', 'TOTAL')
    ana_c6 = Table([td_description], colWidths=[_wt * 60 / 100, _wt * 15 / 100, _wt * 10 / 100, _wt * 15 / 100])
    ana_c6.setStyle(TableStyle(my_style_table3))

    sub_total = 0
    total = 0
    igv_total = 0
    _rows = []
    _counter = order_obj.orderdetail_set.count()
    for d in order_obj.orderdetail_set.all():
        P0 = Paragraph(d.description.upper(), styles["Justify"])
        _rows.append((P0, d.unit.description, str(decimal.Decimal(round(d.quantity))), str(d.amount)))
        base_total = d.quantity * d.price_unit
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        sub_total = sub_total + base_amount
        total = total + base_total
        igv_total = igv_total + igv

    ana_c7 = Table(_rows, colWidths=[_wt * 60 / 100, _wt * 15 / 100, _wt * 10 / 100, _wt * 15 / 100],
                   rowHeights=0.15 * inch)

    ana_c7.setStyle(TableStyle(my_style_table4))

    td_gravada = ('OP.  GRAVADA', '', 'S/', str(decimal.Decimal(round(total, 2))))
    td_inafecta = ('OP.  INAFECTA', '', 'S/', '0.00')
    td_exonerada = ('OP.  EXONERADA', '', 'S/', '0.00')
    td_descuento = ('DESCUENTO', '', 'S/', '0.00')
    td_igv = ('I.G.V.  (18.00)', '', 'S/', '0.00')
    td_importe_total = ('IMPORTE TOTAL', '', 'S/', str(decimal.Decimal(round(total, 2))))

    ana_c8 = Table([td_gravada] + [td_descuento] + [td_importe_total],
                   colWidths=[_wt * 60 / 100, _wt * 10 / 100, _wt * 17 / 100, _wt * 13 / 100])
    ana_c8.setStyle(TableStyle(my_style_table5))

    footer = 'SON: ' + numero_a_moneda(total)
    footer2 = 'ACEPTO LOS TÉRMINOS Y CONDICIONES DEL CONTRATO DE TRANSPORTE PUBLICADOS EN LA EMPRESA'

    buff = io.BytesIO()

    ml = 0.0 * inch
    mr = 0.0 * inch
    ms = 0.0 * inch
    mi = 0.039 * inch
    # pz_termical = (2.55 * inch, 11.6 * inch) # ticket normal
    pz_termical = (2.83 * inch, 11.6 * inch)

    doc = SimpleDocTemplate(buff,
                            pagesize=pz_termical,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='GUIA ENCOMIENDA'
                            )
    dictionary = []
    # dictionary.append(I)
    dictionary.append(Spacer(-4, -4))
    dictionary.append(Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Center_Bold_title"]))
    dictionary.append(Spacer(1, -2))
    dictionary.append(Paragraph("SEDE AREQUIPA: " + str(phone_aqp), styles["Center"]))
    # dictionary.append(Paragraph("SEDE PEDREGAL AV. AREQUIPA: " + str(phone_pedregal), styles["Center"]))
    dictionary.append(Paragraph("SEDE CAMANA: " + str(phone_camana), styles["Center"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Paragraph(name_document, styles["Center2"]))
    dictionary.append(Spacer(-4, -4))
    dictionary.append(Paragraph(serie + ' - ' + correlative, styles["ticketing.regular"]))
    dictionary.append(Spacer(-1, -1))
    dictionary.append(ana_c1)
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(data_title, styles["Center"]))
    dictionary.append(Spacer(-2, -2))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(-2, -2))
    dictionary.append(ana_c3)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(4, 4))
    dictionary.append(ana_c4)
    dictionary.append(Spacer(4, 4))
    dictionary.append(ana_code)
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(-2, -2))
    dictionary.append(ana_c5)
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 0))
    dictionary.append(ana_c6)
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(-2, -2))
    dictionary.append(ana_c7)
    dictionary.append(Spacer(-2, -2))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 0))
    dictionary.append(ana_c8)
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 0))
    dictionary.append(Paragraph(footer, styles["Center"]))
    dictionary.append(Spacer(1, 0))
    '''dictionary.append(Paragraph(
        "CONDICIONES PARA EL SERVICIO DE ENCOMIENDAS: "
        "1.	LA EMPRESA NO TRANSPORTA DINERO, VALORES Y JOYAS, ANIMALES VIVOS, SUSTANCIAS Y/O MATERIALES RESTRINGIDOS O PROHIBIDOS POR SENASA, DIGESA, SUNAT, EL CLIENTE ASUMIRÁ LA TOTAL RESPONSABILIDAD POR DAÑOS Y PERJUICIOS QUE SE OCASIONAN AL ESTADO, TERCEROS Y A LA EMPRESA. "
        "2.	EN CASO DE PERDIDA, EXTRAVIO O SUSTRACCION, DETERIORO O DESTRUCCION ENTREGA ERRONEA DE UNA ENCOMIENDA A EXCEPCIÓN DEL PREVISTO EN EL NUMERAL ANTLRIOR, LA EMPRESA INDEMNIZARA AL CLIENTE DE ACUERDO A LA RESOLUCIÓN DIRECTORAL Nº OO1-2006-MTC/19. "
        "3. EL PLAZO DE ENTREGA DE ENCOMIENDAS DE DESTINOS (AGENCIAS DE LA EMPRESA ES DE 72 HORAS MAXIMO. "
        "4. Si LA ENCOMIENDA NO ES RECLAMADA EN 30 DIAS. LA EMPRESA APLICARA LO ESTABLECIDO EN LA R.M. Nº 572-2008. MTC.",
        styles["Center3"]))'''
    # dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(
        "¡Gracias por confiar en nosotros!",
        styles["Center2"]))

    doc.build(dictionary)

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="WARE[{}].pdf"'.format(
        order_obj.serial + '-' + order_obj.correlative_sale)

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie('ware', value=pk, expires=expires)

    # doc.build(elements)
    # doc.build(Story)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_ticket_order_passenger(request, pk=None):  # Boleto de viaje boleta / factura
    # _wt = 3.14 * inch - 8 * 0.05 * inch # termical
    _wt = 2.83 * inch - 4 * 0.05 * inch  # termical

    tbh_business_name_address = ''
    # _wt = 2.57 * inch - 5 * 0.05 * inch # matricial

    order_obj = Order.objects.get(pk=pk)
    order_bill_obj = order_obj.orderbill
    passenger_name = ""
    passenger_document = ""
    client_document = ""
    client_name = ""
    client_address = ""

    if order_obj.company.id == 1:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '
    elif order_obj.company.id == 2:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '
    elif order_obj.company.id == 3:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083 '

    # tbh_business_name_address = 'TURISMO MENDIVIL S.R.L\n CALLE JAVIER P. DE CUELLAR B-3 INT 105\n TERM. TERRESTRE S/N INT. E1-E / \nURB. ARTURO IBAÑEZ HUNTER AREQUIPA\n RUC: 20442736759'

    date = order_obj.programming_seat.programming.departure_date
    _format_time = utc_to_local(order_obj.create_at).strftime("%H:%M %p")
    _format_date = date.strftime("%d/%m/%Y")

    if order_bill_obj.type == '1':
        tbn_document = 'FACTURA ELECTRÓNICA'
        passenger_set = order_obj.client
        company_set = order_obj.orderaction_set.filter(type='E')
        if passenger_set:
            passenger_name = passenger_set.names
            passenger_document = passenger_set.clienttype_set.first().document_number
        if company_set:
            client_document = company_set.first().client.clienttype_set.first().document_number
            client_name = company_set.first().client.names
            client_address = company_set.first().client.clientaddress_set.first().address
    elif order_bill_obj.type == '2':
        tbn_document = 'BOLETA DE VENTA ELECTRÓNICA'
        passenger_name = order_obj.client.names
        passenger_document = order_obj.client.clienttype_set.first().document_number
        client_name = passenger_name
        client_document = passenger_document
    line = '-----------------------------------------------------'

    I = Image(logo)
    I.drawHeight = 1.95 * inch / 2.9
    I.drawWidth = 7.4 * inch / 2.9

    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        # ('BACKGROUND', (2, 3), (2, 4), colors.blue),
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
    ]
    colwiths_table = [_wt * 30 / 100, _wt * 70 / 100]

    if order_bill_obj.type == '2':
        p0 = Paragraph(client_name, styles["Right"])
        ana_c1 = Table(
            [('CLIENTE: N DOC ', client_document)] +
            [('SR(A): ', p0)] +
            [('ATENDIDO POR: ', order_obj.user.username.upper() + " " + order_obj.subsidiary.name)],
            colWidths=colwiths_table)
    elif order_bill_obj.type == '1':
        p0 = Paragraph(client_name, styles["Justify"])
        p1 = Paragraph(client_address, styles["Justify"])
        ana_c1 = Table(
            [('RUC ', client_document)] +
            [('RAZÓN SOCIAL: ', p0)] +
            [('DIRECCIÓN: ', p1)] +
            [('ATENDIDO POR: ', order_obj.user.username.upper() + " " + order_obj.subsidiary.name)],
            colWidths=colwiths_table)

    ana_c1.setStyle(TableStyle(style_table))

    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('FONTNAME', (0, 0), (0, -1), 'Ticketing'),  # first column
        ('LEFTPADDING', (2, 0), (2, -1), 2),  # third column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # fourth column
        ('FONTSIZE', (3, 0), (3, -1), 10),  # fourth column
        ('FONTNAME', (3, 0), (3, -1), 'Ticketing'),  # fifth row [col 1:2]
        # ('BACKGROUND', (0, 2), (1, 2), colors.pink),

        ('FONTSIZE', (2, 3), (2, 4), 10),  # third column

        ('ALIGNMENT', (1, 2), (1, 4), 'LEFT'),  # second column [row 3:5]
        ('FONTNAME', (2, 3), (2, 4), 'Ticketing'),  # third column [row 4:5]
        # ('BACKGROUND', (2, 3), (2, 4), colors.blue),

        ('LEFTPADDING', (2, 3), (2, 4), 9),

        ('RIGHTPADDING', (3, 3), (3, 4), 0.5),  # fourth column [row 4:5]
        ('FONTNAME', (0, 2), (1, 2), 'Square-Bold'),  # fifth row [col 1:2]
        ('FONTSIZE', (0, 2), (1, 2), 12),  # fifth row [col 1:2]
        ('LEFTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('SPAN', (1, 0), (3, 0)),  # first row
        # ('SPAN', (0, 1), (1, 1)),  # second row
        # ('SPAN', (2, 1), (3, 1)),  # second row
        # ('GRID', (2, 1), (3, 1), 0.5, colors.black)
    ]
    p10 = Paragraph('SR(A): ' + passenger_document + ' - ' + passenger_name, styles["Justify"])
    colwiths_table = [_wt * 25 / 100, _wt * 25 / 100, _wt * 25 / 100, _wt * 25 / 100]
    if order_obj.show_original_name:
        subsidiary_company_obj = SubsidiaryCompany.objects.filter(subsidiary=order_obj.subsidiary,
                                                                  company=order_obj.company).last()
        if subsidiary_company_obj.original_name is not None:
            _short_name_origin = subsidiary_company_obj.original_name
        else:
            _short_name_origin = subsidiary_company_obj.subsidiary.short_name

    else:
        _short_name_origin = order_obj.subsidiary.short_name
    ana_c2 = Table(
        [('PASAJERO:', p10, '', '')] +
        [('DEST:', order_obj.destiny.name, 'FECHA:', str(_format_date))] +
        # [('AGENCIA DE EMBARQUE:', '', order_obj.subsidiary.name, '')] +
        # [('ORIG:', _short_name_origin, '', '')] +

        [('ASIENTO:', order_obj.programming_seat.plan_detail.name, 'HORA:', str(_format_time))],
        # [('ATENDIDO POR: ', '', order_obj.user.username.upper() + " " + order_obj.subsidiary.name)],
        colWidths=colwiths_table)
    ana_c2.setStyle(TableStyle(style_table))

    my_style_table3 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),  # all columns
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    colwiths_table = [_wt * 80 / 100, _wt * 20 / 100]
    ana_c6 = Table([('DESCRIPCIÓN', 'TOTAL')], colWidths=colwiths_table)
    ana_c6.setStyle(TableStyle(my_style_table3))

    sub_total = 0
    total = 0
    igv_total = 0

    # Validar si el origen es distinto a la sede
    if order_obj.origin and order_obj.origin.name != order_obj.subsidiary.name:
        origin_name = order_obj.origin.name
    else:
        origin_name = order_obj.subsidiary.short_name
    
    route = f"SERVICIO DE TRANSPORTE<br/>ORIGEN: {origin_name}<br/>DESTINO: {order_obj.destiny.name}<br/>ASIENTO: {order_obj.programming_seat.plan_detail.name}"
    # P0 = Paragraph(
    #     'SERVICIO DE TRANSPORTE RUTA ' + order_obj.programming_seat.programming.get_origin().short_name + ' - ' + order_obj.destiny.name + '<br/> ASIENTO ' + order_obj.programming_seat.plan_detail.name + '.',
    #     styles["Justify"])
    P0 = Paragraph(route, styles["Justify"])
    P_TRUCK = Paragraph('PLACA: ' + order_obj.programming_seat.programming.truck.license_plate, styles["Justify_Bold"])

    base_total = 1 * 45
    base_amount = base_total / 1.1800
    igv = base_total - base_amount
    sub_total = sub_total + base_amount
    total = total + base_total
    igv_total = igv_total + igv
    ana_truck = Table([(P_TRUCK, '')], colWidths=[_wt * 80 / 100, _wt * 20 / 100])

    my_style_truck = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        # ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    my_style_table4 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    ana_c7 = Table([(P0, 'S/ ' + str(decimal.Decimal(round(order_obj.total, 2))))],
                   colWidths=[_wt * 80 / 100, _wt * 20 / 100])
    ana_c7.setStyle(TableStyle(my_style_table4))
    ana_truck.setStyle(TableStyle(my_style_truck))

    my_style_table5 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns

        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),  # all columns
        ('RIGHTPADDING', (2, 0), (2, -1), 0),  # third column
        ('ALIGNMENT', (2, 0), (2, -1), 'RIGHT'),  # third column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.3),  # four column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('FONTNAME', (0, 2), (-1, 2), 'Square-Bold'),  # third row
        ('FONTSIZE', (0, 2), (-1, 2), 10),  # third row
    ]

    ana_c8 = Table(
        [('OP. NO GRAVADA', '', 'S/', str(decimal.Decimal(round(order_obj.total, 2))))] +
        [('I.G.V.  (18.00)', '', 'S/', '0.00')] +
        [('TOTAL', '', 'S/', str(decimal.Decimal(round(order_obj.total, 2))))],
        colWidths=[_wt * 60 / 100, _wt * 10 / 100, _wt * 10 / 100, _wt * 20 / 100]
    )
    ana_c8.setStyle(TableStyle(my_style_table5))
    footer = 'SON: ' + numero_a_moneda(order_obj.total)

    my_style_table6 = [
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.blue),   # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('ALIGNMENT', (0, 0), (0, -1), 'CENTER'),  # first column
        ('SPAN', (0, 0), (1, 0)),  # first row
    ]

    # datatable = order_bill_obj.code_qr
    datatable = 'https://4soluciones.pse.pe/20455935173'
    ana_c9 = Table([(qr_code(datatable), '')], colWidths=[_wt * 99 / 100, _wt * 1 / 100])
    ana_c9.setStyle(TableStyle(my_style_table6))

    _dictionary = []
    # _dictionary.append(I)
    _dictionary.append(Spacer(1, 5))
    _dictionary.append(Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Center4"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Paragraph(tbn_document, styles["Center_Regular"]))
    _dictionary.append(
        Paragraph(order_bill_obj.serial + ' - ' + str(order_bill_obj.n_receipt).zfill(6), styles["Center_Bold"]))
    _dictionary.append(Spacer(-2, -2))
    _dictionary.append(ana_c1)
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-2, -2))
    _dictionary.append(Spacer(1, 2))
    _dictionary.append(Paragraph('DATOS DE VIAJE ', styles["Center_Regular"]))
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(ana_c2)
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-1, -1))
    _dictionary.append(ana_c6)
    _dictionary.append(Spacer(-1, -1))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(ana_c7)
    # _dictionary.append(ana_truck)
    _dictionary.append(Spacer(-3, -3))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(ana_c8)
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Paragraph(footer, styles["Center"]))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(1, 2))
    _dictionary.append(Paragraph(
        "Representación impresa de la " + str(
            tbn_document) + ", para ver el documento visita ", styles["Square_left"]))
    _dictionary.append(Paragraph("https://tuf4ct.com/cpe ", styles["Square_bold_left"]))
    _dictionary.append(Paragraph("Emitido mediante un PROVEEDOR Autorizado por la SUNAT", styles["Square_left"]), )
    # _dictionary.append(Paragraph("mediante Resolución de Intendencia No. 034-005- 0005315", styles["Square_left"]))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(
        Paragraph("***CONSERVAR SU COMPROBANTE ANTE CUALQUIER EVENTUALIDAD***".replace('***', '"'), styles["Center2"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(ana_c9)
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph("DE LAS CONDICIONES PARA EL SERVICIO DE TRANSPORTE: "
                                 "1. EL BOLETO DE VIAJE ES PERSONAL, TRANSFERIBLE Y/O PO5TERGABLE. "
                                 "2. EL PASAJERO SE PRESENTARÁ 30 MIN ANTES DE LA HORA DE VIAJE, DEBIENDO PRESENTAR SU BOLETO DE VIAJE Y DNI. "
                                 "3. LOS MENORES DE EDAD VIAJAN CON SUS PADRES O EN SU DEFECTO DEBEN PRESENTAR PERMISO NOTARIAL DE SUS PADRES, MAYORES DE 5 AÑOS PAGAN SU PASAJE. "
                                 "4. EN CASO DE ACCIDENTES EL PASAJERO VIAJA  ASEGURADO CON SOAT DE LA COMPAÑIA DE SEGUROS. "
                                 "5. EL PASAJERO TIENE DERECHO A TRANSPORTAR 20 KILOS DE EQUIPAJE, SOLO ARTICULOS DE USO PERSONAL (NO CARGA).  EL EXCESO SERÁ ADMITIDO CUANDO LA CAPACIDAD DEL BUS LO PERMITA, PREVIO PAGO DE LA TARIFA. "
                                 "6. LA EMPRESA NO SE RESPONSABILIZA POR FALLAS AJENAS AL MISMO SERVICIO DE TRANSPORTE (WIFI, TOMACORRIENTES, PANTALLAS, AUDIO Y OTRAS SIMILARES) PUES ESTOS SERVICIOS SON OFRECIDOS EN CALIDAD DE CORTESIA. "
                                 "7. LAS DEVOLUCIONES DE BOLETOS PAGADOS CON VISA SE EFECTUARÁ SEGÚN LOS PLAZOS, PROCEDIMIENTOS Y CANALES ESTABLECIDOS POR VISA, EN NINGUN CASO SE EFECTUARÁ DEVOLUCIÓN EN EFECTIVO.",
                                 styles["Center3"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-2, -2))
    _dictionary.append(Paragraph(
        "¡Gracias por viajar con nosotros!",
        styles["Center2"]))
    buff = io.BytesIO()

    ml = 0.0 * inch
    mr = 0.0 * inch
    ms = 0.039 * inch
    mi = 0.039 * inch

    pz_matricial = (2.57 * inch, 11.6 * inch)
    # pz_termical = (3.14961 * inch, 11.6 * inch)
    pz_termical = (2.83 * inch, 11.6 * inch)

    doc = SimpleDocTemplate(buff,
                            pagesize=pz_termical,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='TICKET'
                            )
    doc.build(_dictionary)
    # doc.build(elements)
    # doc.build(Story)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="CE[{}].pdf"'.format(
        order_obj.serial + '-' + order_obj.correlative_sale)

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie('bp', value=pk, expires=expires)

    response.write(buff.getvalue())

    buff.close()
    return response


def qr_code(table):
    # generate and rescale QR
    qr_code = qr.QrCodeWidget(table)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        3.5 * cm, 3.5 * cm, transform=[3.5 * cm / width, 0, 0, 3.5 * cm / height, 0, 0])
    drawing.add(qr_code)

    return drawing


def print_bill_order_commodity(request, pk=None):  # Boleta / Factura Encomienda
    _wt = 3.14 * inch - 8 * 0.05 * inch

    order_obj = Order.objects.get(pk=pk)
    order_bill_obj = order_obj.orderbill
    client_document = ""
    client_name = ""
    client_address = ""

    order_action_sender_obj = OrderAction.objects.get(order=order_obj, type='R')
    # order_action_addressee_obj = OrderAction.objects.get(order=order_obj, type='D')
    recipients = OrderAction.objects.filter(order=order_obj, type='D')

    tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083'

    subsidiary_aqp = Subsidiary.objects.filter(name='SEDE AREQUIPA').first()
    phone_aqp = subsidiary_aqp.phone

    # subsidiary_pedregal = Subsidiary.objects.filter(name='SEDE PEDREGAL AV AREQUIPA').first()
    # phone_pedregal = subsidiary_pedregal.phone

    subsidiary_camana = Subsidiary.objects.filter(name='SEDE CAMANA').first()
    phone_camana = subsidiary_camana.phone

    if order_bill_obj.type == '1':
        tbn_document = 'FACTURA ELECTRÓNICA'
        client_set = order_obj.client
        company_set = order_obj.orderaction_set.filter(type='R')
        if company_set:
            client_document = company_set.first().client.clienttype_set.first().document_number
            client_name = company_set.first().client.names
            client_address = company_set.first().client.clientaddress_set.first().address
    elif order_bill_obj.type == '2':
        tbn_document = 'BOLETA DE VENTA ELECTRÓNICA'
        passenger_name = order_action_sender_obj.client.names
        passenger_document = order_action_sender_obj.client.clienttype_set.first().document_number
        client_name = passenger_name
        client_document = passenger_document

    line = '-------------------------------------------------------'
    name_document = tbn_document
    data_title = 'DATOS DE ENVIO'
    serie = 'SERIE: ' + order_obj.serial
    colwiths_table = [3.2 / 2.2 * inch, 3.2 / 2.2 * inch]
    correlative = order_obj.correlative_sale

    I = Image(logo)
    I.drawHeight = 1.95 * inch / 2.9
    I.drawWidth = 7.4 * inch / 2.9
    # date = order_obj.create_at.date()
    # date_hour = order_obj.create_at.time()
    # _formatdate = date.strftime("%d/%m/%Y")
    # _formattime = date_hour.strftime("%I:%M:%S %p")
    date = order_obj.create_at.date()
    _date_convert_zone = utc_to_local(order_obj.create_at)
    date_hour = _date_convert_zone.time()
    _formatdate = date.strftime("%d/%m/%Y")
    _formattime = date_hour.strftime("%I:%M:%S %p")

    td_date = ('FECHA DE EMISIÓN: ' + str(_formatdate), 'HORA EMISIÓN: ' + str(_formattime))
    td_user = (
        'ATENDIDO POR: ' + order_obj.user.username.upper(), order_obj.subsidiary.name)
    ana_c1 = Table([td_date] + [td_user], colWidths=colwiths_table)
    my_style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        # ('FONTNAME', (0, 1), (0, -1), 'Newgot'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),
        ('ALIGNMENT', (1, 1), (1, 1), 'RIGHT'),
        ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        # ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]
    my_style_table_recipients = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        # ('FONTNAME', (0, 1), (0, -1), 'Newgot'),
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        # ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),
        ('ALIGNMENT', (1, 1), (1, 1), 'RIGHT'),
        ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        # ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (1, 1), (1, 1), 'Square-Bold'),
        # ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
        # ('BACKGROUND', (1, 1), (1, 1), colors.lightgrey)
    ]
    my_style_table2_1 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        # ('FONTNAME', (0, 1), (0, -1), 'Newgot'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('LEFTPADDING', (1, 0), (1, -1), 0.3),  # second column
        ('VALIGN', (1, 0), (1, -1), 'TOP'),  # second column
        # ('ALIGNMENT', (0, 1), (1, -1), 'LEFT'),
        # ('ALIGNMENT', (1, 0), (1, 0), 'LEFT'),
        # ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (0, -1), 'TOP'),
        # ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]
    my_style_table2_2 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (0, -1), 0.3),  # first column
        ('LEFTPADDING', (1, 0), (1, -1), 0.3),  # second column
        ('RIGHTPADDING', (1, 1), (1, 1), 0.3),  # second column
        ('VALIGN', (1, 0), (1, -1), 'TOP'),  # second column
        ('ALIGNMENT', (1, 1), (1, 1), 'RIGHT'),  # second column second row
        ('VALIGN', (0, 0), (0, -1), 'TOP'),
    ]
    my_style_table2 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        ('FONTNAME', (1, 3), (1, 3), 'Square-Bold'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('VALIGN', (0, 5), (1, 5), 'BOTTOM'),
        # ('BACKGROUND', (0, 5), (1, 5), colors.lightgrey),
        ('FONTNAME', (0, 5), (1, 5), 'Square-Bold'),
        ('FONTSIZE', (0, 5), (1, 5), 10),
    ]
    my_style_table3 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGNMENT', (2, 0), (2, -1), 'CENTER'),  # third column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        ('TOPPADDING', (0, 0), (-1, -1), -1),
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.5),  # four column
    ]
    my_style_table4 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('ALIGNMENT', (1, 0), (1, -1), 'CENTER'),  # second column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGNMENT', (2, 0), (2, -1), 'CENTER'),  # third column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.5),  # four column
    ]
    my_style_table5 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (2, 0), (2, -1), 0),  # third column
        ('ALIGNMENT', (2, 0), (2, -1), 'RIGHT'),  # third column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.3),  # four column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        ('FONTNAME', (0, 5), (3, 5), 'Square-Bold'),
        ('FONTSIZE', (0, 5), (3, 5), 9),
        # ('BACKGROUND', (0, 5), (3, 5), colors.lightgrey),
    ]
    my_style_table6 = [
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.blue),   # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('ALIGNMENT', (0, 0), (0, -1), 'CENTER'),  # first column
        ('SPAN', (0, 0), (1, 0)),  # first row
    ]
    ana_c1.setStyle(TableStyle(my_style_table))

    client_document_type = str(order_action_sender_obj.client.clienttype_set.first().document_type.short_description)

    if order_bill_obj.type == '1':

        p1cn = Paragraph(order_action_sender_obj.client.names, styles["Justify"])
        td_client2 = ('CLIENTE: ', p1cn)
        # td_client = ('CLIENTE: ', str(order_action_sender_obj.client.names))
        td_client_nro_documento = (
            client_document_type + ': ', str(order_action_sender_obj.client.clienttype_set.first().document_number))
        p1c = Paragraph(client_address, styles["Justify"])
        ana_c2 = Table([td_client2] + [td_client_nro_documento], colWidths=[_wt * 20 / 100, _wt * 80 / 100])
        ana_c2.setStyle(TableStyle(my_style_table2_1))
        ana_c2_1 = Table([('DIRECCION :', p1c)], colWidths=[_wt * 20 / 100, _wt * 80 / 100])
        ana_c2_1.setStyle(TableStyle(my_style_table2_1))

    elif order_bill_obj.type == '2':

        p1cn = Paragraph(order_action_sender_obj.client.names, styles["Justify"])
        td_client2 = ('CLIENTE: ', p1cn)
        # td_client = ('CLIENTE: ', str(order_action_sender_obj.client.names))
        td_client_nro_documento = (
            client_document_type + ': ', str(order_action_sender_obj.client.clienttype_set.first().document_number))
        p1c = Paragraph(client_address, styles["Justify"])
        ana_c2 = Table([td_client2] + [td_client_nro_documento], colWidths=[_wt * 20 / 100, _wt * 80 / 100])
        ana_c2.setStyle(TableStyle(my_style_table2_1))
        ana_c2_1 = Table([('DIRECCION :', p1c)], colWidths=[_wt * 20 / 100, _wt * 80 / 100])
        ana_c2_1.setStyle(TableStyle(my_style_table2_1))

    if order_action_sender_obj.client.phone:
        p1r = Paragraph(str(order_action_sender_obj.client.names), styles["Justify"])
        # td_sender = ('REMITENTE: ' + str(order_action_sender_obj.client.names), '')
        td_sender = ('REMITENTE: ', p1r)
        td_sender_document = (
            client_document_type + ': ' + str(order_action_sender_obj.client.clienttype_set.first().document_number),
            'TELEFONO: ' + str(order_action_sender_obj.client.phone))
        ana_c3 = Table([td_sender] + [td_sender_document], colWidths=[_wt * 19 / 100, _wt * 81 / 100])
        ana_c3.setStyle(TableStyle(my_style_table2_2))

    else:
        p1r = Paragraph(str(order_action_sender_obj.client.names), styles["Justify"])
        # td_sender = ('REMITENTE: ' + str(order_action_sender_obj.client.names), '')
        td_sender = ('REMITENTE: ', p1r)
        td_sender_document = (
            client_document_type + ': ' + str(order_action_sender_obj.client.clienttype_set.first().document_number),
            '')
        ana_c3 = Table([td_sender] + [td_sender_document], colWidths=[_wt * 19 / 100, _wt * 81 / 100])
        ana_c3.setStyle(TableStyle(my_style_table2_2))

    _rows = []
    for d in recipients:
        _phone = ''
        if d.client is None:
            _names = Paragraph(d.order_addressee.names.upper(), styles["Center5"])
            _phone = d.order_addressee.phone
            _rows.append(['NOMBRES :', _names, ''])
            _rows.append(['CEL : ' + _phone, '', ''])
        else:
            if d.client.phone is not None:
                _phone = d.client.phone
            _names = Paragraph(d.client.names.upper(), styles["Center5"])
            _rows.append([str(d.client.clienttype_set.first().document_type.short_description) + ':' + str(
                d.client.clienttype_set.first().document_number), '       CEL :' + _phone, ''])
            _rows.append(['NOMBRES :', _names, ''])

    colwiths_table_recipients = [_wt * 20 / 100, _wt * 80 / 100, _wt * 0 / 100]

    ana_c4 = Table([('DESTINATARIO(S):', '', '')] + _rows, colWidths=colwiths_table_recipients)

    ana_c4.setStyle(TableStyle(my_style_table_recipients))

    # document_addressee = str(order_action_addressee_obj.client.clienttype_set.first().document_type.short_description)
    #
    # if order_action_addressee_obj.client.names == 'CLIENTE REMITENTE':
    #     td_addressee = ('DESTINATARIO: ' + str(order_obj.addressee_name), '')
    #     td_addressee_nro_documento = (document_addressee + ': ' + '', '')
    #     ana_c4 = Table([td_addressee] + [td_addressee_nro_documento], colWidths=colwiths_table)
    #     ana_c4.setStyle(TableStyle(my_style_table_recipients))
    #
    # else:
    #     td_addressee = ('DESTINATARIO: ' + str(order_action_addressee_obj.client.names), '')
    #     td_addressee_nro_documento = (
    #         document_addressee + ': ' + str(order_action_addressee_obj.client.clienttype_set.first().document_number),
    #         'TELEFONO: ' + str(order_action_addressee_obj.client.phone))
    #     ana_c4 = Table([td_addressee] + [td_addressee_nro_documento], colWidths=colwiths_table)
    #     ana_c4.setStyle(TableStyle(my_style_table_recipients))

    address_delivery = '-'

    if order_obj.address_delivery:
        address_delivery = Paragraph(str(order_obj.address_delivery.upper()), styles["Justify"])

    td_type = ('TIPO', ': ENCOMIENDA')
    td_origin = ('ORIGEN', ': ' + str(order_obj.orderroute_set.filter(type='O').first().subsidiary.short_name))
    td_destiny = ('DESTINO', ': ' + str(order_obj.orderroute_set.filter(type='D').first().subsidiary.short_name))
    td_way_to_pay = ('COND. PAGO', ': ' + str(order_obj.get_way_to_pay_display()))
    td_service = ('SERVICIO', ': ' + str(order_obj.get_type_guide_display()))
    td_address_delivery = ('DIRECCIÓN REPARTO ' + ' :', address_delivery)
    td_code = ('CÓDIGO DE RECOJO: ' + str(order_obj.code), '')

    if order_obj.address_delivery:
        ana_c5 = Table(
            [td_type] + [td_origin] + [td_destiny] + [td_way_to_pay] + [td_service] + [td_code] + [td_address_delivery],
            colWidths=[_wt * 33 / 100, _wt * 67 / 100])

    else:
        ana_c5 = Table([td_type] + [td_origin] + [td_destiny] + [td_way_to_pay] + [td_service] + [td_code],
                       colWidths=[_wt * 33 / 100, _wt * 67 / 100])

    ana_c5.setStyle(TableStyle(my_style_table2))

    td_description = ('DESCRIPCIÓN', 'U.M.', 'CANT.', 'TOTAL')
    ana_c6 = Table([td_description], colWidths=[_wt * 60 / 100, _wt * 15 / 100, _wt * 10 / 100, _wt * 15 / 100])
    ana_c6.setStyle(TableStyle(my_style_table3))

    sub_total = 0
    total = 0
    igv_total = 0
    _rows = []
    _counter = order_obj.orderdetail_set.count()
    for d in order_obj.orderdetail_set.all():
        P0 = Paragraph(d.description.upper(), styles["Justify"])
        _rows.append((P0, d.unit.description, str(decimal.Decimal(round(d.quantity))), str(d.amount)))
        base_total = d.quantity * d.price_unit
        base_amount = base_total / decimal.Decimal(1.1800)
        igv = base_total - base_amount
        sub_total = sub_total + base_amount
        total = total + base_total
        igv_total = igv_total + igv

    ana_c7 = Table(_rows, colWidths=[_wt * 60 / 100, _wt * 15 / 100, _wt * 10 / 100, _wt * 15 / 100])

    ana_c7.setStyle(TableStyle(my_style_table4))

    td_gravada = ('OP.  GRAVADA', '', 'S/', str(decimal.Decimal(round(sub_total, 2))))
    td_inafecta = ('OP.  INAFECTA', '', 'S/', '0.00')
    td_exonerada = ('OP.  EXONERADA', '', 'S/', '0.00')
    td_descuento = ('DESCUENTO', '', 'S/', '0.00')
    td_igv = ('I.G.V.  (18.00)', '', 'S/', str(decimal.Decimal(round(igv_total, 2))))
    td_importe_total = ('IMPORTE TOTAL', '', 'S/', str(decimal.Decimal(round(total, 2))))

    ana_c8 = Table([td_gravada] + [td_inafecta] + [td_exonerada] + [td_descuento] + [td_igv] + [td_importe_total],
                   colWidths=[_wt * 60 / 100, _wt * 10 / 100, _wt * 17 / 100, _wt * 13 / 100])
    ana_c8.setStyle(TableStyle(my_style_table5))

    # datatable = order_bill_obj.code_qr
    datatable = 'https://4soluciones.pse.pe/20455935173'
    ana_c9 = Table([(qr_code(datatable), '')], colWidths=[_wt * 99 / 100, _wt * 1 / 100])
    ana_c9.setStyle(TableStyle(my_style_table6))

    footer = 'SON: ' + numero_a_moneda(total)
    footer2 = 'ACEPTO LOS TÉRMINOS Y CONDICIONES DEL CONTRATO DE TRANSPORTE PUBLICADOS EN LA EMPRESA'

    buff = io.BytesIO()

    ml = 0.05 * inch
    mr = 0.055 * inch
    ms = 0.039 * inch
    mi = 0.039 * inch

    doc = SimpleDocTemplate(buff,
                            pagesize=(3.14961 * inch, (11.6 * inch + (_counter * 0.13 * inch))),
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Encomienda Turnee'
                            )
    dictionary = []
    # dictionary.append(I)
    dictionary.append(Spacer(1, 5))
    dictionary.append(Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Center_Bold_title"]))
    dictionary.append(Spacer(1, -2))
    dictionary.append(Paragraph("SEDE AREQUIPA: " + str(phone_aqp), styles["Center"]))
    # dictionary.append(Paragraph("SEDE PEDREGAL AV. AREQUIPA: " + str(phone_pedregal), styles["Center"]))
    dictionary.append(Paragraph("SEDE CAMANA: " + str(phone_camana), styles["Center"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Paragraph(name_document, styles["Center_Regular"]))
    dictionary.append(Paragraph(serie + ' - ' + correlative, styles["Center_Bold"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c1)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c2)
    dictionary.append(ana_c2_1)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(data_title, styles["Center"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c3)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c4)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c5)
    dictionary.append(Spacer(1, 2))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 2))
    dictionary.append(ana_c6)
    dictionary.append(Spacer(1, 2))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 2))
    dictionary.append(ana_c7)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(ana_c8)
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(footer, styles["Center"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(footer2, styles["Center"]))
    dictionary.append(Spacer(1, 1))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Paragraph(
        "Representación impresa de la " + str(
            tbn_document) + ", para ver el documento visita ", styles["Square_left"]))
    dictionary.append(Paragraph("https://4soluciones.pse.pe/20455935173 ", styles["Square_bold_left"]))
    dictionary.append(Paragraph("Emitido mediante un PROVEEDOR Autorizado por la SUNAT", styles["Square_left"]), )
    dictionary.append(Paragraph("mediante Resolución de Intendencia No. 034-005- 0005315", styles["Square_left"]))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(-10, -10))
    dictionary.append(ana_c9)
    dictionary.append(Spacer(-10, -10))
    dictionary.append(Paragraph(
        "CONDICIONES PARA EL SERVICIO DE ENCOMIENDAS: "
        "1.	LA EMPRESA NO TRANSPORTA DINERO, VALORES Y JOYAS, ANIMALES VIVOS, SUSTANCIAS Y/O MATERIALES RESTRINGIDOS O PROHIBIDOS POR SENASA, DIGESA, SUNAT, EL CLIENTE ASUMIRÁ LA TOTAL RESPONSABILIDAD POR DAÑOS Y PERJUICIOS QUE SE OCASIONAN AL ESTADO, TERCEROS Y A LA EMPRESA. "
        "2.	EN CASO DE PERDIDA, EXTRAVIO O SUSTRACCION, DETERIORO O DESTRUCCION ENTREGA ERRONEA DE UNA ENCOMIENDA A EXCEPCIÓN DEL PREVISTO EN EL NUMERAL ANTERIOR, LA EMPRESA INDEMNIZARA AL CLIENTE DE ACUERDO A LA RESOLUCIÓN DIRECTORAL Nº OO1-2006-MTC/19. "
        "3. EL PLAZO DE ENTREGA DE ENCOMIENDAS DE DESTINOS (AGENCIAS DE LA EMPRESA ES DE 72 HORAS MAXIMO. "
        "4. SI LA ENCOMIENDA NO ES RECLAMADA EN 30 DIAS. LA EMPRESA APLICARA LO ESTABLECIDO EN LA R.M. Nº 572-2008. MTC.",
        styles["Center3"]))
    dictionary.append(Spacer(1, 2))
    dictionary.append(Paragraph(line, styles["Center2"]))
    dictionary.append(Spacer(1, 2))
    dictionary.append(Paragraph(
        "¡Gracias por enviar con TURNEE!",
        styles["Center2"]))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="WARE[{}].pdf"'.format(
        order_obj.serial + '-' + order_obj.correlative_sale)
    doc.build(dictionary)
    # doc.build(elements)
    # doc.build(Story)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_manifest_passengers(request, pk=None):  # Manifiesto de Pasajeros
    _legal = (8.5 * inch, 14 * inch)

    ml = 0.75 * inch
    mr = 0.75 * inch
    ms = 0.75 * inch
    mi = 1.0 * inch

    _bts = 8.5 * inch - 0.5 * inch - 0.5 * inch
    programming_obj = Programming.objects.get(id=pk)

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=(8.5 * inch, 14 * inch),
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Manifiesto de pasajeros'
                            )
    response = HttpResponse(content_type='application/pdf')

    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),      # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('SPAN', (0, 0), (3, 0)),  # first row
        ('ALIGNMENT', (0, 0), (3, 0), 'LEFT'),  # first row

        ('SPAN', (4, 0), (4, 0)),  # first row
        ('ALIGNMENT', (4, 0), (4, 0), 'RIGHT'),  # first row

        ('SPAN', (0, 1), (3, 1)),  # second row
        ('ALIGNMENT', (0, 1), (2, 1), 'LEFT'),  # second row
        ('ALIGNMENT', (4, 1), (4, 1), 'RIGHT'),  # second row

        # ('SPAN', (3, 1), (4, 1)),  # second row

        # ('SPAN', (4, 1), (5, 1)),  # second row
        ('SPAN', (7, 1), (9, 1)),  # second row
        ('SPAN', (1, 2), (2, 2)),  # third row
        ('ALIGNMENT', (1, 2), (2, 2), 'RIGHT'),  # third row
        ('SPAN', (4, 2), (5, 2)),  # third row
        ('ALIGNMENT', (4, 2), (5, 2), 'CENTER'),  # third row
        ('SPAN', (7, 2), (9, 2)),  # third row
        ('SPAN', (1, 3), (2, 3)),  # fourth row
        ('ALIGNMENT', (1, 3), (2, 3), 'RIGHT'),  # fourth row
        ('TOPPADDING', (1, 3), (2, 3), -4),  # fourth row

        ('SPAN', (4, 3), (5, 3)),  # fourth row
        ('ALIGNMENT', (4, 3), (5, 3), 'CENTER'),  # fourth row
        ('TOPPADDING', (4, 3), (5, 3), -4),  # fourth row

        ('SPAN', (7, 3), (9, 3)),  # fourth row
        ('SPAN', (1, 4), (2, 4)),  # fifth row
        ('ALIGNMENT', (1, 4), (2, 4), 'RIGHT'),  # fifth row
        ('ALIGNMENT', (6, 4), (6, 4), 'RIGHT'),  # fifth row
        ('ALIGNMENT', (9, 4), (9, 4), 'RIGHT'),  # fifth row
    ]

    col_widths = [
        _bts * 5 / 100,  # destiny
        _bts * 10 / 100,
        _bts * 5 / 100,  # origin
        _bts * 10 / 100,

        _bts * 20 / 100,  # passengers
        _bts * 5 / 100,

        _bts * 10 / 100,  # date
        _bts * 10 / 100,
        _bts * 10 / 100,
        _bts * 15 / 100
    ]

    col_heights = [
        1 * inch / 8,
        1 * inch / 4,
        1 * inch / 4,
        1 * inch / 4,
        1 * inch / 8,
    ]

    _pilot = programming_obj.get_pilot()
    _copilot = programming_obj.get_copilot()

    _n_license_pilot = _pilot.n_license
    _n_license_copilot = ''
    _copilot_full_name = ''
    if _copilot:
        _copilot_full_name = _copilot.full_name()
        _n_license_copilot = _copilot.n_license

    _truck = programming_obj.truck
    _hour = programming_obj.get_turn_display()
    _date = str(programming_obj.departure_date.strftime("%d/%m/%y"))
    programming_seat_set = programming_obj.programmingseat_set.filter(status='4')  # sold

    p0 = Paragraph(programming_obj.path.get_first_point().short_name, styles["Justify-Dotcirful"])
    p1 = Paragraph(programming_obj.path.get_last_point().short_name, styles["Justify-Dotcirful"])
    p2 = Paragraph('Nº PASAJEROS EN LA RUTA', styles["Justify"])

    ana_c1 = Table(
        [(_pilot.full_name(), '', '', '', _n_license_pilot, '', '', '', '', '')] +
        [(_copilot_full_name, '', '', '', _n_license_copilot, '', '', '', '', '')] +
        [('', _truck.truck_model.truck_brand.name, '', '', _truck.license_plate, '', '', '', '', '')] +
        [('', _truck.certificate, '', '', _truck.nro_passengers, '', '', '', '', '')] +
        [('', p1, '', '', p0, '', programming_seat_set.count(), '', _date, _hour[0:8])], colWidths=col_widths,
        rowHeights=col_heights)
    ana_c1.setStyle(TableStyle(style_table))

    _rows = []

    for ps in programming_obj.programmingseat_set.filter(status='4'):
        order_obj = Order.objects.filter(programming_seat=ps).last()
        client_obj = order_obj.client
        client_type_obj = client_obj.clienttype_set.get(document_type_id__in=['01', '04', '07'])
        _birthday = 0
        _short_name = ''
        if order_obj.subsidiary.short_name:
            _short_name = order_obj.subsidiary.short_name
        if client_obj.birthday:
            _birthday = calculate_age(client_obj.birthday)
        _rows.append((
            order_obj.serial[1:4],
            order_obj.correlative_sale,
            client_obj.names,
            '',
            ps.plan_detail.name,
            client_type_obj.document_type.id,
            client_type_obj.document_number,
            _birthday,
            # client_obj.nationality,
            _short_name,
            order_obj.destiny.name,
            order_obj.total,
        ))

    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('ALIGNMENT', (0, 0), (0, -1), 'RIGHT'),  # first column
        ('ALIGNMENT', (1, 0), (1, -1), 'CENTER'),  # second column
        ('ALIGNMENT', (7, 0), (7, -1), 'CENTER'),  # eighth column
        ('ALIGNMENT', (10, 0), (10, -1), 'RIGHT'),  # eleventh column
    ]
    _bts2 = 8.5 * inch - 1.0 * inch
    col_widths = [
        _bts2 * 8 / 100,  # serial
        _bts2 * 10 / 100,  # correlative
        _bts2 * 32 / 100,  # names

        _bts2 * 8 / 100,  # void

        _bts2 * 3 / 100,  # seat
        _bts2 * 3 / 100,  # document type

        _bts2 * 9 / 100,  # document number
        _bts2 * 5 / 100,  # age

        _bts2 * 9 / 100,
        _bts2 * 9 / 100,
        _bts2 * 5 / 100,

    ]
    if len(_rows) == 0:
        _rows.append(('', '', '', '', '', '', '', '', '', '', '',))

    ana_c2 = Table(_rows, colWidths=col_widths)

    ana_c2.setStyle(TableStyle(style_table))

    _dictionary = []
    _dictionary.append(Spacer(1, 43))
    _dictionary.append(ana_c1)
    _dictionary.append(Spacer(1, 25))
    _dictionary.append(ana_c2)

    doc.build(_dictionary)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_mock_up_passengers(request, pk=None):
    _a4 = (8.3 * inch, 11.7 * inch)

    ml = 0.25 * inch
    mr = 0.25 * inch
    ms = 0.25 * inch
    mi = 0.25 * inch

    _bts = 8.3 * inch - 0.25 * inch - 0.25 * inch

    programming_obj = Programming.objects.get(id=pk)

    plan_obj = programming_obj.truck.plan

    rows = plan_obj.rows
    cols = plan_obj.columns

    first_floor_set = plan_obj.plandetail_set.filter(position='I')

    _data_first_floor = []
    _first_floor_style = []

    x_style = 1
    x2_style = 1
    for x in range(1, rows + 1):
        _row_first_floor = []
        _count_void_first_floor = 0
        for y in range(1, cols + 1):
            search_first_floor_seat = first_floor_set.filter(row=x, column=y)

            if search_first_floor_seat:
                _row_first_floor.append(search_first_floor_seat.last().name)
                _first_floor_style.append(('BOX', (y - 1, x_style - 1), (y - 1, x_style - 1), 1, colors.gray))
                _first_floor_style.append(('FONTNAME', (y - 1, x_style - 1), (y - 1, x_style - 1), 'Dotcirful-Regular'))
                _first_floor_style.append(('TOPPADDING', (y - 1, x_style - 1), (y - 1, x_style - 1), 0))
                _first_floor_style.append(('LEFTPADDING', (y - 1, x_style - 1), (y - 1, x_style - 1), 0))
                _first_floor_style.append(('VALIGN', (y - 1, x_style - 1), (y - 1, x_style - 1), 'TOP'))
            else:
                _row_first_floor.append('')
                _count_void_first_floor = _count_void_first_floor + 1

        if _count_void_first_floor != cols:
            _data_first_floor.append(_row_first_floor)
            x_style = x_style + 1

    # _first_floor_style.append(('BOX', (0, 0), (-1, -1), 1, colors.gray))
    square_width = 0.87 * inch
    square_height = 0.87 * inch
    first_floor = Table(_data_first_floor, colWidths=cols * [square_width], rowHeights=(x_style - 1) * [square_height])
    first_floor.setStyle(TableStyle(_first_floor_style))

    p0 = Paragraph('EMPRESA DE TRANSPORTES SUPER RAPIDO NUEVA FLECHA S.A. - CROQUIS DE CONTROL DE VIAJE',
                   styles["Justify-Dotcirful"])
    p1 = Paragraph(programming_obj.path.get_first_point().short_name, styles["Justify-Dotcirful"])
    p2 = Paragraph(programming_obj.path.get_last_point().short_name, styles["Justify-Dotcirful"])
    _pilot = programming_obj.get_pilot()
    _n_license = _pilot.n_license
    _truck = programming_obj.truck
    _hour = programming_obj.get_turn_display()
    _date = str(programming_obj.departure_date.strftime("%d/%m/%y"))

    labeled = [
        [p0, '', '', ''],
        ['BUS: ', _truck.license_plate, 'HORARIO:', _hour[0:8]],
        ['ORIGEN:', p1, '', ''],
        ['DESTINO:', p2, '', ''],
        ['PILOTO:', _pilot.full_name(), '', ''],
        ['COPILOTO:', '', '', ''],
        ['FECHA:', _date, '', ''],
    ]
    t_labeled = Table(labeled)
    t_labeled.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),      # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        ('SPAN', (0, 0), (3, 0)),  # first row
        ('SPAN', (1, 2), (3, 2)),  # third row
        ('SPAN', (1, 3), (3, 3)),  # fourth row
        ('SPAN', (1, 4), (3, 4)),  # fifth row
        ('SPAN', (1, 5), (3, 5)),  # sixth row

    ]))
    bus = [
        [t_labeled, ''],
        ['', ''],
        ['', first_floor],
        ['DESPACHADO POR:...................', '']
    ]
    t = Table(bus)

    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),      # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns

        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (1, 0), (-1, -1), 'MIDDLE'),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('SPAN', (0, 0), (0, 1)),  # first and second row
    ]))
    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=(8.3 * inch, 11.7 * inch),
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Croquis de pasajeros'
                            )
    response = HttpResponse(content_type='application/pdf')

    _dictionary = []
    _dictionary.append(t)

    doc.build(_dictionary)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_manifest_comidity(request, pk=None):  # Manifiesto de Encomiendas
    _a4 = (8.3 * inch, 11.7 * inch)

    ml = 0.25 * inch
    mr = 0.25 * inch
    ms = 0.25 * inch
    mi = 0.25 * inch

    _bts = 8.3 * inch - 0.25 * inch - 0.25 * inch

    manifest_obj = Manifest.objects.get(id=pk)
    orders_programmings_set = OrderProgramming.objects.filter(manifest=manifest_obj)
    programming_obj = orders_programmings_set.first().programming

    # I = Image(logo)
    # I.drawHeight = 2.00 * inch / 2.9
    # I.drawWidth = 5.4 * inch / 2.9

    tbh_business_name_address = ''

    if manifest_obj.company.id == 1:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083'
    elif manifest_obj.company.id == 2:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083'
    elif manifest_obj.company.id == 3:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C.\n RUC: 20612403083'

    # tbh_business_name_address = 'TURISMO MENDIVIL S.R.L <br/> CALLE JAVIER P. DE CUELLAR B-3 INT 105 TERM. TERRESTRE S/N INT. E1-E / URB. ARTURO IBAÑEZ HUNTER AREQUIPA <br/> RUC: 20442736759'
    ph = Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Justify-Dotcirful-table"])
    tbn_name_document = 'MANIFIESTO DE ENCOMIENDAS'

    p0 = Paragraph('MANIFIESTO DE CARGA', styles["CenterTitle-Dotcirful"])

    _tbl_small = [
        [p0, ''],
        ['SERIE:', manifest_obj.serial],
        ['CORRELATIVO:', manifest_obj.correlative],
    ]

    ana_c_1 = Table(_tbl_small)

    _tbl_header = [
        [ph, '', ana_c_1],
    ]

    ana_c = Table(_tbl_header)

    # date = manifest_obj.create_at.date()
    _date_convert_zone = utc_to_local(manifest_obj.created_at)
    date_hour = _date_convert_zone.time()
    # date = datetime.now()
    _formatdate = _date_convert_zone.strftime("%d/%m/%Y")

    td_date = ('FECHA: ', _formatdate, 'TURNO: ', programming_obj.truck_exit)
    td_data_drive = ('PILOTO: ', str(programming_obj.setemployee_set.first().employee.full_name()), 'ESTADO: ',
                     str(programming_obj.get_status_display()).upper())
    td_data_vehicle = (
        'PLACA: ', str(programming_obj.truck.license_plate), 'TIPO: ',
        str(programming_obj.truck.get_drive_type_display()))
    td_route = ('ORIGEN: ', str(programming_obj.path.get_first_point().short_name), 'DESTINO: ',
                str(programming_obj.path.get_last_point().short_name))

    colwiths_table = [_bts * 10 / 100, _bts * 30 / 100, _bts * 10 / 100, _bts * 50 / 100]
    ana_c1 = Table([td_date] + [td_data_drive] + [td_data_vehicle] + [td_route], colWidths=colwiths_table)

    td_title = (
        '#', 'SERIE', 'NRO.', 'CANT.', 'UND.', 'PESO', 'DESCRIPCIÓN', 'DESTINATARIO', 'DESTINO', 'COND. PAGO', 'MONTO')
    colwiths_table_title = [_bts * 3 / 100,
                            _bts * 4 / 100,
                            _bts * 4 / 100,
                            _bts * 4 / 100,
                            _bts * 6 / 100,
                            _bts * 4 / 100,
                            _bts * 25 / 100,
                            _bts * 20 / 100,
                            _bts * 14 / 100,
                            _bts * 9 / 100,
                            _bts * 7 / 100]
    # ana_c2 = Table([td_title], colWidths=colwiths_table_title)
    detail_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Dotcirful-Regular'),
        ('FONTNAME', (0, 0), (0, -1), 'Dotcirful-Regular'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('FONTSIZE', (0, 0), (-1, 0), 9)
    ]
    _rows = []

    _rows.append(td_title)
    _pi = 0
    _pf = 0
    _c2 = 1
    y = 8
    cont_counted = 0
    cont_destination_payment = 0
    serial_row = ''
    name_addreess = ''
    for op in orders_programmings_set:
        order_obj = op.order
        _rows_recipients = []
        recipients = OrderAction.objects.filter(order=order_obj, type='D')
        for r in recipients:
            if r.client is None:
                _rows_recipients.append(str(r.order_addressee.names.upper()))
            else:
                _rows_recipients.append(str(r.client.names))
        name_addreess = str(_rows_recipients).replace(',', ' /').replace("'", '').replace(']', '').replace('[', '')
        number_details = order_obj.orderdetail_set.all().count()
        for d in order_obj.orderdetail_set.all():
            if order_obj and OrderBill.objects.filter(order=order_obj).count() > 0:
                serial_row = order_obj.orderbill.serial
            else:
                serial_row = 'G' + order_obj.serial[-3:]
            _rows.append((_c2,
                          # order_obj.id,
                          serial_row,
                          str(order_obj.correlative_sale[-4:]),
                          str(decimal.Decimal(round(d.quantity))),
                          d.unit.description,
                          str(decimal.Decimal(round(d.weight))) + ' KG',
                          Paragraph(d.description.upper(), styles["Justify-Dotcirful"]),
                          Paragraph(name_addreess, styles["Justify-Dotcirful"]),
                          order_obj.orderprogramming.programming.path.get_last_point().short_name,
                          # str(programming_obj.path.get_last_point().short_name),
                          order_obj.get_way_to_pay_display(),
                          'S/. ' + str(decimal.Decimal(round(order_obj.total, 2)))))

        _pf = _pf + number_details
        _pi = _pf - (number_details - 1)
        detail_style.append(('SPAN', (y - 1, _pi), (y - 1, _pf)))
        detail_style.append(('SPAN', (y - 1 + 1, _pi), (y - 1 + 1, _pf)))
        detail_style.append(('SPAN', (y - 1 + 2, _pi), (y - 1 + 2, _pf)))
        detail_style.append(('SPAN', (y - 1 + 3, _pi), (y - 1 + 3, _pf)))
        detail_style.append(('SPAN', (y - 1 - 7, _pi), (y - 1 - 7, _pf)))
        detail_style.append(('SPAN', (y - 1 - 6, _pi), (y - 1 - 6, _pf)))
        detail_style.append(('SPAN', (y - 1 - 5, _pi), (y - 1 - 5, _pf)))
        if order_obj.way_to_pay == 'C':
            cont_counted = cont_counted + order_obj.total
        elif order_obj.way_to_pay == 'D':
            cont_destination_payment = cont_destination_payment + order_obj.total
        _c2 = _c2 + 1
    ana_c3 = Table(_rows, colWidths=colwiths_table_title)

    colwiths_table_totals = [_bts * 80 / 100, _bts * 10 / 100, _bts * 10 / 100]
    p4 = Paragraph('TOTALES ENCOMIENDAS', styles["CenterTitle-Dotcirful"])
    _tbl_totals = [
        ['', p4, ''],
        ['', 'TOTAL PAGO CONTADO:', 'S/. ' + str(decimal.Decimal(round(cont_counted, 2)))],
        ['', 'TOTAL PAGO DESTINO:', 'S/. ' + str(decimal.Decimal(round(cont_destination_payment, 2)))],
    ]
    ana_c4 = Table(_tbl_totals, colWidths=colwiths_table_totals)

    my_style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        # ('FONTNAME', (0, 1), (0, -1), 'Newgot'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (0, -1), 'Dotcirful-Regular'),
        ('FONTNAME', (2, 0), (2, -1), 'Dotcirful-Regular'),
        # ('BOTTOMPADDING', (0, 0), (-1, -1), -6),
        # ('ALIGNMENT', (1, 1), (1, 1), 'RIGHT'),
        # ('ALIGNMENT', (1, 0), (1, 0), 'RIGHT'),
        # ('TOPPADDING', (0, 0), (-1, -1), 1),
        # ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # ('LINEBELOW', (0, 0), (-1, 0), 1, colors.darkblue),
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]
    ana_c1.setStyle(TableStyle(my_style_table))

    my_style_table_header_1 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('SPAN', (0, 0), (1, 0)),
        ('VALIGN', (0, 0), (0, -1), 'MIDDLE')  # first column

    ]
    ana_c_1.setStyle(TableStyle(my_style_table_header_1))

    my_style_table_header = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (1, 0), (1, -1), 'MIDDLE')  # first column

    ]
    ana_c.setStyle(TableStyle(my_style_table_header))

    my_style_table_totals = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (1, 0), (1, -1), 'MIDDLE'),  # first column
        ('SPAN', (1, 0), (2, 0)),  # first row
        ('ALIGNMENT', (1, 0), (2, -1), 'RIGHT'),  # second column
    ]
    ana_c4.setStyle(TableStyle(my_style_table_totals))

    ana_c3.setStyle(TableStyle(detail_style))

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=(8.3 * inch, 11.7 * inch),
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Manifiesto de Encomiendas'
                            )
    dictionary = []
    dictionary.append(ana_c)
    dictionary.append(Spacer(1, 5))
    # dictionary.append(Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Left"]))
    dictionary.append(Spacer(1, 5))
    dictionary.append(Paragraph(tbn_name_document, styles["CenterTitle-Dotcirful"]))
    dictionary.append(Spacer(20, 20))
    dictionary.append(ana_c1)
    dictionary.append(Spacer(10, 10))
    # dictionary.append(ana_c2)
    dictionary.append(ana_c3)
    dictionary.append(Spacer(10, 10))
    dictionary.append(ana_c4)

    response = HttpResponse(content_type='application/pdf')
    doc.build(dictionary)

    response['Content-Disposition'] = 'attachment; filename="Manifiesto-Encomienda_[{}].pdf"'.format(manifest_obj.id)
    # doc.build(elements)
    # doc.build(Story)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_guide_comidity(request, pk=None):  # Guia Remision Transportista
    _a5 = (5.8 * inch, 8.3 * inch)

    ml = 0.25 * inch
    mr = 0.25 * inch
    ms = 0.25 * inch
    mi = 0.25 * inch

    _bts = 5.8 * inch - 0.25 * inch - 0.25 * inch
    # _bts2 = 8.3 * inch - 0.25 * inch - 0.25 * inch
    colwiths_table = [_bts * 10 / 100, _bts * 30 / 100, _bts * 10 / 100, _bts * 50 / 100]
    orders_programmings_obj = OrderProgramming.objects.filter(order_id=pk)
    programming_obj = orders_programmings_obj.first().programming
    order_obj = orders_programmings_obj.first().order
    date = datetime.now()
    _formatdate = date.strftime("%d/%m/%Y")

    td_dates_1 = _formatdate
    td_dates_2 = _formatdate
    td_serial_guide = orders_programmings_obj.first().guide_serial + ' - '
    td_nro_guide = orders_programmings_obj.first().guide_code

    _tbl_header = [
        ['', td_serial_guide, td_nro_guide],
        ['', td_dates_1, td_dates_2],

    ]
    ana_c = Table(_tbl_header, colWidths=[_bts * 10 / 100, _bts * 35 / 100, _bts * 55 / 100],
                  rowHeights=[_bts * 10 / 100, _bts * 10 / 100])

    my_style_table_header = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (2, 0), (2, 0), 180),
        ('LEFTPADDING', (1, 0), (1, 0), 291),
        ('BOTTOMPADDING', (0, 0), (3, 0), -20),
        # ('BACKGROUND',  (0, 0), (3, 0), colors.pink)
        # ('VALIGN', (1, 0), (1, -1), 'MIDDLE')  # first column
    ]
    ana_c.setStyle(TableStyle(my_style_table_header))

    td_subsidiary_origin = order_obj.orderroute_set.filter(type='O').last().subsidiary.address
    td_subsidiary_destiny = order_obj.orderroute_set.filter(type='D').last().subsidiary.address

    _tbl_subsidiarys = [
        ['', '', td_subsidiary_origin],
        ['', '', td_subsidiary_destiny],
    ]
    ana_c1 = Table(_tbl_subsidiarys, colWidths=[_bts * 10 / 100, _bts * 5 / 100, _bts * 85 / 100])

    my_style_table_subsidiary = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (3, 0), -6),  # first row
        ('TOPPADDING', (0, 1), (3, 1), 2),  # second row
        # ('BACKGROUND',  (0, 1), (3, 1), colors.pink),
    ]
    ana_c1.setStyle(TableStyle(my_style_table_subsidiary))

    td_client_sender = order_obj.orderaction_set.filter(type='R').last().client.names.upper()
    td_client_addreesse = order_obj.orderaction_set.filter(type='D').last().client.names.upper()
    td_client_sender_type_document = order_obj.orderaction_set.filter(
        type='R').last().client.clienttype_set.first().document_type.short_description + ':'
    td_client_sender_document = order_obj.orderaction_set.filter(
        type='R').last().client.clienttype_set.first().document_number
    td_client_addreesse_type_document = order_obj.orderaction_set.filter(
        type='D').last().client.clienttype_set.first().document_type.short_description + ':'
    td_client_addreesse_document = order_obj.orderaction_set.filter(
        type='D').last().client.clienttype_set.first().document_number

    _tbl_clients = [
        ['', '', td_client_sender] + [td_client_sender_type_document] + [td_client_sender_document],
        ['', '', td_client_addreesse] + [td_client_addreesse_type_document] + [td_client_addreesse_document],
    ]
    ana_c2 = Table(_tbl_clients,
                   colWidths=[_bts * 5 / 100, _bts * 4 / 100, _bts * 79 / 100, _bts * 5 / 100, _bts * 7 / 100])

    my_style_table_client = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (3, 0), (4, -1), 6),
        ('LEFTPADDING', (3, 0), (3, -1), 21),
        ('LEFTPADDING', (4, 0), (4, -1), 12),
        ('TOPPADDING', (0, 0), (4, 0), -1),  # first row
        ('TOPPADDING', (0, 1), (4, 1), 3),  # second row
    ]
    ana_c2.setStyle(TableStyle(my_style_table_client))

    colwiths_table_title = [_bts * 10 / 100,
                            _bts * 65 / 100,
                            _bts * 9 / 100,
                            _bts * 9 / 100,
                            _bts * 7 / 100]

    _rows = []
    _counter = 1
    _c2 = 1
    for op in orders_programmings_obj:
        order_obj = op.order
        for d in order_obj.orderdetail_set.all():
            number_details = order_obj.orderdetail_set.all().count()
            _rows.append((_c2,
                          Paragraph(d.description.upper(), styles["Justify-Dotcirful-table"]),
                          d.unit.description,
                          str(decimal.Decimal(round(d.quantity))),
                          str(decimal.Decimal(round(d.weight))) + ' KG'))
            _c2 = _c2 + 1

    ana_c3 = Table(_rows, colWidths=colwiths_table_title)

    detail_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGNMENT', (4, 0), (4, -1), 'RIGHT'),  # four column
        ('RIGHTPADDING', (4, 0), (4, -1), -4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),  # all columns
        # ('BACKGROUND', (4, 0), (4, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Dotcirful-Regular'),
        ('FONTNAME', (0, 0), (0, -1), 'Dotcirful-Regular'),
        ('FONTSIZE', (0, 0), (0, -1), 7),
        ('FONTSIZE', (0, 0), (-1, 0), 7)
    ]
    ana_c3.setStyle(TableStyle(detail_style))

    td_truck = programming_obj.truck.truck_model.truck_brand.name
    td_plate = programming_obj.truck.license_plate
    td_certificate = programming_obj.truck.certificate
    td_license_nro = programming_obj.get_pilot().n_license

    _tbl_truck_data = [
        ['', td_truck],
        ['', td_plate],
        ['', ''],
        ['', td_certificate],
        ['', td_license_nro]
    ]
    ana_c4 = Table(_tbl_truck_data, colWidths=[_bts * 23 / 100, _bts * 77 / 100])

    my_style_table_truck_data = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), -5),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('TOPPADDING', (0, 0), (1, 0), -1),  # first row
        ('TOPPADDING', (0, 1), (2, 1), 3),  # second row
        ('TOPPADDING', (0, 2), (2, 2), -1),  # third row
        ('BOTTOMPADDING', (0, 3), (3, 3), -10),  # fourth row
        ('BOTTOMPADDING', (0, 4), (4, 4), -14),  # fourth row
    ]
    ana_c4.setStyle(TableStyle(my_style_table_truck_data))

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=A5,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Manifiesto de Encomiendas'
                            )
    dictionary = []
    dictionary.append(ana_c)
    dictionary.append(Spacer(1, 5))
    dictionary.append(ana_c1)
    dictionary.append(Spacer(1, 5))
    dictionary.append(ana_c2)
    dictionary.append(Spacer(4, 10))
    dictionary.append(ana_c3)
    dictionary.append(Spacer(54, 54))
    dictionary.append(ana_c4)

    response = HttpResponse(content_type='application/pdf')
    doc.build(dictionary)
    response['Content-Disposition'] = 'attachment; filename="GuiaRemisionTransportista_[{}].pdf"'.format(
        orders_programmings_obj.first().order.id)
    # doc.build(elements)
    # doc.build(Story)
    response.write(buff.getvalue())
    buff.close()
    return response


# ---------------------------------------------------------------------------------------------------------------


def print_ticket_old(request, pk=None):  # TICKET PASSENGER OLD

    _wt = 2.83 * inch - 4 * 0.05 * inch  # termical
    tbh_business_name_address = ''
    ml = 0.0 * inch
    mr = 0.0 * inch
    ms = 0.039 * inch
    mi = 0.039 * inch
    order_obj = Order.objects.get(pk=pk)
    passenger_name = ""
    passenger_document = ""
    client_document = ""
    client_name = ""
    client_address = ""

    passenger_set = order_obj.client
    passenger_name = passenger_set.names
    passenger_document = passenger_set.clienttype_set.first().document_number

    entity_set = order_obj.orderaction_set.filter(type='E')
    if entity_set.exists():
        client_document = entity_set.first().client.clienttype_set.first().document_number
        client_name = entity_set.first().client.names
        client_address = entity_set.first().client.clientaddress_set.first().address

    if order_obj.company.id == 1:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C. \n RUC: 20612403083'
    elif order_obj.company.id == 2:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C. \n RUC: 20612403083'
    elif order_obj.company.id == 3:
        tbh_business_name_address = 'TRANSPORTES COXMAN S.A.C. \n RUC: 20612403083'

    date = order_obj.programming_seat.programming.departure_date
    _format_time = utc_to_local(order_obj.create_at).strftime("%H:%M %p")
    _format_date = date.strftime("%d/%m/%Y")

    line = '-----------------------------------------------------'

    I = Image(logo)
    I.drawHeight = 1.95 * inch / 2.9
    I.drawWidth = 7.4 * inch / 2.9

    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),  # all columns
        # ('BACKGROUND', (1, 0), (3, 0), colors.blue),
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('SPAN', (1, 0), (3, 0)),

    ]
    colwiths_table = [_wt * 30 / 100, _wt * 70 / 100]

    # p0 = Paragraph(client_name, styles["Right"])
    # ana_c1 = Table(
    #     [('CLIENTE: N DOC ', client_document)] +
    #     [('SR(A): ', p0)] +
    #     [('ATENDIDO POR: ', order_obj.user.username.upper() + " " + order_obj.subsidiary.name)],
    #     colWidths=colwiths_table)
    #
    # ana_c1.setStyle(TableStyle(style_table))

    p10 = Paragraph('SR(A): ' + passenger_document + ' - ' + passenger_name, styles["Justify"])
    colwiths_table = [_wt * 25 / 100, _wt * 25 / 100, _wt * 25 / 100, _wt * 25 / 100]
    if order_obj.show_original_name:
        subsidiary_company_obj = SubsidiaryCompany.objects.filter(subsidiary=order_obj.subsidiary,
                                                                  company=order_obj.company).last()
        if subsidiary_company_obj.original_name is not None:
            _short_name_origin = subsidiary_company_obj.original_name
        else:
            _short_name_origin = subsidiary_company_obj.subsidiary.short_name

    else:
        _short_name_origin = order_obj.subsidiary.short_name

    ana_c2 = Table(
        [('PASAJERO:', p10, '', '')] +
        # [('AGENCIA DE EMBARQUE:', '', order_obj.subsidiary.name, '')] +
        # [('ORIG:', _short_name_origin, '', '')] +
        [('DEST:', order_obj.destiny.name, 'FECHA:', str(_format_date))] +
        [('ASIENTO:', order_obj.programming_seat.plan_detail.name, 'HORA:', str(_format_time))] +
        [('ATENDIDO POR: ', '', order_obj.user.username.upper() + " " + order_obj.subsidiary.name)],
        colWidths=colwiths_table)
    ana_c2.setStyle(TableStyle(style_table))

    my_style_table3 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),  # all columns
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    colwiths_table = [_wt * 80 / 100, _wt * 20 / 100]
    ana_c6 = Table([('DESCRIPCIÓN', 'TOTAL')], colWidths=colwiths_table)
    ana_c6.setStyle(TableStyle(my_style_table3))

    sub_total = 0
    total = 0
    igv_total = 0

    # Validar si el origen es distinto a la sede
    if order_obj.origin and order_obj.origin.name != order_obj.subsidiary.name:
        origin_name = order_obj.origin.name
    else:
        origin_name = order_obj.subsidiary.short_name
    
    route = f"SERVICIO DE TRANSPORTE<br/>ORIGEN: {origin_name}<br/>DESTINO: {order_obj.destiny.name}<br/>ASIENTO: {order_obj.programming_seat.plan_detail.name}"
    # P0 = Paragraph(
    #     'SERVICIO DE TRANSPORTE RUTA ' + order_obj.programming_seat.programming.get_origin().short_name + ' - ' + order_obj.destiny.name + '<br/> ASIENTO ' + order_obj.programming_seat.plan_detail.name + '.',
    #     styles["Justify"])
    P0 = Paragraph(route, styles["Justify"])
    P_TRUCK = Paragraph('PLACA: ' + order_obj.programming_seat.programming.truck.license_plate, styles["Justify_Bold"])

    base_total = 1 * 45
    base_amount = base_total / 1.1800
    igv = base_total - base_amount
    sub_total = sub_total + base_amount
    total = total + base_total
    igv_total = igv_total + igv
    # ana_truck = Table([(P_TRUCK, '')], colWidths=[_wt * 80 / 100, _wt * 20 / 100])

    my_style_truck = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        # ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    my_style_table4 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('RIGHTPADDING', (1, 0), (1, -1), 0.5),  # second column
        ('ALIGNMENT', (1, 0), (1, -1), 'RIGHT'),  # second column
    ]
    ana_c7 = Table([(P0, 'S/ ' + str(decimal.Decimal(round(order_obj.total, 2))))],
                   colWidths=[_wt * 80 / 100, _wt * 20 / 100])
    ana_c7.setStyle(TableStyle(my_style_table4))
    # ana_truck.setStyle(TableStyle(my_style_truck))

    my_style_table5 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns

        # ('GRID', (0, 0), (-1, -1), 0.5, colors.pink),   # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # all columns
        ('BOTTOMPADDING', (0, 0), (-1, -1), -6),  # all columns
        ('RIGHTPADDING', (2, 0), (2, -1), 0),  # third column
        ('ALIGNMENT', (2, 0), (2, -1), 'RIGHT'),  # third column
        ('RIGHTPADDING', (3, 0), (3, -1), 0.3),  # four column
        ('ALIGNMENT', (3, 0), (3, -1), 'RIGHT'),  # four column
        ('LEFTPADDING', (0, 0), (0, -1), 0.5),  # first column
        ('FONTNAME', (0, 2), (-1, 2), 'Square-Bold'),  # third row
        ('FONTSIZE', (0, 2), (-1, 2), 10),  # third row
    ]

    ana_c8 = Table(
        [('OP. NO GRAVADA', '', 'S/', str(decimal.Decimal(round(order_obj.total, 2))))] +
        [('I.G.V.  (18.00)', '', 'S/', '0.00')] +
        [('TOTAL', '', 'S/', str(decimal.Decimal(round(order_obj.total, 2))))],
        colWidths=[_wt * 60 / 100, _wt * 10 / 100, _wt * 10 / 100, _wt * 20 / 100]
    )
    ana_c8.setStyle(TableStyle(my_style_table5))
    footer = 'SON: ' + numero_a_moneda(order_obj.total)

    my_style_table6 = [
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.blue),   # all columns
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # all columns
        ('ALIGNMENT', (0, 0), (0, -1), 'CENTER'),  # first column
        ('SPAN', (0, 0), (1, 0)),  # first row
    ]

    datatable = order_obj.correlative_sale
    ana_c9 = Table([(qr_code(datatable), '')], colWidths=[_wt * 99 / 100, _wt * 1 / 100])
    ana_c9.setStyle(TableStyle(my_style_table6))

    _dictionary = []
    # _dictionary.append(I)
    _dictionary.append(Spacer(1, 5))
    _dictionary.append(Paragraph(tbh_business_name_address.replace("\n", "<br />"), styles["Center4"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Paragraph('TICKET', styles["Center_Regular"]))
    _dictionary.append(
        Paragraph(order_obj.serial + ' - ' + str(order_obj.correlative_sale).zfill(6), styles["Center_Bold"]))
    _dictionary.append(Spacer(-2, -2))
    # _dictionary.append(ana_c1)
    # _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-2, -2))
    _dictionary.append(Spacer(1, 2))
    _dictionary.append(Paragraph('DATOS DE VIAJE ', styles["Center_Regular"]))
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(ana_c2)
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-1, -1))
    _dictionary.append(ana_c6)
    _dictionary.append(Spacer(-1, -1))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(1, 1))
    _dictionary.append(ana_c7)
    # _dictionary.append(ana_truck)
    _dictionary.append(Spacer(-3, -3))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(ana_c8)
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Paragraph(footer, styles["Center"]))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(
        Paragraph("***COMPROBANTE NO TRIBUTARIO.***".replace('***', '"'), styles["Center2"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(ana_c9)
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph("DE LAS CONDICIONES PARA EL SERVICIO DE TRANSPORTE: "
                                 "1. EL BOLETO DE VIAJE ES PERSONAL, TRANSFERIBLE Y/O PO5TERGABLE. "
                                 "2. EL PASAJERO SE PRESENTARÁ 30 MIN ANTES DE LA HORA DE VIAJE, DEBIENDO PRESENTAR SU BOLETO DE VIAJE Y DNI. "
                                 "3. LOS MENORES DE EDAD VIAJAN CON SUS PADRES O EN SU DEFECTO DEBEN PRESENTAR PERMISO NOTARIAL DE SUS PADRES, MAYORES DE 5 AÑOS PAGAN SU PASAJE. "
                                 "4. EN CASO DE ACCIDENTES EL PASAJERO VIAJA  ASEGURADO CON SOAT DE LA COMPANIA RIMAC SEGUROS. "
                                 "5. EL PASAJERO TIENE DERECHO A TRANSPORTAR 20 KILOS DE EQUIPAJE, SOLO ARTICULOS DE USO PERSONAL (NO CARGA).  EL EXCESO SERÁ ADMITIDO CUANDO LA CAPACIDAD DEL BUS LO PERMITA, PREVIO PAGO DE LA TARIFA. "
                                 "6. LA EMPRESA NO SE RESPONSABILIZA POR FALLAS AJENAS AL MISMO SERVICIO DE TRANSPORTE (WIFI, TOMACORRIENTES, PANTALLAS, AUDIO Y OTRAS SIMILARES) PUES ESTOS SERVICIOS SON OFRECIDOS EN CALIDAD DE CORTESIA. "
                                 "7. LAS DEVOLUCIONES DE BOLETOS PAGADOS CON VISA SE EFECTUARÁ SEGÚN LOS PLAZOS, PROCEDIMIENTOS Y CANALES ESTABLECIDOS POR VISA, EN NINGUN CASO SE EFECTUARÁ DEVOLUCIÓN EN EFECTIVO.",
                                 styles["Center3"]))
    _dictionary.append(Spacer(-4, -4))
    _dictionary.append(Paragraph(line, styles["Center2"]))
    _dictionary.append(Spacer(-2, -2))
    _dictionary.append(Paragraph(
        "¡Gracias por viajar con nosotros!",
        styles["Center2"]))
    buff = io.BytesIO()

    pz_matricial = (2.57 * inch, 11.6 * inch)
    # pz_termical = (3.14961 * inch, 11.6 * inch)
    pz_termical = (2.83 * inch, 11.6 * inch)

    doc = SimpleDocTemplate(buff,
                            pagesize=pz_termical,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='TICKET'
                            )
    doc.build(_dictionary)
    # doc.build(elements)
    # doc.build(Story)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="CE[{}-{}].pdf"'.format(
        order_obj.serial, order_obj.correlative_sale)

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie('bp', value=pk, expires=expires)

    response.write(buff.getvalue())

    buff.close()
    return response


def print_manifest_passengers_old(request, pk=None):  # Manifiesto de Pasajeros antiguo matricial
    # _legal = (8.5 * inch, 14 * inch)
    _a6 = 8.27 * inch - 0.5 * inch
    _custom_a5 = (8.27 * inch, 5.75 * inch)

    ml = 0.00 * inch
    mr = 0.00 * inch
    ms = 0.00 * inch
    mi = 0.00 * inch

    # _bts = 8.5 * inch - 0.5 * inch - 0.5 * inch

    style_table0 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        ('GRID', (0, 0), (-1, -1), 0.5, colors.blue),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 12),  # all columns
        # ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
    ]
    style_table = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        ('GRID', (0, 0), (-1, -1), 0.5, colors.green),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 12),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
    ]
    style_table2 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        ('GRID', (0, 0), (-1, -1), 0.5, colors.red),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 12),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
    ]
    style_table3 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Dotcirful-Regular'),  # all columns
        ('GRID', (0, 0), (-1, -1), 0.5, colors.yellow),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # all columns
        ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
    ]

    style_table4 = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),  # all columns
        ('GRID', (0, 0), (-1, -1), 0.5, colors.fuchsia),  # all columns
        ('FONTSIZE', (0, 0), (-1, -1), 9),  # all columns
        # ('TOPPADDING', (0, 0), (-1, -1), -3),  # all columns
    ]

    colwiths_table0 = [_a6 * 75 / 100, _a6 * 25 / 100]
    colwiths_table = [_a6 * 20 / 100, _a6 * 25 / 100, _a6 * 25 / 100, _a6 * 15 / 100, _a6 * 15 / 100]
    colwiths_table2 = [_a6 * 45 / 100, _a6 * 15 / 100, _a6 * 20 / 100, _a6 * 20 / 100]
    colwiths_table3 = [_a6 * 10 / 100, _a6 * 30 / 100, _a6 * 7 / 100, _a6 * 27 / 100, _a6 * 13 / 100, _a6 * 13 / 100]
    colwiths_table4 = [_a6 * 5 / 100, _a6 * 15 / 100, _a6 * 45 / 100, _a6 * 15 / 100, _a6 * 10 / 100, _a6 * 10 / 100]

    programming_obj = Programming.objects.get(id=pk)

    _pilot = programming_obj.get_pilot()
    _copilot = programming_obj.get_copilot()
    _n_license_pilot = _pilot.n_license
    if _copilot:
        _copilot_full_name = _copilot.full_name()
        _n_license_copilot = _copilot.n_licens

    _serial_correlative = str(programming_obj.serial + '-' + programming_obj.correlative.zfill(6))
    _truck = programming_obj.truck
    _driver = _pilot.full_name()
    _brand = _truck.truck_model.truck_brand.name
    # _hour = programming_obj.get_turn_display()
    _date = str(programming_obj.departure_date.strftime("%d/%m/%y"))
    # _hour = str(programming_obj.departure_date.strftime("%I:%M:%S %p"))
    my_date = datetime.now()
    _hour = str(my_date.strftime("%I:%M %p"))

    if programming_obj.truck_exit is None:
        programming_obj.truck_exit = my_date
        departure_set = Departure.objects.filter(truck=_truck, month=my_date.month)
        departure_obj = None
        if departure_set.exists():
            departure_obj = departure_set.first()
        else:
            departure_obj = Departure(truck=_truck, month=my_date.month)
            departure_obj.save()

        departure_detail_set = DepartureDetail.objects.filter(departure=departure_obj, register_date=my_date.date())
        if not departure_detail_set.exists():
            departure_detail_obj = DepartureDetail(departure=departure_obj, register_date=my_date.date())
            departure_detail_obj.save()

    user_id = request.user.id
    user_obj = User.objects.get(pk=int(user_id))
    subsidiary_origin_obj = get_subsidiary_by_user(user_obj)
    company_rotation_obj = user_obj.companyuser.company_rotation

    subsidiary_company_origin_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_origin_obj,
                                                                     company=company_rotation_obj).last()
    _short_name_origin = subsidiary_company_origin_obj.short_name

    subsidiary_destiny_obj = programming_obj.path.get_last_point()
    # subsidiary_company_destiny_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_destiny_obj,
    #                                                                   company=company_rotation_obj).last()

    subsidiary_company_destiny_obj = SubsidiaryCompany.objects.filter(subsidiary=subsidiary_destiny_obj,
                                                                      company=programming_obj.company).last()

    _short_name_destiny = subsidiary_company_destiny_obj.short_name

    p0 = Paragraph(_short_name_origin, styles["Justify-Dotcirful"])
    p1 = Paragraph(_short_name_destiny, styles["Justify-Dotcirful"])

    ana_c0 = Table([('', _serial_correlative)], colWidths=colwiths_table0)
    ana_c0.setStyle(TableStyle(style_table0))

    ana_c1 = Table([('', '', _brand, _hour, _date)], colWidths=colwiths_table)
    ana_c1.setStyle(TableStyle(style_table))

    ana_c2 = Table([(_pilot.full_name(), _truck, _n_license_pilot, _pilot.document_number)], colWidths=colwiths_table2)
    ana_c2.setStyle(TableStyle(style_table2))

    arr_ps_set = ProgrammingSeat.objects.filter(programming=programming_obj.id).values_list('plan_detail__name',
                                                                                            flat=True)
    arr_ps_strings = list(map(int, arr_ps_set))
    arr_ps_strings.sort()
    _rows = []
    for element in arr_ps_strings:
        ps = ProgrammingSeat.objects.get(programming=programming_obj, plan_detail__name=str(element))
        name = ''
        document = ''
        serial_correlative = ''
        price = ''
        if ps.status == '4':
            order_obj = Order.objects.filter(programming_seat=ps, status='C').last()
            name = order_obj.client.names
            price = str(order_obj.total)
            document = order_obj.client.clienttype_set.first().document_number
            serial_correlative = str(order_obj.serial + '-' + order_obj.correlative_sale.zfill(6))
        # _rows.append((ps.plan_detail.name, name, document, serial_correlative))
        _rows.append(('', serial_correlative, name, document, price, ''))

    ana_c4 = Table(_rows, colWidths=colwiths_table4, rowHeights=0.22 * inch)
    ana_c4.setStyle(TableStyle(style_table4))

    programming_obj.status = 'F'
    programming_obj.save()

    '''
        printer_name = 'EPSON FX-890 (PLUS)'
    
        p = win32print.OpenPrinter(printer_name)
        job = win32print.StartDocPrinter(p, 1, ("test of raw data", None, "RAW"))
        win32print.StartPagePrinter(p)
        win32print.WritePrinter(p, "data to print")
        win32print.EndPagePrinter(p)
    '''

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=_custom_a5,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Manifiesto de pasajeros'
                            )
    response = HttpResponse(content_type='application/pdf')

    # response['Content-Disposition'] = 'attachment; filename="MPE_{}_{}.pdf"'.format(
    #     programming_obj.serial, programming_obj.correlative)

    # Wait for 5 seconds
    # time.sleep(8)

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0)
    expires = datetime.strftime(tomorrow, "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie('mpe', value=pk, expires=expires)

    _dictionary = []
    _dictionary.append(Spacer(53, 53))  # antes estaba en 100, 100
    _dictionary.append(ana_c0)
    _dictionary.append(Spacer(15, 15))
    _dictionary.append(ana_c1)
    _dictionary.append(Spacer(5, 5))
    _dictionary.append(ana_c2)
    _dictionary.append(Spacer(15, 15))
    _dictionary.append(ana_c4)

    doc.build(_dictionary)

    response.write(buff.getvalue())
    buff.close()
    return response


def print_report_commodity(request, start_date=None, end_date=None, user_type=None, way_to_pay=None,
                           destiny=None):  # reporte de encomiendas

    _a5 = (5.8 * inch, 8.3 * inch)

    date_start_date = datetime.strptime(start_date, '%Y-%m-%d')
    date_end_date = datetime.strptime(end_date, '%Y-%m-%d')

    ml = 0.25 * inch
    mr = 0.25 * inch
    ms = 0.25 * inch
    mi = 0.25 * inch

    _bts = 5.8 * inch - 0.25 * inch - 0.25 * inch

    date = datetime.now()
    _formatdate = date.strftime("%d/%m/%Y")

    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    order_route_set = ''

    if destiny == 'T' and way_to_pay == 'T':
        if user_type == 1:
            order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                        order__type_order='E',
                                                        order__traslate_date__range=[start_date, end_date]).order_by(
                'order__id').distinct('order__id')
        elif user_type == 2:
            order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                        order__type_order='E', order__user=user_obj,
                                                        order__traslate_date__range=[start_date, end_date]).order_by(
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
                                                        order__traslate_date__range=[start_date, end_date]).order_by(
                'order__id')
        elif user_type == 2:
            order_route_set = OrderRoute.objects.filter(order__subsidiary=subsidiary_obj,
                                                        order__type_order='E', order__user=user_obj,
                                                        type='D',
                                                        subsidiary__id=destiny,
                                                        order__traslate_date__range=[start_date, end_date]).order_by(
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
                                                        order__type_order='E', user=user_obj,
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
                                                        order__type_order='E', user=user_obj,
                                                        type='D',
                                                        subsidiary__id=destiny,
                                                        order__traslate_date__range=[start_date, end_date],
                                                        order__way_to_pay='D').order_by('order__id')

    _tbl_header = ('REPORTE DE ENCOMIENDAS',)

    ana_c = Table([_tbl_header], colWidths=[_bts * 100 / 100])

    my_style_table_header = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),  # third column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # first column
        # ('LEFTPADDING', (2, 0), (2, 0), 180),
        # ('LEFTPADDING', (1, 0), (1, 0), 291),
        # ('BOTTOMPADDING', (0, 0), (3, 0), -20),
        # ('BACKGROUND',  (0, 0), (3, 0), colors.pink)
    ]
    ana_c.setStyle(TableStyle(my_style_table_header))

    td_title = ('FECHA', 'SERIE', 'NRO.', 'PAGO\n CONTADO', 'PAGO\n DESTINO', 'DESTINO', 'USUARIO',)
    colwiths_table_title = [_bts * 20 / 100,
                            _bts * 10 / 100,
                            _bts * 10 / 100,
                            _bts * 10 / 100,
                            _bts * 10 / 100,
                            _bts * 20 / 100,
                            _bts * 20 / 100,
                            ]
    _rows = []
    _rows.append(td_title)
    cont_counted = 0
    cont_destination_payment = 0

    for o in order_route_set:
        _total_pay_counted = 0
        _total_pay_destiny = 0
        destiny_obj = ''

        if o.order.status != 'A':
            if o.order.way_to_pay == 'C':
                _total_pay_counted = o.order.total
            elif o.order.way_to_pay == 'D':
                _total_pay_destiny = o.order.total

        # destiny_set = o.orderroute_set.filter(type='D')
        destiny_set = o.type = 'D'
        if destiny_set != None:
            destiny_obj = o.subsidiary.short_name

        # if destiny_set.exists():
        #     destiny_obj = destiny_set.first().subsidiary.short_name
        else:
            destiny_obj = 'ANULADO'
        _rows.append((o.order.traslate_date,
                      o.order.serial,
                      str(o.order.correlative_sale),
                      _total_pay_counted,
                      _total_pay_destiny,
                      destiny_obj,
                      o.order.user.worker_set.last().employee.names
                      ))
        if o.order.status != 'A':
            if o.order.way_to_pay == 'C':
                cont_counted = cont_counted + o.order.total
            elif o.order.way_to_pay == 'D':
                cont_destination_payment = cont_destination_payment + o.order.total

    ana_c3 = Table(_rows, colWidths=colwiths_table_title)

    colwiths_table_totals = [_bts * 80 / 100, _bts * 10 / 100, _bts * 10 / 100]
    p4 = Paragraph('TOTALES ENCOMIENDAS', styles["Center"])
    _tbl_totals = [
        ['', p4, ''],
        ['', 'TOTAL PAGO CONTADO:', 'S/. ' + str(decimal.Decimal(round(cont_counted, 2)))],
        ['', 'TOTAL PAGO DESTINO:', 'S/. ' + str(decimal.Decimal(round(cont_destination_payment, 2)))],
    ]
    ana_c4 = Table(_tbl_totals, colWidths=colwiths_table_totals)

    detail_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (2, 1), (-5, -1), 'Square-Bold'),
        # ('BACKGROUND', (2, 1), (-5, -1), colors.blue),
        ('FONTNAME', (0, 0), (-1, 0), 'Square'),
        ('FONTNAME', (0, 0), (0, -1), 'Square'),
        # ('FONTSIZE', (0, 0), (0, -1), 10),
        ('FONTSIZE', (0, 0), (-1, 0), 9)
    ]
    ana_c3.setStyle(TableStyle(detail_style))

    my_style_table_totals = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (1, 0), (1, -1), 'MIDDLE'),  # first column
        ('SPAN', (1, 0), (2, 0)),  # first row
        ('ALIGNMENT', (1, 0), (2, -1), 'RIGHT'),  # second column
    ]
    ana_c4.setStyle(TableStyle(my_style_table_totals))

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=A5,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Reporte de Encomiendas'
                            )
    dictionary = []
    dictionary.append(ana_c)
    dictionary.append(Spacer(10, 10))
    dictionary.append(ana_c3)
    dictionary.append(Spacer(10, 10))
    dictionary.append(ana_c4)

    response = HttpResponse(content_type='application/pdf')
    doc.build(dictionary)
    response['Content-Disposition'] = 'attachment; filename="ReporteDeEncomiendas_[{}].pdf"'.format(_formatdate)
    # doc.build(elements)
    # doc.build(Story)
    response.write(buff.getvalue())
    buff.close()
    return response


def print_report_receive_commodity(request, start_date=None, end_date=None):
    _a5 = (5.8 * inch, 8.3 * inch)

    ml = 0.25 * inch
    mr = 0.25 * inch
    ms = 0.25 * inch
    mi = 0.25 * inch

    _bts = 5.8 * inch - 0.25 * inch - 0.25 * inch

    date = datetime.now()
    _formatdate = date.strftime("%d/%m/%Y")

    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)

    if start_date == end_date:
        orders_set = OrderProgramming.objects.filter(order__orderroute__subsidiary=subsidiary_obj,
                                                     order__orderroute__type='D',
                                                     order__traslate_date=start_date).order_by('order_id')
    else:
        orders_set = OrderProgramming.objects.filter(order__orderroute__subsidiary=subsidiary_obj,
                                                     order__orderroute__type='D',
                                                     order__traslate_date__range=[start_date, end_date]).order_by(
            'order_id')

    _tbl_header = ('REPORTE DE RECEPCIÓN DE ENCOMIENDAS',)

    ana_c = Table([_tbl_header], colWidths=[_bts * 100 / 100])

    my_style_table_header = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),  # third column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # first column
        # ('LEFTPADDING', (2, 0), (2, 0), 180),
        # ('LEFTPADDING', (1, 0), (1, 0), 291),
        # ('BOTTOMPADDING', (0, 0), (3, 0), -20),
        # ('BACKGROUND',  (0, 0), (3, 0), colors.pink)
    ]
    ana_c.setStyle(TableStyle(my_style_table_header))

    td_title = ('FECHA', 'TIPO', 'SERIE', 'NRO.', 'TOTAl\n VENTA',)
    colwiths_table_title = [_bts * 20 / 100,
                            _bts * 20 / 100,
                            _bts * 20 / 100,
                            _bts * 20 / 100,
                            _bts * 20 / 100,
                            ]
    _rows = []
    _rows.append(td_title)

    for op in orders_set:
        order_obj = op.order

        _rows.append((order_obj.traslate_date,
                      order_obj.get_way_to_pay_display(),
                      order_obj.serial,
                      str(order_obj.correlative_sale),
                      order_obj.total))

    ana_c3 = Table(_rows, colWidths=colwiths_table_title)

    detail_style = [
        ('FONTNAME', (0, 0), (-1, -1), 'Square'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (2, 1), (-5, -1), 'Square-Bold'),
        # ('BACKGROUND', (2, 1), (-5, -1), colors.blue),
        ('FONTNAME', (0, 0), (-1, 0), 'Square'),
        ('FONTNAME', (0, 0), (0, -1), 'Square'),
        # ('FONTSIZE', (0, 0), (0, -1), 10),
        ('FONTSIZE', (0, 0), (-1, 0), 9)
    ]
    ana_c3.setStyle(TableStyle(detail_style))

    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=A5,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Reporte de Recepción Encomiendas'
                            )
    dictionary = []
    dictionary.append(ana_c)
    dictionary.append(Spacer(10, 10))
    dictionary.append(ana_c3)
    dictionary.append(Spacer(10, 10))
    response = HttpResponse(content_type='application/pdf')
    doc.build(dictionary)
    response['Content-Disposition'] = 'attachment; filename="ReporteDeRecepcion_[{}].pdf"'.format(_formatdate)
    response.write(buff.getvalue())
    buff.close()
    return response
