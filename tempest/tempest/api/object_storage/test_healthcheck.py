# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from tempest.api.object_storage import base
from tempest import clients
from tempest.test import attr
from tempest.test import HTTP_SUCCESS


class HealthcheckTest(base.BaseObjectTest):

    @classmethod
    def setUpClass(cls):
        super(HealthcheckTest, cls).setUpClass()

        # creates a test user. The test user will set its base_url to the Swift
        # endpoint and test the healthcheck feature.
        cls.data.setup_test_user()

        cls.os_test_user = clients.Manager(
            cls.data.test_user,
            cls.data.test_password,
            cls.data.test_tenant)

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(HealthcheckTest, cls).tearDownClass()

    def setUp(self):
        super(HealthcheckTest, self).setUp()
        client = self.os_test_user.account_client
        client._set_auth()

        # Turning http://.../v1/foobar into http://.../
        client.base_url = "/".join(client.base_url.split("/")[:-2])

    def tearDown(self):
        # clear the base_url for subsequent requests
        self.os_test_user.account_client.base_url = None
        super(HealthcheckTest, self).tearDown()

    @attr('gate')
    def test_get_healthcheck(self):

        resp, _ = self.os_test_user.account_client.get("healthcheck", {})

        # The status is expected to be 200
        self.assertIn(int(resp['status']), HTTP_SUCCESS)
