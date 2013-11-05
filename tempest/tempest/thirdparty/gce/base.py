# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

import httplib2
import json
import subprocess
import unittest
import urlparse

import testtools

from keystoneclient.v2_0 import client
from tempest.common.utils.linux.remote_client import RemoteClient
import tempest.config
import tempest.test


class GCEConnection(object):
    config = tempest.config.TempestConfig()

    def __init__(self):
        auth_cfg = self.config.identity
        self.keystone = client.Client(username=auth_cfg.username,
                                      password=auth_cfg.password,
                                      tenant_name=auth_cfg.tenant_name,
                                      auth_url=auth_cfg.uri)
        self.connection = httplib2.Http()

    def set_zone(self, zone):
        self.zone = zone

    def auth_request(self, uri, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['X-Auth-Token'] = self.keystone.auth_token
        return self.connection.request(uri, **kwargs)

    def _combine_uri(self, *path):
        if not len(path):
            return None
        gce_cfg = self.config.gce
        auth_cfg = self.config.identity
        parts = []
        if not urlparse.urlsplit(path[0]).netloc:
            parts = [gce_cfg.api_host,
                     gce_cfg.api_path,
                     auth_cfg.tenant_name]
        parts.extend(path)
        uri = "/".join(x.strip("/") for x in parts if x)
        return uri

    def _add_params(self, uri, params):
        if not params:
            return uri
        param_list = ["%s=%s" % (param, value)
                      for (param, value) in params.iteritems()]
        return "%s?%s" % (uri, ";".join(param_list))

    def _convert_response(self, response):
        header = response[0]
        body = (json.loads(response[1])
                if header.get("content-type") == "application/json"
                else None)
        return (header.status, body)

    def request(self, *path, **kwargs):
        uri = self._combine_uri(*path)
        params = kwargs.pop("params", None)
        uri = self._add_params(uri, params)
        response = self.auth_request(uri, **kwargs)
        return self._convert_response(response)

    def _add_zone_path(self, *path):
        return ('zones', self.zone) + path

    def get(self, *path):
        return self.request(*path)

    def zone_get(self, *path):
        return self.get(*self._add_zone_path(*path))

    def post(self, *path, **kwargs):
        req_args = {"method": "POST"}
        if "body" in kwargs:
            req_args["body"] = json.dumps(kwargs["body"])
            req_args["headers"] = {"Content-Type": "application/json"}
        if "params" in kwargs:
            req_args["params"] = kwargs["params"]
        return self.request(*path, **req_args)

    def zone_post(self, *path, **kwargs):
        return self.post(*self._add_zone_path(*path), **kwargs)

    def delete(self, *path):
        return self.request(
                *path,
                method="DELETE")

    def zone_delete(self, *path):
        return self.delete(*self._add_zone_path(*path))


class GCESmokeTestCase(testtools.TestCase):
    config = tempest.config.TempestConfig()
    failed = False

    @classmethod
    def setUpClass(cls):
        super(GCESmokeTestCase, cls).setUpClass()
        cls.gce = GCEConnection()
        cls._trash_bin = []

    @classmethod
    def tearDownClass(cls):
        resource_link = None

        def check_delete():
            (status, dummy) = cls.gce.get(resource_link)
            if status not in (200, 404):
                raise Exception()
            return status == 404

        while cls._trash_bin:
            (resource_link, timeout, idle) = cls._trash_bin.pop()
            (status, dummy) = cls.gce.delete(resource_link)
            if status == 200:
                try:
                    tempest.test.call_until_true(check_delete, timeout, idle)
                except Exception:
                    pass

    @classmethod
    def add_resource_cleanup(cls, resource_link, delete_timeout=0, idle=0):
        if next((x for x, y, z in cls._trash_bin if x == resource_link), None):
            return
        cls._trash_bin.append((resource_link, delete_timeout, idle))

    @classmethod
    def cancel_resource_cleanup(cls, resource_link):
        resource_index = next((i for i, x in enumerate(cls._trash_bin)
                               if x[0] == resource_link), -1)
        if resource_index > 0:
            del cls._trash_bin[resource_index]

    @staticmethod
    def incremental(meth):
        def decorator(*args, **kwargs):
            try:
                meth(*args, **kwargs)
            except unittest.SkipTest:
                raise
            except Exception:
                GCESmokeTestCase.failed = True
                raise
        decorator.__test__ = True
        return decorator

    def setUp(self):
        if GCESmokeTestCase.failed:
            raise unittest.SkipTest("Skipped by previous exception")
        super(GCESmokeTestCase, self).setUp()

    def wait_for(self, uri, http_status, gce_status, timeout, idle, options):
        idle_http_statuses = options.get("idle_http_statuses", ())
        idle_gce_statuses = options.get("idle_gce_statuses", ())

        def check():
            (now_http_status, body) = self.gce.get(uri)
            now_gce_status = body.get("status") if body else None
            if (now_http_status == http_status and
                    (not gce_status or gce_status == now_gce_status)):
                return True
            elif ((now_http_status == http_status or
                   now_http_status in idle_http_statuses) and
                  (not now_gce_status or not idle_gce_statuses or
                   now_gce_status in idle_gce_statuses)):
                return False
            else:
                msg = ""
                if now_http_status not in idle_http_statuses:
                    msg = "Unexpected HTTP status %s" % now_http_status
                if (now_gce_status and idle_gce_statuses and
                        now_gce_status not in idle_gce_statuses):
                    msg += "Unexpected GCE oject status %s" % now_gce_status
                self.fail(msg)

        return tempest.test.call_until_true(check, timeout, idle)

    def verify_resource_uri(self, uri, resource_path=None, resource_name=None):
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(str(uri))
        self.assertEqual(self.config.gce.api_host,
                         scheme + "://" + netloc + "/")
        resource_parts = [self.config.gce.api_path.strip("/"),
                          self.config.identity.tenant_name]
        if resource_path is not None:
            resource_parts.append(resource_path.strip("/"))
        if resource_name is not None:
            resource_parts.append(resource_name)

        self.assertEqual("/" + "/".join(resource_parts), path)
        self.assertFalse(query)
        self.assertFalse(fragment)

    def verify_zone_resource_uri(self, uri, resource_path, resource_name):
        resource_path = "/".join(["zones", self.ctx.zone["name"],
                                  resource_path.strip("/")])
        self.verify_resource_uri(uri, resource_path, resource_name)

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode == 0:
                return True

        return tempest.test.call_until_true(
            ping, self.config.compute.ping_timeout, 1)

    def _check_ssh_connectivity(self, ip_address, username, pkey):
        ssh_client = RemoteClient(ip_address, username, pkey=pkey)
        self.assertTrue(ssh_client.can_authenticate())
