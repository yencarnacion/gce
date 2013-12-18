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
from gceapi.api import clients
from gceapi.api import utils
from gceapi import exception


class API(base_api.API):
    """GCE Image API"""

    _status_map = {
        "queued": "PENDING",
        "saving": "PENDING",
        "active": "READY",
        "killed": "FAILED",
        # "deleted": "",
        # "pending_delete": ""
    }

    def get_item(self, context, name, scope=None):
        image_service = clients.Clients(context).glance().images
        images = image_service.list(
            filters={"name": name, "disk_format": "raw"})
        result = None
        for image in images:
            if result:
                msg = _("Image resource '%s' could not be found" % name)
                raise exception.NotFound(msg)
            result = self._prepare_item(utils.todict(image))
        if not result:
            msg = _("Image resource '%s' could not be found" % name)
            raise exception.NotFound(msg)
        return result

    def get_items(self, context, scope=None):
        image_service = clients.Clients(context).glance().images
        images = image_service.list(filters={"disk_format": "raw"})
        items = list()
        for image in images:
            items.append(self._prepare_item(utils.todict(image)))
        return items

    def _prepare_item(self, item):
        item["status"] = self._status_map.get(item["status"], item["status"])
        return item

    def delete_item(self, context, name, scope=None):
        """Delete an image, if allowed."""
        image = self.get_item(context, name, scope)
        image_service = clients.Clients(context).glance().images
        image_service.delete(image["id"])

    def add_item(self, context, name, body, scope=None):
        name = body['name']
        image_ref = body['rawDisk']['source']
        meta = {
            'name': name,
            'disk_format': 'raw',
            'container_format': 'bare',
            'min_disk': 0,
            'min_ram': 0,
            'copy_from': image_ref,
        }
        image_service = clients.Clients(context).glance().images
        image = image_service.create(**meta)

        return self._prepare_item(utils.todict(image))

    def get_item_by_id(self, context, image_id):
        try:
            image_service = clients.Clients(context).glance().images
            return utils.todict(image_service.get(image_id))
        except exception.NotFound:
            return None
