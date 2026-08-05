import logging
import os
from typing import Any, Dict, Type

import ping3
from nornir import InitNornir
from nornir.core.inventory import (
    Inventory,
    Group,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
    ParentGroups,
)
from nornir.core.plugins.inventory import InventoryPluginRegister

logger = logging.getLogger(__name__)


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


def _get_defaults(data: Dict[str, Any]) -> Defaults:
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


def _get_inventory_element(
        typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get(
            "groups"
        ),  # this is a hack, we will convert it later to the correct type
        defaults=defaults,
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


class DictInventory:
    def __init__(
            self,
            hosts_dict: Dict[str, Any],
            groups_dict: Dict[str, Any],
            defaults_dict: Dict[str, Any],
    ) -> None:
        """
        DictInventory is an inventory plugin that loads data from Dict.
        follow the same structure as the native objects

        Args:

          hosts_dict: path to file with hosts definition
          groups_dict: path to file with groups definition. If
                it doesn't exist it will be skipped
          defaults_dict: path to file with defaults definition.
                If it doesn't exist it will be skipped
        """

        self.hosts_dict = hosts_dict
        self.groups_dict = groups_dict
        self.defaults_dict = defaults_dict

    def load(self) -> Inventory:

        if self.defaults_dict:
            defaults = _get_defaults(self.defaults_dict)
        else:
            defaults = Defaults()

        hosts = Hosts()
        for n, h in self.hosts_dict.items():
            hosts[n] = _get_inventory_element(Host, h, n, defaults)

        groups = Groups()
        if self.groups_dict:
            for n, g in self.groups_dict.items():
                groups[n] = _get_inventory_element(Group, g, n, defaults)

            for g in groups.values():
                g.groups = ParentGroups([groups[g] for g in g.groups])

        for h in hosts.values():
            h.groups = ParentGroups([groups[g] for g in h.groups])

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)


def single_ping(dev, up_list, down_list, timeout=2):
    ping_time = ping3.ping(dev.ip, timeout=timeout)
    if ping_time:
        up_list.append(dev)
    else:
        down_list.append(dev)


def getNornir(dev_list):
    InventoryPluginRegister.register('DictInventory', DictInventory)
    routerosapi_dict = {'routerosapi': {'extras': {'plaintext_login': True, 'use_ssl': False}}}
    mt_user = os.environ.get('MT_USER')
    mt_pass = os.environ.get('MT_PASS')
    ROUTEROSAPI = 'routeros'
    hosts_dict = {}
    for dev in dev_list:
        h = {}
        h['connection_options'] = routerosapi_dict
        h['hostname'] = dev.ip
        h['name'] = dev.name
        h['password'] = mt_user
        h['platform'] = ROUTEROSAPI
        h['username'] = mt_pass
        hosts_dict[h['name']] = h
    nr = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 100,
            },
        },
        inventory={
            "plugin": "DictInventory",
            "options": {
                "hosts_dict": hosts_dict,
                "groups_dict": {},
                "defaults_dict": {},
            },
        },
    )
    return nr


def getNornirByDict(dev_list):
    InventoryPluginRegister.register('DictInventory', DictInventory)
    routerosapi_dict = {'routerosapi': {'extras': {'plaintext_login': True, 'use_ssl': False}}}
    mt_user = os.environ.get('MT_USER')
    mt_pass = os.environ.get('MT_PASS')
    ROUTEROSAPI = 'routeros'
    hosts_dict = {}
    for dev in dev_list:
        h = {}
        h['connection_options'] = routerosapi_dict
        h['hostname'] = dev['ip']
        h['name'] = dev['name']
        h['password'] = mt_pass
        h['platform'] = ROUTEROSAPI
        h['username'] = mt_user
        hosts_dict[h['name']] = h
    nr = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 100,
            },
        },
        inventory={
            "plugin": "DictInventory",
            "options": {
                "hosts_dict": hosts_dict,
                "groups_dict": {},
                "defaults_dict": {},
            },
        },
    )
    return nr
