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
from gceapi.api import clients
from gceapi.api import utils
from gceapi import exception


class API(base_api.API):
    """GCE Address API - nova-network implementation"""

    def get_item(self, context, name, scope=None):
        client = clients.Clients(context).nova()
        return self._get_floating_ips(client, context, scope, name)[0]

    def get_items(self, context, scope=None):
        client = clients.Clients(context).nova()
        return self._get_floating_ips(client, context, scope)

    def delete_item(self, context, name, scope=None):
        client = clients.Clients(context).nova()
        floating_ip = self._get_floating_ips(client, context, scope, name)[0]
        client.floating_ips.delete(floating_ip["id"])

    def add_item(self, context, name, body, scope=None):
        client = clients.Clients(context).nova()
        result = client.floating_ips.create()
        return self._prepare_floating_ip(client, context, result, scope)

    def _get_floating_ips(self, client, context, scope, ip=None):
        results = client.floating_ips.list()
        results = [self._prepare_floating_ip(client, context, x, scope)
                   for x in results]

        if ip is None:
            return results

        for item in results:
            if item["name"] == ip:
                return [item]

        raise exception.NotFound

    def _prepare_floating_ip(self, client, context, floating_ip, scope):
        floating_ip = utils.todict(floating_ip)
        fixed_ip = floating_ip.get("fixed_ip")
        result = {
            "fixed_ip_address": fixed_ip if fixed_ip else None,
            "floating_ip_address": floating_ip["ip"],
            "id": floating_ip["id"],
            "port_id": None,
            "tenant_id": context.project_id,
            "name": self._generate_floating_ip_name(floating_ip["ip"]),
            "scope": scope,
            "status": "IN USE" if fixed_ip else "RESERVED",
        }

        instance_id = floating_ip.get("instance_id")
        if instance_id is not None:
            instance = client.servers.get(instance_id)
            result["instance_name"] = instance.name
            result["instance_zone"] = getattr(
                instance, "OS-EXT-AZ:availability_zone")

        return result

    # TODO(apavlov): Until we have own DB for gce names translation
    # we should generate new ones. As a result, some clients code may not
    # work correctly.
    def _generate_floating_ip_name(self, ip):
        return "ip-" + ip.replace(".", "-")
