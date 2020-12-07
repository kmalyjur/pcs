import json

from textwrap import dedent
from unittest import TestCase

from pcs_test.tools.assertions import AssertPcsMixin
from pcs_test.tools.misc import (
    get_tmp_file,
    write_data_to_tmpfile,
)
from pcs_test.tools.pcs_runner import PcsRunner


class UpdateLocal(AssertPcsMixin, TestCase):
    def setUp(self):
        self.corosync_conf_file = get_tmp_file(
            "tier1_cluster_config_update_corosync.conf"
        )
        self.pcs_runner = PcsRunner(
            cib_file=None, corosync_conf_opt=self.corosync_conf_file.name,
        )

    def tearDown(self):
        self.corosync_conf_file.close()

    @staticmethod
    def fixture_corosync_conf_minimal():
        return dedent(
            """\
            totem {
                version: 2
                cluster_name: cluster_name
                transport: knet
                ip_version: ipv6
                crypto_cipher: aes256
                crypto_hash: sha256
            }

            nodelist {
                node {
                    ring0_addr: node1_addr
                    name: node1
                    nodeid: 1
                }

                node {
                    ring0_addr: node2_addr
                    name: node2
                    nodeid: 2
                }
            }

            quorum {
                provider: corosync_votequorum
                two_node: 1
            }

            logging {
                to_logfile: yes
                logfile: /var/log/cluster/corosync.log
                to_syslog: yes
                timestamp: on
            }
            """
        )

    def test_minimal(self):
        write_data_to_tmpfile(
            self.fixture_corosync_conf_minimal(), self.corosync_conf_file
        )
        self.assert_pcs_success(
            "cluster config update transport ip_version=ipv4 totem token=12".split()
        )
        self.assertEqual(
            self.corosync_conf_file.read(),
            dedent(
                """\
                totem {
                    version: 2
                    cluster_name: cluster_name
                    transport: knet
                    ip_version: ipv4
                    crypto_cipher: aes256
                    crypto_hash: sha256
                    token: 12
                }

                nodelist {
                    node {
                        ring0_addr: node1_addr
                        name: node1
                        nodeid: 1
                    }

                    node {
                        ring0_addr: node2_addr
                        name: node2
                        nodeid: 2
                    }
                }

                quorum {
                    provider: corosync_votequorum
                    two_node: 1
                }

                logging {
                    to_logfile: yes
                    logfile: /var/log/cluster/corosync.log
                    to_syslog: yes
                    timestamp: on
                }
                """
            ),
        )

    def test_multiple_options(self):
        write_data_to_tmpfile(
            self.fixture_corosync_conf_minimal(), self.corosync_conf_file
        )
        self.assert_pcs_success(
            (
                "cluster config update "
                "transport ip_version= link_mode=passive "
                "compression level=2 model=zlib threshold=10 "
                "crypto cipher=aes256 hash=sha512 model=openssl "
                "totem consensus=0 downcheck=1 token=12"
            ).split()
        )
        self.assertEqual(
            self.corosync_conf_file.read(),
            dedent(
                """\
                totem {
                    version: 2
                    cluster_name: cluster_name
                    transport: knet
                    crypto_cipher: aes256
                    crypto_hash: sha512
                    consensus: 0
                    downcheck: 1
                    token: 12
                    link_mode: passive
                    knet_compression_level: 2
                    knet_compression_model: zlib
                    knet_compression_threshold: 10
                    crypto_model: openssl
                }

                nodelist {
                    node {
                        ring0_addr: node1_addr
                        name: node1
                        nodeid: 1
                    }

                    node {
                        ring0_addr: node2_addr
                        name: node2
                        nodeid: 2
                    }
                }

                quorum {
                    provider: corosync_votequorum
                    two_node: 1
                }

                logging {
                    to_logfile: yes
                    logfile: /var/log/cluster/corosync.log
                    to_syslog: yes
                    timestamp: on
                }
                """
            ),
        )

    def test_file_does_not_exist(self):
        file_name = self.corosync_conf_file.name + ".non-existing"
        self.pcs_runner.corosync_conf_opt = file_name
        self.assert_pcs_fail(
            "cluster config update transport ip_version=ipv4 totem token=12".split(),
            stdout_full=(
                f"Error: Unable to read Corosync configuration '{file_name}': "
                f"No such file or directory: '{file_name}'\n"
            ),
        )

    def test_validation_errors(self):
        write_data_to_tmpfile(
            self.fixture_corosync_conf_minimal(), self.corosync_conf_file
        )
        self.assert_pcs_fail(
            (
                "cluster config update "
                "transport ip_version=ipvx link_mode=passive "
                "compression level=2 model=zlib threshold=NaN "
                "crypto hash= model=openssl "
                "totem consensus=0 down_check=1 token=12"
            ).split(),
            stdout_full=dedent(
                """\
                Error: invalid totem option 'down_check', allowed options are: 'consensus', 'downcheck', 'fail_recv_const', 'heartbeat_failures_allowed', 'hold', 'join', 'max_messages', 'max_network_delay', 'merge', 'miss_count_const', 'send_join', 'seqno_unchanged_const', 'token', 'token_coefficient', 'token_retransmit', 'token_retransmits_before_loss_const', 'window_size'
                Error: 'ipvx' is not a valid ip_version value, use 'ipv4', 'ipv4-6', 'ipv6', 'ipv6-4'
                Error: 'NaN' is not a valid threshold value, use a non-negative integer
                Error: If crypto option 'cipher' is enabled, crypto option 'hash' must be enabled as well
                Error: Errors have occurred, therefore pcs is unable to continue
                """
            ),
        )
        self.assertEqual(
            self.corosync_conf_file.read(),
            self.fixture_corosync_conf_minimal(),
        )


