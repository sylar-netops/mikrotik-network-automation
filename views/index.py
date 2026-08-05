from django.http import JsonResponse
from django.shortcuts import render
from nornir.core.task import Task, Result
from nornir_routeros.plugins.tasks import routeros_get

from cmdb.models import Device
from views.tool import getNornir, getNornirByDict


def index(request):
    return render(request, 'index.html')


def temp(request):
    # print(request.POST.getlist('name'))
    # print(request.POST.getlist('ip'))
    return render(request, 'temp.html', {'temp': request.POST.getlist('name')})


def devices(request):
    results = Device.objects.all()
    dev_list = []
    for i in results:
        if not i.model:
            i.model = 'null'
        if not i.sn:
            i.sn = 'null'
        dev_list.append(dict(i))
    return JsonResponse({'data': dev_list})


def routes(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'routes.html', {'url': 'getRoutes'})


def connections(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'connections.html', {'name': dev_list[0]['name'], 'ip': dev_list[0]['ip']})


def eoips(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'eoips.html')


def mangles(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'mangles.html')


def ppp(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'ppp.html')


def bgp(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'bgp.html')


def all_routes(request):
    return render(request, 'routes.html', {"url": "getAllRoutes"})


def get_routes(request):
    dev_list = request.session.get('devices', [])
    nr = getNornirByDict(dev_list)
    routes = get_res_routes(nr)
    return JsonResponse({'data': routes})


def get_connections(request):
    dev_list = request.session.get('devices', [])
    nr = getNornirByDict(dev_list)
    conns = get_res_conns(nr)
    return JsonResponse({'data': conns})


def get_eoips(request):
    dev_list = request.session.get('devices', [])
    nr = getNornirByDict(dev_list)
    eoips = get_res_eoips(nr)
    return JsonResponse({'data': eoips})


def get_ppp(request):
    dev_list = request.session.get('devices', [])
    nr = getNornirByDict(dev_list)
    ppp = get_res_ppp(nr)
    return JsonResponse({'data': ppp})


def get_bgp(request):
    dev_list = request.session.get('devices', [])
    nr = getNornirByDict(dev_list)
    bgp = get_res_bgp(nr)
    return JsonResponse({'data': bgp})


def get_mangles(request):
    dev_list = request.session.get('devices', [])
    return JsonResponse({'data': []})


def get_all_routes(request):
    # print(time.strftime("%Y-%m-%d %X", time.localtime()))
    nr = getNornir(Device.objects.all())
    routes = get_res_routes(nr)
    # print(time.strftime("%Y-%m-%d %X", time.localtime()))
    return JsonResponse({'data': routes})


def get_res_routes(nr):
    result = nr.run(
        task=routeros_get,
        path='/ip/route'
    )
    routes = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                rinfo = {}
                rinfo['host'] = k
                rinfo['active'] = 'true' if i.get('active', -1) == 'true' else 'false'
                rinfo['dst-address'] = i['dst-address']
                rinfo['gateway'] = i['gateway'].replace('<', '&#60;').replace('>', '&#62;') if '<' in i['gateway'] else \
                    i['gateway']
                rinfo['protocol'] = 'static' if i.get('static', -1) == 'true' else 'connect' if i.get('connect',
                                                                                                      -1) == 'true' else 'bgp'
                rinfo['distance'] = i['distance']
                # A if 条件1 else (B if 条件2 else C)
                rinfo['routing-table'] = i['routing-table'] if i.get('routing-table', -1) != -1 else 'main' if i.get(
                    'routing-mark', -1) == -1 else i['routing-mark']
                rinfo['disabled'] = 'true' if i.get('disabled', -1) == 'true' else 'false'
                routes.append(rinfo)
    return routes


def get_res_conns(nr):
    result = nr.run(
        task=routeros_get,
        path='/ip/firewall/connection'
    )
    data = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            data = list(v[0].result)
    return data


