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

from nova.api.gce import common as gce_common
from nova.api.gce import wsgi as gce_wsgi
from nova.api.gce import kernel_api


class Controller(gce_common.Controller):
    """GCE Kernel controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._api = kernel_api.API()

    def _get_type(self):
        return "kernel"

    def basic(self, request, kernel, zone_id):
        result_dict = {
            "creationTimestamp": self._format_date(kernel["created_at"]),
            "name": kernel["name"],
            "description": kernel["description"],
        }

        return self._format_item(request,
                                 result_dict,
                                 kernel["id"],
                                 zone_id
                                 )


def create_resource():
    return gce_wsgi.GCEResource(Controller())
