from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from apps.hrm import models
# Register your models here.


class DocumentTypeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description', 'short_description', 'is_available')
    ordering = ('id',)
    list_editable = ['is_available', ]


admin.site.register(models.DocumentType, DocumentTypeAdmin)


class DocumentIssuingCountryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.DocumentIssuingCountry, DocumentIssuingCountryAdmin)


class NationalityAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.Nationality, NationalityAdmin)


class RoadTypeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.RoadType, RoadTypeAdmin)


class ZoneTypeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.ZoneType, ZoneTypeAdmin)


class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.Department, DepartmentAdmin)


class ProvinceAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.Province, ProvinceAdmin)


class DistrictAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.District, DistrictAdmin)


class TelephoneNationalLongDistanceCodeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description')
    ordering = ('id',)


admin.site.register(models.TelephoneNationalLongDistanceCode,
                    TelephoneNationalLongDistanceCodeAdmin)


class EmployeeAdmin(ImportExportModelAdmin):
    list_display = ('document_type', 'document_number', 'document_issuing_country',
                    'birthdate', 'paternal_last_name', 'maternal_last_name', 'names')
    ordering = ('paternal_last_name',)


admin.site.register(models.Employee, EmployeeAdmin)


class LaborRegimeAdmin(ImportExportModelAdmin):
    list_display = ('id', 'description', 'short_description',
                    'private_sector', 'public_sector', 'other_entities')
    ordering = ('id',)


admin.site.register(models.LaborRegime, LaborRegimeAdmin)


class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('id', 'business_name', 'ruc',
                    'district', 'short_name')
    ordering = ('id',)


admin.site.register(models.Company, CompanyAdmin)


class SubsidiaryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'short_name')
    ordering = ('id',)
    list_editable = ['name', 'short_name']


admin.site.register(models.Subsidiary, SubsidiaryAdmin)


class CompanyUserAdmin(ImportExportModelAdmin):
    list_display = ('id', 'company_initial', 'company_rotation', 'user')
    ordering = ('id',)


admin.site.register(models.CompanyUser, CompanyUserAdmin)


class SubsidiaryCompanyAdmin(ImportExportModelAdmin):
    ordering = ('id',)
    list_display = (
        'id', 'company', 'subsidiary',
        'serial_voucher_to_passenger', 'correlative_of_vouchers_to_passenger',
        'serial_invoice_to_passenger', 'correlative_of_invoices_to_passenger',
        'serial_two', 'correlative_serial_two',
        'serial_three', 'correlative_serial_three',
        'serial', 'correlative_serial',
        'serial_voucher_to_commodity', 'correlative_of_vouchers_to_commodity',
        'serial_invoice_to_commodity', 'correlative_of_invoices_to_commodity',
        'serial_fourth', 'correlative_serial_fourth', 'short_name',
        'original_name'

    )
    list_editable = [
        'company', 'subsidiary',
        'serial_voucher_to_passenger', 'correlative_of_vouchers_to_passenger',
        'serial_invoice_to_passenger', 'correlative_of_invoices_to_passenger',
        'serial_two', 'correlative_serial_two',
        'serial_three', 'correlative_serial_three',
        'serial', 'correlative_serial',
        'serial_voucher_to_commodity', 'correlative_of_vouchers_to_commodity',
        'serial_invoice_to_commodity', 'correlative_of_invoices_to_commodity',
        'serial_fourth', 'correlative_serial_fourth', 'short_name',
        'original_name'
    ]


admin.site.register(models.SubsidiaryCompany, SubsidiaryCompanyAdmin)


class UserSubsidiaryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'subsidiary', 'user', 'rol', 'office', 'printer')
    ordering = ('id',)
    list_editable = [
        'subsidiary',
        'user',
        'rol',
        'office',
        'printer'
    ]


admin.site.register(models.UserSubsidiary, UserSubsidiaryAdmin)
