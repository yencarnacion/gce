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

"""Base classes of GCE API conversion layer.

Classes in this layer aggregate functionality of OpenStack necessary
and sufficient to handle supported GCE API requests
"""

from oslo.config import cfg

from gceapi import exception

FLAGS = cfg.CONF


class Singleton(type):
    """Singleton metaclass."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls) \
                .__call__(*args, **kwargs)
        return cls._instances[cls]


class API(object):
    """Base GCE API abstraction class

    Inherited classes should implement one class of GCE API functionality.
    There should be enough public methods implemented to cover necessary
    methods of GCE API in the class. Other public methods can exist to be
    invoked from other APIs of this layer.
    Class in this layer should use each others functionality instead of
    calling corresponding low-level routines.
    Basic methods should be named including "item(s)" instead of specific
    functional names.

    Descendants are stateless singletons.
    Supports callbacks for interaction of APIs in this layer
    """
    # TODO(Alex): Now action methods get body of parameters straight from GCE
    # request while returning results in terms of Openstack to be converted
    # to GCE terms in controller. In next version this layer should be revised
    # to work symmetrically with incoming and outgoing data.

    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._callbacks = []

    def get_item(self, context, name, scope=None):
        """Returns fully filled item for particular inherited API."""

        raise exception.NotFound

    def get_items(self, context, scope=None):
        """Returns list of items."""

        return []

    def delete_item(self, context, name, scope=None):
        """Deletes an item."""

        raise exception.NotFound

    def add_item(self, context, name, body, scope=None):
        """Creates an item. It returns created item."""

        raise exception.NotFound

    def get_scopes(self, context, item):
        """Returns which zones/regions the item belongs too."""

        return []

    def _process_callbacks(self, context, reason, item, **kwargs):
        for cb_reason, cb_func in self._callbacks:
            if cb_reason == reason:
                cb_func(context, item, **kwargs)

    def _register_callback(self, reason, func):
        """Callbacks registration

        Callbacks can be registered by one API to be called by another before
        some action for checking possibility of the action or to process
        pre-actions
        """

        self._callbacks.append((reason, func))


class BaseScopeAPI(API):
    """Base class for API which contains other resources."""

    def get_name(self):
        """Must return name of scope controller."""
        raise exception.NotFound

    def get_scope_qualifier(self):
        """Must return name for result dict property."""
        raise exception.NotFound


class BaseNetAPI(API):
    """Base class for API that uses one of various network api."""

    _api = None

    def __init__(self, neutron_api, nova_api, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)

        net_api = "nova"
        # TODO(apavlov): get it from config
        #net_api = FLAGS.has("network_api_class")

        # NOTE(Alex): Initializing proper network singleton
        if net_api is None or ("quantum" in net_api
                               or "neutron" in net_api):
            self._api = neutron_api.API()
        else:
            self._api = nova_api.API()

    def get_item(self, context, name, scope=None):
        return self._api.get_item(context, name, scope)

    def get_items(self, context, scope=None):
        return self._api.get_items(context, scope)

    def delete_item(self, context, name, scope=None):
        return self._api.delete_item(context, name, scope)

    def add_item(self, context, name, body, scope=None):
        return self._api.add_item(context, name, body, scope)

    def get_scopes(self, context, item):
        return self._api.get_scopes(context, item)

    def _process_callbacks(self, context, reason, item, **kwargs):
        self._api._process_callback(context, reason, item, kwargs)

    def _register_callback(self, reason, func):
        self._api._register_callback(reason, func)


class _CallbackReasons(object):
    check_delete = 1
    pre_delete = 2
    post_add = 3


_callback_reasons = _CallbackReasons()
