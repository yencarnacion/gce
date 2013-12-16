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

from keystoneclient.v2_0 import client as keystone_client
from oslo.config import cfg

from nova import exception
from gceapi.api import base_api
from nova.compute import api as compute_api

FLAGS = cfg.CONF


class API(base_api.API):
    """GCE Projects API"""

    def get_item(self, context, name, scope=None):
        project_name = context.project_name

        try:
            keystone = keystone_client.Client(
                token=context.auth_token, auth_url=FLAGS.keystone_gce_url)
        except Exception:
            msg = "Failed to connect to Keystone at %s", FLAGS.keystone_gce_url
            return exception.ServiceUnavailable(explanation=msg)

        project = [t for t in keystone.tenants.list()
                if t.name == project_name][0]

        result = {}
        result["project"] = project
        result["keypair"] = self._get_gce_keypair(context)
        return result

    def get_items(self, context, scope=None):
        raise exception.NotFound

    def set_common_instance_metadata(self, context, metadata_list):
        instance_metadata = dict(
            [(x['key'], x['value']) for x in metadata_list])
        ssh_keys = instance_metadata.pop('sshKeys', None)
        if ssh_keys:
            for key_data in ssh_keys.split('\n'):
                user_name, ssh_key = key_data.split(":")
                self._update_key(context, user_name, ssh_key)

    def get_gce_user_keypair(self, context):
        allpairs = compute_api.KeypairAPI().get_key_pairs(
            context, context.user_id)
        for keypair in allpairs:
            if keypair['name'] == context.user_name:
                return keypair['name'], keypair['public_key']

        return None, None

    def _get_gce_keypair(self, context):
        allpairs = compute_api.KeypairAPI().get_key_pairs(
            context, context.user_id)
        key_datas = []
        for keypair in allpairs:
            key_datas.append(keypair['name'] + ':' + keypair['public_key'])

        if not key_datas:
            return None

        return {'key': 'sshKeys', 'value': "\n".join(key_datas)}

    def _update_key(self, context, user_name, ssh_key):
        try:
            keypair = compute_api.KeypairAPI().get_key_pair(
                context, context.user_id, user_name)
            if keypair['public_key'] == ssh_key:
                return

            compute_api.KeypairAPI().delete_key_pair(
                context, context.user_id, user_name)
        except exception.KeypairNotFound:
            pass

        keypair = compute_api.KeypairAPI().import_key_pair(
            context, context.user_id, user_name, ssh_key)
