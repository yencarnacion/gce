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

from oslo.config import cfg

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import network_api
from gceapi import exception

CONF = cfg.CONF


class API(base_api.API):
    """GCE Address API - neutron implementation"""

    KIND = "address"

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._public_network_name = CONF.public_network

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        return self._get_floating_ips(context, scope, name)[0]

    def get_items(self, context, scope=None):
        return self._get_floating_ips(context, scope)

    def delete_item(self, context, name, scope=None):
        address = self._get_floating_ips(context, scope, name)
        ip_id = address[0]["id"]
        clients.Clients(context).neutron().delete_floatingip(ip_id)

    def add_item(self, context, name, body, scope=None):
        public_network_id = network_api.API().get_public_network_id(context)
        floating_ip = clients.Clients(context).neutron().create_floatingip(
            {"floatingip": {"floating_network_id": public_network_id}})
        return self._prepare_floating_ip(
            context, floating_ip["floatingip"], scope)

    def _get_floating_ips(self, context, scope, ip=None):
        results = clients.Clients(context).neutron().list_floatingips()
        results = results.get("floatingips")
        if results is None:
            return []

        results = [self._prepare_floating_ip(context, x, scope)
                   for x in results
                   if context.project_id == x["tenant_id"]]
        if ip is None:
            return results

        for item in results:
            if item["name"] == ip:
                return [item]

        raise exception.NotFound

    def _prepare_floating_ip(self, context, floating_ip, scope):
        ip = floating_ip["floating_ip_address"]
        floating_ip["name"] = self._generate_floating_ip_name(ip)
        floating_ip["scope"] = scope
        fixed_ip_address = floating_ip.get("fixed_ip_address")
        floating_ip["status"] = "IN USE" if fixed_ip_address else "RESERVED"

        if fixed_ip_address is not None:
            nova_client = clients.Clients(context).nova()
            instances = nova_client.servers.list(
                search_opts={"fixed_ip": fixed_ip_address})
            if instances:
                floating_ip["instance_name"] = instances[0].name
                floating_ip["instance_zone"] = getattr(
                    instances[0], "OS-EXT-AZ:availability_zone")

        return floating_ip

    # TODO(apavlov): Until we have own DB for gce names translation
    # we should generate new ones. As a result, some clients code may not
    # work correctly.
    def _generate_floating_ip_name(self, ip):
        return "ip-" + ip.replace(".", "-")
