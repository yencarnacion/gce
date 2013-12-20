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
from webob import exc

from gceapi import exception
from gceapi.openstack.common.rpc import common as rpc_common
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
    def __init__(self, api, scope_api=None):
        """Base initialization.

        Inherited classes should init _api and call super().
        """

        self._api = api
        self._scope_api = scope_api
        self._type_name = self._api._get_type()
        self._collection_name = "%ss" % self._type_name
        self._type_kind = "compute#%s" % self._type_name
        self._list_kind = "compute#%sList" % self._type_name
        self._aggregated_kind = "compute#%sAggregatedList" % self._type_name

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
        filter_name = self._get_filtering_name(req)
        result_list = list()
        for item in items:
            if not filter_name or item["name"] == filter_name:
                result_list.append(self.format_item(req, item, scope))

        return self._format_list(req, result_list, scope)

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

        filter_name = self._get_filtering_name(req)
        items = self._api.get_items(self._get_context(req), None)
        items_by_scopes = {}
        context = self._get_context(req)
        for item in items:
            if filter_name and item["name"] != filter_name:
                continue

            scopes = self._api.get_scopes(context, item)
            for scope_name in scopes:
                az = os.path.join(self._scope_api.get_name(), scope_name)
                items_by_scope = items_by_scopes.setdefault(
                    az, {self._collection_name: []})[self._collection_name]
                scope = Scope(self._scope_api.get_name(), scope_name)
                items_by_scope.append(self.format_item(req, item, scope))
        return self._format_list(req, items_by_scopes,
            Scope.create_aggregated())

    def delete(self, req, id, scope_id=None):
        """GCE delete requests."""

        try:
            scope = self._get_scope(req, scope_id)
            self._api.delete_item(self._get_context(req), id, scope)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Resource '%s' could not be found") % id
            raise exc.HTTPNotFound(explanation=msg)

        return self._format_operation(req, id, "delete", scope)

    def create(self, req, body, scope_id=None):
        """GCE add requests."""

        name = body['name']
        try:
            scope = self._get_scope(req, scope_id)
            item = self._api.add_item(
                self._get_context(req), name, body, scope)
            return self._format_operation(
                req, item["name"], "insert", scope)
        except rpc_common.RemoteError as err:
            raise exc.HTTPInternalServerError(explanation=err.message)

    # Utility
    def _get_context(self, req):
        return req.environ['gceapi.context']

    def _get_scope(self, req, scope_id):
        scope = Scope.construct(req, scope_id)
        if scope and self._scope_api:
            try:
                context = self._get_context(req)
                self._scope_api.get_item(context, scope.get_name(), None)
            except ValueError as ex:
                raise exc.HTTPNotFound(detail=ex)

        return scope

    def _get_filtering_name(self, request):
        if 'filter' not in request.params:
            return None

        filter_def = request.params['filter'].split()
        if (len(filter_def) != 3 or filter_def[0] != 'name'
                or filter_def[1] != 'eq'):
            return None

        return filter_def[2]

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

    def _format_operation(self, request, item_id, op_type, scope):
        target_link = self._qualify(request, self._collection_name,
                                    item_id, scope)
        op_scope = scope if scope else Scope.create_global()
        self_link = self._qualify(request, "operations", "stub", op_scope)
        result_dict = {
           "kind": "compute#operation",
           "id": "0",
           "name": "stub",
           "status": "DONE",
           "selfLink": self_link,
           "targetLink": target_link,
           "targetId": self._get_id(target_link),
           "operationType": op_type,
           "progress": 100,
        }
        if self._scope_api is not None:
            scope_name = self._scope_api.get_scope_qualifier()
            result_dict[scope_name] = self._qualify(request,
                scope.get_type(), scope.get_name(), None)
        return result_dict

    def _format_item(self, request, result_dict, scope):
        if self._scope_api is not None:
            result_dict[self._scope_api.get_scope_qualifier()] = self._qualify(
                request, scope.get_type(), scope.get_name(), None)
        result_dict["kind"] = self._type_kind
        result_dict["selfLink"] = self._qualify(request,
            self._collection_name, result_dict.get("name"), scope)
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

        result_dict["selfLink"] = self._qualify(request,
            self._collection_name, None, scope)
        return result_dict


class Scope(object):
    """Scope that contains resource.

    The following scopes exists: global, aggregated, zones, regions."""

    _type = None
    _name = None

    @classmethod
    def create_global(cls):
        return Scope("global", None)

    @classmethod
    def create_aggregated(cls):
        return Scope("aggregated", None)

    @classmethod
    def create_zone(cls, zone_name):
        return Scope("zones", zone_name)

    @classmethod
    def create_region(cls, region_name):
        return Scope("regions", region_name)

    @classmethod
    def construct(self, req, scope_id):
        path_info = [item for item in req.path_info.split("/") if item]
        path_count = len(path_info)
        if path_count == 0:
            raise exc.HTTPBadRequest(comment="Bad path %s" % req.path_info)
        if path_count < 3:
            return None
        scope_type = path_info[1]
        if scope_type in ("zones", "regions") and scope_id is None:
            return None
        if scope_type in ("zones", "regions", "global", "aggregated"):
            return Scope(scope_type, scope_id)
        raise exc.HTTPBadRequest(comment="Bad path %s" % req.path_info)

    def __init__(self, scope_type, scope_name):
        self._type = scope_type
        self._name = scope_name

    def is_aggregated(self):
        return self._type == "aggregated"

    def get_type(self):
        return self._type

    def get_name(self):
        return self._name

    def get_path(self):
        result = self._type
        if self._name:
            result = os.path.join(result, self._name)
        return result
