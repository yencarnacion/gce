# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
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

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest.services.compute.xml.common import xml_to_json


class AvailabilityZoneClientXML(RestClientXML):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AvailabilityZoneClientXML, self).__init__(config, username,
                                                        password, auth_url,
                                                        tenant_name)
        self.service = self.config.compute.catalog_type

    def _parse_array(self, node):
        return [xml_to_json(x) for x in node]

    def get_availability_zone_list(self):
        resp, body = self.get('os-availability-zone', self.headers)
        availability_zone = self._parse_array(etree.fromstring(body))
        return resp, availability_zone

    def get_availability_zone_list_detail(self):
        resp, body = self.get('os-availability-zone/detail', self.headers)
        availability_zone = self._parse_array(etree.fromstring(body))
        return resp, availability_zone
