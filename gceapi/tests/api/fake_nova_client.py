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


FAKE_DETAILED_ZONES = [{
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
}, {
    u'zoneState': {
        u'available': True},
    u'hosts': {
        u'grizzly': {
            u'nova-compute': {
                u'available': True,
                u'active': True,
                u'updated_at': u'2013-12-24T14:14:47.000000'}}},
    u'zoneName': u'nova'
}]


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
                return []

        return FakeAvailabilityZones()


def fake_discover_extensions(self, version):
    return list()
