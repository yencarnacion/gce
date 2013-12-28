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

import copy
import uuid

from gceapi.api import base_api
from gceapi import exception
from gceapi.openstack.common import timeutils


class API(base_api.API):
    """GCE operation API"""

    KIND = "operation"
    PERSISTENT_ATTRIBUTES = ["id", "insert_time", "start_time", "end_time",
                             "name", "type", "user", "status", "progress",
                             "scope_type", "scope_name",
                             "target_type", "target_name", "target_id"]

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_scopes(self, context, item):
        return [(item["scope_type"], item["scope_name"])]

    def get_item(self, context, name, scope=None):
        return self._get_db_item_by_name(context, name)

    def get_items(self, context, scope=None):
        operations = self._get_db_items(context)
        if scope is None:
            return operations
        else:
            return [operation for operation in operations
                    if (operation["scope_type"] == scope.get_type() and
                        operation["scope_name"] == scope.get_name())]

    def _add_item(self, context, body, scope):
        operation = copy.copy(body)
        operation_id = str(uuid.uuid4())
        operation.update(id=operation_id,
                         name="operation-" + operation_id,
                         insert_time=timeutils.isotime(context.timestamp,
                                                       True),
                         user=context.user_name)
        if scope is not None:
            operation.update(scope_type=scope.get_type(),
                             scope_name=scope.get_name())
        target_api = base_api.Singleton.get_instance(body["target_type"])
        if target_api._are_api_operations_pending():
            operation.update(status="RUNNING", progress=0)
        else:
            operation.update(status="DONE", progress=100,
                             end_time=timeutils.isotime(None, True))
        return self._add_db_item(context, operation)

    def delete_item(self, context, name, scope=None):
        item = self.get_item(context, name, scope)
        if item is None:
            raise exception.NotFound
        self._delete_db_item(context, item)
