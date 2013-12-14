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

from nova.api.gce import base_api
from nova.api.gce import zone_api
from nova.compute import instance_types


class API(base_api.API):
    """GCE Machine types API"""

    def get_item(self, context, name, scope=None):
        item = instance_types.get_instance_type_by_name(self._from_gce(name))
        if item:
            item["name"] = self._to_gce(item["name"])
        return item

    def get_items(self, context, scope=None):
        flavors = instance_types.get_all_types(context, filters={})
        items = flavors.values()
        for item in items:
            item["name"] = self._to_gce(item["name"])
        return items

    def get_scopes(self, context, item):
        return zone_api.API().get_item_names(context)

    def _from_gce(self, name):
        return name.replace("-", ".")

    def _to_gce(self, name):
        return name.replace(".", "-")
