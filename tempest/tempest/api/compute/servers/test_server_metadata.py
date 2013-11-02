# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest import exceptions
from tempest.test import attr


class ServerMetadataTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServerMetadataTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.quotas = cls.quotas_client
        cls.admin_client = cls._get_identity_admin_client()
        resp, tenants = cls.admin_client.list_tenants()
        cls.tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                         cls.client.tenant_name][0]
        resp, server = cls.create_server(meta={}, wait_until='ACTIVE')

        cls.server_id = server['id']

    def setUp(self):
        super(ServerMetadataTestJSON, self).setUp()
        meta = {'key1': 'value1', 'key2': 'value2'}
        resp, _ = self.client.set_server_metadata(self.server_id, meta)
        self.assertEqual(resp.status, 200)

    @attr(type='gate')
    def test_list_server_metadata(self):
        # All metadata key/value pairs for a server should be returned
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)

        # Verify the expected metadata items are in the list
        self.assertEqual(200, resp.status)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_set_server_metadata(self):
        # The server's metadata should be replaced with the provided values
        # Create a new set of metadata for the server
        req_metadata = {'meta2': 'data2', 'meta3': 'data3'}
        resp, metadata = self.client.set_server_metadata(self.server_id,
                                                         req_metadata)
        self.assertEqual(200, resp.status)

        # Verify the expected values are correct, and that the
        # previous values have been removed
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        self.assertEqual(resp_metadata, req_metadata)

    @attr(type='gate')
    def test_server_create_metadata_key_too_long(self):
        # Attempt to start a server with a meta-data key that is > 255
        # characters

        # Try a few values
        for sz in [256, 257, 511, 1023]:
            key = "k" * sz
            meta = {key: 'data1'}
            self.assertRaises(exceptions.OverLimit,
                              self.create_server,
                              meta=meta)

        # no teardown - all creates should fail

    @attr(type='gate')
    def test_update_server_metadata(self):
        # The server's metadata values should be updated to the
        # provided values
        meta = {'key1': 'alt1', 'key3': 'value3'}
        resp, metadata = self.client.update_server_metadata(self.server_id,
                                                            meta)
        self.assertEqual(200, resp.status)

        # Verify the values have been updated to the proper values
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'alt1', 'key2': 'value2', 'key3': 'value3'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_update_metadata_empty_body(self):
        # The original metadata should not be lost if empty metadata body is
        # passed
        meta = {}
        _, metadata = self.client.update_server_metadata(self.server_id, meta)
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_get_server_metadata_item(self):
        # The value for a specific metadata key should be returned
        resp, meta = self.client.get_server_metadata_item(self.server_id,
                                                          'key2')
        self.assertEqual('value2', meta['key2'])

    @attr(type='gate')
    def test_set_server_metadata_item(self):
        # The item's value should be updated to the provided value
        # Update the metadata value
        meta = {'nova': 'alt'}
        resp, body = self.client.set_server_metadata_item(self.server_id,
                                                          'nova', meta)
        self.assertEqual(200, resp.status)

        # Verify the meta item's value has been updated
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'value1', 'key2': 'value2', 'nova': 'alt'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_delete_server_metadata_item(self):
        # The metadata value/key pair should be deleted from the server
        resp, meta = self.client.delete_server_metadata_item(self.server_id,
                                                             'key1')
        self.assertEqual(204, resp.status)

        # Verify the metadata item has been removed
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type=['negative', 'gate'])
    def test_server_metadata_negative(self):
        # Blank key should trigger an error.
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.create_server,
                          meta=meta)

        # GET on a non-existent server should not succeed
        self.assertRaises(exceptions.NotFound,
                          self.client.get_server_metadata_item, 999, 'test2')

        # List metadata on a non-existent server should not succeed
        self.assertRaises(exceptions.NotFound,
                          self.client.list_server_metadata, 999)

        # Raise BadRequest if key in uri does not match
        # the key passed in body.
        meta = {'testkey': 'testvalue'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata_item,
                          self.server_id, 'key', meta)

        # Set metadata on a non-existent server should not succeed
        meta = {'meta1': 'data1'}
        self.assertRaises(exceptions.NotFound,
                          self.client.set_server_metadata, 999, meta)

        # An update should not happen for a non-existent image
        meta = {'key1': 'value1', 'key2': 'value2'}
        self.assertRaises(exceptions.NotFound,
                          self.client.update_server_metadata, 999, meta)

        # Blank key should trigger an error
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_server_metadata,
                          self.server_id, meta=meta)

        # Should not be able to delete metadata item from a non-existent server
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_server_metadata_item, 999, 'd')

        # Raise a 413 OverLimit exception while exceeding metadata items limit
        # for tenant.
        _, quota_set = self.quotas.get_quota_set(self.tenant_id)
        quota_metadata = quota_set['metadata_items']
        req_metadata = {}
        for num in range(1, quota_metadata + 2):
            req_metadata['key' + str(num)] = 'val' + str(num)
        self.assertRaises(exceptions.OverLimit,
                          self.client.set_server_metadata,
                          self.server_id, req_metadata)

        # Raise a 413 OverLimit exception while exceeding metadata items limit
        # for tenant (update).
        self.assertRaises(exceptions.OverLimit,
                          self.client.update_server_metadata,
                          self.server_id, req_metadata)

        # Raise a bad request error for blank key.
        # set_server_metadata will replace all metadata with new value
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta)

        # Raise a bad request error for a missing metadata field
        # set_server_metadata will replace all metadata with new value
        meta = {'meta1': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta, no_metadata_field=True)


class ServerMetadataTestXML(ServerMetadataTestJSON):
    _interface = 'xml'
