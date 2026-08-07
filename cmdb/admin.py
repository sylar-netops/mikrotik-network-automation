from cmdb.models import Device
from cmdb.utils import getNornir
from django.contrib import admin
from nornir.core.task import Task, Result
from nornir_routeros.plugins.tasks import routeros_get

from .utils import generic_admin_updater, get_sn_task, _parse_sn_fields, _parse_resource_fields


@admin.action(description='Update SN')
def update_sn(modeladmin, request, queryset):
    # to update sn
    generic_admin_updater(queryset, get_sn_task, _parse_sn_fields, request)


@admin.action(description='Update Version/CPU/Model')
def update_version_cpu_model(modeladmin, request, queryset):
    # to update version, cpu and model
    generic_admin_updater(queryset, None, _parse_resource_fields, request, task_path='/system/resource')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    actions = [update_sn, update_version_cpu_model]
    list_display = ['id', 'name', 'ip', 'version', 'cpu', 'model', 'sn', 'created_time', 'update_time']
    # list_per_page = 15
    search_fields = ['name', 'ip']
    list_display_links = ['id', 'name', 'ip']
    # list_editable = ['name', 'ip']
    # ordering = ['-update_time', 'ip']
    list_filter = ['model', 'version', 'cpu']
    # exclude = ['password']
    fields = ['id', 'name', 'ip', 'version', 'cpu', 'model', 'sn', 'created_time', 'update_time']
    readonly_fields = ['id', 'update_time', 'created_time']