def get_res_eoips(nr):
    result = nr.run(
        task=routeros_get,
        path='/interface/eoip'
    )
    data = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                rinfo = {}
                rinfo['host'] = k
                rinfo['name'] = i['name']
                rinfo['local-address'] = i['local-address']
                rinfo['remote-address'] = i['remote-address']
                rinfo['tunnel-id'] = i['tunnel-id']
                rinfo['keepalive'] = i['keepalive'] if i.get('keepalive', -1) != -1 else 'none'
                rinfo['running'] = i['running']
                rinfo['disabled'] = i['disabled']
                data.append(rinfo)
    return data


def get_res_ppp(nr):
    result = nr.run(
        task=routeros_get,
        path='/ppp/secret'
    )
    data = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                rinfo = {}
                rinfo['host'] = k
                rinfo['name'] = i['name']
                rinfo['local-address'] = i['local-address']
                rinfo['remote-address'] = i['remote-address']
                rinfo['service'] = i['service']
                rinfo['disabled'] = i['disabled']
                data.append(rinfo)
    return data


def get_res_bgp(nr):
    result = nr.run(task=get_bgp_peers)
    data = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                rinfo = {}
                rinfo['host'] = k
                rinfo['name'] = i['name']
                rinfo['remote-address'] = i['remote-address'] if 'remote-address' in i else i[
                    'remote.address'] if 'remote.address' in i else 'null'
                rinfo['remote-as'] = i['remote-as'] if 'remote-as' in i else i[
                    'remote.as'] if 'remote.as' in i else 'null'
                rinfo['out-filter'] = i['out-filter'] if 'out-filter' in i else i[
                    'output.filter-chain'] if 'output.filter-chain' in i else 'null'
                rinfo['in-filter'] = i['in-filter'] if 'in-filter' in i else i[
                    'in.filter'] if 'in.filter' in i else 'null'
                rinfo['disabled'] = i['disabled'] if 'disabled' in i else i['inactive']
                data.append(rinfo)
    return data


def get_bgp_peers(task: Task) -> Result:
    # 获取设备的 RouterOS 版本
    version_result = task.run(task=routeros_get, path='/system/resource')
    version = version_result[0].result[0]['version']
    # 根据版本选择不同的 BGP 命令
    if version.startswith('6'):
        path = '/routing/bgp/peer'
    elif version.startswith('7'):
        path = '/routing/bgp/connection'
    else:
        return Result(host=task.host, failed=True, result=f"Unsupported RouterOS version: {version}")

    # 获取 BGP 对等体信息
    bgp_result = task.run(task=routeros_get, path=path)
    return Result(host=task.host, result=bgp_result[0].result)


def get_res_mangles(nr):
    result = nr.run(
        task=routeros_get,
        path='/ip/firewall/mangle'
    )
    data = []
    for k, v in result.items():
        if k in result.failed_hosts.keys():
            print(k, ' error')
            print(v.exception)
        else:
            for i in list(v[0].result):
                rinfo = {}
                rinfo['host'] = k
                rinfo['active'] = 'true' if i.get('active', -1) == 'true' else 'false'
                rinfo['dst-address'] = i['dst-address']
                rinfo['gateway'] = i['gateway'].replace('<', '&#60;').replace('>', '&#62;') if '<' in i['gateway'] else \
                    i['gateway']
                # print(rinfo['gateway'])
                rinfo['protocol'] = 'static' if i.get('static', -1) == 'true' else 'connect' if i.get('connect',
                                                                                                      -1) == 'true' else 'bgp'
                rinfo['distance'] = i['distance']
                rinfo['routing-table'] = i['routing-table'] if i.get('routing-table', -1) != -1 else 'main' if i.get(
                    'routing-mark', -1) == -1 else i['routing-mark']
                rinfo['disabled'] = 'true' if i.get('disabled', -1) == 'true' else 'false'
                data.append(rinfo)
    return data
