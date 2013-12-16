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
from gceapi.api import network_neutron_api
from gceapi.api import network_nova_api


class API(base_api.BaseNetAPI):
    """GCE Network API"""

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(
            network_neutron_api, network_nova_api, *args, **kwargs)

    # For quantumv2, requested_networks(for instance creation)
    # should be tuple of (network_uuid, fixed_ip, port_id)
    def format_network(self, network_settings):
        return self._api.format_network(network_settings)
