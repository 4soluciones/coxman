from django.db import models
from django.contrib.auth.models import User
from apps.hrm.models import Subsidiary, Employee, SubsidiaryCompany
from apps.sales.models import Client, Product, Unit, SubsidiaryStore
from django.db.models import Sum, Q
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Adjust


# Create your models here.


class Owner(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=100, unique=True)
    associated = models.CharField('Asociado', max_length=100, null=True, blank=True)
    ruc = models.CharField(max_length=11)
    address = models.CharField('Dirección', max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Propietario'
        verbose_name_plural = 'Propietarios'


class TruckBrand(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Marca de tracto'
        verbose_name_plural = 'Marcas de tractos'


class TruckModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, unique=True)
    truck_brand = models.ForeignKey('TruckBrand', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Modelo de tracto'
        verbose_name_plural = 'Modelos de tractos'


class Truck(models.Model):
    DRIVE_TYPE_CHOICES = (('O', 'MINIBUS '), ('C', 'FURGON'), ('S', 'SEMITRAILER'), ('A', 'CAMION'),)
    FUEL_TYPE_CHOICES = (('1', 'DIESEL'), ('2', 'GASOLINA'), ('3', 'GAS'),)
    CONDITION_OWNER_CHOICES = (('P', 'PROPIO'), ('A', 'ALQUILADO'),)
    id = models.AutoField(primary_key=True)
    license_plate = models.CharField('Placa', max_length=10, unique=True)
    num_axle = models.IntegerField('Numero de Ejes', null=True, default=0)
    year = models.CharField('Fabricación', max_length=4, null=True, blank=True)
    truck_model = models.ForeignKey('TruckModel', on_delete=models.SET_NULL, null=True, blank=True)
    drive_type = models.CharField('Tipo de Unidad', max_length=2,
                                  choices=DRIVE_TYPE_CHOICES, default='O')
    plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, null=True, blank=True)
    contact_phone = models.CharField(max_length=45, null=True, blank=True)
    certificate = models.CharField(max_length=15, null=True, blank=True)
    nro_passengers = models.CharField(max_length=2, null=True, blank=True)
    engine = models.CharField('Motor', max_length=100, null=True, blank=True)
    chassis = models.CharField('Chasis', max_length=100, null=True, blank=True)
    color = models.CharField(max_length=45, null=True, blank=True)
    fuel_type = models.CharField('Tipo de Combustible', max_length=1,
                                 choices=FUEL_TYPE_CHOICES, default='1')
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, blank=True)
    condition_owner = models.CharField('Condicion', max_length=1,
                                       choices=CONDITION_OWNER_CHOICES, default='P')
    technical_review_expiration_date = models.DateField('Fecha de expiracion de revisión técnica', null=True,
                                                        blank=True)
    soat_expiration_date = models.DateField('Fecha de expiracion del soat', null=True, blank=True)

    def __str__(self):
        return self.license_plate

    class Meta:
        verbose_name = 'Tracto'
        verbose_name_plural = 'Tractos'


class TruckGallery(models.Model):
    id = models.AutoField(primary_key=True)
    truck = models.ForeignKey('Truck', on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='truck/',
                              default='pic_folder/None/no-img.jpg', blank=True)
    photo_thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(
        800, 400)], source='photo', format='JPEG', options={'quality': 90})
    description = models.CharField('Descripcion', max_length=200, null=True, blank=True)
    sequence = models.IntegerField('Secuencia', null=True, default=0)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Galería de unidad'
        verbose_name_plural = 'Galería de unidades'


