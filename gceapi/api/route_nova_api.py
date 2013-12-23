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
from gceapi import exception


NOT_SUPPORTED_MESSAGE = _("Routes are not supported with nova network")


class API(base_api.API):
    """GCE Address API - nova-network implementation"""

    def get_item(self, context, name, scope_id=None):
        raise exception.InvalidInput(reason=NOT_SUPPORTED_MESSAGE)

    def get_items(self, context, scope_id=None):
        raise exception.InvalidInput(reason=NOT_SUPPORTED_MESSAGE)

    def delete_item(self, context, name, scope_id=None):
        raise exception.InvalidInput(reason=NOT_SUPPORTED_MESSAGE)

    def add_item(self, context, name, body, scope_id=None):
        raise exception.InvalidInput(reason=NOT_SUPPORTED_MESSAGE)
