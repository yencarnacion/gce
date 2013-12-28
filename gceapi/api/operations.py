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
from gceapi.api import operation_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Route controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(operation_api.API(), *args, **kwargs)

    def format_item(self, request, operation, scope):
        return self._format_operation(request, operation, scope)

def create_resource():
    return gce_wsgi.GCEResource(Controller())
