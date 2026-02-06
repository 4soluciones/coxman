from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from imagekit.admin import AdminThumbnail
from apps.comercial import models
# Register your models here.


class TowingBrandAdmin(ImportExportModelAdmin):
    list_display = ('name',)


admin.site.register(models.TowingBrand, TowingBrandAdmin)


class TowingModelAdmin(ImportExportModelAdmin):
    list_display = ('name', 'towing_brand')


admin.site.register(models.TowingModel, TowingModelAdmin)


class TruckBrandAdmin(ImportExportModelAdmin):
    list_display = ('name',)


admin.site.register(models.TruckBrand, TruckBrandAdmin)


class TruckModelAdmin(ImportExportModelAdmin):
    list_display = ('name', 'truck_brand')


admin.site.register(models.TruckModel, TruckModelAdmin)


class OwnerAdmin(ImportExportModelAdmin):
    list_display = ('name',)


admin.site.register(models.Owner, OwnerAdmin)


class PlanAdmin(ImportExportModelAdmin):
    list_display = ('name', 'rows', 'columns',)


admin.site.register(models.Plan, PlanAdmin)


class PlanDetailAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'plan', 'row', 'column', 'position', 'type', 'is_enabled',)
    ordering = ('id',)
    list_filter = ('plan', 'type', 'position')
    list_editable = ['name', 'row', 'column', 'plan', 'position', 'type', 'is_enabled',]


admin.site.register(models.PlanDetail, PlanDetailAdmin)


class PathSubsidiaryAdmin(ImportExportModelAdmin):
    list_display = ('path_detail', 'subsidiary', 'type',)
    ordering = ('id',)


admin.site.register(models.PathSubsidiary, PathSubsidiaryAdmin)


class DestinyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'path_detail',)
    ordering = ('id',)


admin.site.register(models.Destiny, DestinyAdmin)


class TruckGalleryAdmin(ImportExportModelAdmin):
    list_display = ('truck', 'photo', 'description', 'sequence', 'admin_thumbnail')
    admin_thumbnail = AdminThumbnail(image_field='photo_thumbnail')
    list_editable = ['description', 'photo', 'sequence']
    ordering = ('sequence',)


admin.site.register(models.TruckGallery, TruckGalleryAdmin)
