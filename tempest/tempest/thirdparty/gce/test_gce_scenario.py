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

import BaseHTTPServer
from itertools import ifilter
import netaddr
import os
import socket
import tarfile
import tempfile
import thread
import urlparse
import urllib2

import testtools

from tempest.common.utils.data_utils import rand_name
import tempest.config
import tempest.thirdparty.gce.base as base_gce


PUBLIC_KEY = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCiU5kpbgCLrKxP1LYH9"
              "dumtf8d6Rb+CX/6irKYyJNbsNYSX1skM9jur17TiFlXQFCjorNYXZ/A1e"
              "EKbiDcZUKrINhibQfQlAJZpYP1isLUwJlUhJtGFFBW38wTuyG0MFBO+TF"
              "RtAG8GQRRfGDxIXvwUxuDR8sClNuTc0MURTbLCJGPFaK2S99NElNYP7R0"
              "QpzQyTHkfl492NKD9Zr7kjvnssqihuQ8dZ0dh5xE2RuF9VChdmmPmsfQG"
              "qtRXS6xf1Dy0rPHilEcJpGevcUs/JcqEnUd455uugfdueHLqhOvUt3WJU"
              "6mThQ28kTAe7nN17Pj3yKRyurF42bigVKNBudD GCE API testing")

PRIVATE_KEY = (
"""-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAolOZKW4Ai6ysT9S2B/XbprX/HekW/gl/+oqymMiTW7DWEl9b
JDPY7q9e04hZV0BQo6KzWF2fwNXhCm4g3GVCqyDYYm0H0JQCWaWD9YrC1MCZVISb
RhRQVt/ME7shtDBQTvkxUbQBvBkEUXxg8SF78FMbg0fLApTbk3NDFEU2ywiRjxWi
tkvfTRJTWD+0dEKc0Mkx5H5ePdjSg/Wa+5I757LKoobkPHWdHYecRNkbhfVQoXZp
j5rH0BqrUV0usX9Q8tKzx4pRHCaRnr3FLPyXKhJ1HeOebroH3bnhy6oTr1Ld1iVO
pk4UNvJEwHu5zdez498ikcrqxeNm4oFSjQbnQwIDAQABAoIBAG0MkjlF3/H1V3Dt
6jfgz+XoH/H9E+gng6VRpfeDz5LqcnW3P6hLeHGouKCM2dAGseWsOKWlh9vpExyJ
rWPCVw5Vq2g77OMPe6Cz07mRtZ9tn9QqnZFvtiUWhae/sD23s0vKlnpX3k550+/W
Cd4T64ogmrwP7+7VB8m/xhGJCe1My2j3bziloNo/3hmmZQPjgSAVn8sDLCmRGt84
TYO/f4yY9ftGsWZEa0GhtixBGs9YviyuHz1ANyTGJg6VJ/GIwaK/sefD22MGKWTN
AMuVdPThDwGftcL6Apd44yiiIbm5ufD7w2ZS2l9/dG+0RXV+iSTXQZlNn6MHo3zw
ebc+m6ECgYEAzqImO6hyKAEnWFgXc/NgLk4xxdumEbn3FqVqeTKlJTuUGqiAVzfD
+UDswIvRKwxGnJXlNTMwkT6w9LeFC5W7xvnr4a2YFj68oDNY4Gi6CFcv3kG7/6MR
u9bLtxDh3Q4JHwhLO5cWejIdZ4P+9aG7GzUTqofPMmXEEaiiam7NonMCgYEAyRuc
J1TOm3B/zy29rYgY8BLgdEsdQN07v1JA1xcNG6A24mxBbPrkOuDrZ0kLtnFewVFG
4fLEO5MQBhsRKHK0pw3VE5azO8jHyFzccEjuObUeuYXSLxZFmK8jdcIkRirh6O7D
qCm/cEePnkxIFEIjMrctWXxa/jYEZYheRCXH4/ECgYB0PfvMK+KsZpm/tS7cZ9l/
szWE3R/7cOZzsvLG45rL60xSAuDQL+rrWX7WgtFUqj8+74RV/UohK2dZA7Sw47cT
JJ1yA7o/KWPrq3cgJ0ogTwv6uHgOQ6pCRX+sqK6nMLIo5v2LtF9Mtsyb40GW5Tjh
AWbi1CvXajB2zqsvvM2pyQKBgG6dSBt+ExH+I96BqzWaiRTrXRe6BQIbbXSDOnTU
Efqi+e06XBYkPYqBEhnCXLXhz5uHJ/S5geO+tO6Wzq4vwVutSQi4OCdm/TQgl4MP
KjEFhTvH9l694lPj6R4pRahuh8mGIooJRGnugnkwPekeo5uOk1wIAUiXz31FL4xO
N48RAoGAK7+20dPiStPo8dnFrYjQ2j5xuMO2/0+BaLFhDWTiHHjALCWOHkXJ1JtN
9LM2cIlCC79p4+7KQwUXvMBcnAx6qwTMHisGg3WfxlD8f7MuDDR+or1fd/c0byti
z1r/I9Ya6/bAXQOjruxpHkECZl5DEdVvT0E2qL/pQx0rfqnkdfE=
-----END RSA PRIVATE KEY-----""")


