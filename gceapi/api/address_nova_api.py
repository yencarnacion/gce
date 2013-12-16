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

from gceapi.api import base_api
from gceapi import exception
#from gceapi import network as nova_network


class API(base_api.API):
    """GCE Address API - nova-network implementation"""

    def get_item(self, context, name, scope=None):
        return self._get_floating_ips(context, scope, name)[0]

    def get_items(self, context, scope=None):
        return self._get_floating_ips(context, scope)

    def delete_item(self, context, name, scope=None):
        address = self._get_floating_ips(context, scope, name)
        nova_network.API().release_floating_ip(context, address[0]["address"])

    def add_item(self, context, name, body, scope=None):
        ip = nova_network.API().allocate_floating_ip(context)
        fip = nova_network.API().get_floating_ip_by_address(context, ip)
        return self._prepare_floating_ip(fip, scope)

    def _get_floating_ips(self, context, scope, ip=None):
        results = nova_network.API().get_floating_ips_by_project(context)
        results = [self._prepare_floating_ip(x, scope)
                   for x in results
                   if not x.deleted and context.project_id == x.project_id]

        if ip is None:
            return results

        for item in results:
            if item["name"] == ip:
                return [item]

        raise exception.NotFound

    def _prepare_floating_ip(self, floating_ip, scope):
        result = {
            "fixed_ip_address": floating_ip["fixed_ip"]["address"],
            "floating_ip_address": floating_ip["address"],
            "id": floating_ip["id"],
            "port_id": floating_ip["fixed_ip_id"],
            "tenant_id": floating_ip["project_id"],
            "name": self._generate_floating_ip_name(floating_ip["address"]),
            "scope": scope,
            "status": "IN USE" if floating_ip["fixed_ip_address"]
                      else "RESERVED",
        }
        return result

    # TODO(apavlov): Until we have own DB for gce names translation
    # we should generate new ones. As a result, some clients code may not
    # work correctly.
    def _generate_floating_ip_name(self, ip):
        return "ip-" + ip.replace(".", "-")
