# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Red Hat, Inc.
# All Rights Reserved.
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

"""Tests for network API."""

import itertools
import random

import mox

from nova.compute import flavors
from nova import context
from nova import exception
from nova import network
from nova.network import api
from nova.network import floating_ips
from nova.network import rpcapi as network_rpcapi
from nova import policy
from nova import test
from nova import utils

FAKE_UUID = 'a47ae74e-ab08-547f-9eee-ffd23fc46c16'


class NetworkPolicyTestCase(test.TestCase):
    def setUp(self):
        super(NetworkPolicyTestCase, self).setUp()

        policy.reset()
        policy.init()

        self.context = context.get_admin_context()

    def tearDown(self):
        super(NetworkPolicyTestCase, self).tearDown()
        policy.reset()

    def test_check_policy(self):
        self.mox.StubOutWithMock(policy, 'enforce')
        target = {
            'project_id': self.context.project_id,
            'user_id': self.context.user_id,
        }
        policy.enforce(self.context, 'network:get_all', target)
        self.mox.ReplayAll()
        api.check_policy(self.context, 'get_all')


class ApiTestCase(test.TestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.network_api = network.API()
        self.context = context.RequestContext('fake-user',
                                              'fake-project')

    def test_allocate_for_instance_handles_macs_passed(self):
        # If a macs argument is supplied to the 'nova-network' API, it is just
        # ignored. This test checks that the call down to the rpcapi layer
        # doesn't pass macs down: nova-network doesn't support hypervisor
        # mac address limits (today anyhow).
        macs = set(['ab:cd:ef:01:23:34'])
        self.mox.StubOutWithMock(
            self.network_api.network_rpcapi, "allocate_for_instance")
        kwargs = dict(zip(['host', 'instance_id', 'project_id',
                'requested_networks', 'rxtx_factor', 'vpn', 'macs',
                'dhcp_options'],
                itertools.repeat(mox.IgnoreArg())))
        self.network_api.network_rpcapi.allocate_for_instance(
            mox.IgnoreArg(), **kwargs).AndReturn([])
        self.mox.ReplayAll()
        inst_type = flavors.get_default_flavor()
        inst_type['rxtx_factor'] = 0
        sys_meta = flavors.save_flavor_info({}, inst_type)
        instance = dict(id='id', uuid='uuid', project_id='project_id',
            host='host', system_metadata=utils.dict_to_metadata(sys_meta))
        self.network_api.allocate_for_instance(
            self.context, instance, 'vpn', 'requested_networks', macs=macs)

    def _do_test_associate_floating_ip(self, orig_instance_uuid):
        """Test post-association logic."""

        new_instance = {'uuid': 'new-uuid'}

        def fake_associate(*args, **kwargs):
            return orig_instance_uuid

        self.stubs.Set(floating_ips.FloatingIP, 'associate_floating_ip',
                       fake_associate)

        def fake_instance_get_by_uuid(context, instance_uuid):
            return {'uuid': instance_uuid}

        self.stubs.Set(self.network_api.db, 'instance_get_by_uuid',
                       fake_instance_get_by_uuid)

        def fake_get_nw_info(ctxt, instance):
            class FakeNWInfo(object):
                def json(self):
                    pass
            return FakeNWInfo()

        self.stubs.Set(self.network_api, '_get_instance_nw_info',
                       fake_get_nw_info)

        if orig_instance_uuid:
            expected_updated_instances = [new_instance['uuid'],
                                          orig_instance_uuid]
        else:
            expected_updated_instances = [new_instance['uuid']]

        def fake_instance_info_cache_update(context, instance_uuid, cache):
            self.assertEqual(instance_uuid,
                             expected_updated_instances.pop())

        self.stubs.Set(self.network_api.db, 'instance_info_cache_update',
                       fake_instance_info_cache_update)

        self.network_api.associate_floating_ip(self.context,
                                               new_instance,
                                               '172.24.4.225',
                                               '10.0.0.2')

    def test_associate_preassociated_floating_ip(self):
        self._do_test_associate_floating_ip('orig-uuid')

    def test_associate_unassociated_floating_ip(self):
        self._do_test_associate_floating_ip(None)

    def _stub_migrate_instance_calls(self, method, multi_host, info):
        fake_instance_type = flavors.get_default_flavor()
        fake_instance_type['rxtx_factor'] = 1.21
        sys_meta = utils.dict_to_metadata(
            flavors.save_flavor_info({}, fake_instance_type))
        fake_instance = {'uuid': 'fake_uuid',
                         'instance_type_id': fake_instance_type['id'],
                         'project_id': 'fake_project_id',
                         'system_metadata': sys_meta}
        fake_migration = {'source_compute': 'fake_compute_source',
                          'dest_compute': 'fake_compute_dest'}

        def fake_mig_inst_method(*args, **kwargs):
            info['kwargs'] = kwargs

        def fake_is_multi_host(*args, **kwargs):
            return multi_host

        def fake_get_floaters(*args, **kwargs):
            return ['fake_float1', 'fake_float2']

        self.stubs.Set(network_rpcapi.NetworkAPI, method,
                fake_mig_inst_method)
        self.stubs.Set(self.network_api, '_is_multi_host',
                fake_is_multi_host)
        self.stubs.Set(self.network_api, '_get_floating_ip_addresses',
                fake_get_floaters)

        expected = {'instance_uuid': 'fake_uuid',
                    'source_compute': 'fake_compute_source',
                    'dest_compute': 'fake_compute_dest',
                    'rxtx_factor': 1.21,
                    'project_id': 'fake_project_id',
                    'floating_addresses': None}
        if multi_host:
            expected['floating_addresses'] = ['fake_float1', 'fake_float2']
        return fake_instance, fake_migration, expected

    def test_migrate_instance_start_with_multhost(self):
        info = {'kwargs': {}}
        arg1, arg2, expected = self._stub_migrate_instance_calls(
                'migrate_instance_start', True, info)
        expected['host'] = 'fake_compute_source'
        self.network_api.migrate_instance_start(self.context, arg1, arg2)
        self.assertEqual(info['kwargs'], expected)

    def test_migrate_instance_start_without_multhost(self):
        info = {'kwargs': {}}
        arg1, arg2, expected = self._stub_migrate_instance_calls(
                'migrate_instance_start', False, info)
        self.network_api.migrate_instance_start(self.context, arg1, arg2)
        self.assertEqual(info['kwargs'], expected)

    def test_migrate_instance_finish_with_multhost(self):
        info = {'kwargs': {}}
        arg1, arg2, expected = self._stub_migrate_instance_calls(
                'migrate_instance_finish', True, info)
        expected['host'] = 'fake_compute_dest'
        self.network_api.migrate_instance_finish(self.context, arg1, arg2)
        self.assertEqual(info['kwargs'], expected)

    def test_migrate_instance_finish_without_multhost(self):
        info = {'kwargs': {}}
        arg1, arg2, expected = self._stub_migrate_instance_calls(
                'migrate_instance_finish', False, info)
        self.network_api.migrate_instance_finish(self.context, arg1, arg2)
        self.assertEqual(info['kwargs'], expected)

    def test_is_multi_host_instance_has_no_fixed_ip(self):
        def fake_fixed_ip_get_by_instance(ctxt, uuid):
            raise exception.FixedIpNotFoundForInstance(instance_uuid=uuid)
        self.stubs.Set(self.network_api.db, 'fixed_ip_get_by_instance',
                       fake_fixed_ip_get_by_instance)
        instance = {'uuid': FAKE_UUID}
        self.assertFalse(self.network_api._is_multi_host(self.context,
                                                         instance))

    def test_is_multi_host_network_has_no_project_id(self):
        is_multi_host = random.choice([True, False])
        network = {'project_id': None,
                   'multi_host': is_multi_host, }
        network_ref = self.network_api.db.network_create_safe(
                                                 self.context.elevated(),
                                                 network)

        def fake_fixed_ip_get_by_instance(ctxt, uuid):
            fixed_ip = [{'network_id': network_ref['id'],
                         'instance_uuid': FAKE_UUID, }]
            return fixed_ip

        self.stubs.Set(self.network_api.db, 'fixed_ip_get_by_instance',
                       fake_fixed_ip_get_by_instance)

        instance = {'uuid': FAKE_UUID}
        result = self.network_api._is_multi_host(self.context, instance)
        self.assertEqual(is_multi_host, result)

    def test_is_multi_host_network_has_project_id(self):
        is_multi_host = random.choice([True, False])
        network = {'project_id': self.context.project_id,
                   'multi_host': is_multi_host, }
        network_ref = self.network_api.db.network_create_safe(
                                                 self.context.elevated(),
                                                 network)

        def fake_fixed_ip_get_by_instance(ctxt, uuid):
            fixed_ip = [{'network_id': network_ref['id'],
                         'instance_uuid': FAKE_UUID, }]
            return fixed_ip

        self.stubs.Set(self.network_api.db, 'fixed_ip_get_by_instance',
                       fake_fixed_ip_get_by_instance)

        instance = {'uuid': FAKE_UUID}
        result = self.network_api._is_multi_host(self.context, instance)
        self.assertEqual(is_multi_host, result)

    def test_network_disassociate_project(self):
        def fake_network_disassociate(ctx, network_id, disassociate_host,
                                      disassociate_project):
            self.assertEqual(network_id, 1)
            self.assertEqual(disassociate_host, False)
            self.assertEqual(disassociate_project, True)

        def fake_get(context, network_uuid):
            return {'id': 1}

        self.stubs.Set(self.network_api.db, 'network_disassociate',
                       fake_network_disassociate)
        self.stubs.Set(self.network_api, 'get', fake_get)

        self.network_api.associate(self.context, FAKE_UUID, project=None)
