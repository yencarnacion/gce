#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 OpenStack LLC.
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

"""
Gceapi API Server
"""

import eventlet
import sys

eventlet.patcher.monkey_patch(os=False, thread=False)

from gceapi import config
from gceapi import service
from gceapi.openstack.common import log as logging


def main():
    config.parse_args(sys.argv)
    logging.setup('gceapi')

    # TODO(apavlov): get it from config
    use_ssl = False

    server = service.WSGIService('gce', use_ssl=use_ssl, max_url_len=16384)
    service.serve(server, workers=server.workers)
    service.wait()


if __name__ == '__main__':
    main()
