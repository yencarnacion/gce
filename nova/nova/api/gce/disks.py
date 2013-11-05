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

from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import common as gce_common
from nova.api.gce import disk_api


class Controller(gce_common.Controller):
    """GCE Disk controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = disk_api.API()

    def _get_type(self):
        return "disk"

    def basic(self, request, volume, zone_id=None):
        result_dict = {
                "creationTimestamp": self._format_date(volume["created_at"]),
                "status": volume["status"],
                "name": volume["display_name"],
                "description": volume["display_description"],
                "sizeGb": volume["size"],
                }
        snapshot = volume["snapshot"]
        if snapshot:
            result_dict["sourceSnapshot"] = self._qualify(
                    request, "snapshots", snapshot["display_name"], None)
            result_dict["sourceSnapshotId"] = snapshot["id"]
        image = volume.get("image")
        if image:
            result_dict["sourceImage"] = self._qualify(
                    request, "images", image["name"], None)

        return self._format_item(request,
                                 result_dict,
                                 volume["id"],
                                 zone_id)

    def create(self, req, body, zone_id):
        source_image = req.params.get("sourceImage")
        if source_image is not None:
            body["sourceImage"] = source_image
        return super(Controller, self).create(req, body, zone_id)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