class TowingBrand(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Marca de furgon'
        verbose_name_plural = 'Marcas de furgones'


class TowingModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, unique=True)
    towing_brand = models.ForeignKey(
        'TowingBrand', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Modelo de furgon'
        verbose_name_plural = 'Modelos de furgones'


class Towing(models.Model):
    TOWING_TYPE_CHOICES = (('F', 'FURGON'), ('C', 'CISTERNA'), ('P', 'PLATAFORMA'),)
    CONDITION_OWNER_CHOICES = (('P', 'PROPIO'), ('A', 'ALQUILADO'),)
    id = models.AutoField(primary_key=True)
    license_plate = models.CharField('Placa', max_length=10, unique=True)
    num_axle = models.IntegerField('Numero de Ejes', null=True, default=0)
    weight_towing = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    year = models.CharField('Fabricación', max_length=4, null=True, blank=True)
    color = models.CharField(max_length=45, null=True, blank=True)
    denomination = models.CharField(max_length=15, null=True, blank=True)
    towing_model = models.ForeignKey(
        'TowingModel', on_delete=models.SET_NULL, null=True, blank=True)
    towing_type = models.CharField('Condicion', max_length=1,
                                   choices=TOWING_TYPE_CHOICES, default='F')
    is_available = models.BooleanField('Condicion', default=True)
    owner = models.ForeignKey('Owner', on_delete=models.SET_NULL, null=True, blank=True)
    condition_owner = models.CharField('Condicion', max_length=1,
                                       choices=CONDITION_OWNER_CHOICES, default='P')

    def __str__(self):
        return self.license_plate

    class Meta:
        verbose_name = 'Furgon'
        verbose_name_plural = 'Furgones'


class Programming(models.Model):
    STATUS_CHOICES = (('P', 'Programado'), ('R', 'En Ruta'),
                      ('F', 'Finalizado'), ('C', 'Cancelado'))
    TYPE_CHOICES = (('E', 'Encomienda'), ('V', 'Viajes'))
    TURN_CHOICES = (('1', '12:00 AM'),
                    ('2', '12:15 AM'),
                    ('3', '12:30 AM'),
                    ('4', '12:45 AM'),
                    ('5', '01:00 AM'),
                    ('6', '01:15 AM'),
                    ('7', '01:30 AM'),
                    ('8', '01:45 AM'),
                    ('9', '02:00 AM'),
                    ('10', '02:15 AM'),
                    ('11', '02:30 AM'),
                    ('12', '02:45 AM'),
                    ('13', '03:00 AM'),
                    ('14', '03:15 AM'),
                    ('15', '03:30 AM'),
                    ('16', '03:45 AM'),
                    ('17', '04:00 AM'),
                    ('18', '04:15 AM'),
                    ('19', '04:30 AM'),
                    ('20', '04:45 AM'),
                    ('21', '05:00 AM'),
                    ('22', '05:15 AM'),
                    ('23', '05:30 AM'),
                    ('24', '05:45 AM'),
                    ('25', '06:00 AM'),
                    ('26', '06:15 AM'),
                    ('27', '06:30 AM'),
                    ('28', '06:45 AM'),
                    ('29', '07:00 AM'),
                    ('30', '07:15 AM'),
                    ('31', '07:30 AM'),
                    ('32', '07:45 AM'),
                    ('33', '08:00 AM'),
                    ('34', '08:15 AM'),
                    ('35', '08:30 AM'),
                    ('36', '08:45 AM'),
                    ('37', '09:00 AM'),
                    ('38', '09:15 AM'),
                    ('39', '09:30 AM'),
                    ('40', '09:45 AM'),
                    ('41', '10:00 AM'),
                    ('42', '10:15 AM'),
                    ('43', '10:30 AM'),
                    ('44', '10:45 AM'),
                    ('45', '11:00 AM'),
                    ('46', '11:15 AM'),
                    ('47', '11:30 AM'),
                    ('48', '11:45 AM'),
                    ('49', '12:00 PM'),
                    ('50', '12:15 PM'),
                    ('51', '12:30 PM'),
                    ('52', '12:45 PM'),
                    ('53', '01:00 PM'),
                    ('54', '01:15 PM'),
                    ('55', '01:30 PM'),
                    ('56', '01:45 PM'),
                    ('57', '02:00 PM'),
                    ('58', '02:15 PM'),
                    ('59', '02:30 PM'),
                    ('60', '02:45 PM'),
                    ('61', '03:00 PM'),
                    ('62', '03:15 PM'),
                    ('63', '03:30 PM'),
                    ('64', '03:45 PM'),
                    ('65', '04:00 PM'),
                    ('66', '04:15 PM'),
                    ('67', '04:30 PM'),
                    ('68', '04:45 PM'),
                    ('69', '05:00 PM'),
                    ('70', '05:15 PM'),
                    ('71', '05:30 PM'),
                    ('72', '05:45 PM'),
                    ('73', '06:00 PM'),
                    ('74', '06:15 PM'),
                    ('75', '06:30 PM'),
                    ('76', '06:45 PM'),
                    ('77', '07:00 PM'),
                    ('78', '07:15 PM'),
                    ('79', '07:30 PM'),
                    ('80', '07:45 PM'),
                    ('81', '08:00 PM'),
                    ('82', '08:15 PM'),
                    ('83', '08:30 PM'),
                    ('84', '08:45 PM'),
                    ('85', '09:00 PM'),
                    ('86', '09:15 PM'),
                    ('87', '09:30 PM'),
                    ('88', '09:45 PM'),
                    ('89', '10:00 PM'),
                    ('90', '10:15 PM'),
                    ('91', '10:30 PM'),
                    ('92', '10:45 PM'),
                    ('93', '11:00 PM'),
                    ('94', '11:15 PM'),
                    ('95', '11:30 PM'),
                    ('96', '11:45 PM'),)
    id = models.AutoField(primary_key=True)
    departure_date = models.DateField('Fecha Salida', null=True, blank=True)
    arrival_date = models.DateField('Fecha Llegada', null=True, blank=True)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='E', )
    turn = models.CharField('Horario', max_length=2, choices=TURN_CHOICES, default='1', )
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, null=True, )
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    truck = models.ForeignKey('Truck', verbose_name='Tracto',
                              on_delete=models.SET_NULL, null=True, blank=True)
    towing = models.ForeignKey('Towing', verbose_name='Furgon',
                               on_delete=models.SET_NULL, null=True, blank=True)
    subsidiary = models.ForeignKey(Subsidiary, verbose_name='Sede',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    observation = models.CharField(max_length=200, null=True, blank=True)
    order = models.IntegerField('Turno', default=0)
    km_initial = models.CharField('km inicial', max_length=6, null=True, blank=True)
    km_ending = models.CharField('km inicial', max_length=6, null=True, blank=True)
    path = models.ForeignKey('Path', on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    correlative = models.CharField(verbose_name='Correlativo', max_length=45, null=True, blank=True)
    serial = models.CharField(verbose_name='Serie', max_length=4, null=True, blank=True)
    company = models.ForeignKey('hrm.Company', on_delete=models.SET_NULL, null=True, blank=True)
    truck_exit = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # return str(self.subsidiary.name) + "/" + str(self.departure_date)
        return str(self.id)

    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    #
    #     if self.pk is None:
    #         search = SubsidiaryCompany.objects.filter(subsidiary=self.subsidiary, company=self.company)
    #         if search.exists():
    #             subsidiary_company_obj = search.last()
    #             c_three = subsidiary_company_obj.correlative_serial_three
    #             result = 0
    #             c_three = c_three + 1
    #             subsidiary_company_obj.correlative_serial_three = c_three
    #             result = c_three
    #             subsidiary_company_obj.save()
    #             self.correlative = str(result).zfill(6)
    #     super(Programming, self).save(force_insert, force_update, using, update_fields)

    def get_pilot(self):
        set_employee_set = SetEmployee.objects.filter(programming=self.id, function='P')
        pilot = None
        if set_employee_set.count() > 0:
            pilot = set_employee_set.first().employee
        return pilot

    def get_copilot(self):
        set_employee_set = SetEmployee.objects.filter(programming=self.id, function='C')
        copilot = None
        if set_employee_set.count() > 0:
            copilot = set_employee_set.first().employee
        return copilot

    def get_route(self):
        subsidiary_origin_obj = self.get_origin()
        subsidiary_destiny_obj = self.get_destiny()
        return subsidiary_origin_obj.name + " - " + subsidiary_destiny_obj.name

    def get_origin(self):
        return self.path.get_first_point()

    def get_destiny(self):
        return self.path.get_last_point()

    def get_count_seats_sold(self):
        return self.programmingseat_set.filter(status='4').count()

    def get_count_seats_reserved(self):
        return self.programmingseat_set.filter(Q(status='5') | Q(status='6')).count()

    def get_count_seats(self):
        return self.programmingseat_set.count()

    def has_parent(self):
        has_parent = False
        if self.parent is not None:
            has_parent = True
        return has_parent

    def get_total_sold(self):
        response = 0
        programming_seat_set = ProgrammingSeat.objects.filter(programming_id=self.id, status='4')
        for ps in programming_seat_set:
            if ps.order_set.exists():
                from apps.sales.models import Order
                total = Order.objects.filter(programming_seat=ps).values_list('total', flat=True).first()
                response = response + total
        return response

    def get_programming_seat_set(self):
        arr = []
        from apps.sales.models import Order
        order_set = Order.objects.filter(
            programming_seat__programming_id=self.id, programming_seat__status='4', status='C'
        ).order_by('correlative_sale').values(
            'serial', 'correlative_sale', 'client__names', 'create_at', 'total',
            'programming_seat_id', 'programming_seat__plan_detail__name'
        )
        for seat in order_set:
            item = {
                'id': seat['programming_seat_id'],
                'name': seat['programming_seat__plan_detail__name'],
                'serial': seat['serial'],
                'correlative': seat['correlative_sale'],
                'client': seat['client__names'],
                'create_at': seat['create_at'],
                'total': str(seat['total'])
            }
            arr.append(item)
        return arr

    class Meta:
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'


class SetEmployee(models.Model):
    FUNCTION_CHOICES = (('R', 'Responsable'), ('P', 'Piloto'),
                        ('C', 'COPILOTO'), ('E', 'Estibador'),)
    id = models.AutoField(primary_key=True)
    programming = models.ForeignKey('Programming', on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    function = models.CharField('Función', max_length=1, choices=FUNCTION_CHOICES, default='P', )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Cuadrilla'
        verbose_name_plural = 'Cuadrillas'


class GuideMotive(models.Model):
    TYPE_CHOICES = (('E', 'ENTRADA'), ('S', 'SALIDA'))
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='E', )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Motivo'
        verbose_name_plural = 'Motivos'


class Guide(models.Model):
    STATUS_CHOICES = (('1', 'En transito'), ('2', 'Aprobada'), ('3', 'Entregada'), ('4', 'Anulada'), ('5', 'Extraido'),)
    DOCUMENT_TYPE_ATTACHED_CHOICES = (
        ('F', 'Factura'), ('B', 'Boleta'), ('T', 'Guia de Encomienda'),
        ('O', 'Otro'))
    WAY_TO_PAY_CHOICES = (('C', 'AL CONTADO'), ('D', 'PAGO DESTINO'), ('S', 'SERVICIO'), ('O', 'Otro'))
    id = models.AutoField(primary_key=True)
    serial = models.CharField('Serie', max_length=10, null=True, blank=True)
    code = models.CharField('Codigo', max_length=20, null=True, blank=True)
    document_number = models.CharField('Numero de Documento', max_length=20, null=True, blank=True)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='1', )
    document_type_attached = models.CharField('Tipo documento', max_length=1, choices=DOCUMENT_TYPE_ATTACHED_CHOICES,
                                              default='G', )
    minimal_cost = models.DecimalField('Costo minimo', max_digits=10, decimal_places=2, default=0)
    observation = models.CharField(max_length=500, null=True, blank=True)
    user = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    programming = models.ForeignKey('Programming', on_delete=models.SET_NULL, null=True, blank=True)
    guide_motive = models.ForeignKey('GuideMotive', on_delete=models.SET_NULL, null=True, blank=True)
    subsidiary = models.ForeignKey(Subsidiary, verbose_name='Sede', on_delete=models.SET_NULL, null=True, blank=True)
    way_to_pay = models.CharField('Tipo documento', max_length=1, choices=WAY_TO_PAY_CHOICES, default='C', )

    def __str__(self):
        return str(self.serial) + "-" + str(self.code)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.code:
            c = Guide.objects.filter(subsidiary=self.subsidiary,
                                     document_type_attached=self.document_type_attached,
                                     guide_motive=self.guide_motive).last()
            if c:
                character = str(c.code[5:])
                number_without_character = str(c.code[:5])
                character_code = ord(character)

                counter = 0
                for i in range(0, len(number_without_character) - 1):
                    if number_without_character[i:i + 1] != '0':
                        break
                    if number_without_character[i:i + 1] == '0':
                        counter += 1

                numeric_value = int(number_without_character[counter:])

                if numeric_value == 99999:
                    new_numeric_value = 1
                    character_code += 1
                    character = chr(character_code)
                else:
                    new_numeric_value = numeric_value + 1

                result = '0' * (len(number_without_character) - len(str(new_numeric_value))) + \
                         str(new_numeric_value) + str(character)

                self.code = result
            else:
                self.code = '00000A'
        super(Guide, self).save(force_insert, force_update, using, update_fields)

    def get_origin(self):
        origin_set = Route.objects.filter(guide__id=self.id, type='O')
        origin = None
        if origin_set.count() > 0:
            origin = origin_set.last().subsidiary_store
        return origin

    def get_destiny(self):
        destiny_set = Route.objects.filter(guide__id=self.id, type='D')
        destiny = None
        if destiny_set.count() > 0:
            destiny = destiny_set.last().subsidiary_store
        return destiny

    def the_one_that_approves(self):
        guide_employee_set = GuideEmployee.objects.filter(guide__id=self.id, function='A')
        guide_employee = None
        if guide_employee_set.count() > 0:
            guide_employee = guide_employee_set.last()
        return guide_employee

    def the_one_that_requests(self):
        guide_employee_set = GuideEmployee.objects.filter(guide__id=self.id, function='S')
        guide_employee = None
        if guide_employee_set.count() > 0:
            guide_employee = guide_employee_set.last()
        return guide_employee

    def the_one_that_receives(self):
        guide_employee_set = GuideEmployee.objects.filter(guide__id=self.id, function='R')
        guide_employee = None
        if guide_employee_set.count() > 0:
            guide_employee = guide_employee_set.last()
        return guide_employee

    def the_one_that_cancel(self):
        guide_employee_set = GuideEmployee.objects.filter(guide__id=self.id, function='C')
        guide_employee = None
        if guide_employee_set.count() > 0:
            guide_employee = guide_employee_set.last()
        return guide_employee

    def get_serial(self):
        serial = ''
        if self.guide_motive:
            serial = '{}{}'.format(self.guide_motive.type, self.guide_motive.id)
        return serial

    class Meta:
        verbose_name = 'Guia'
        verbose_name_plural = 'Guias'


class GuideDetail(models.Model):
    id = models.AutoField(primary_key=True)
    guide = models.ForeignKey('Guide', on_delete=models.CASCADE)
    description = models.CharField(max_length=500, null=True, blank=True)
    quantity_request = models.DecimalField('Cantidad pedida', max_digits=10, decimal_places=2, default=0)
    quantity_sent = models.DecimalField('Cantidad enviada', max_digits=10, decimal_places=2, default=0)
    quantity = models.DecimalField('Cantidad recibida', max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.guide.code + " - " + str(self.description)

    class Meta:
        verbose_name = 'Detalle guia'
        verbose_name_plural = 'Detalles de guias'


class GuideAction(models.Model):
    TYPE_CHOICES = (('R', 'Remitente'), ('D', 'Destinatario'),)
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    guide = models.ForeignKey('Guide', on_delete=models.CASCADE)
    type = models.CharField('Tipo de Clientes', max_length=1, choices=TYPE_CHOICES, default='R', )


class Route(models.Model):
    TYPE_CHOICES = (('O', 'Origen'), ('D', 'Destino'),)
    id = models.AutoField(primary_key=True)
    programming = models.ForeignKey('Programming', on_delete=models.CASCADE, null=True, blank=True)
    guide = models.ForeignKey('Guide', on_delete=models.CASCADE, null=True, blank=True)
    subsidiary = models.ForeignKey(Subsidiary, verbose_name='Sede', on_delete=models.SET_NULL, null=True, blank=True)
    subsidiary_store = models.ForeignKey(SubsidiaryStore, verbose_name='Almacen', on_delete=models.SET_NULL, null=True,
                                         blank=True)
    type = models.CharField('Tipo de Ruta', max_length=1, choices=TYPE_CHOICES, default='O', )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'


class GuideEmployee(models.Model):
    FUNCTION_CHOICES = (('S', 'Solicita'), ('A', 'Aprueba'),
                        ('R', 'Recibe'), ('C', 'Cancela'), ('E', 'Ejecuta'),)
    id = models.AutoField(primary_key=True)
    guide = models.ForeignKey('Guide', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    function = models.CharField('Función', max_length=1, choices=FUNCTION_CHOICES, default='S', )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Actor'
        verbose_name_plural = 'Actores'


class DistributionMobil(models.Model):
    STATUS_CHOICES = (('P', 'PROGRAMADO'), ('F', 'FINALIZADO'), ('A', 'ANULADO'),)
    id = models.AutoField(primary_key=True)
    truck = models.ForeignKey('Truck', verbose_name='Tracto',
                              on_delete=models.SET_NULL, null=True, blank=True)
    date_distribution = models.DateField('Fecha de Distribucion', null=True, blank=True)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='P', )
    subsidiary = models.ForeignKey(Subsidiary, on_delete=models.SET_NULL, null=True, blank=True)
    pilot = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class DistributionDetail(models.Model):
    STATUS_CHOICES = (('E', 'EGRESO'), ('D', 'DEVOLUCION'),)
    TYPE_CHOICES = (('V', 'VACIOS'), ('L', 'LLENOS'), ('M', 'MALOGRADOS'), ('VM', 'VACIO(S) MALOGRADO(S)'),)
    distribution_mobil = models.ForeignKey(DistributionMobil, on_delete=models.SET_NULL, null=True,
                                           blank=True)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='E', )
    type = models.CharField('Tipo', max_length=2, choices=TYPE_CHOICES, default='L', )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    def calculate_total_b_quantity(self):
        response = DistributionDetail.objects.filter(
            distribution_mobil_id=self.distribution_mobil.id, status='E').values(
            'distribution_mobil').annotate(totals=Sum('quantity'))
        # return response.count
        return response[0].get('totals')


class MantenimentProduct(models.Model):
    STATUS_CHOICES = (('P', 'PROGRAMADO'), ('F', 'FINALIZADO'), ('E', 'EN PROCESO'),)
    TYPE_CHOICES = (('G', 'GRANALLAR'), ('V', 'CAMBIO DE VALVULA'), ('B', 'CAMBIO DE BASE/ASA'),)
    id = models.AutoField(primary_key=True)
    date_programing = models.DateField('Fecha de Programado', null=True, blank=True)
    date_process = models.DateField('Fecha de Inicio', null=True, blank=True)
    date_finish = models.DateField('Fecha de Fianal', null=True, blank=True)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='P', )
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='G', )
    subsidiary = models.ForeignKey(Subsidiary, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person_in_charge = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class MantenimentProductDetail(models.Model):
    TYPE_CHOICES = (('T', 'TRASFUGAR'), ('S', 'SIN TRASFUGAR'),)
    manteniment_product = models.ForeignKey(DistributionMobil, on_delete=models.SET_NULL, null=True,
                                            blank=True)
    id = models.AutoField(primary_key=True)
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='S', )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


