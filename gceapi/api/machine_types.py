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
from nova.api.gce import machine_type_api
from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import zone_api


class Controller(gce_common.Controller):
    """GCE Machine types controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(scope_api=zone_api.API(),
                                         *args, **kwargs)
        self._api = machine_type_api.API()

    def _get_type(self):
        return "machineType"

    def format_item(self, request, flavor, scope):
        result_dict = {
            "creationTimestamp": self._format_date(flavor["created_at"]),
            "name": flavor["name"],
            "description": "",
            "guestCpus": flavor["vcpus"],
            "memoryMb": flavor["memory_mb"],
            "imageSpaceGb": flavor["root_gb"],
            # NOTE(Alex): Is not supported by Openstack
            "maximumPersistentDisks": 0,
            # NOTE(Alex): Is not supported by Openstack
            "maximumPersistentDisksSizeGb": 0,
            }

        if flavor["ephemeral_gb"] != 0:
            result_dict["scratchDisks"] = [{"diskGb": flavor["ephemeral_gb"]}]

        # NOTE(Alex): The following code is written but disabled because
        # it seems "deleted" is deprecated now (see comment in
        # db/sqlalchemy/api instance_type_get_all()).
        # And Disabled flag cannot be normally set up via existing APIs.
        #if flavor["deleted"] != 0:
        #    result_dict["deprecated"] = {
        #        "state": "DELETED", "deleted": flavor["deleted_at"]}

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
