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

from cmdb import views

# 提示：中大型项目应使用 include() 将路由分流到各 APP 内部的 urls.py 中。
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', admin.site.urls),
    path('', views.index),
    path('routes', views.routes),
    path('getRoutes', views.get_routes),
    path('allRoutes', views.all_routes),
    path('getAllRoutes', views.get_all_routes),
    path('mangles', views.mangles),
    path('getMangles', views.get_mangles),
    path('bgp', views.bgp),
    path('getBGP', views.get_bgp),
    path('devices', views.devices),
]


