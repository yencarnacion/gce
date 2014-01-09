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
from gceapi.api import scopes
from gceapi import exception
from gceapi.openstack.common import timeutils


class API(base_api.API):
    """GCE operation API"""

    KIND = "operation"
    PERSISTENT_ATTRIBUTES = ["id", "insert_time", "start_time", "end_time",
                             "name", "type", "user", "status", "progress",
                             "scope_type", "scope_name",
                             "target_type", "target_name",
                             "method_key", "item_id", "item_name"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._method_keys = {}
        self._get_progress_methods = {}

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def register_deferred_operation_method(self, method_key, method,
                                           get_progress_method):
        if method_key in self._get_progress_methods:
            raise exception.Invalid()
        # TODO(ft): check 'get_progress_method' formal arguments
        self._method_keys[method] = method_key
        self._get_progress_methods[method_key] = get_progress_method

    def get_scopes(self, context, item):
        return [scopes.Scope(item["scope_type"], item["scope_name"])]

    def get_item(self, context, name, scope=None):
        operation = self._get_db_item_by_name(context, name)
        operation = self._update_operation(context, scope, operation)
        return operation

    def get_items(self, context, scope=None):
        operations = self._get_db_items(context)
        if scope is not None:
            operations = [operation for operation in operations
                          if (operation["scope_type"] == scope.get_type() and
                              operation["scope_name"] == scope.get_name())]
        for operation in operations:
            operation = self._update_operation(context, scope, operation)
        return operations

    def delete_item(self, context, name, scope=None):
        item = self.get_item(context, name, scope)
        if item is None:
            raise exception.NotFound
        self._delete_db_item(context, item)

    def _add_item(self, context, body, scope, method):
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
        method_key = self._method_keys.get(method)
        if method_key is None:
            operation.update(status="DONE", progress=100,
                             end_time=timeutils.isotime(None, True))
        else:
            operation.update(status="RUNNING", progress=0,
                             method_key=method_key)
        return self._add_db_item(context, operation)

    def _update_operation(self, context, scope, operation):
        if operation["status"] == "DONE":
            return operation
        method_key = operation["method_key"]
        get_progress = self._get_progress_methods[method_key]
        operation_progress = get_progress(
                context,
                operation.get("item_name", operation["target_name"]),
                operation["item_id"],
                scope)
        if operation_progress is None:
            return operation
        operation.update(operation_progress)
        if operation["progress"] == 100:
            operation.update(status="DONE",
                             end_time=timeutils.isotime(None, True))
        self._update_db_item(context, operation)
        return operation
