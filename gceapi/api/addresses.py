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

from gceapi.api import address_api
from gceapi.api import common as gce_common
from gceapi.api import instance_api
from gceapi.api import region_api
from gceapi.api import wsgi as gce_wsgi
from gceapi.api import zone_api


class Controller(gce_common.Controller):
    """GCE Address controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(scope_api=region_api.API(),
                                         *args, **kwargs)
        self._api = address_api.API()
        self._collection_name = "%ses" % self._type_name

    def _get_type(self):
        return "address"

    def format_item(self, request, floating_ip, scope):
        result_dict = {
            "creationTimestamp": None,
            "status": floating_ip["status"],
            "region": scope.get_name(),
            "name": floating_ip["name"],
            "description": "",
            "address": floating_ip["floating_ip_address"],
        }

        ctx = self._get_context(request)
        fixed_ip_address = floating_ip.get("fixed_ip_address")
        if fixed_ip_address is not None:
            instances = instance_api.API().search_items(
                ctx, {"fixed_ip": fixed_ip_address}, None)
            if instances:
                instance = instances[0]
                zone = instance["OS-EXT-AZ:availability_zone"]
                result_dict["users"] = [self._qualify(
                    request, "instances", instance["name"],
                    gce_common.Scope.create_zone(zone))]

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
