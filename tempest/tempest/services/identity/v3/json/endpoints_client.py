# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
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

import json
import urlparse

from tempest.common.rest_client import RestClient


class EndPointClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(EndPointClientJSON, self).__init__(config,
                                                 username, password,
                                                 auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(
            urlparse.urlparse(self.base_url).path, "/v3")
        return super(EndPointClientJSON, self).request(method, url,
                                                       headers=headers,
                                                       body=body)

    def list_endpoints(self):
        """GET endpoints."""
        resp, body = self.get('endpoints')
        body = json.loads(body)
        return resp, body['endpoints']

    def create_endpoint(self, service_id, interface, url, **kwargs):
        """Create endpoint."""
        region = kwargs.get('region', None)
        enabled = kwargs.get('enabled', None)
        post_body = {
            'service_id': service_id,
            'interface': interface,
            'url': url,
            'region': region,
            'enabled': enabled
        }
        post_body = json.dumps({'endpoint': post_body})
        resp, body = self.post('endpoints', post_body, self.headers)
        body = json.loads(body)
        return resp, body['endpoint']

    def update_endpoint(self, endpoint_id, service_id=None, interface=None,
                        url=None, region=None, enabled=None):
        """Updates an endpoint with given parameters."""
        post_body = {}
        if service_id is not None:
            post_body['service_id'] = service_id
        if interface is not None:
            post_body['interface'] = interface
        if url is not None:
            post_body['url'] = url
        if region is not None:
            post_body['region'] = region
        if enabled is not None:
            post_body['enabled'] = enabled
        post_body = json.dumps({'endpoint': post_body})
        resp, body = self.patch('endpoints/%s' % endpoint_id, post_body,
                                self.headers)
        body = json.loads(body)
        return resp, body['endpoint']

    def delete_endpoint(self, endpoint_id):
        """Delete endpoint."""
        resp_header, resp_body = self.delete('endpoints/%s' % endpoint_id)
        return resp_header, resp_body
