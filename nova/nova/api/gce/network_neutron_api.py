#    Copyright 2012 Cloudscaling Group, Inc
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

from nova.openstack.common.gettextutils import _
from nova import exception
from nova.network import neutronv2 as neutron
from nova.api.gce import base_api
from nova.api.gce import base_network_api
from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class API(base_network_api.API):
    """GCE Network API - neutron implementation"""

    def get_item(self, context, name, zone_id=None):
        search_opts = {'name': name}
        client = neutron.get_client(context)
        networks = client.list_networks(**search_opts)["networks"]
        if not networks:
            msg = _("Network resource '%s' could not be found." % name)
            raise exception.NotFound(msg)
        else:
            # NOTE(Alex) There might be more than one network with this name.
            # TODO: We have to decide if we should support IDs as parameters
            # for names as well and return error if we have multi-results
            # when addressed by name.
            return self._fill_subnet_info(context, networks[0])

    def get_items(self, context, zone_id=None):
        networks = neutron.get_client(context).list_networks()
        networks = networks["networks"]
        result_networks = []
        for network in networks:
            if network["tenant_id"] != context.project_id:
                continue
            result_networks.append(self._fill_subnet_info(context, network))
        return result_networks

    def delete_item(self, context, name, zone_id=None):
        quantum_api = neutron.get_client(context)
        network = self.get_item(context, name)

        self._process_callbacks(
            context, base_api._callback_reasons.check_delete, network)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, network)

        self._remove_network_from_routers(context, network)
        quantum_api.delete_network(network["id"])

    def add_item(self, context, name, body, zone_id=None):
        ip_range = body['IPv4Range']
        gateway = body.get('gatewayIPv4')
        if gateway is None:
            network_cidr = netaddr.IPNetwork(ip_range)
            gateway_ip = netaddr.IPAddress(network_cidr.first + 1)
            gateway = str(gateway_ip)
        quantum_api = neutron.get_client(context)
        network = None
        try:
            network = self.get_item(context, name)
        except exception.NotFound:
            pass
        if network is not None:
            raise exception.Duplicate
        network_body = {}
        network_body["network"] = {"name": name}
        network = quantum_api.create_network(network_body)
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
            result_data = quantum_api.create_subnet(subnet_body)
            subnet_id = result_data["subnet"]["id"]
            self._add_subnet_to_external_router(context, subnet_id)
        return network

    def format_network(self, network_settings):
        return (network_settings['id'], None, None)

    def _fill_subnet_info(self, context, network):
        subnets = network['subnets']
        if subnets and len(subnets) > 0:
            subnet = neutron.get_client(context).show_subnet(subnets[0])
            subnet = subnet["subnet"]
            network["IPv4Range"] = subnet.get("cidr")
            network["gatewayIPv4"] = subnet.get("gateway_ip")
        return network

    def _add_subnet_to_external_router(self, context, subnet_id):
        routers = neutron.get_client(context).list_routers()
        routers = routers["routers"]
        router = next((r for r in routers
                       if (r["status"] == "ACTIVE" and
                           r["tenant_id"] == context.project_id and
                           r["external_gateway_info"])), None)
        if router is None:
            return
        try:
            neutron.get_client(context).add_interface_router(
                    router["id"], {"subnet_id": subnet_id})
        except Exception:
            LOG.exception("Failed to add subnet (%s) to router (%s)",
                          subnet_id, router["id"])

    def _remove_network_from_routers(self, context, network):
        ports = neutron.get_client(context).list_ports(
                network_id=network["id"])
        for port in ports["ports"]:
            if port["device_owner"] != "network:router_interface":
                continue
            neutron.get_client(context).remove_interface_router(
                    port["device_id"], {"port_id": port["id"]})

