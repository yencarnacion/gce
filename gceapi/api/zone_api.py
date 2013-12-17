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
from gceapi import context as ctxt
from gceapi import exception


class API(base_api.BaseScopeAPI):
    """GCE Zones API."""

    COMPUTE_SERVICE = "nova-compute"

    def get_name(self):
        return "zones"

    def get_scope_qualifier(self):
        return "zone"

    def get_item(self, context, name, scope=None):
        zones = self.get_items(context)
        for zone in zones:
            if zone["name"] == name:
                return zone
        raise exception.NotFound

    def get_items(self, context, scope=None):
        nova_client = clients.Clients(context).nova()
        nova_zones = list()
        for zone in nova_client.availability_zones.list():
            for host in zone.hosts:
                if self.COMPUTE_SERVICE in zone.hosts[host]:
                    nova_zones.append(zone)
                    break
        zones = list()
        for zone in nova_zones:
            zones.append({
                "name": zone.zoneName,
                "status": "UP" if zone.zoneState["available"] else "DOWN",
                "hosts": [host for host in zone.hosts]
            })
        return zones

    def get_item_names(self, context, scope=None):
        return [zone["name"] for zone in self.get_items(context, scope)]

    def get_item_by_host(self, context, host):
        zones = self.get_items(context, None)
        for zone in zones:
            if host in zone.hosts:
                return zone
        return None
