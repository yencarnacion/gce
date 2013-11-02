# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2012 Nebula, Inc.
# Copyright 2013 IBM Corp.
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

from nova.tests.integrated.v3 import api_sample_base


class LimitsSampleJsonTest(api_sample_base.ApiSampleTestBaseV3):
    extension_name = "limits"

    def test_limits_get(self):
        response = self._do_get('limits')
        subs = self._get_regexes()
        self._verify_response('limit-get-resp', subs, response, 200)


class LimitsSampleXmlTest(LimitsSampleJsonTest):
    ctype = 'xml'
