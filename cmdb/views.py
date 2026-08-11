import json

from django.http import JsonResponse
from django.shortcuts import render

from .models import Device
from .utils import get_nornir, get_nornir_from_dict, get_res_routes, get_res_bgp


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
    return render(request, 'routes.html', {'url': 'getRoutes', 'devlist': json.dumps(dev_list)})


def mangles(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'mangles.html', {'devlist': json.dumps(dev_list)})


def bgp(request):
    names = request.POST.getlist('name')
    ips = request.POST.getlist('ip')
    dev_list = [{'name': name, 'ip': ip} for name, ip in zip(names, ips)]
    request.session['devices'] = dev_list
    return render(request, 'bgp.html', {'devlist': json.dumps(dev_list)})


def all_routes(request):
    return render(request, 'routes.html', {"url": "getAllRoutes"})


def get_routes(request):
    dev_list = request.session.get('devices', [])
    nr = get_nornir_from_dict(dev_list)
    routes = get_res_routes(nr)
    return JsonResponse({'data': routes})


def get_bgp(request):
    devices_json = request.POST.get('devices_json')
    if not devices_json:
        return JsonResponse({'data': [], 'message': 'devices_json is none'}, status=400)
    dev_list = json.loads(devices_json)
    nr = get_nornir_from_dict(dev_list)
    bgp = get_res_bgp(nr)
    return JsonResponse({'data': bgp})


def get_mangles(request):
    dev_list = request.session.get('devices', [])
    return JsonResponse({'data': []})


def get_all_routes(request):
    # print(time.strftime("%Y-%m-%d %X", time.localtime()))
    nr = get_nornir(Device.objects.all())
    routes = get_res_routes(nr)
    # print(time.strftime("%Y-%m-%d %X", time.localtime()))
    return JsonResponse({'data': routes})