class FuelProgramming(models.Model):
    STATUS_CHOICES = (('1', 'EMITIDO'), ('2', 'ANULADO'),)
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey('sales.Product', on_delete=models.CASCADE)
    quantity_fuel = models.DecimalField('Quantity', max_digits=10, decimal_places=2, default=0)
    unit_fuel = models.ForeignKey('sales.Unit', on_delete=models.CASCADE)
    date_fuel = models.DateField('Date', null=True, blank=True)
    programming = models.ForeignKey('Programming', on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey('sales.Supplier', on_delete=models.CASCADE)
    price_fuel = models.DecimalField('Price', max_digits=30, decimal_places=15, default=0)
    status = models.CharField('Estado', max_length=1, choices=STATUS_CHOICES, default='1', )
    subsidiary = models.ForeignKey(Subsidiary, on_delete=models.SET_NULL, null=True, blank=True)
    correlative_fuel = models.CharField('Correlativo', max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def amount(self):
        return self.quantity_fuel * self.price_fuel

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.correlative_fuel:
            c = FuelProgramming.objects.filter(subsidiary=self.subsidiary).last()
            if c:

                number_without_character = str(c.correlative_fuel[:10])

                counter = 0
                for i in range(0, len(number_without_character) - 1):
                    if number_without_character[i:i + 1] != '0':
                        break
                    if number_without_character[i:i + 1] == '0':
                        counter += 1

                numeric_value = int(number_without_character[counter:])

                if numeric_value == 9999999999:
                    new_numeric_value = 1
                else:
                    new_numeric_value = numeric_value + 1

                result = '0' * (len(number_without_character) - len(str(new_numeric_value))) + \
                         str(new_numeric_value)

                self.correlative_fuel = result
            else:
                self.correlative_fuel = '0000000001'
        super(FuelProgramming, self).save(force_insert, force_update, using, update_fields)

    def get_correlative(self):
        code = "C{}".format(self.correlative_fuel)
        return code

    class Meta:
        verbose_name = 'Combustible'
        verbose_name_plural = 'Combustibles'


class Plan(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, null=True, blank=True)
    rows = models.IntegerField('Filas', default=0)
    columns = models.IntegerField('Columnas', default=0)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'


class PlanDetail(models.Model):
    POSITION_CHOICES = (
        ('I', 'Inferior'),
        ('S', 'Superior'),
    )
    TYPE_CHOICES = (
        ('S', 'Asiento'),
        ('D', 'Conductor'),
        ('F', 'Primera puerta'),
        ('S', 'Segunda puerta'),
        ('T', 'Servicios higienicos'),
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=10, null=True, blank=True)
    plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, null=True, blank=True)
    row = models.IntegerField('Fila', default=0)
    column = models.IntegerField('Columna', default=0)
    position = models.CharField('Posicion', max_length=1, choices=POSITION_CHOICES, default='I', )
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='S', )
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Detalle plano'
        verbose_name_plural = 'Detalle de planos'


