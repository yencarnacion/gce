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

import inspect
from novaclient.client import exceptions as nova_exceptions
from gceapi.tests.api import utils


FAKE_DETAILED_ZONES = [utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': {
        u'grizzly': {
            u'nova-conductor': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:47.000000'},
            u'nova-consoleauth': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:49.000000'},
            u'nova-scheduler': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:48.000000'},
            u'nova-cert': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:49.000000'}}},
    u'zoneName': u'internal'
}), utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': {
        u'grizzly': {
            u'nova-compute': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:47.000000'}}},
    u'zoneName': u'nova'
})]

FAKE_SIMPLE_ZONES = [utils.to_obj({
    u'zoneState': {
        u'available': True},
    u'hosts': None,
    u'zoneName': u'nova'
})]


FAKE_FLAVORS = [utils.to_obj({
    u'name': u'm1.small',
    u'links': [],
    u'ram': 2048,
    u'OS-FLV-DISABLED:disabled': False,
    u'vcpus': 1,
    u'swap': u'',
    u'os-flavor-access:is_public': True,
    u'rxtx_factor': 1.0,
    u'OS-FLV-EXT-DATA:ephemeral': 0,
    u'disk': 20,
    u'id': u'2'
}), utils.to_obj({
    u'name': u'm1.large',
    u'links': [],
    u'ram': 8192,
    u'OS-FLV-DISABLED:disabled': False,
    u'vcpus': 4,
    u'swap': u'',
    u'os-flavor-access:is_public': True,
    u'rxtx_factor': 1.0,
    u'OS-FLV-EXT-DATA:ephemeral': 870,
    u'disk': 80,
    u'id': u'4'
})]


class FakeClassWithFind(object):
    def list(self):
        pass

    def find(self, **kwargs):
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise nova_exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise nova_exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        found = []
        searches = kwargs.items()

        detailed = True
        list_kwargs = {}

        list_argspec = inspect.getargspec(self.list)
        if 'detailed' in list_argspec.args:
            detailed = ("human_id" not in kwargs and
                        "name" not in kwargs and
                        "display_name" not in kwargs)
            list_kwargs['detailed'] = detailed

        if 'is_public' in list_argspec.args and 'is_public' in kwargs:
            is_public = kwargs['is_public']
            list_kwargs['is_public'] = is_public
            if is_public is None:
                tmp_kwargs = kwargs.copy()
                del tmp_kwargs['is_public']
                searches = tmp_kwargs.items()

        listing = self.list(**list_kwargs)

        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    if detailed:
                        found.append(obj)
                    else:
                        found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class FakeNovaClient(object):
    def __init__(self, version, *args, **kwargs):
        pass

    @property
    def client(self):
        return self

    @property
    def availability_zones(self):
        class FakeAvailabilityZones(object):
            def list(self, detailed=True):
                if detailed:
                    return FAKE_DETAILED_ZONES
                return FAKE_SIMPLE_ZONES

        return FakeAvailabilityZones()

    @property
    def flavors(self):
        class FakeFlavors(FakeClassWithFind):
            def list(self, detailed=True, is_public=True):
                return FAKE_FLAVORS

            def get(self, flavor):
                flavor_id = utils.get_id(flavor)
                for flavor in FAKE_FLAVORS:
                    if flavor.id == flavor_id:
                        return flavor
                raise nova_exceptions.NotFound()

        return FakeFlavors()

    @property
    def keypairs(self):
        class FakeKeypairs(object):
            def get(self, keypair):
                raise nova_exceptions.NotFound()

            def create(self, name, public_key=None):
                pass

            def delete(self, key):
                raise nova_exceptions.NotFound()

            def list(self):
                return []

        return FakeKeypairs()


def fake_discover_extensions(self, version):
    return list()
