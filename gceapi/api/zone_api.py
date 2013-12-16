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
        zones = nova_client.availability_zones.list()
        for zone in zones:
            zone.name = zone.display_name
        return zones
        for zone in available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append({"name": zone,
                              "status": "UP"})
        for zone in not_available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append({"name": zone,
                              "status": "DOWN"})
        return zones

    def get_item_names(self, context, scope=None):
        return [zone.name for zone in self.get_items(context, scope)]

        available_zones, not_available_zones = availability_zones \
            .get_availability_zones(ctxt.get_admin_context())
        zones = []
        for zone in available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append(zone)
        for zone in not_available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append(zone)
        return zones

    def get_item_by_host(self, context, host):
        return availability_zones.get_host_availability_zone(
            ctxt.get_admin_context(), host)
