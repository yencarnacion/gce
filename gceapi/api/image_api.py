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

import os.path
import tarfile
import tempfile
import urllib2

from nova.api.gce import base_api
from nova import exception
from nova.image import glance


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

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._image_service = glance.get_default_image_service()

    def get_item(self, context, name, scope=None):
        images = self._image_service.detail(context,
            filters={"name": name, "disk_format": "raw"})
        if not images or len(images) == 0:
            msg = _("Image resource '%s' could not be found" % name)
            raise exception.NotFound(msg)
        return self._prepare_item(images[0])

    def get_items(self, context, scope=None):
        images = self._image_service.detail(context,
            filters={"disk_format": "raw"})
        for image in images:
            self._prepare_item(image)
        return images

    def _prepare_item(self, item):
        item["status"] = self._status_map.get(item["status"], item["status"])
        return item

    def delete_item(self, context, name, scope=None):
        """Delete an image, if allowed."""
        image = self._image_service.detail(context, filters={'name': name})[0]
        self._image_service.delete(context, image['id'])

    def add_item(self, context, name, body, scope=None):
        name = body['name']
        image_ref = body['rawDisk']['source']
        resp = urllib2.urlopen(image_ref)
        tar = tempfile.TemporaryFile()
        for line in resp:
            tar.write(line)
        tar.seek(0)
        tar_file = tarfile.open(fileobj=tar)
        member = tar_file.next()
        if member is None:
            msg = _("TAR-file is empty")
            raise exception.InvalidRequest(msg)
        img_filename = member.name
        tar_file.extract(member, tempfile.gettempdir())
        img_filename = os.path.join(tempfile.gettempdir(), img_filename)
        img_file = open(img_filename, 'rb')
        meta = {'name': name,
                'disk_format': 'raw',
                'container_format': 'bare',
                'min_disk': 0,
                'min_ram': 0}
        image = self._image_service.create(context, meta, img_file)

        tar_file.close()
        img_file.close()
        tar.close()
        os.remove(img_filename)
        return self._prepare_item(image)

    def get_item_by_id(self, context, image_id):
        try:
            return self._image_service.show(context, image_id)
        except exception.NotFound:
            return None
