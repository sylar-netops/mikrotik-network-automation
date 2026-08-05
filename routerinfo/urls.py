"""routerinfo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', admin.site.urls),
    path('', index.index),
    path('routes', index.routes),
    path('getRoutes', index.get_routes),
    path('allRoutes', index.all_routes),
    path('getAllRoutes', index.get_all_routes),
    path('connections', index.connections),
    path('getConnections', index.get_connections),
    path('eoips', index.eoips),
    path('getEOIPs', index.get_eoips),
    path('mangles', index.mangles),
    path('getMangles', index.get_mangles),
    path('ppp', index.ppp),
    path('getPPP', index.get_ppp),
    path('bgp', index.bgp),
    path('getBGP', index.get_bgp),
    path('devices', index.devices),
    path('temp', index.temp),
]


