from django.contrib import admin, messages
from cmdb.models import Device
from cmdb.utils import getNornir
from nornir.core.task import Task, Result
from nornir_routeros.plugins.tasks import routeros_get

def update_sn(modeladmin, request, queryset):
    # to update sn
    nr = getNornir(queryset)
    # results = nr.run(task=routeros_get, path='/system/routerboard')
    results = nr.run(task=get_sn)
    fail_dev = []
    for k, v in results.items():
        if k in results.failed_hosts.keys():
            fail_dev.append(k)
            print(k,' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                dev = Device.objects.get(name=k)
                if 'serial-number' in i:
                    # dev.model = i['model']
                    dev.sn = i['serial-number']
                elif 'system-id' in i:
                    dev.sn = i['system-id']
                elif 'software-id' in i:
                    dev.sn = i['software-id']
                dev.save()
    success_num = len(queryset) - len(fail_dev)
    messages.info(request, 'update sn successful: {}, failed: {}, failed device: {}'.format(success_num, len(fail_dev), fail_dev))

def get_sn(task: Task) -> Result:
    # /system/routerboard or /system/license
    routerboard_result = task.run(task=routeros_get, path='/system/routerboard')
    routerboard = routerboard_result[0].result[0]['routerboard']
    if routerboard == 'true':
        return Result(host=task.host, result=routerboard_result[0].result)
    elif routerboard == 'false':
        license_result = task.run(task=routeros_get, path='/system/license')
        return Result(host=task.host, result=license_result[0].result)
    else:
        return Result(host=task.host, failed=True, result=f"Unsupported routerboard value: {routerboard}")

def update_version_cpu_model(modeladmin, request, queryset):
    # to update version, cpu and model
    nr = getNornir(queryset)
    results = nr.run(task=routeros_get, path='/system/resource')
    fail_dev = []
    for k, v in results.items():
        if k in results.failed_hosts.keys():
            fail_dev.append(k)
            print(k,' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                dev = Device.objects.get(name=k)
                dev.version = i['version']
                dev.cpu = i['cpu']
                dev.model = i['board-name']
                dev.save()
    success_num = len(queryset) - len(fail_dev)
    messages.info(request, 'update version, cpu and model successful: {}, failed: {}, failed device: {}'.format(success_num, len(fail_dev), fail_dev))

update_sn.short_description = 'Update sn'
update_version_cpu_model.short_description = 'Update version cpu model'


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

admin.site.register(Device, DeviceAdmin)