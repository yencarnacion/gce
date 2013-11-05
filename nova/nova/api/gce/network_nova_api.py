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
from nova.api.gce import base_api
from nova.api.gce import base_network_api
from nova.openstack.common import log as logging
from nova import network as nova_network

LOG = logging.getLogger(__name__)


class API(base_network_api.API):
    """GCE Network API - nova-network implementation"""

    def get_item(self, context, name, zone_id=None):
        networks = self.get_items(context, zone_id)
        for network in networks:
            if network['name'] == name:
                return network
        msg = _("Network resource '%s' could not be found." % name)
        raise exception.NotFound(msg)

    def get_items(self, context, zone_id=None):
        networks = nova_network.API().get_all(context)
        # networks = networks["networks"]
        result_networks = []
        for network in networks:
            result_network = {'name': network['label'],
                              'IPv4Range': network['cidr'],
                              'gatewayIPv4': network['gateway'],
                              'id': network['id'],
                              'uuid': network['uuid']}
            result_networks.append(result_network)
        #    result_networks.append(self._fill_subnet_info(context, network))
        return result_networks

    def delete_item(self, context, name, zone_id=None):
        network = self.get_item(context, name)
        self._process_callbacks(
            context, base_api._callback_reasons.check_delete, network)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, network)
        nova_network.API().delete(context, network['uuid'])

    def add_item(self, context, name, body, zone_id=None):
        ip_range = body['IPv4Range']
        gateway = body.get('gatewayIPv4')
        if gateway is None:
            network_cidr = netaddr.IPNetwork(ip_range)
            gateway_ip = netaddr.IPAddress(network_cidr.first + 1)
            gateway = str(gateway_ip)
        network = None
        try:
            network = self.get_item(context, name)
        except exception.NotFound:
            pass
        if network is not None:
            raise exception.Duplicate
        kwargs = {'label': name, 'cidr': ip_range, 'gateway': gateway}
        network = nova_network.API().create(context, **kwargs)
        return network

    def format_network(self, network_settings):
        return (network_settings['uuid'], None)
