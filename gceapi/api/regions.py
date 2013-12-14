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

from nova.api.gce import common as gce_common
from nova.api.gce import region_api
from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import zone_api


class Controller(gce_common.Controller):
    """GCE Regions controller."""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = region_api.API()
        self._zone_api = zone_api.API()

    def _get_type(self):
        return "region"

    def format_item(self, req, region, scope):
        zones = self._zone_api.get_item_names(self._get_context(req), scope)
        result_dict = {
            "name": region["name"],
            "status": "UP",
            "zones": [self._qualify(req, "zones", zone, None)
                      for zone in zones]
        }

        return self._format_item(req, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
