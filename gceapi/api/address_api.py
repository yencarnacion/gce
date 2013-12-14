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

from nova.api.gce import address_neutron_api
from nova.api.gce import address_nova_api
from nova.api.gce import base_api
from nova.api.gce import region_api


class API(base_api.BaseNetAPI):
    """GCE Address API"""

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(
            address_neutron_api, address_nova_api, *args, **kwargs)

    def get_scopes(self, context, item):
        region = item["scope"]
        if region is not None:
            return [region]
        return [item["name"] for item in region_api.API().get_items(context)]
