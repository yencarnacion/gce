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

from gceapi.api import common as gce_common
from gceapi.api import snapshot_api
from gceapi.api import wsgi as gce_wsgi
from gceapi import exception


class Controller(gce_common.Controller):
    """GCE Snapshot controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = snapshot_api.API()

    def _get_type(self):
        return "snapshot"

    def format_item(self, request, snapshot, scope):
        result_dict = {
            "creationTimestamp": self._format_date(snapshot["created_at"]),
            "status": snapshot["status"],
            "diskSizeGb": snapshot["size"],
            "name": snapshot["name"],
            "description": snapshot["display_description"],
            # TODO(apavlov): return hashed from qualify as ID
            "sourceDiskId": snapshot["volume_id"],
            }
        disk = snapshot.get("disk")
        if disk is not None:
            result_dict["sourceDisk"] = self._qualify(
                request, "disks", disk["display_name"],
                gce_common.Scope.create_zone(disk["availability_zone"]))

        return self._format_item(request, result_dict, scope)

    def create(self, req, body, scope):
        raise exception.NotFound


def create_resource():
    return gce_wsgi.GCEResource(Controller())
