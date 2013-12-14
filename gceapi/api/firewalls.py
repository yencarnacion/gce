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
from nova.api.gce import firewall_api
from nova.api.gce import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Firewall controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = firewall_api.API()

    def _get_type(self):
        return "firewall"

    def format_item(self, request, firewall, scope):
        result_dict = {
                       # not stored in OpenStack
                       # "creationTimestamp": string,
                       "name": firewall["name"],
                       "description": firewall["description"],
                       "sourceRanges": firewall["sourceRanges"],
                       # not stored in OpenStack
                       # "sourceTags": [
                       #   string
                       # ],
                       # "targetTags": [
                       #   string
                       # ],
                       "allowed": firewall["allowed"]
                       }
        if firewall["network_name"] is not None:
            result_dict["network"] = self._qualify(request,
                "networks", firewall["network_name"],
                gce_common.Scope.create_global())
        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
