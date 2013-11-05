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

from nova.api.gce import base_network_api
from nova.api.gce import network_nova_api
from nova.api.gce import network_neutron_api
from nova.openstack.common import log as logging
from oslo.config import cfg

LOG = logging.getLogger(__name__)
FLAGS = cfg.CONF


class API(base_network_api.API):
    """GCE Network API"""

    _api = None

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        net_api = FLAGS.get("network_api_class")
        # NOTE(Alex): Initializing proper network singleton
        if net_api is not None and ("quantum" in net_api
                                    or "neutron" in net_api):
            self._api = network_neutron_api.API()
        else:
            self._api = network_nova_api.API()

    def get_item(self, context, name, zone_id=None):
        return self._api.get_item(context, name, zone_id)

    def get_items(self, context, zone_id=None):
        return self._api.get_items(context, zone_id)

    def delete_item(self, context, name, zone_id=None):
        return self._api.delete_item(context, name, zone_id)

    def add_item(self, context, name, body, zone_id=None):
        return self._api.add_item(context, name, body, zone_id)

    def format_network(self, network_settings):
        return self._api.format_network(network_settings)