class _HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != self.server.file_name:
            self.send_response(404)
            return
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        fd = os.open(self.server.file_name, os.O_RDONLY)
        fo = os.fdopen(fd)
        for line in fo:
            self.wfile.write(line)

    def log_message(self, msgformat, *args):
        pass


class _ImageService(object):
    config = tempest.config.TempestConfig()

    def __init__(self, image_ref):
        self.srv = None
        self._tar_name = None
        self.image_ref = image_ref
        self._out_ref = self.image_ref
        url_parts = urlparse.urlsplit(image_ref)
        self.is_local = url_parts.scheme in ("", "file")
        self.image_path = url_parts.path
        if self.is_local:
            self.image_path = os.path.abspath(os.path.expanduser(
                    os.path.normpath(os.path.expandvars(self.image_path))))
            self.is_tar = tarfile.is_tarfile(self.image_path)
        else:
            self.is_tar = (os.path.splitext(self.image_path)[1]
                           in (".tar", ".gz"))

    def __enter__(self):
        if self.is_local or not self.is_tar:
            image_path = self.image_path
            if not self.is_tar:
                if self.is_local:
                    fileobj = None
                else:
                    fileobj = self._load_file(self.image_ref)
                self._tar_name = self._make_tar(self.image_path, fileobj)
                image_path = self._tar_name
            self._start_server(image_path)
            (host, port) = self._get_server_address()
            self._out_ref = "http://%s:%s%s" % (host, str(port), image_path)
        return self

    def __exit__(self, extype, value, traceback):
        if self.srv is not None:
            self.srv.shutdown()
            self.srv.server_close()
        if self._tar_name is not None:
            os.remove(self._tar_name)

    def get_out_image_ref(self):
        return self._out_ref

    def _start_server(self, file_name):
        self.srv = BaseHTTPServer.HTTPServer(('', 0), _HTTPRequestHandler)
        self.srv.file_name = file_name
        thread.start_new_thread(self.srv.serve_forever, ())

    def _get_server_address(self):
        if self.srv is None:
            return (None, None)
        (dummy, port) = self.srv.server_address
        host = self._get_host()
        return (host, port)

    @staticmethod
    def _make_tar(filename, fileobj=None):
        tar_file = tempfile.NamedTemporaryFile(suffix=".gz", delete=False)
        tar = tarfile.open(mode="w:gz", fileobj=tar_file)
        if fileobj is None:
            tar.add(filename)
        else:
            tar_info = tar.gettarinfo(
                    fileobj=fileobj,
                    arcname=os.path.split(filename)[1])
            tar.addfile(tar_info, fileobj=fileobj)
        tar.close()
        tar_file.flush()
        return tar_file.name

    @staticmethod
    def _load_file(url):
        resp = urllib2.urlopen(url)
        fileobj = tempfile.TemporaryFile()
        for line in resp:
            fileobj.write(line)
        fileobj.seek(0)
        return fileobj

    @staticmethod
    def _get_host():
        host_parts = urlparse.urlsplit(_ImageService.config.gce.api_host)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host_parts.hostname, host_parts.port))
        (host, dummy) = s.getsockname()
        return host


class GCEScenarioContext(object):
    zone = None
    machine_type = None
    image_name = None
    image = None
    boot_disk_name = None
    boot_disk = None
    empty_disk_name = None
    empty_disk = None
    network_name = None
    network_cidr = None
    gateway_ip = None
    network = None
    firewall_name = None
    instance_name = None
    instance = None