class ClusterConfigMixin(AssertPcsMixin):
    # pylint: disable=invalid-name
    command = None

    @staticmethod
    def fixture_text_output():
        return dedent(
            """\
            Cluster Name: cluster_name
            Transport: knet
            Nodes:
              node1 (nodeid: 1)
                node1_addr (link: 0)
              node2 (nodeid: 2)
                node2_addr (link: 0)
            Transport Options:
              ip_version: ipv6
            Crypto Options:
              cipher: aes256
              hash: sha256
          """
        )

    @staticmethod
    def fixture_json_output():
        return (
            json.dumps(
                {
                    "cluster_name": "cluster_name",
                    "transport": "KNET",
                    "totem_options": {},
                    "transport_options": {"ip_version": "ipv6"},
                    "compression_options": {},
                    "crypto_options": {"cipher": "aes256", "hash": "sha256"},
                    "nodes": [
                        {
                            "name": "node1",
                            "nodeid": "1",
                            "addrs": [
                                {
                                    "addr": "node1_addr",
                                    "link": "0",
                                    "type": "FQDN",
                                }
                            ],
                        },
                        {
                            "name": "node2",
                            "nodeid": "2",
                            "addrs": [
                                {
                                    "addr": "node2_addr",
                                    "link": "0",
                                    "type": "FQDN",
                                }
                            ],
                        },
                    ],
                    "links_options": {},
                    "quorum_options": {},
                    "quorum_device": None,
                }
            )
            + "\n"
        )

    @staticmethod
    def fixture_cmd_output():
        return dedent(
            """\
            pcs cluster setup cluster_name \\
              node1 addr=node1_addr \\
              node2 addr=node2_addr \\
              transport \\
              knet \\
                  ip_version=ipv6 \\
                crypto \\
                  cipher=aes256 \\
                  hash=sha256
            """
        )

    def setUp(self):
        self.corosync_conf_file = get_tmp_file(
            "tier1_cluster_config_update_corosync.conf"
        )
        self.pcs_runner = PcsRunner(
            cib_file=None, corosync_conf_opt=self.corosync_conf_file.name,
        )
        write_data_to_tmpfile(
            UpdateLocal.fixture_corosync_conf_minimal(), self.corosync_conf_file
        )

    def tearDown(self):
        self.corosync_conf_file.close()

    def test_default_output(self):
        self.assert_pcs_success(
            self.command.split(), stdout_full=self.fixture_text_output(),
        )

    def test_text_output(self):
        self.assert_pcs_success(
            (self.command + " --output-format=text").split(),
            stdout_full=self.fixture_text_output(),
        )

    def test_json_output(self):
        self.assert_pcs_success(
            (self.command + " --output-format=json").split(),
            stdout_full=self.fixture_json_output(),
        )

    def test_cmd_output(self):
        self.assert_pcs_success(
            (self.command + " --output-format=cmd").split(),
            stdout_full=self.fixture_cmd_output(),
        )

    def test_output_format_unsupported_value(self):
        self.assert_pcs_fail(
            (self.command + " --output-format=xml").split(),
            stdout_full=dedent(
                """\
                Error: Unknown value 'xml' for '--output-format' option. Supported values are: 'cmd', 'json', 'text'
                """
            ),
        )

    def test_unsupported_option(self):
        self.assert_pcs_fail(
            (self.command + " --corosync").split(),
            stdout_full=dedent(
                """\
                Error: Specified option '--corosync' is not supported in this command
                """
            ),
        )


class ClusterConfig(ClusterConfigMixin, TestCase):
    command = "cluster config"


class ClusterConfigShow(ClusterConfigMixin, TestCase):
    command = "cluster config show"
