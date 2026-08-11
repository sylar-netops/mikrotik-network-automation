import logging
import os
from typing import Any, Dict, Type

from django.contrib import messages
from django.utils import timezone
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
from nornir.core.task import Task, Result, AggregatedResult
from nornir_routeros.plugins.tasks import routeros_get

from .models import Device

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


InventoryPluginRegister.register('DictInventory', DictInventory)

ROUTEROSAPI = 'routeros'
routerosapi_dict = {'routerosapi': {'extras': {'plaintext_login': True, 'use_ssl': False}}}
mt_user = os.environ.get('MT_USER')
mt_pass = os.environ.get('MT_PASS')


def get_nornir(queryset):
    dev_list = [{'ip': d.ip, 'name': d.name} for d in queryset]
    nr = get_nornir_from_dict(dev_list)
    return nr


def get_nornir_from_dict(dev_list):
    hosts_dict = {}
    for dev in dev_list:
        h = {
            'connection_options': routerosapi_dict,
            'hostname': dev.get('ip'),
            'name': dev.get('name'),
            'password': mt_pass,
            'platform': ROUTEROSAPI,
            'username': mt_user
        }
        hosts_dict[dev.get('name')] = h
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
        logging={
            "enabled": False,
        },
    )
    return nr


def generic_data_cleaner(result: AggregatedResult, parse_callback):
    """
    [General Cleaning Shell]
    :param result: The raw result object returned by Nornir.
    :param parse_callback: A function defining how a single entry is parsed into a dictionary.
    """
    cleaned_data = []

    for host, task_result in result.items():
        # 1. error handling
        if host in result.failed_hosts:
            logger.error(f"Host {host} failed: {task_result.exception}")
            continue

        # 2. data robustness check
        try:
            raw_list = task_result.result
            if not isinstance(raw_list, list):
                continue

            for item in raw_list:
                logger.info(item)
                rinfo = parse_callback(host, item)
                if rinfo:  # Filter out dirty data that might return None
                    cleaned_data.append(rinfo)

        except Exception as e:
            logger.error(f"Error parsing data for host {host}: {str(e)}")

    return cleaned_data


def _parse_route_item(host, i):
    """Extraction rules for routing entries."""
    return {
        'host': host,
        'active': 'true' if i.get('active', -1) == 'true' else 'false',
        'dst-address': i.get('dst-address', 'null'),
        'gateway': i.get('gateway', 'null').replace('<', '&#60;').replace('>', '&#62;'),
        'protocol': next((k for k in ['static', 'connect', 'bgp'] if i.get(k) == 'true'), 'other'),
        'distance': i.get('distance', 'null'),
        'routing-table': i.get('routing-table') or i.get('routing-mark') or 'main',
        'disabled': 'true' if i.get('disabled', -1) == 'true' else 'false'
    }


def get_res_routes(nr):
    result = nr.run(
        task=routeros_get,
        path='/ip/route'
    )
    return generic_data_cleaner(result, parse_callback=_parse_route_item)


def get_bgp_peers(task: Task) -> Result:
    version_result = task.run(task=routeros_get, path='/system/resource')
    version = version_result[0].result[0]['version']

    if version.startswith('6'):
        path = '/routing/bgp/peer'
    elif version.startswith('7'):
        path = '/routing/bgp/session'
    else:
        return Result(host=task.host, failed=True, result=f"Unsupported RouterOS version: {version}")

    bgp_result = task.run(task=routeros_get, path=path)
    return Result(host=task.host, failed=bgp_result.failed, result=bgp_result[0].result)


def _parse_bgp_peer_item(host, i):
    """Extraction rules for BGP neighbor entries."""
    return {
        'host': host,
        'name': i.get('name', 'null'),
        'local-address': i.get('local-address') or i.get('local.address') or 'null',
        'local-as': i.get('local-as') or i.get('local.as') or 'null',
        'remote-address': i.get('remote-address') or i.get('remote.address') or 'null',
        'remote-as': i.get('remote-as') or i.get('remote.as') or 'null',
        'established': i.get('established', 'null')
    }


def get_res_bgp(nr):
    """Clean the retrieved BGP neighbor data."""
    result = nr.run(task=get_bgp_peers)
    return generic_data_cleaner(result, _parse_bgp_peer_item)


def _parse_mangle_item(host, i):
    """Extraction rules for IP Firewall Mangle."""
    # TODO: Incomplete, routing-mark, routing rules
    return {
        'host': host,
        'chain': i.get('chain', 'null'),
        'action': i.get('action', 'null'),
        'src-address': i.get('src-address', 'any'),
        'dst-address': i.get('dst-address', 'any'),
        'comment': i.get('comment', '')
    }


def get_res_mangles(nr):
    result = nr.run(
        task=routeros_get,
        path='/ip/firewall/mangle'
    )
    return generic_data_cleaner(result, _parse_mangle_item)


def generic_admin_updater(queryset, nornir_task, parse_callback, request, task_path=None):
    """
    [Admin Universal Update Shell]
    :param task_path: Pass 'path' if calling 'routeros_get' directly without custom tasks.
    """

    # 1. Run Nornir
    nr = get_nornir(queryset)

    if task_path:
        results = nr.run(task=routeros_get, path=task_path)
    else:
        results = nr.run(task=nornir_task)

    fail_dev = []
    update_list = []  # Staging list for bulk_update
    actual_modified_fields = set()

    # 2. Unified loop & error handling
    for host, task_result in results.items():
        if host in results.failed_hosts:
            fail_dev.append(host)
            logger.error(f"Admin Action failed to update device {host}: {task_result.exception}")
            continue

        try:
            raw_list = task_result.result
            if not raw_list or not isinstance(raw_list, list):
                continue

            # Process data
            dev = Device.objects.get(name=host)
            i = raw_list[0]
            modified_columns = parse_callback(dev, i)
            if modified_columns:
                # Manually add timestamp since bulk_update skips auto_now
                dev.update_time = timezone.now()
                update_list.append(dev)
                actual_modified_fields.update(modified_columns)

        except Exception as e:
            fail_dev.append(host)
            logger.error(f"Crash occurred while parsing/updating database fields for device {host}: {str(e)}")

    # 3. Performance: Use bulk_update for one-time DB write
    if update_list:
        actual_modified_fields.add('update_time')
        fields_to_update = list(actual_modified_fields)
        Device.objects.bulk_update(update_list, fields_to_update)

    # 4. Unified notification alerts
    success_num = len(queryset) - len(fail_dev)
    messages.info(request, f'Update completed. Success: {success_num}, Failed: {len(fail_dev)}. Failed devices: {fail_dev}')


def _parse_sn_fields(dev, i):
    """Extract SN info."""
    sn_val = i.get('serial-number') or i.get('system-id') or i.get('software-id') or 'null'
    dev.sn = sn_val
    return ['sn']


def _parse_resource_fields(dev, i):
    """Extract Version/CPU/Model info."""
    dev.version = i.get('version', 'null')
    dev.cpu = i.get('cpu', 'null')
    dev.model = i.get('board-name', 'null')
    return ['version', 'cpu', 'model']


def get_sn_task(task):
    """Custom Nornir task: Get SN."""
    routerboard_result = task.run(task=routeros_get, path='/system/routerboard')
    if not routerboard_result or not routerboard_result.result:
        return Result(host=task.host, failed=True, result="Failed to get routerboard")

    routerboard = str(routerboard_result.result[0].get('routerboard', 'false'))

    if routerboard == 'true':
        return routerboard_result[0]
    else:
        license_result = task.run(task=routeros_get, path='/system/license')
        return license_result[0]
