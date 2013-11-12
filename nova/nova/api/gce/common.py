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

from nova.api.gce import zone_api
from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common.rpc import common as rpc_common
from nova.openstack.common import timeutils


AGGREGATED = "*"


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
    def __init__(self):
        """Base initialization.

        Inherited classes should init _api and call super().
        """

        self._zone_api = zone_api.API()
        self._type_name = self._get_type()
        self._collection_name = "%ss" % self._type_name
        self._type_kind = "compute#%s" % self._type_name
        self._list_kind = "compute#%sList" % self._type_name
        self._aggregated_kind = "compute#%sAggregatedList" % self._type_name

    # Base methods, should be overriden

    def _get_type(self):
        """Controller type method. Should be overriden."""

        return ""

    def basic(self, request, image, zone_id=None):
        """Main item resource conversion routine

        Overriden in inherited classes should implement conversion of
        OpenStack resource into GCE resource.
        """

        raise exc.HTTPNotImplemented

    # Utility
    def _get_context(self, req):
        return req.environ['nova.context']

    def _check_zone(self, context, zone_id):
        if zone_id is not None:
            try:
                self._zone_api.get_item(context, zone_id)
            except ValueError:
                raise exc.HTTPNotFound
        return zone_id

    def _filter_result(self, request, result_list):
        if 'filter' not in request.params:
            return result_list

        filter_def = request.params['filter'].split(' ')
        if (len(filter_def) != 3 or filter_def[0] != 'name'
                or filter_def[1] != 'eq'):
            return result_list

        return [item for item in result_list if item["name"] == filter_def[2]]

    # Actions
    def index(self, req, zone_id=None):
        """GCE list requests, global or with zone specified."""

        context = self._get_context(req)
        self._check_zone(context, zone_id)

        items = self._api.get_items(context, zone_id)
        result_list = [self.basic(req, item, zone_id) for item in items]
        result_list = self._filter_result(req, result_list)

        return self._format_list(req, result_list, zone_id)

    def show(self, req, id=None, zone_id=None):
        """GCE get requests, global or zone specified."""

        context = self._get_context(req)
        self._check_zone(context, zone_id)
        try:
            item = self._api.get_item(context, id, zone_id)
            return self.basic(req, item, zone_id)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Resource '%s' could not be found") % id
            if zone_id is not None:
                msg += _(" in zone '%s'") % zone_id
            raise exc.HTTPNotFound(explanation=msg)

    def aggregated_list(self, req):
        """GCE aggregated list requests for all zones."""

        items = self._api.get_items(self._get_context(req))
        items_by_zones = {}
        context = self._get_context(req)
        for item in items:
            zones = self._api.get_zones(context, item)
            for zone in zones:
                az = os.path.join("zones", zone)
                items_by_zone = items_by_zones.setdefault(
                        az, {self._collection_name: []})[self._collection_name]
                items_by_zone.append(self.basic(req, item, zone))
        return self._format_list(req, items_by_zones, AGGREGATED)

    def delete(self, req, id, zone_id=None):
        """GCE delete requests."""

        try:
            self._api.delete_item(self._get_context(req), id, zone_id)
        except (exception.NotFound, KeyError, IndexError):
            msg = _("Resource '%s' could not be found") % id
            if zone_id is not None:
                msg += _(" in zone '%s'") % zone_id
            raise exc.HTTPNotFound(explanation=msg)

        return self._format_operation(req, id, "delete", zone_id)

    def create(self, req, body, zone_id=None):
        """GCE add requests."""

        name = body['name']
        try:
            self._api.add_item(self._get_context(req), name, body, zone_id)
        except rpc_common.RemoteError as err:
            raise exc.HTTPInternalServerError(explanation=err.message)

        return self._format_operation(req, name, "insert", zone_id)

    # Result formatting
    def _format_date(self, date_string):
        """Returns standard format for given date."""
        if date_string is None:
            return None
        if isinstance(date_string, basestring):
            date_string = timeutils.parse_isotime(date_string)
        return date_string.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _get_path(self, request, controller, identifier, zone_id):
        """Generates a path for resources.

        For projects and zones we have specific formatting
        For global resources we have 'global' prefix
        For zone resources we have 'zones/zone_id' prefix
        """

        if (controller == "projects"):
            return request.environ['nova.context'].project_name

        if (controller == "zones"):
            result = os.path.join(
                request.environ['nova.context'].project_name,
                controller)
        else:
            if zone_id is AGGREGATED:
                middle_component = "aggregated"
            elif zone_id is None:
                middle_component = "global"
            else:
                middle_component = os.path.join("zones", zone_id)
            result = os.path.join(
                request.environ['nova.context'].project_name,
                middle_component,
                controller)

        if identifier is not None:
            result = os.path.join(result, str(identifier))

        return result

    def _qualify(self, request, controller, identifier, zone_id):
        """Creates fully qualified selfLink for an item or collection

        Specific formatting for projects and zones,
        'global' prefix For global resources,
        'zones/zone_id' prefix for zone resources.
        """

        base_url = request.application_url
        return os.path.join(base_url, self._get_path(request, controller,
                                                     identifier, zone_id))

    def _format_zone(self, zone_id=None):
        return ("aggregated" if zone_id is AGGREGATED
                else ("global" if zone_id is None
                      else os.path.join("zones", zone_id)))

    def _format_operation(self, request, item_id, type, zone_id=None):
        targetLink = self._qualify(request, self._collection_name,
                                   item_id, zone_id)
        result_dict = {
           "kind": "compute#operation",
           "id": "0",
           "name": "stub",
           "status": "DONE",
           "selfLink": self._qualify(request, "operations", "stub", zone_id),
           "targetLink": targetLink,
           "operationType": type
        }
        if zone_id is not None:
            result_dict["zone"] = zone_id
        return result_dict

    def _format_item(self, request, result_dict, item_id, zone_id=None):
        if zone_id is not None:
            result_dict["zone"] = self._qualify(
                request, "zones", zone_id, None)
        result_dict["kind"] = self._type_kind
        result_dict["selfLink"] = self._qualify(request, self._collection_name,
                                                result_dict["name"], zone_id)
        hashed_link = hash(result_dict["selfLink"])
        result_dict["id"] = hashed_link if hashed_link >= 0 else -hashed_link
        return result_dict

    def _format_list(self, request, result_list, zone_id=None):
        result_dict = {}
        result_dict["items"] = result_list
        result_dict["kind"] = (self._aggregated_kind if zone_id is AGGREGATED
                               else self._list_kind)
        result_dict["id"] = os.path.join(
                 "projects",
                 self._get_path(request, self._collection_name, None, zone_id))
        result_dict["selfLink"] = self._qualify(request, self._collection_name,
                                                None, zone_id)
        return result_dict