class ProgrammingSeat(models.Model):
    STATUS_CHOICES = (
        ('1', 'Libre'),
        ('2', 'Ocupado'),
        ('3', 'Vendido sin registrar'),
        ('4', 'Vendido y registrado'),
        ('5', 'Reservar sin nombre'),
        ('6', 'Reservado con nombre'),
        ('7', 'Vendido por otra sede'),
        ('8', 'Asientos proximos a liberarse'),
        ('9', 'Venta con limite de destino'),
        ('10', 'Vendiendo con limite de destino'),
    )
    id = models.AutoField(primary_key=True)
    status = models.CharField('Estado', max_length=2, choices=STATUS_CHOICES, default='1', )
    description = models.CharField('Nombre', max_length=200, null=True, blank=True)
    plan_detail = models.ForeignKey('PlanDetail', on_delete=models.SET_NULL, null=True, blank=True)
    programming = models.ForeignKey('Programming', on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="successors")
    subsidiary_who_puts_limit = models.ForeignKey('hrm.Subsidiary', verbose_name='Sede que pone limite',
                                                  on_delete=models.SET_NULL, null=True, blank=True,
                                                  related_name="who_puts_limit")
    subsidiary_than_sold = models.ForeignKey('hrm.Subsidiary', verbose_name='Sede que Vende', on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name="who_sold")
    subsidiary_than_reserve = models.ForeignKey('hrm.Subsidiary', verbose_name='Sede que Reserva',
                                                on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name="who_reserve")

    def __str__(self):
        return str(self.plan_detail.name)

    def get_destiny_of_order(self):
        destiny = None
        if self.order_set:
            destiny = self.order_set.first().destiny
        return destiny

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'


