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

from nova.compute import flavors as instance_types
from nova.api.gce import base_api
from nova.api.gce import zone_api


class API(base_api.API):
    """GCE Machine types API"""

    def get_item(self, context, name, zone_id=None):
        return instance_types.get_flavor_by_name(name.replace("-", "."))

    def get_items(self, context, zone_id=None):
        flavors = instance_types.get_all_flavors(context, filters={})
        return flavors.values()

    def get_zones(self, context, item):
        return zone_api.API().get_item_names(context)
