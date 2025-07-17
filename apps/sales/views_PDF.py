import reportlab
from django.http import HttpResponse
from reportlab.lib.colors import black, white, gray, red, green, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, tables
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4, A5, C7
from reportlab.lib.units import mm, cm, inch
from reportlab.platypus import Table, Flowable
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.colors import PCMYKColor, PCMYKColorSep, Color, black, blue, red, pink, green
from .models import Product, Client, Order, OrderDetail, SubsidiaryStore, ProductStore, Kardex
from django.contrib.auth.models import User
from apps.hrm.views import get_subsidiary_by_user
from .views import get_context_kardex_glp, get_dict_orders
from django.template import loader
from coxman import settings
from datetime import datetime
from django.db.models import Sum
import io
import pdfkit
# Register Fonts
PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']


def product_print(self, pk=None):
    response = HttpResponse(content_type='application/pdf')
    buff = io.BytesIO()
    doc = SimpleDocTemplate(buff,
                            pagesize=letter,
                            rightMargin=40,
                            leftMargin=40,
                            topMargin=60,
                            bottomMargin=18,
                            )
    products = []
    styles = getSampleStyleSheet()
    header = Paragraph("Listado de Productos", styles['Heading1'])
    products.append(header)
    headings = ('Id', 'Descrición', 'Activo', 'Creación')
    if not pk:
        all_products = [(p.id, p.name, p.is_enabled, p.code)
                        for p in Product.objects.all().order_by('pk')]
    else:
        all_products = [(p.id, p.name, p.is_enabled, p.code)
                        for p in Product.objects.filter(id=pk)]
    t = Table([headings] + all_products)
    t.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (3, -1), 1, colors.dodgerblue),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.darkblue),
            ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue)
        ]
    ))

    products.append(t)
    doc.build(products)
    response.write(buff.getvalue())
    buff.close()
    return response


def kardex_glp_pdf(request, pk):
    user_id = request.user.id
    user_obj = User.objects.get(id=user_id)
    subsidiary_obj = get_subsidiary_by_user(user_obj)
    if request.method == 'GET':
        if pk != '':

            html = get_context_kardex_glp(subsidiary_obj, pk, is_pdf=True)
            options = {
                'page-size': 'A3',
                'orientation': 'Landscape',
                'encoding': "UTF-8",
            }
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

            pdf = pdfkit.from_string(html, False, options, configuration=config)
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment;filename="kardex_pdf.pdf"'
            return response


def account_order_list_pdf(request, pk):

    if request.method == 'GET':
        client_obj = Client.objects.get(pk=int(pk))
        order_set = Order.objects.filter(client=client_obj, type='R')

        if pk != '':
            html = get_dict_orders(order_set, client_obj=client_obj, is_pdf=True,)
            options = {
                'page-size': 'A3',
                'orientation': 'Landscape',
                'encoding': "UTF-8",
            }
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

            pdf = pdfkit.from_string(html, False, options, configuration=config)
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment;filename="kardex_pdf.pdf"'
            return response


Title = "Estado de cuentas"
pageinfo = "VICTORIA JUAN GAS S.A.C."
date_now = datetime.now().strftime("%d/%m/%y %H:%M")
# A4 CM 21.0 x 29.7


def all_account_order_list_pdf(self, pk=None):
    buff = io.BytesIO()
    ml = 2.5 * cm
    mr = 2.5 * cm
    ms = 3.0 * cm
    mi = 2.5 * cm
    doc = SimpleDocTemplate(buff,
                            pagesize=A4,
                            rightMargin=mr,
                            leftMargin=ml,
                            topMargin=ms,
                            bottomMargin=mi,
                            title='Estado de cuentas'
                            )
    Story = []

    Story.append(Spacer(1, 50))

    headings = (
        'Id'.upper(),
        'Cliente'.upper(),
        'Pago Faltante (Efectivo)'.upper(),
        'Cantidad Faltante (Fierros)'.upper(),
    )
    all_orders = []

    for c in Client.objects.all().order_by('pk'):

        sum_total_remaining_repay_loan = 0
        sum_total_remaining_return_loan = 0

        order_set = Order.objects.filter(client=c).order_by('id')
        if order_set.count() > 0:
            for o in order_set:
                sum_total_remaining_repay_loan = sum_total_remaining_repay_loan + o.total_remaining_repay_loan()
                sum_total_remaining_return_loan = sum_total_remaining_return_loan + o.total_remaining_return_loan()
        all_orders.append(
            (
                c.id,
                c.names.upper(),
                round(sum_total_remaining_repay_loan, 4),
                round(sum_total_remaining_return_loan, 4),
            )
        )

    t = Table([headings] + all_orders)
    t.setStyle(TableStyle(
        [
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # header
            ('FONTSIZE', (0, 0), (-1, 0), 8),  # header
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # header
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),  # row
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # row
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # row
        ]
    ))
    Story.append(t)
    doc.build(Story, onFirstPage=all_account_order_list_first_page,
              onLaterPages=all_account_order_list_later_pages)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Estado_de_cuentas[{}].pdf"'.format(
        date_now)
    response.write(buff.getvalue())
    buff.close()
    return response


def all_account_order_list_first_page(canvas, doc):
    canvas.saveState()
    canvas.line(2.5 * cm, 26.75 * cm, 18.5 * cm, 26.75 * cm)
    canvas.line(2.5 * cm, 25.5 * cm, 18.5 * cm, 25.5 * cm)
    canvas.line(2.5 * cm, 25.4 * cm, 18.5 * cm, 25.4 * cm)
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title)
    canvas.setFont('Times-Roman', 9)
    canvas.drawString(cm, 0.75 * cm, "Pagina 1 - %s" % pageinfo)
    canvas.drawString(16.5 * cm, 26.25 * cm, date_now)
    canvas.restoreState()


def all_account_order_list_later_pages(canvas, doc):

    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.drawString(cm, 0.75 * cm, "Pagina %d - %s" % (doc.page, pageinfo))
    canvas.restoreState()
