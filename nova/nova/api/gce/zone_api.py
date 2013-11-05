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

from oslo.config import cfg

from nova import exception
from nova import availability_zones
from nova import context as ctxt

from nova.api.gce import base_api


CONF = cfg.CONF


class API(base_api.API):
    """GCE Zones API"""

    def get_item(self, context, name, dummy=None):
        zones = self.get_items(context)
        for zone in zones:
            if zone["name"] == name:
                return zone
        raise exception.NotFound

    def get_items(self, context, dummy=None):
        available_zones, not_available_zones = availability_zones \
            .get_availability_zones(ctxt.get_admin_context())
        zones = []
        for zone in available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append({"name": zone,
                              "status": "UP"})
        for zone in not_available_zones:
            if zone != CONF.internal_service_availability_zone:
                zones.append({"name": zone,
                              "status": "DOWN"})
        return zones

    def get_item_names(self, context, dummy=None):
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
