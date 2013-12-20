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
from gceapi.api import zone_api
from gceapi import exception


class API(base_api.API):
    """GCE Machine types API"""

    KIND = "machineType"

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        nova_client = clients.Clients(context).nova()
        try:
            item = nova_client.flavors.find(name=self._from_gce(name))
        except (clients.novaclient.exceptions.NotFound,
                clients.novaclient.exceptions.NoUniqueMatch):
            raise exception.NotFound
        if item:
            item = utils.todict(item)
            item["name"] = self._to_gce(item["name"])
        return item

    def get_items(self, context, scope=None):
        nova_client = clients.Clients(context).nova()
        items = [utils.todict(item) for item in nova_client.flavors.list()]
        for item in items:
            item["name"] = self._to_gce(item["name"])
        return items

    def get_scopes(self, context, item):
        # TODO(apavlov): too slow for all...
        return zone_api.API().get_item_names(context)

    def _from_gce(self, name):
        return name.replace("-", ".")

    def _to_gce(self, name):
        return name.replace(".", "-")