class Path(models.Model):
    TYPE_CHOICES = (
        ('O', 'Viajes con una parada'),
        ('M', 'Viajes con varias paradas'),
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=200)
    subsidiary = models.ForeignKey('hrm.Subsidiary', verbose_name='Sede', on_delete=models.SET_NULL, null=True,
                                   blank=True)
    type = models.CharField('Planificación de la ruta', max_length=1, choices=TYPE_CHOICES, default='O', )
    company = models.ForeignKey('hrm.Company', on_delete=models.SET_NULL, null=True, blank=True)

    def get_first_point(self):
        point_set = PathDetail.objects.filter(path__id=self.id).order_by('stopping')
        first_point = None
        if point_set.count() > 0:
            first_point = point_set.first().get_origin()
        return first_point

    def get_last_point(self):
        point_set = PathDetail.objects.filter(path__id=self.id).order_by('stopping')
        last_point = None
        if point_set.count() > 0:
            last_point = point_set.last().get_destiny()
        return last_point

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'


class PathDetail(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.ForeignKey('Path', on_delete=models.SET_NULL, null=True, blank=True)
    stopping = models.IntegerField('Parada', default=1)

    def get_origin(self):
        origin_set = PathSubsidiary.objects.filter(path_detail__id=self.id, type='O')
        origin = None
        if origin_set.count() > 0:
            origin = origin_set.last().subsidiary
        return origin

    def get_destiny(self):
        destiny_set = PathSubsidiary.objects.filter(path_detail__id=self.id, type='D')
        destiny = None
        if destiny_set.count() > 0:
            destiny = destiny_set.last().subsidiary
        return destiny

    def __str__(self):
        return str(self.id)

    class Meta:
        # unique_together = ['']
        verbose_name = 'Detalle ruta'
        verbose_name_plural = 'Detalles de rutas'


class PathSubsidiary(models.Model):
    TYPE_CHOICES = (
        ('O', 'Origen'),
        ('D', 'Destino'),
    )
    id = models.AutoField(primary_key=True)
    path_detail = models.ForeignKey('PathDetail', on_delete=models.SET_NULL, null=True, blank=True)
    subsidiary = models.ForeignKey('hrm.Subsidiary', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='O', )

    def __str__(self):
        return str(self.id)

    class Meta:
        # unique_together = ['']
        verbose_name = 'Detalle ruta sede'
        verbose_name_plural = 'Detalles ruta sede'


class Destiny(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, null=True, blank=True)
    path_detail = models.ForeignKey('PathDetail', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def get_initial_subsidiary(self):
        return self.path_detail.get_origin()

    def get_final_subsidiary(self):
        return self.path_detail.get_destiny()

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'


class Origin(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nombre', max_length=45, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Associate(models.Model):
    subsidiary = models.OneToOneField('hrm.Subsidiary', verbose_name='Sede Central', on_delete=models.CASCADE,
                                      primary_key=True)

    def __str__(self):
        return str(self.subsidiary.name)

    class Meta:
        verbose_name = 'Asociado'
        verbose_name_plural = 'Asociados'


class AssociateDetail(models.Model):
    id = models.AutoField(primary_key=True)
    associate = models.ForeignKey('Associate', on_delete=models.CASCADE)
    subsidiary = models.ForeignKey('hrm.Subsidiary', verbose_name='Sede de Acopio', on_delete=models.SET_NULL,
                                   null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Detalle asociado'
        verbose_name_plural = 'Detalle asociados'


class Postponement(models.Model):
    STATUS_CHOICES = (('P', 'Pendiente'), ('C', 'Completado'), ('A', 'Anulado'),)
    PROCESS_CHOICES = (('A', 'Anulación'), ('P', 'Postergación'),)
    id = models.AutoField(primary_key=True)
    subsidiary = models.ForeignKey('hrm.Subsidiary', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, verbose_name='Usuario', on_delete=models.CASCADE)
    status = models.CharField('Tipo', max_length=1, choices=STATUS_CHOICES, default='P', )
    process = models.CharField('Proceso', max_length=1, choices=PROCESS_CHOICES, default='P', )
    reason = models.CharField('Motivo', max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def get_detail_aborted(self):
        detail_aborted_set = PostponementDetail.objects.filter(postponement__id=self.id, type='A')
        detail_aborted = None
        if detail_aborted_set.count() > 0:
            detail_aborted = detail_aborted_set.last()
        return detail_aborted

    def get_detail_rescheduled(self):
        detail_rescheduled_set = PostponementDetail.objects.filter(postponement__id=self.id, type='R')
        detail_rescheduled = None
        if detail_rescheduled_set.count() > 0:
            detail_rescheduled = detail_rescheduled_set.last()
        return detail_rescheduled

    class Meta:
        verbose_name = 'Aplazamiento'
        verbose_name_plural = 'Aplazamientos/Cancelacioness'


class PostponementDetail(models.Model):
    TYPE_CHOICES = (('A', 'Abortado'), ('R', 'Reagendado'),)
    id = models.AutoField(primary_key=True)
    postponement = models.ForeignKey('Postponement', on_delete=models.CASCADE)
    order = models.ForeignKey('sales.Order', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default='A', )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Aplazamiento'
        verbose_name_plural = 'Aplazamientos'


class TruckAssociate(models.Model):
    id = models.AutoField(primary_key=True)
    truck = models.ForeignKey('Truck', on_delete=models.CASCADE)
    employee = models.ForeignKey('hrm.Employee', verbose_name='Piloto Asociado', on_delete=models.SET_NULL, null=True,
                                 blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Pilotos Asociado'
        verbose_name_plural = 'Pilotos Asociados'


class Departure(models.Model):
    id = models.AutoField(primary_key=True)
    truck = models.ForeignKey('Truck', on_delete=models.SET_NULL, null=True, blank=True)
    month = models.IntegerField(null=True, default=0)
    complement = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gps = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    garage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Salida de mes'
        verbose_name_plural = 'Salidas de mes'


class DepartureDetail(models.Model):
    departure = models.ForeignKey('Departure', on_delete=models.SET_NULL, null=True, blank=True)
    register_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.id)