class TestGCEScenario(base_gce.GCESmokeTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestGCEScenario, cls).setUpClass()
        cls.ctx = GCEScenarioContext()

    @classmethod
    def tearDownClass(cls):
        super(TestGCEScenario, cls).tearDownClass()

    def setUp(self):
        super(TestGCEScenario, self).setUp()

    @base_gce.GCESmokeTestCase.incremental
    def test_000_get_zone(self):
        (status, body) = self.gce.get("/zones")
        self.assertEqual(200, status)
        self.ctx.zone = next(ifilter(lambda x: x["status"] == "UP",
                                     body["items"]),
                             None)
        self.assertIsNotNone(self.ctx.zone)
        self.gce.set_zone(self.ctx.zone["name"])

    @base_gce.GCESmokeTestCase.incremental
    def test_001_get_machine_type(self):
        (status, body) = self.gce.zone_get("/machineTypes")
        self.assertEqual(200, status)
        machine_types = body.get("items")
        self.assertTrue(machine_types)
        if self.config.gce.machine_type:
            self.ctx.machine_type = next(
                     t for t in machine_types
                     if t["name"] == self.config.gce.machine_type)
        else:
            self.ctx.machine_type = min(machine_types,
                                        key=lambda x: x["memoryMb"])

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
            not base_gce.GCESmokeTestCase.config.gce.use_existing_image,
            "Skipped by config settings")
    def test_010_get_image(self):
        (status, body) = self.gce.get("/global/images")
        self.assertEqual(200, status)
        self.ctx.image = next(ifilter(lambda x: x["sourceType"] == "AMI" and
                                                x["status"] == "READY",
                                      body["items"]),
                          None)
        self.assertIsNotNone(self.ctx.image)

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.use_existing_image,
                      "Skipped by config settings")
    def test_011_create_image(self):
        self.ctx.image_name = rand_name("image-")
        with _ImageService(self.config.gce.http_raw_image) as srv:
            (status, body) = self.gce.post(
                "/global/images",
                body={
                    "name": self.ctx.image_name,
                    "rawDisk": {
                        "source": srv.get_out_image_ref(),
                    },
                    "sourceType": "RAW",
                })
        self.assertEqual(200, status)
        self.wait_for(body["targetLink"], 200, "READY",
                      self.config.gce.image_saving_timeout,
                      self.config.gce.image_saving_interval,
                      {
                          "idle_http_statuses": (404,),
                          "idle_gce_statuses": ("PENDING",),
                      })
        self.verify_resource_uri(body["targetLink"], "/global/images",
                                 self.ctx.image_name)
        self.add_resource_cleanup(body["targetLink"],
                                  self.config.gce.image_saving_timeout,
                                  self.config.gce.image_saving_interval)

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.use_existing_image,
                      "Skipped by config settings")
    def test_012_check_image_info(self):
        (status, body) = self.gce.get("/global/images", self.ctx.image_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.image_name, body["name"])
        self.assertEqual("READY", body["status"])
        self.assertEqual("RAW", body["sourceType"])
        self.verify_resource_uri(body["selfLink"], "/global/images",
                                 self.ctx.image_name)
        self.ctx.image = body

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
            base_gce.GCESmokeTestCase.config.gce.skip_bootable_volume,
            "Skipped by config settings")
    def test_020_create_bootable_disk(self):
        self.ctx.boot_disk_name = rand_name("boot-disk-")
        (status, body) = self.gce.zone_post(
                "/disks",
                params={
                    "sourceImage": self.ctx.image["selfLink"],
                },
                body={
                    "name": self.ctx.boot_disk_name,
                })
        self.assertEqual(200, status)
        self.wait_for(body["targetLink"], 200, "READY",
                      self.config.volume.build_timeout,
                      self.config.volume.build_interval,
                      {
                          "idle_http_statuses": (404,),
                          "idle_gce_statuses": ("CREATING",),
                      })
        self.verify_zone_resource_uri(body["targetLink"], "/disks",
                                      self.ctx.boot_disk_name)
        self.add_resource_cleanup(body["targetLink"],
                                  self.config.volume.build_timeout,
                                  self.config.volume.build_interval)

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
            base_gce.GCESmokeTestCase.config.gce.skip_bootable_volume,
            "Skipped by config settings")
    def test_021_check_bootable_disk_info(self):
        (status, body) = self.gce.zone_get("/disks/", self.ctx.boot_disk_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.boot_disk_name, body["name"])
        self.assertIsNone(body["description"])
        self.assertEqual("READY", body["status"])
        self.verify_zone_resource_uri(body["selfLink"], "/disks",
                                      self.ctx.boot_disk_name)
        self.ctx.boot_disk = body

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.skip_empty_volume,
                      "Skipped by config settings")
    def test_022_create_empty_disk(self):
        self.ctx.empty_disk_name = rand_name("empty-disk-")
        (status, body) = self.gce.zone_post(
                "/disks",
                body={
                    "name": self.ctx.empty_disk_name,
                    "sizeGb": 1,
                    "description": "test empty volume",
                })
        self.assertEqual(200, status)
        self.wait_for(body["targetLink"], 200, "READY",
                      self.config.volume.build_timeout,
                      self.config.volume.build_interval,
                      {
                          "idle_http_statuses": (404,),
                          "idle_gce_statuses": ("CREATING",),
                      })
        self.verify_zone_resource_uri(body["targetLink"], "/disks",
                                      self.ctx.empty_disk_name)
        self.add_resource_cleanup(body["targetLink"],
                                  self.config.volume.build_timeout,
                                  self.config.volume.build_interval)

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.skip_empty_volume,
                      "Skipped by config settings")
    def test_023_check_empty_disk_info(self):
        (status, body) = self.gce.zone_get("/disks/", self.ctx.empty_disk_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.empty_disk_name, body["name"])
        self.assertEqual("test empty volume", body["description"])
        self.assertEqual("READY", body["status"])
        self.assertEqual(1, body["sizeGb"])
        self.verify_zone_resource_uri(body["selfLink"], "/disks",
                                      self.ctx.empty_disk_name)
        self.ctx.empty_disk = body

    @base_gce.GCESmokeTestCase.incremental
    def test_030_create_network(self):
        self.ctx.network_name = rand_name("network-")
        cfg = self.config.network
        network_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        subnet_cidr = next(s for s in network_cidr.
                           subnet(cfg.tenant_network_mask_bits))
        gateway_ip = netaddr.IPAddress(subnet_cidr.last - 1)
        self.ctx.network_cidr = str(subnet_cidr)
        self.ctx.gateway_ip = str(gateway_ip)
        (status, body) = self.gce.post(
                "/global/networks",
                body={
                    "name": self.ctx.network_name,
                    "IPv4Range": self.ctx.network_cidr,
                    "gatewayIPv4": self.ctx.gateway_ip,
                })
        self.assertEqual(200, status)
        self.verify_resource_uri(body["targetLink"], "/global/networks",
                                 self.ctx.network_name)
        self.add_resource_cleanup(body["targetLink"])

    @base_gce.GCESmokeTestCase.incremental
    def test_031_check_network_info(self):
        (status, body) = self.gce.get("/global/networks",
                                      self.ctx.network_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.network_name, body["name"])
        self.assertEqual(self.ctx.network_cidr, body["IPv4Range"])
        self.assertEqual(self.ctx.gateway_ip, body["gatewayIPv4"])
        self.verify_resource_uri(body["selfLink"], "/global/networks",
                                 self.ctx.network_name)
        self.ctx.network = body

    @base_gce.GCESmokeTestCase.incremental
    def test_040_create_firewall(self):
        self.ctx.firewall_name = rand_name("firewall-")
        (status, body) = self.gce.post(
                "/global/firewalls",
                body={
                    "name": self.ctx.firewall_name,
                    "description": "test firewall",
                    "network": self.ctx.network["selfLink"],
                    "sourceRanges": ["0.0.0.0/0"],
                    "allowed": [
                        {"IPProtocol": "icmp"},
                        {
                            "IPProtocol": "tcp",
                            "ports": ["22", "80", "8080-8089"],
                        },
                    ],
                })
        self.assertEqual(200, status)
        self.verify_resource_uri(body["targetLink"], "/global/firewalls",
                                 self.ctx.firewall_name)
        self.add_resource_cleanup(body["targetLink"])

    @base_gce.GCESmokeTestCase.incremental
    def test_041_check_firewall_info(self):
        (status, body) = self.gce.get("/global/firewalls",
                                      self.ctx.firewall_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.firewall_name, body["name"])
        self.assertTrue(body["description"].startswith("test firewall"))
        self.assertTrue(body["description"].endswith(self.ctx.network_name))
        self.assertEqual(body["network"], self.ctx.network["selfLink"])
        self.assertEqual(body["sourceRanges"], ["0.0.0.0/0"])
        self.assertEqual(2, len(body["allowed"]))
        self.assertIn({"IPProtocol": "icmp"}, body["allowed"])
        tcp_range = next((x for x in body["allowed"]
                          if x["IPProtocol"] == "tcp"), None)
        self.assertIsNotNone(tcp_range)
        self.assertItemsEqual(["22", "80", "8080-8089"], tcp_range["ports"])
        self.verify_resource_uri(body["selfLink"], "/global/firewalls",
                                 self.ctx.firewall_name)

    @base_gce.GCESmokeTestCase.incremental
    def test_050_run_instance(self):
        self.ctx.instance_name = rand_name("instance-")
        disks = []
        if not self.config.gce.skip_bootable_volume:
            disks.append({
                "kind": self.ctx.boot_disk["kind"],
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self.ctx.boot_disk["selfLink"],
                "deviceName": "vda",
                "boot": True,
            })
        if not self.config.gce.skip_empty_volume:
            disks.append({
                "kind": self.ctx.empty_disk["kind"],
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self.ctx.empty_disk["selfLink"],
                "deviceName": "vdb",
                "boot": False,
            })
        body = {
            "name": self.ctx.instance_name,
            "description": "test instance",
            "machineType": self.ctx.machine_type["selfLink"],
            "disks": disks,
            "metadata": {
                "items": [
                    {
                        "key": "sshKeys",
                        "value": ":".join([rand_name("keypair-"),
                                           PUBLIC_KEY])
                    },
                ],
            },
            "networkInterfaces": [{
                "network":
                    self.ctx.network["selfLink"],
            }],
            "tags": {
                "items": [],
            },
        }
        if self.config.gce.skip_bootable_volume:
            body["image"] = self.ctx.image["selfLink"]
        (status, body) = self.gce.zone_post("/instances", body=body)
        self.assertEqual(200, status)
        self.wait_for(body["targetLink"], 200, "RUNNING",
                      self.config.compute.build_timeout,
                      self.config.compute.build_interval,
                      {
                          "idle_http_statuses": (404,),
                          "idle_gce_statuses": ("PROVISIONING",),
                      })
        self.verify_zone_resource_uri(body["targetLink"], "/instances",
                                      self.ctx.instance_name)
        self.add_resource_cleanup(body["targetLink"],
                                  self.config.compute.build_timeout,
                                  self.config.compute.build_interval)

    @base_gce.GCESmokeTestCase.incremental
    def test_051_check_instance_info(self):
        (status, body) = self.gce.zone_get("/instances/",
                                           self.ctx.instance_name)
        self.assertEqual(200, status)
        self.assertEqual(self.ctx.instance_name, body["name"])
        self.assertEqual("test instance", body["description"])
        self.assertEqual("RUNNING", body["status"])
        self.assertEqual("active", body["statusMessage"])
        self.assertEqual(self.ctx.machine_type["selfLink"],
                         body["machineType"])
        nwifs = body.get("networkInterfaces")
        self.assertEqual(1, len(nwifs))
        nwif = nwifs[0]
        self.assertEqual(self.ctx.network_name, nwif["name"])
        cidrs = netaddr.all_matching_cidrs(nwif["networkIP"],
                                           [self.ctx.network_cidr])
        self.assertEqual(1, len(cidrs))
        self.assertEqual(self.ctx.network_cidr, str(cidrs[0]))
        self.verify_zone_resource_uri(body["selfLink"], "/instances",
                                      self.ctx.instance_name)
        self.ctx.instance = body

    @base_gce.GCESmokeTestCase.incremental
    def test_052_ping_instance(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            self.assertTrue(
                    self._ping_ip_address(network_interface["networkIP"]))

    @base_gce.GCESmokeTestCase.incremental
    def test_060_associate_floating_ip(self):
        (status, dummy) = self.gce.zone_post(
                "/instances",
                self.ctx.instance_name,
                "addAccessConfig",
                params={
                    "networkInterface": self.ctx.network_name,
                },
                body={
                    "type": "ONE_TO_ONE_NAT",
                })
        self.assertEqual(200, status)

    @base_gce.GCESmokeTestCase.incremental
    def test_061_get_floating_ip_info(self):
        (status, body) = self.gce.zone_get("/instances/",
                                           self.ctx.instance_name)
        self.assertEqual(200, status)
        nwifs = body.get("networkInterfaces")
        self.assertEqual(1, len(nwifs))
        nwif = nwifs[0]
        fp_infs = nwif.get("accessConfigs")
        self.assertEqual(1, len(fp_infs))
        fp_inf = fp_infs[0]
        self.assertEqual("ONE_TO_ONE_NAT", fp_inf["type"])
        self.assertIsNotNone(fp_inf["natIP"])
        self.ctx.instance = body

    @base_gce.GCESmokeTestCase.incremental
    def test_062_ping_floating_ip(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            floating_ip = network_interface["accessConfigs"][0]["natIP"]
            self.assertTrue(self._ping_ip_address(floating_ip))

    @base_gce.GCESmokeTestCase.incremental
    def test_063_ssh_floating_ip(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            floating_ip = network_interface["accessConfigs"][0]["natIP"]
            self._check_ssh_connectivity(floating_ip,
                                         self.config.compute.image_ssh_user,
                                         PRIVATE_KEY)

    @base_gce.GCESmokeTestCase.incremental
    def test_100_reset_instance(self):
        (status, dummy) = self.gce.zone_post("/instances",
                                             self.ctx.instance_name,
                                             "reset")
        self.assertEqual(200, status)

    @base_gce.GCESmokeTestCase.incremental
    def test_101_ping_reseted_instance(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            self.assertTrue(
                    self._ping_ip_address(network_interface["networkIP"]))

    @base_gce.GCESmokeTestCase.incremental
    def test_900_stop_instance(self):
        instance_link = self.ctx.instance["selfLink"]
        self.cancel_resource_cleanup(instance_link)
        (status, dummy) = self.gce.delete(instance_link)
        self.assertEqual(200, status)
        self.wait_for(instance_link, 404, None,
                      self.config.compute.build_timeout,
                      self.config.compute.build_interval,
                      {
                          "idle_http_statuses": (200,),
                          "idle_gce_statuses": ("RUNNING", "TERMINATED",),
                      })
        self.ctx.instance = None

    @base_gce.GCESmokeTestCase.incremental
    def test_910_delete_network(self):
        network_link = self.ctx.network["selfLink"]
        self.cancel_resource_cleanup(network_link)
        (status, dummy) = self.gce.delete(network_link)
        self.assertEqual(200, status)
        (status, dummy) = self.gce.get(network_link)
        self.assertEqual(404, status)
        self.ctx.network = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.skip_empty_volume,
                      "Skipped by config settings")
    def test_920_delete_empty_disk(self):
        disk_link = self.ctx.empty_disk["selfLink"]
        self.cancel_resource_cleanup(disk_link)
        (status, dummy) = self.gce.delete(disk_link)
        self.assertEqual(200, status)
        self.wait_for(disk_link, 404, None,
                      self.config.volume.build_timeout,
                      self.config.volume.build_interval,
                      {
                          "idle_http_statuses": (200,),
                          "idle_gce_statuses": ("READY", "deleting",),
                      })
        (status, dummy) = self.gce.get(disk_link)
        self.assertEqual(404, status)
        self.ctx.empty_disk = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
            base_gce.GCESmokeTestCase.config.gce.skip_bootable_volume,
            "Skipped by config settings")
    def test_921_delete_bootable_disk(self):
        disk_link = self.ctx.boot_disk["selfLink"]
        self.cancel_resource_cleanup(disk_link)
        (status, dummy) = self.gce.delete(disk_link)
        self.assertEqual(200, status)
        self.wait_for(disk_link, 404, None,
                      self.config.volume.build_timeout,
                      self.config.volume.build_interval,
                      {
                          "idle_http_statuses": (200,),
                          "idle_gce_statuses": ("READY", "deleting",),
                      })
        (status, dummy) = self.gce.get(disk_link)
        self.assertEqual(404, status)
        self.ctx.boot_disk = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(base_gce.GCESmokeTestCase.config.gce.use_existing_image,
                      "Skipped by config settings")
    def test_922_delete_image(self):
        image_link = self.ctx.image["selfLink"]
        self.cancel_resource_cleanup(image_link)
        (status, dummy) = self.gce.delete(image_link)
        self.assertEqual(200, status)
        self.wait_for(image_link, 404, None,
                      self.config.gce.image_saving_timeout,
                      self.config.gce.image_saving_interval,
                      {
                           "idle_http_statuses": (200,),
                           "idle_gce_statuses": ("READY", "pending_delete",),
                      })
        (status, dummy) = self.gce.get(image_link)
        self.assertEqual(404, status)
        self.ctx.image = None
