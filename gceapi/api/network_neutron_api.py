#    Copyright 2013 Cloudscaling Group, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import netaddr

from gceapi.openstack.common.gettextutils import _
from gceapi import exception
from gceapi.api import clients
from gceapi.api import base_api
from gceapi.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Network API - neutron implementation"""

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)

    def get_item(self, context, name, scope=None):
        search_opts = {'name': name}
        client = clients.Clients(context).neutron()
        networks = client.list_networks(**search_opts)["networks"]
        if not networks:
            msg = _("Network resource '%s' could not be found." % name)
            raise exception.NotFound(msg)
        else:
            # NOTE(Alex) There might be more than one network with this name.
            # TODO: We have to decide if we should support IDs as parameters
            # for names as well and return error if we have multi-results
            # when addressed by name.
            return self._prepare_network(context, networks[0])

    def get_items(self, context, scope=None):
        networks = clients.Clients(context).neutron().list_networks()
        networks = networks["networks"]
        result_networks = []
        for network in networks:
            if network["tenant_id"] != context.project_id:
                continue
            result_networks.append(self._prepare_network(context, network))
        return result_networks

    def delete_item(self, context, name, scope=None):
        neutron_api = clients.Clients(context).neutron()
        network = self.get_item(context, name)

        self._process_callbacks(
            context, base_api._callback_reasons.check_delete, network)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, network)

        self._remove_network_from_routers(context, network)
        neutron_api.delete_network(network["id"])

    def add_item(self, context, name, body, scope=None):
        ip_range = body['IPv4Range']
        gateway = body.get('gatewayIPv4')
        if gateway is None:
            network_cidr = netaddr.IPNetwork(ip_range)
            gateway_ip = netaddr.IPAddress(network_cidr.first + 1)
            gateway = str(gateway_ip)
        neutron_api = clients.Clients(context).neutron()
        network = None
        try:
            network = self.get_item(context, name)
        except exception.NotFound:
            pass
        if network is not None:
            raise exception.DuplicateVlan
        network_body = {}
        network_body["network"] = {"name": name}
        network = neutron_api.create_network(network_body)
        network = network["network"]
        if ip_range:
            subnet_body = {}
            subnet_body["subnet"] = {
                # NOTE(Alex) "name": name + ".default_subnet",
                # Won't give it a name for now
                "network_id": network["id"],
                "ip_version": "4",
                "cidr": ip_range,
                "gateway_ip": gateway}
            result_data = neutron_api.create_subnet(subnet_body)
            subnet_id = result_data["subnet"]["id"]
            self._add_subnet_to_external_router(context, subnet_id)

        return self._prepare_network(context, network)

    def format_network(self, network_settings):
        return (network_settings['id'], None, None)

    def _prepare_network(self, context, network):
        subnets = network['subnets']
        if subnets and len(subnets) > 0:
            subnet = clients.Clients(context).neutron().show_subnet(subnets[0])
            subnet = subnet["subnet"]
            network["IPv4Range"] = subnet.get("cidr", None)
            network["gatewayIPv4"] = subnet.get("gateway_ip", None)
        return network

    def _add_subnet_to_external_router(self, context, subnet_id):
        routers = clients.Clients(context).neutron().list_routers()
        routers = routers["routers"]
        router = next((r for r in routers
                       if (r["status"] == "ACTIVE" and
                           r["tenant_id"] == context.project_id and
                           r["external_gateway_info"])), None)
        if router is None:
            return
        try:
            clients.Clients(context).neutron().add_interface_router(
                    router["id"], {"subnet_id": subnet_id})
        except Exception:
            LOG.exception("Failed to add subnet (%s) to router (%s)",
                          subnet_id, router["id"])

    def _remove_network_from_routers(self, context, network):
        ports = clients.Clients(context).neutron().list_ports(
                network_id=network["id"])
        for port in ports["ports"]:
            if port["device_owner"] != "network:router_interface":
                continue
            clients.Clients(context).neutron().remove_interface_router(
                    port["device_id"], {"port_id": port["id"]})
