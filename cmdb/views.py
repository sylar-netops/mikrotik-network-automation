from django.http import JsonResponse
from django.shortcuts import render

from cmdb.models import Device
from cmdb.utils import getNornir, getNornirByDict, get_res_routes, get_res_bgp


def index(request):
    return render(request, 'index.html')


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


def mangles(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'mangles.html')


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
