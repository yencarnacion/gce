#    Copyright 2012 Cloudscaling Group, Inc
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

from nova import exception


class FakeKeypairAPI(object):

    def get_key_pairs(self, context, context_user_id):
        return []

    def get_key_pair(self, context, context_user_id, user_name):
        raise exception.NotFound

    def delete_key_pair(self, context, context_user_id, user_name):
        raise exception.NotFound

    def import_key_pair(self, context, context_user_id, user_name, ssh_key):
        pass
