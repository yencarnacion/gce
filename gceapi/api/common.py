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

"""Base GCE API controller"""

import os.path
import re
from webob import exc

from gceapi.api import operation_api
from gceapi.api import scopes
from gceapi.api import utils
from gceapi import exception
from gceapi.openstack.common import timeutils


class Controller(object):
    """Base controller

    Implements base CRUD methods.
    Individual GCE controllers should inherit this and:
    - implement format_item() method,
    - override _get_type() method,
    - add necessary specific request handlers,
    - use _api to hold instance of related GCE API (see base_api.py).
    """

    _api = None

    # Initialization
    def __init__(self, api):
        """Base initialization.

        Inherited classes should init _api and call super().
        """

        self._api = api
        self._type_name = self._api._get_type()
        self._collection_name = utils.get_collection_name(self._type_name)
        self._type_kind = utils.get_type_kind(self._type_name)
        self._list_kind = utils.get_list_kind(self._type_name)
        self._aggregated_kind = utils.get_aggregated_kind(self._type_name)
        self._operation_api = operation_api.API()

    # Base methods, should be overriden

    def format_item(self, request, image, scope):
        """Main item resource conversion routine

        Overriden in inherited classes should implement conversion of
        OpenStack resource into GCE resource.
        """

        raise exc.HTTPNotImplemented

    # Actions
    def index(self, req, scope_id=None):
        """GCE list requests, global or with zone/region specified."""

        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)

        items = self._api.get_items(context, scope)
        items = [self.format_item(req, i, scope) for i in items]
        items = self._filter_result(req, items)

        return self._format_list(req, items, scope)

    def show(self, req, id=None, scope_id=None):
        """GCE get requests, global or zone/region specified."""

        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        try:
            item = self._api.get_item(context, id, scope)
            return self.format_item(req, item, scope)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Resource '%s' could not be found") % id
            raise exc.HTTPNotFound(explanation=msg)

    def aggregated_list(self, req):
        """GCE aggregated list requests for all zones/regions."""

        items = self._api.get_items(self._get_context(req), None)
        items_by_scopes = {}
        context = self._get_context(req)
        for item in items:
            for scope in self._api.get_scopes(context, item):
                scope_path = scope.get_path()
                items_by_scope = items_by_scopes.setdefault(scope_path,
                    {self._collection_name: []})[self._collection_name]
                items_by_scope.append(self.format_item(req, item, scope))

        for scope in items_by_scopes:
            items = items_by_scopes[scope]
            items_by_scopes[scope][self._collection_name] =\
                self._filter_result(req, items[self._collection_name])

        return self._format_list(req, items_by_scopes,
            scopes.AggregatedScope())

    def delete(self, req, id, scope_id=None):
        """GCE delete requests."""

        start_time = timeutils.isotime(None, True)
        try:
            scope = self._get_scope(req, scope_id)
            context = self._get_context(req)
            item = self._api.delete_item(context, id, scope)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Resource '%s' could not be found") % id
            raise exc.HTTPNotFound(explanation=msg)

        if item is None:
            return None
        else:
            return self._create_operation(req, "delete", scope, start_time,
                                          item["name"], item["id"],
                                          self._api.delete_item)

    def create(self, req, body, scope_id=None):
        """GCE add requests."""

        start_time = timeutils.isotime(None, True)
        scope = self._get_scope(req, scope_id)
        context = self._get_context(req)
        item = self._api.add_item(context, body['name'], body, scope)
        return self._create_operation(req, "insert", scope, start_time,
                                      item["name"], item["id"],
                                      self._api.add_item)

    # Filtering
    def _filter_result(self, req, items):
        """Filtering result list

        Only one filter is supported(eg. by one field)
        Only two comparison strings are supported: 'eq' and 'ne'
        There are no ligical expressions with fields
        """
        if not items:
            return items
        if 'filter' not in req.params:
            return items

        filter_def = req.params['filter'].split()
        if len(filter_def) != 3:
            return items
        if filter_def[1] != 'eq' and filter_def[1] != 'ne':
            return items
        if filter_def[0] not in items[0]:
            return items

        filter_field = filter_def[0]
        filter_cmp = filter_def[1] == 'eq'
        filter_pattern = filter_def[2]
        if filter_pattern[0] == "'" and filter_pattern[-1] == "'":
            filter_pattern = filter_pattern[1:-1]

        result_list = list()
        for item in items:
            field = item[filter_field]
            result = re.match(filter_pattern, field)
            if filter_cmp != (result is None):
                result_list.append(item)

        return result_list

    # Utility
    def _get_context(self, req):
        return req.environ['gceapi.context']

    def _get_scope(self, req, scope_id):
        scope = scopes.construct_from_path(req.path_info, scope_id)
        if scope is None:
            return
        scope_api = scope.get_scope_api()
        if scope_api is not None:
            try:
                context = self._get_context(req)
                scope_api.get_item(context, scope.get_name(), None)
            except ValueError as ex:
                raise exc.HTTPNotFound(detail=ex)

        return scope

    # Result formatting
    def _format_date(self, date_string):
        """Returns standard format for given date."""
        if date_string is None:
            return None
        if isinstance(date_string, basestring):
            date_string = timeutils.parse_isotime(date_string)
        return date_string.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _get_id(self, link):
        hashed_link = hash(link)
        if hashed_link < 0:
            hashed_link = -hashed_link
        return str(hashed_link)

    def _qualify(self, request, controller, identifier, scope):
        """Creates fully qualified selfLink for an item or collection

        Specific formatting for projects and zones/regions,
        'global' prefix For global resources,
        'zones/zone_id' prefix for zone(similar for regions) resources.
        """

        result = os.path.join(
            request.application_url, self._get_context(request).project_name)
        if scope:
            result = os.path.join(result, scope.get_path())
        if controller:
            result = os.path.join(result, controller)
            if identifier:
                result = os.path.join(result, identifier)
        return result

    def _create_operation(self, request, op_type, scope, start_time,
                          target_name, item_id=None, method=None,
                          item_name=None):
        operation = {
            "type": op_type,
            "start_time": start_time,
            "target_type": self._type_name,
            "target_name": target_name,
        }
        if item_id is not None:
            operation["item_id"] = item_id
        if item_name is not None:
            operation["item_name"] = item_name
        operation = self._operation_api._add_item(self._get_context(request),
                                                  operation, scope, method)
        operation = self._format_operation(request, operation, scope)
        return operation

    def _format_operation(self, request, operation, scope):
        result_dict = {
            "name": operation["name"],
            "operationType": operation["type"],
            "insertTime": operation["insert_time"],
            "startTime": operation["start_time"],
            "status": operation["status"],
            "progress": operation["progress"],
            "user": operation["user"],
        }
        result_dict["targetLink"] = self._qualify(
                request, utils.get_collection_name(operation["target_type"]),
                operation["target_name"], scope)
        result_dict["targetId"] = self._get_id(result_dict["targetLink"])
        if "end_time" in operation:
            result_dict["endTime"] = operation["end_time"]
        if scope is None:
            scope = scopes.GlobalScope()
        type_name = self._operation_api._get_type()
        return self._add_item_header(request, result_dict, scope,
                                     utils.get_type_kind(type_name),
                                     utils.get_collection_name(type_name))

    def _format_item(self, request, result_dict, scope):
        return self._add_item_header(request, result_dict, scope,
                                     self._type_kind, self._collection_name)

    def _add_item_header(self, request, result_dict, scope,
                         _type_kind, _collection_name):
        if scope is not None and scope.get_name() is not None:
            result_dict[scope.get_type()] = self._qualify(
                    request, None, None, scope)
        result_dict["kind"] = _type_kind
        result_dict["selfLink"] = self._qualify(
                request, _collection_name, result_dict.get("name"), scope)
        result_dict["id"] = self._get_id(result_dict["selfLink"])
        return result_dict

    def _format_list(self, request, result_list, scope):
        result_dict = {}
        result_dict["items"] = result_list
        result_dict["kind"] = (self._aggregated_kind
            if scope and scope.is_aggregated()
            else self._list_kind)

        context = self._get_context(request)
        list_id = os.path.join("projects", context.project_name)
        if scope:
            list_id = os.path.join(list_id, scope.get_path())
        list_id = os.path.join(list_id, self._collection_name)
        result_dict["id"] = list_id

        result_dict["selfLink"] = self._qualify(
                request, self._collection_name, None, scope)
        return result_dict
