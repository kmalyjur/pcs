# pylint: disable=too-many-lines
from unittest import mock, TestCase

from pcs_test.tools import fixture
from pcs_test.tools.command_env import get_env_tools
from pcs_test.tools.misc import (
    get_test_resource as rc,
    outdent,
)

from pcs import settings
from pcs.common import reports
from pcs.common.reports import codes as report_codes
from pcs.lib.commands import resource
from pcs.lib.errors import LibraryError


TIMEOUT = 10


def create(
    env,
    wait=False,
    disabled=False,
    meta_attributes=None,
    operation_list=None,
    allow_invalid_operation=False,
):
    return resource.create(
        env,
        "A",
        "ocf:heartbeat:Dummy",
        operation_list=operation_list if operation_list else [],
        meta_attributes=meta_attributes if meta_attributes else {},
        instance_attributes={},
        wait=wait,
        ensure_disabled=disabled,
        allow_invalid_operation=allow_invalid_operation,
    )


def create_group(
    env,
    wait=TIMEOUT,
    disabled=False,
    meta_attributes=None,
    operation_list=None,
):
    return resource.create_in_group(
        env,
        "A",
        "ocf:heartbeat:Dummy",
        "G",
        operation_list=operation_list if operation_list else [],
        meta_attributes=meta_attributes if meta_attributes else {},
        instance_attributes={},
        wait=wait,
        ensure_disabled=disabled,
    )


def create_clone(
    env,
    wait=TIMEOUT,
    disabled=False,
    meta_attributes=None,
    clone_options=None,
    operation_list=None,
    clone_id=None,
):
    return resource.create_as_clone(
        env,
        "A",
        "ocf:heartbeat:Dummy",
        operation_list=operation_list if operation_list else [],
        meta_attributes=meta_attributes if meta_attributes else {},
        instance_attributes={},
        clone_meta_options=clone_options if clone_options else {},
        clone_id=clone_id,
        wait=wait,
        ensure_disabled=disabled,
    )


def create_bundle(
    env,
    wait=TIMEOUT,
    disabled=False,
    meta_attributes=None,
    allow_not_accessible_resource=False,
    operation_list=None,
):
    return resource.create_into_bundle(
        env,
        "A",
        "ocf:heartbeat:Dummy",
        operation_list=operation_list if operation_list else [],
        meta_attributes=meta_attributes if meta_attributes else {},
        instance_attributes={},
        bundle_id="B",
        wait=wait,
        ensure_disabled=disabled,
        allow_not_accessible_resource=allow_not_accessible_resource,
    )


wait_error_message = outdent(
    """\
    Pending actions:
            Action 39: stonith-vm-rhel72-1-reboot  on vm-rhel72-1
    Error performing operation: Timer expired
    """
).strip()

fixture_cib_resources_xml_primitive_simplest = """
    <resources>
        <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
            <operations>
                <op id="A-migrate_from-interval-0s" interval="0s"
                    name="migrate_from" timeout="20"
                />
                <op id="A-migrate_to-interval-0s" interval="0s"
                    name="migrate_to" timeout="20"
                />
                <op id="A-monitor-interval-10" interval="10" name="monitor"
                    timeout="20"
                />
                <op id="A-reload-interval-0s" interval="0s" name="reload"
                    timeout="20"
                />
                <op id="A-start-interval-0s" interval="0s" name="start"
                    timeout="20"
                />
                <op id="A-stop-interval-0s" interval="0s" name="stop"
                    timeout="20"
                />
            </operations>
        </primitive>
    </resources>
"""

fixture_cib_resources_xml_simplest_disabled = """<resources>
    <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
        <meta_attributes id="A-meta_attributes">
            <nvpair id="A-meta_attributes-target-role" name="target-role"
                value="Stopped"
            />
        </meta_attributes>
        <operations>
            <op id="A-migrate_from-interval-0s" interval="0s"
                name="migrate_from" timeout="20"
            />
            <op id="A-migrate_to-interval-0s" interval="0s" name="migrate_to"
                timeout="20"
            />
            <op id="A-monitor-interval-10" interval="10" name="monitor"
                timeout="20"
            />
            <op id="A-reload-interval-0s" interval="0s" name="reload"
                timeout="20"
            />
            <op id="A-start-interval-0s" interval="0s" name="start"
                timeout="20"
            />
            <op id="A-stop-interval-0s" interval="0s" name="stop" timeout="20"/>
        </operations>
    </primitive>
</resources>"""

fixture_cib_resources_xml_group_simplest = """<resources>
    <group id="G">
        <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
            <operations>
                <op id="A-migrate_from-interval-0s" interval="0s"
                    name="migrate_from" timeout="20"
                />
                <op id="A-migrate_to-interval-0s" interval="0s"
                    name="migrate_to" timeout="20"
                />
                <op id="A-monitor-interval-10" interval="10" name="monitor"
                    timeout="20"
                />
                <op id="A-reload-interval-0s" interval="0s" name="reload"
                    timeout="20"
                />
                <op id="A-start-interval-0s" interval="0s" name="start"
                    timeout="20"
                />
                <op id="A-stop-interval-0s" interval="0s" name="stop"
                    timeout="20"
                />
            </operations>
        </primitive>
    </group>
</resources>"""


fixture_cib_resources_xml_group_simplest_disabled = """<resources>
    <group id="G">
        <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
            <meta_attributes id="A-meta_attributes">
                <nvpair id="A-meta_attributes-target-role" name="target-role"
                    value="Stopped"
                />
            </meta_attributes>
            <operations>
                <op id="A-migrate_from-interval-0s" interval="0s"
                    name="migrate_from" timeout="20"
                />
                <op id="A-migrate_to-interval-0s" interval="0s"
                    name="migrate_to" timeout="20"
                />
                <op id="A-monitor-interval-10" interval="10" name="monitor"
                    timeout="20"
                />
                <op id="A-reload-interval-0s" interval="0s" name="reload"
                    timeout="20"
                />
                <op id="A-start-interval-0s" interval="0s" name="start"
                    timeout="20"
                />
                <op id="A-stop-interval-0s" interval="0s" name="stop"
                    timeout="20"
                />
            </operations>
        </primitive>
    </group>
</resources>"""


fixture_cib_resources_xml_clone_simplest_template = """<resources>
    <clone id="{clone_id}">
        <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
            <operations>
                <op id="A-migrate_from-interval-0s" interval="0s"
                    name="migrate_from" timeout="20"
                />
                <op id="A-migrate_to-interval-0s" interval="0s"
                    name="migrate_to" timeout="20"
                />
                <op id="A-monitor-interval-10" interval="10" name="monitor"
                    timeout="20"
                />
                <op id="A-reload-interval-0s" interval="0s" name="reload"
                    timeout="20"
                />
                <op id="A-start-interval-0s" interval="0s" name="start"
                    timeout="20"
                />
                <op id="A-stop-interval-0s" interval="0s" name="stop"
                    timeout="20"
                />
            </operations>
        </primitive>
    </clone>
</resources>"""


fixture_cib_resources_xml_clone_simplest = (
    fixture_cib_resources_xml_clone_simplest_template.format(clone_id="A-clone")
)


fixture_cib_resources_xml_clone_custom_id = (
    fixture_cib_resources_xml_clone_simplest_template.format(
        clone_id="CustomCloneId"
    )
)


fixture_cib_resources_xml_clone_simplest_disabled = """<resources>
    <clone id="A-clone">
        <meta_attributes id="A-clone-meta_attributes">
            <nvpair id="A-clone-meta_attributes-target-role"
                name="target-role"
                value="Stopped"
            />
        </meta_attributes>
        <primitive class="ocf" id="A" provider="heartbeat" type="Dummy">
            <operations>
                <op id="A-migrate_from-interval-0s" interval="0s"
                    name="migrate_from" timeout="20"
                />
                <op id="A-migrate_to-interval-0s" interval="0s"
                    name="migrate_to" timeout="20"
                />
                <op id="A-monitor-interval-10" interval="10" name="monitor"
                    timeout="20"
                />
                <op id="A-reload-interval-0s" interval="0s" name="reload"
                    timeout="20"
                />
                <op id="A-start-interval-0s" interval="0s" name="start"
                    timeout="20"
                />
                <op id="A-stop-interval-0s" interval="0s" name="stop"
                    timeout="20"
                />
            </operations>
        </primitive>
    </clone>
</resources>"""


class Create(TestCase):
    fixture_sanitized_operation = """
        <resources>
            <primitive class="ocf" id="A" provider="heartbeat"
                type="Dummy"
            >
                <operations>
                    <op id="A-migrate_from-interval-0s" interval="0s"
                        name="migrate_from" timeout="20"
                    />
                    <op id="A-migrate_to-interval-0s" interval="0s"
                        name="migrate_to" timeout="20"
                    />
                    <op id="A-monitor-interval-20" interval="20"
                        name="moni*tor" timeout="20"
                    />
                    <op id="A-monitor-interval-10" interval="10"
                        name="monitor" timeout="20"
                    />
                    <op id="A-reload-interval-0s" interval="0s"
                        name="reload" timeout="20"
                    />
                    <op id="A-start-interval-0s" interval="0s"
                        name="start" timeout="20"
                    />
                    <op id="A-stop-interval-0s" interval="0s"
                        name="stop" timeout="20"
                    />
                </operations>
            </primitive>
        </resources>
    """

    def setUp(self):
        self.env_assist, self.config = get_env_tools(test_case=self)
        (self.config.runner.pcmk.load_agent().runner.cib.load())

    def test_simplest_resource(self):
        self.config.env.push_cib(
            resources=fixture_cib_resources_xml_primitive_simplest
        )
        return create(self.env_assist.get_env())

    def test_resource_with_operation(self):
        self.config.env.push_cib(
            resources="""
                <resources>
                    <primitive class="ocf" id="A" provider="heartbeat"
                        type="Dummy"
                    >
                        <operations>
                            <op id="A-migrate_from-interval-0s" interval="0s"
                                name="migrate_from" timeout="20"
                            />
                            <op id="A-migrate_to-interval-0s" interval="0s"
                                name="migrate_to" timeout="20"
                            />
                            <op id="A-monitor-interval-10" interval="10"
                                name="monitor" timeout="10s"
                            />
                            <op id="A-reload-interval-0s" interval="0s"
                                name="reload" timeout="20"
                            />
                            <op id="A-start-interval-0s" interval="0s"
                                name="start" timeout="20"
                            />
                            <op id="A-stop-interval-0s" interval="0s"
                                name="stop" timeout="20"
                            />
                        </operations>
                    </primitive>
                </resources>
            """
        )

        create(
            self.env_assist.get_env(),
            operation_list=[
                {"name": "monitor", "timeout": "10s", "interval": "10"}
            ],
        )

    def test_sanitize_operation_id_from_agent(self):
        self.config.runner.pcmk.load_agent(
            instead="runner.pcmk.load_agent",
            agent_filename=(
                "resource_agent_ocf_heartbeat_dummy_insane_action.xml"
            ),
        )
        self.config.env.push_cib(resources=self.fixture_sanitized_operation)
        return create(self.env_assist.get_env())

    def test_sanitize_operation_id_from_user(self):
        self.config.env.push_cib(resources=self.fixture_sanitized_operation)
        create(
            self.env_assist.get_env(),
            operation_list=[
                {"name": "moni*tor", "timeout": "20", "interval": "20"}
            ],
            allow_invalid_operation=True,
        )
        self.env_assist.assert_reports(
            [
                fixture.warn(
                    report_codes.INVALID_OPTION_VALUE,
                    option_name="operation name",
                    option_value="moni*tor",
                    allowed_values=[
                        "start",
                        "stop",
                        "monitor",
                        "reload",
                        "migrate_to",
                        "migrate_from",
                        "meta-data",
                        "validate-all",
                    ],
                    cannot_be_empty=False,
                    forbidden_characters=None,
                ),
            ]
        )

    def test_unique_option(self):
        self.config.runner.cib.load(
            instead="runner.cib.load",
            resources="""
                <resources>
                    <primitive class="ocf" id="X" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="X-instance_attributes">
                            <nvpair
                                id="X-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="A" provider="pacemaker"
                        type="Dummy"
                    >
                        <instance_attributes id="A-instance_attributes">
                            <nvpair
                                id="A-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="B" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="B-instance_attributes">
                            <nvpair
                                id="B-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                </resources>
            """,
        )
        self.env_assist.assert_raise_library_error(
            lambda: resource.create(
                self.env_assist.get_env(),
                "C",
                "ocf:heartbeat:Dummy",
                operation_list=[],
                meta_attributes={},
                instance_attributes={"state": "1"},
            ),
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_INSTANCE_ATTR_VALUE_NOT_UNIQUE,
                    instance_attr_name="state",
                    instance_attr_value="1",
                    agent_name="ocf:heartbeat:Dummy",
                    resource_id_list=["B", "X"],
                    force_code=report_codes.FORCE_OPTIONS,
                )
            ]
        )

    def test_unique_option_forced(self):
        self.config.runner.cib.load(
            instead="runner.cib.load",
            resources="""
                <resources>
                    <primitive class="ocf" id="X" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="X-instance_attributes">
                            <nvpair
                                id="X-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="A" provider="pacemaker"
                        type="Dummy"
                    >
                        <instance_attributes id="A-instance_attributes">
                            <nvpair
                                id="A-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="B" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="B-instance_attributes">
                            <nvpair
                                id="B-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                </resources>
            """,
        )
        self.config.env.push_cib(
            resources="""
                <resources>
                    <primitive class="ocf" id="X" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="X-instance_attributes">
                            <nvpair
                                id="X-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="A" provider="pacemaker"
                        type="Dummy"
                    >
                        <instance_attributes id="A-instance_attributes">
                            <nvpair
                                id="A-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="B" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="B-instance_attributes">
                            <nvpair
                                id="B-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                    </primitive>
                    <primitive class="ocf" id="C" provider="heartbeat"
                        type="Dummy"
                    >
                        <instance_attributes id="C-instance_attributes">
                            <nvpair
                                id="C-instance_attributes-state"
                                name="state"
                                value="1"
                            />
                        </instance_attributes>
                        <operations>
                            <op id="C-monitor-interval-10" interval="10"
                                name="monitor" timeout="20"
                            />
                        </operations>
                    </primitive>
                </resources>
            """
        )
        resource.create(
            self.env_assist.get_env(),
            "C",
            "ocf:heartbeat:Dummy",
            operation_list=[],
            meta_attributes={},
            instance_attributes={"state": "1"},
            use_default_operations=False,
            allow_invalid_instance_attributes=True,
        )
        self.env_assist.assert_reports(
            [
                fixture.warn(
                    report_codes.RESOURCE_INSTANCE_ATTR_VALUE_NOT_UNIQUE,
                    instance_attr_name="state",
                    instance_attr_value="1",
                    agent_name="ocf:heartbeat:Dummy",
                    resource_id_list=["B", "X"],
                )
            ]
        )

    def test_cib_upgrade_on_onfail_demote(self):
        self.config.runner.cib.load(
            filename="cib-empty-3.3.xml",
            instead="runner.cib.load",
            name="load_cib_old_version",
        )
        self.config.runner.cib.upgrade()
        self.config.runner.cib.load(filename="cib-empty-3.4.xml")
        self.config.env.push_cib(
            resources="""
                <resources>
                    <primitive class="ocf" id="A" provider="heartbeat"
                        type="Dummy"
                    >
                        <operations>
                            <op id="A-migrate_from-interval-0s" interval="0s"
                                name="migrate_from" timeout="20"
                            />
                            <op id="A-migrate_to-interval-0s" interval="0s"
                                name="migrate_to" timeout="20"
                            />
                            <op id="A-monitor-interval-10" interval="10"
                                name="monitor" timeout="10" on-fail="demote"
                            />
                            <op id="A-reload-interval-0s" interval="0s"
                                name="reload" timeout="20"
                            />
                            <op id="A-start-interval-0s" interval="0s"
                                name="start" timeout="20"
                            />
                            <op id="A-stop-interval-0s" interval="0s"
                                name="stop" timeout="20"
                            />
                        </operations>
                    </primitive>
                </resources>
            """
        )

        create(
            self.env_assist.get_env(),
            operation_list=[
                {
                    "name": "monitor",
                    "timeout": "10",
                    "interval": "10",
                    "on-fail": "demote",
                }
            ],
        )
        self.env_assist.assert_reports(
            [fixture.info(report_codes.CIB_UPGRADE_SUCCESSFUL)]
        )


@mock.patch.object(settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng"))
class CreateWait(TestCase):
    def setUp(self):
        self.env_assist, self.config = get_env_tools(test_case=self)
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load()
            .env.push_cib(
                resources=fixture_cib_resources_xml_primitive_simplest,
                wait=TIMEOUT,
            )
        )

    def test_fail_wait(self):
        self.config.env.push_cib(
            resources=fixture_cib_resources_xml_primitive_simplest,
            wait=TIMEOUT,
            exception=LibraryError(
                reports.item.ReportItem.error(
                    reports.messages.WaitForIdleTimedOut(wait_error_message)
                )
            ),
            instead="env.push_cib",
        )
        self.env_assist.assert_raise_library_error(
            lambda: create(self.env_assist.get_env(), wait=TIMEOUT),
            [fixture.report_wait_for_idle_timed_out(wait_error_message)],
            expected_in_processor=False,
        )

    def test_wait_ok_run_fail(self):
        (self.config.runner.pcmk.load_state(raw_resources=dict(failed="true")))

        self.env_assist.assert_raise_library_error(
            lambda: create(self.env_assist.get_env(), wait=TIMEOUT)
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    def test_wait_ok_run_ok(self):
        self.config.runner.pcmk.load_state(raw_resources=dict())
        create(self.env_assist.get_env(), wait=TIMEOUT)
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                ),
            ]
        )

    def test_wait_ok_disable_fail(self):
        (
            self.config.runner.pcmk.load_state(
                raw_resources=dict()
            ).env.push_cib(
                resources=fixture_cib_resources_xml_simplest_disabled,
                wait=TIMEOUT,
                instead="env.push_cib",
            )
        )

        self.env_assist.assert_raise_library_error(
            lambda: create(
                self.env_assist.get_env(), wait=TIMEOUT, disabled=True
            )
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                ),
            ]
        )

    def test_wait_ok_disable_ok(self):
        (
            self.config.runner.pcmk.load_state(
                raw_resources=dict(role="Stopped")
            ).env.push_cib(
                resources=fixture_cib_resources_xml_simplest_disabled,
                wait=TIMEOUT,
                instead="env.push_cib",
            )
        )

        create(self.env_assist.get_env(), wait=TIMEOUT, disabled=True)
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    def test_wait_ok_disable_ok_by_target_role(self):
        (
            self.config.runner.pcmk.load_state(
                raw_resources=dict(role="Stopped")
            ).env.push_cib(
                resources=fixture_cib_resources_xml_simplest_disabled,
                wait=TIMEOUT,
                instead="env.push_cib",
            )
        )
        create(
            self.env_assist.get_env(),
            wait=TIMEOUT,
            meta_attributes={"target-role": "Stopped"},
        )

        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )


class CreateInGroup(TestCase):
    def setUp(self):
        self.env_assist, self.config = get_env_tools(test_case=self)
        self.config.runner.pcmk.load_agent()
        self.config.runner.cib.load()

    def test_simplest_resource(self):
        (
            self.config.env.push_cib(
                resources="""
                    <resources>
                        <group id="G">
                            <primitive class="ocf" id="A" provider="heartbeat"
                                type="Dummy"
                            >
                                <operations>
                                    <op id="A-migrate_from-interval-0s"
                                        interval="0s" name="migrate_from"
                                        timeout="20"
                                    />
                                    <op id="A-migrate_to-interval-0s"
                                        interval="0s" name="migrate_to"
                                        timeout="20"
                                    />
                                    <op id="A-monitor-interval-10" interval="10"
                                        name="monitor" timeout="20"
                                    />
                                    <op id="A-reload-interval-0s" interval="0s"
                                        name="reload" timeout="20"
                                    />
                                    <op id="A-start-interval-0s" interval="0s"
                                        name="start" timeout="20"
                                    />
                                    <op id="A-stop-interval-0s" interval="0s"
                                        name="stop" timeout="20"
                                    />
                                </operations>
                            </primitive>
                        </group>
                    </resources>
                """
            )
        )

        create_group(self.env_assist.get_env(), wait=False)

    def test_cib_upgrade_on_onfail_demote(self):
        self.config.runner.cib.load(
            filename="cib-empty-3.3.xml",
            instead="runner.cib.load",
            name="load_cib_old_version",
        )
        self.config.runner.cib.upgrade()
        self.config.runner.cib.load(filename="cib-empty-3.4.xml")
        self.config.env.push_cib(
            resources="""
                <resources>
                    <group id="G">
                        <primitive class="ocf" id="A" provider="heartbeat"
                            type="Dummy"
                        >
                            <operations>
                                <op id="A-migrate_from-interval-0s"
                                    interval="0s" name="migrate_from"
                                    timeout="20"
                                />
                                <op id="A-migrate_to-interval-0s"
                                    interval="0s" name="migrate_to"
                                    timeout="20"
                                />
                                <op id="A-monitor-interval-10" interval="10"
                                    name="monitor" timeout="10" on-fail="demote"
                                />
                                <op id="A-reload-interval-0s" interval="0s"
                                    name="reload" timeout="20"
                                />
                                <op id="A-start-interval-0s" interval="0s"
                                    name="start" timeout="20"
                                />
                                <op id="A-stop-interval-0s" interval="0s"
                                    name="stop" timeout="20"
                                />
                            </operations>
                        </primitive>
                    </group>
                </resources>
            """
        )

        create_group(
            self.env_assist.get_env(),
            operation_list=[
                {
                    "name": "monitor",
                    "timeout": "10",
                    "interval": "10",
                    "on-fail": "demote",
                }
            ],
            wait=False,
        )
        self.env_assist.assert_reports(
            [fixture.info(report_codes.CIB_UPGRADE_SUCCESSFUL)]
        )

    def test_fail_wait(self):
        self.config.env.push_cib(
            resources=fixture_cib_resources_xml_group_simplest,
            wait=TIMEOUT,
            exception=LibraryError(
                reports.item.ReportItem.error(
                    reports.messages.WaitForIdleTimedOut(wait_error_message)
                )
            ),
        )

        self.env_assist.assert_raise_library_error(
            lambda: create_group(self.env_assist.get_env()),
            [fixture.report_wait_for_idle_timed_out(wait_error_message)],
            expected_in_processor=False,
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_fail(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_group_simplest, wait=TIMEOUT
            ).runner.pcmk.load_state(raw_resources=dict(failed="true"))
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_group(self.env_assist.get_env())
        )
        self.env_assist.assert_reports(
            [fixture.error(report_codes.RESOURCE_DOES_NOT_RUN, resource_id="A")]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_ok(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_group_simplest, wait=TIMEOUT
            ).runner.pcmk.load_state(raw_resources=dict())
        )
        create_group(self.env_assist.get_env())
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_fail(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_group_simplest_disabled,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict())
        )

        self.env_assist.assert_raise_library_error(
            lambda: create_group(self.env_assist.get_env(), disabled=True)
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_group_simplest_disabled,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_group(self.env_assist.get_env(), disabled=True)
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok_by_target_role(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_group_simplest_disabled,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_group(
            self.env_assist.get_env(),
            meta_attributes={"target-role": "Stopped"},
        )
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )


class CreateAsClone(TestCase):
    def setUp(self):
        self.env_assist, self.config = get_env_tools(test_case=self)
        self.config.runner.pcmk.load_agent()
        self.config.runner.cib.load()

    def test_simplest_resource(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_simplest
            )
        )
        create_clone(self.env_assist.get_env(), wait=False)

    def test_custom_clone_id(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_custom_id
            )
        )
        create_clone(
            self.env_assist.get_env(), wait=False, clone_id="CustomCloneId"
        )

    def test_custom_clone_id_error_invalid_id(self):
        self.env_assist.assert_raise_library_error(
            lambda: create_clone(
                self.env_assist.get_env(), wait=False, clone_id="1invalid"
            ),
        )
        self.env_assist.assert_reports(
            [fixture.report_invalid_id("1invalid", "1")],
        )

    def test_custom_clone_id_error_id_already_exist(self):
        self.config.remove(name="runner.cib.load")
        self.config.runner.cib.load(
            resources="""
                <resources>
                    <primitive class="ocf" id="C" provider="heartbeat"
                        type="Dummy"
                    >
                        <operations>
                            <op id="C-monitor-interval-10s" interval="10s"
                                name="monitor" timeout="20s"/>
                        </operations>
                    </primitive>
                </resources>
            """,
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_clone(
                self.env_assist.get_env(), wait=False, clone_id="C"
            ),
        )
        self.env_assist.assert_reports([fixture.report_id_already_exist("C")])

    def test_cib_upgrade_on_onfail_demote(self):
        self.config.runner.cib.load(
            filename="cib-empty-3.3.xml",
            instead="runner.cib.load",
            name="load_cib_old_version",
        )
        self.config.runner.cib.upgrade()
        self.config.runner.cib.load(filename="cib-empty-3.4.xml")
        self.config.env.push_cib(
            resources="""<resources>
                <clone id="A-clone">
                    <primitive class="ocf" id="A" provider="heartbeat"
                        type="Dummy"
                    >
                        <operations>
                            <op id="A-migrate_from-interval-0s" interval="0s"
                                name="migrate_from" timeout="20"
                            />
                            <op id="A-migrate_to-interval-0s" interval="0s"
                                name="migrate_to" timeout="20"
                            />
                            <op id="A-monitor-interval-10" interval="10"
                                name="monitor" timeout="10" on-fail="demote"
                            />
                            <op id="A-reload-interval-0s" interval="0s"
                                name="reload" timeout="20"
                            />
                            <op id="A-start-interval-0s" interval="0s"
                                name="start" timeout="20"
                            />
                            <op id="A-stop-interval-0s" interval="0s"
                                name="stop" timeout="20"
                            />
                        </operations>
                    </primitive>
                </clone>
            </resources>"""
        )

        create_clone(
            self.env_assist.get_env(),
            operation_list=[
                {
                    "name": "monitor",
                    "timeout": "10",
                    "interval": "10",
                    "on-fail": "demote",
                }
            ],
            wait=False,
        )
        self.env_assist.assert_reports(
            [fixture.info(report_codes.CIB_UPGRADE_SUCCESSFUL)]
        )

    def test_fail_wait(self):
        self.config.env.push_cib(
            resources=fixture_cib_resources_xml_clone_simplest,
            wait=TIMEOUT,
            exception=LibraryError(
                reports.item.ReportItem.error(
                    reports.messages.WaitForIdleTimedOut(wait_error_message)
                )
            ),
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_clone(self.env_assist.get_env()),
            [fixture.report_wait_for_idle_timed_out(wait_error_message)],
            expected_in_processor=False,
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_fail(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_simplest, wait=TIMEOUT
            ).runner.pcmk.load_state(raw_resources=dict(failed="true"))
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_clone(self.env_assist.get_env())
        )
        self.env_assist.assert_reports(
            [fixture.error(report_codes.RESOURCE_DOES_NOT_RUN, resource_id="A")]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_ok(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_simplest, wait=TIMEOUT
            ).runner.pcmk.load_state(raw_resources=dict())
        )
        create_clone(self.env_assist.get_env())
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_fail(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_simplest_disabled,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict())
        )

        self.env_assist.assert_raise_library_error(
            lambda: create_clone(self.env_assist.get_env(), disabled=True)
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    roles_with_nodes={"Started": ["node1"]},
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok(self):
        (
            self.config.env.push_cib(
                resources=fixture_cib_resources_xml_clone_simplest_disabled,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_clone(self.env_assist.get_env(), disabled=True)
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok_by_target_role(self):
        (
            self.config.env.push_cib(
                resources="""
                    <resources>
                        <clone id="A-clone">
                            <primitive class="ocf" id="A" provider="heartbeat"
                                type="Dummy"
                            >
                                <meta_attributes id="A-meta_attributes">
                                    <nvpair id="A-meta_attributes-target-role"
                                        name="target-role"
                                        value="Stopped"
                                    />
                                </meta_attributes>
                                <operations>
                                    <op id="A-migrate_from-interval-0s"
                                        interval="0s" name="migrate_from"
                                        timeout="20"
                                    />
                                    <op id="A-migrate_to-interval-0s"
                                        interval="0s" name="migrate_to"
                                        timeout="20"
                                    />
                                    <op id="A-monitor-interval-10" interval="10"
                                        name="monitor" timeout="20"
                                    />
                                    <op id="A-reload-interval-0s" interval="0s"
                                        name="reload" timeout="20"
                                    />
                                    <op id="A-start-interval-0s" interval="0s"
                                        name="start" timeout="20"
                                    />
                                    <op id="A-stop-interval-0s" interval="0s"
                                        name="stop" timeout="20"
                                    />
                                </operations>
                            </primitive>
                        </clone>
                    </resources>
                """,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_clone(
            self.env_assist.get_env(),
            meta_attributes={"target-role": "Stopped"},
        )
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok_by_target_role_in_clone(self):
        (
            self.config.env.push_cib(
                resources="""
                    <resources>
                        <clone id="A-clone">
                            <primitive class="ocf" id="A" provider="heartbeat"
                                type="Dummy"
                            >
                                <operations>
                                    <op id="A-migrate_from-interval-0s"
                                        interval="0s" name="migrate_from"
                                        timeout="20"
                                    />
                                    <op id="A-migrate_to-interval-0s"
                                        interval="0s" name="migrate_to"
                                        timeout="20"
                                    />
                                    <op id="A-monitor-interval-10" interval="10"
                                        name="monitor" timeout="20"
                                    />
                                    <op id="A-reload-interval-0s" interval="0s"
                                        name="reload" timeout="20"
                                    />
                                    <op id="A-start-interval-0s" interval="0s"
                                        name="start" timeout="20"
                                    />
                                    <op id="A-stop-interval-0s" interval="0s"
                                        name="stop" timeout="20"
                                    />
                                </operations>
                            </primitive>
                            <meta_attributes id="A-clone-meta_attributes">
                                <nvpair id="A-clone-meta_attributes-target-role"
                                    name="target-role" value="Stopped"
                                />
                            </meta_attributes>
                        </clone>
                    </resources>
                """,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_clone(
            self.env_assist.get_env(), clone_options={"target-role": "Stopped"}
        )
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok_by_clone_max(self):
        (
            self.config.env.push_cib(
                resources="""
                    <resources>
                        <clone id="A-clone">
                            <primitive class="ocf" id="A" provider="heartbeat"
                                type="Dummy"
                            >
                                <operations>
                                    <op id="A-migrate_from-interval-0s"
                                        interval="0s" name="migrate_from"
                                        timeout="20"
                                    />
                                    <op id="A-migrate_to-interval-0s"
                                        interval="0s" name="migrate_to"
                                        timeout="20"
                                    />
                                    <op id="A-monitor-interval-10" interval="10"
                                        name="monitor" timeout="20"
                                    />
                                    <op id="A-reload-interval-0s" interval="0s"
                                        name="reload" timeout="20"
                                    />
                                    <op id="A-start-interval-0s" interval="0s"
                                        name="start" timeout="20"
                                    />
                                    <op id="A-stop-interval-0s" interval="0s"
                                        name="stop" timeout="20"
                                    />
                                </operations>
                            </primitive>
                            <meta_attributes id="A-clone-meta_attributes">
                                <nvpair id="A-clone-meta_attributes-clone-max"
                                    name="clone-max" value="0"
                                />
                            </meta_attributes>
                        </clone>
                    </resources>
                """,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_clone(
            self.env_assist.get_env(), clone_options={"clone-max": "0"}
        )
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_disable_ok_by_clone_node_max(self):
        (
            self.config.env.push_cib(
                resources="""
                    <resources>
                        <clone id="A-clone">
                            <primitive class="ocf" id="A" provider="heartbeat"
                                type="Dummy"
                            >
                                <operations>
                                    <op id="A-migrate_from-interval-0s"
                                        interval="0s" name="migrate_from"
                                        timeout="20"
                                    />
                                    <op id="A-migrate_to-interval-0s"
                                        interval="0s" name="migrate_to"
                                        timeout="20"
                                    />
                                    <op id="A-monitor-interval-10" interval="10"
                                        name="monitor" timeout="20"
                                    />
                                    <op id="A-reload-interval-0s" interval="0s"
                                        name="reload" timeout="20"
                                    />
                                    <op id="A-start-interval-0s" interval="0s"
                                        name="start" timeout="20"
                                    />
                                    <op id="A-stop-interval-0s" interval="0s"
                                        name="stop" timeout="20"
                                    />
                                </operations>
                            </primitive>
                            <meta_attributes id="A-clone-meta_attributes">
                                <nvpair
                                    id="A-clone-meta_attributes-clone-node-max"
                                    name="clone-node-max" value="0"
                                />
                            </meta_attributes>
                        </clone>
                    </resources>
                """,
                wait=TIMEOUT,
            ).runner.pcmk.load_state(raw_resources=dict(role="Stopped"))
        )
        create_clone(
            self.env_assist.get_env(), clone_options={"clone-node-max": "0"}
        )
        self.env_assist.assert_reports(
            [
                fixture.info(
                    report_codes.RESOURCE_DOES_NOT_RUN,
                    resource_id="A",
                )
            ]
        )


class CreateInToBundle(TestCase):
    fixture_empty_resources = "<resources />"

    fixture_resources_pre = """
        <resources>
            <bundle id="B">
                <network control-port="12345" ip-range-start="192.168.100.200"/>
            </bundle>
        </resources>
    """

    fixture_resource_post_simple_without_network = """
        <resources>
            <bundle id="B">
                {network}
                <primitive
                    class="ocf" id="A" provider="heartbeat" type="Dummy"
                >
                    <operations>
                        <op id="A-migrate_from-interval-0s" interval="0s"
                            name="migrate_from" timeout="20"
                        />
                        <op id="A-migrate_to-interval-0s" interval="0s"
                            name="migrate_to" timeout="20"
                        />
                        <op id="A-monitor-interval-10" interval="10"
                            name="monitor" timeout="20" {onfail}
                        />
                        <op id="A-reload-interval-0s" interval="0s" name="reload"
                            timeout="20"
                        />
                        <op id="A-start-interval-0s" interval="0s"
                            name="start" timeout="20"
                        />
                        <op id="A-stop-interval-0s" interval="0s"
                            name="stop" timeout="20"
                        />
                    </operations>
                </primitive>
            </bundle>
        </resources>
    """

    # fmt: off
    fixture_resources_post_simple = (
        fixture_resource_post_simple_without_network.format(
            network="""
                <network control-port="12345" ip-range-start="192.168.100.200"/>
            """,
            onfail=""
        )
    )
    # fmt: on

    fixture_resources_post_disabled = """
        <resources>
            <bundle id="B">
                <network control-port="12345" ip-range-start="192.168.100.200"/>
                <primitive
                    class="ocf" id="A" provider="heartbeat" type="Dummy"
                >
                    <meta_attributes id="A-meta_attributes">
                        <nvpair id="A-meta_attributes-target-role"
                            name="target-role" value="Stopped"
                        />
                    </meta_attributes>
                    <operations>
                        <op id="A-migrate_from-interval-0s" interval="0s"
                            name="migrate_from" timeout="20"
                        />
                        <op id="A-migrate_to-interval-0s" interval="0s"
                            name="migrate_to" timeout="20"
                        />
                        <op id="A-monitor-interval-10" interval="10"
                            name="monitor" timeout="20"
                        />
                        <op id="A-reload-interval-0s" interval="0s" name="reload"
                            timeout="20"
                        />
                        <op id="A-start-interval-0s" interval="0s"
                            name="start" timeout="20"
                        />
                        <op id="A-stop-interval-0s" interval="0s"
                            name="stop" timeout="20"
                        />
                    </operations>
                </primitive>
            </bundle>
        </resources>
    """

    fixture_status_stopped = """
        <resources>
            <bundle id="B" managed="true">
                <replica id="0">
                    <resource id="B-0" managed="true" role="Stopped" />
                </replica>
            </bundle>
        </resources>
    """

    fixture_status_running_with_primitive = """
        <resources>
            <bundle id="B" managed="true">
                <replica id="0">
                    <resource id="B-0" managed="true" role="Started">
                        <node name="node1" id="1" cached="false"/>
                    </resource>
                    <resource id="A" managed="true" role="Started">
                        <node name="node1" id="1" cached="false"/>
                    </resource>
                </replica>
            </bundle>
        </resources>
    """

    fixture_status_primitive_not_running = """
        <resources>
            <bundle id="B" managed="true">
                <replica id="0">
                    <resource id="B-0" managed="true" role="Started">
                        <node name="node1" id="1" cached="false"/>
                    </resource>
                    <resource id="A" managed="true" role="Stopped"/>
                </replica>
            </bundle>
        </resources>
    """

    def setUp(self):
        self.env_assist, self.config = get_env_tools(
            test_case=self,
            base_cib_filename="cib-empty-2.8.xml",
        )

    def test_upgrade_cib(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(
                filename="cib-empty-2.0.xml", name="load_cib_old_version"
            )
            .runner.cib.upgrade()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(resources=self.fixture_resources_post_simple)
        )
        create_bundle(self.env_assist.get_env(), wait=False)
        self.env_assist.assert_reports(
            [fixture.info(report_codes.CIB_UPGRADE_SUCCESSFUL)]
        )

    def test_cib_upgrade_on_onfail_demote(self):
        self.config.runner.pcmk.load_agent()
        self.config.runner.cib.load(
            filename="cib-empty-3.3.xml",
            name="load_cib_old_version",
        )
        self.config.runner.cib.upgrade()
        self.config.runner.cib.load(
            filename="cib-empty-3.4.xml", resources=self.fixture_resources_pre
        )
        self.config.env.push_cib(
            resources=self.fixture_resource_post_simple_without_network.format(
                network="""
                    <network
                        control-port="12345" ip-range-start="192.168.100.200"
                    />
                """,
                onfail='on-fail="demote"',
            )
        )

        create_bundle(
            self.env_assist.get_env(),
            operation_list=[
                {
                    "name": "monitor",
                    "timeout": "20",
                    "interval": "10",
                    "on-fail": "demote",
                }
            ],
            wait=False,
        )
        self.env_assist.assert_reports(
            [fixture.info(report_codes.CIB_UPGRADE_SUCCESSFUL)]
        )

    def test_simplest_resource(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(resources=self.fixture_resources_post_simple)
        )
        create_bundle(self.env_assist.get_env(), wait=False)

    def test_bundle_doesnt_exist(self):
        (
            self.config.runner.pcmk.load_agent().runner.cib.load(
                resources=self.fixture_empty_resources
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env(), wait=False),
            [
                fixture.error(
                    report_codes.ID_NOT_FOUND,
                    id="B",
                    expected_types=["bundle"],
                    context_type="resources",
                    context_id="",
                )
            ],
            expected_in_processor=False,
        )

    def test_id_not_bundle(self):
        (
            self.config.runner.pcmk.load_agent().runner.cib.load(
                resources="""
                    <resources>
                        <primitive id="B"/>
                    </resources>
                """
            )
        )

        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env(), wait=False),
            [
                fixture.error(
                    report_codes.ID_BELONGS_TO_UNEXPECTED_TYPE,
                    id="B",
                    expected_types=["bundle"],
                    current_type="primitive",
                )
            ],
            expected_in_processor=False,
        )

    def test_bundle_not_empty(self):
        (
            self.config.runner.pcmk.load_agent().runner.cib.load(
                resources="""
                    <resources>
                        <bundle id="B">
                            <network control-port="12345"/>
                            <primitive id="P"/>
                        </bundle>
                    </resources>
                """
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env(), wait=False),
            [
                fixture.error(
                    report_codes.RESOURCE_BUNDLE_ALREADY_CONTAINS_A_RESOURCE,
                    bundle_id="B",
                    resource_id="P",
                )
            ],
            expected_in_processor=False,
        )

    def test_wait_fail(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(
                resources=self.fixture_resources_post_simple,
                wait=TIMEOUT,
                exception=LibraryError(
                    reports.item.ReportItem.error(
                        reports.messages.WaitForIdleTimedOut(wait_error_message)
                    )
                ),
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env()),
            [
                fixture.report_wait_for_idle_timed_out(wait_error_message),
            ],
            expected_in_processor=False,
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_ok(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(
                resources=self.fixture_resources_post_simple, wait=TIMEOUT
            )
            .runner.pcmk.load_state(
                resources=self.fixture_status_running_with_primitive
            )
        )
        create_bundle(self.env_assist.get_env())
        self.env_assist.assert_reports(
            [
                fixture.report_resource_running("A", {"Started": ["node1"]}),
            ]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_wait_ok_run_fail(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(
                resources=self.fixture_resources_post_simple, wait=TIMEOUT
            )
            .runner.pcmk.load_state(
                resources=self.fixture_status_primitive_not_running
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env())
        )
        self.env_assist.assert_reports(
            [fixture.error(report_codes.RESOURCE_DOES_NOT_RUN, resource_id="A")]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_disabled_wait_ok_not_running(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(
                resources=self.fixture_resources_post_disabled, wait=TIMEOUT
            )
            .runner.pcmk.load_state(
                resources=self.fixture_status_primitive_not_running
            )
        )
        create_bundle(self.env_assist.get_env(), disabled=True)
        self.env_assist.assert_reports(
            [fixture.report_resource_not_running("A")]
        )

    @mock.patch.object(
        settings, "crm_mon_schema", rc("crm_mon_rng/crm_mon.rng")
    )
    def test_disabled_wait_ok_running(self):
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=self.fixture_resources_pre)
            .env.push_cib(
                resources=self.fixture_resources_post_disabled, wait=TIMEOUT
            )
            .runner.pcmk.load_state(
                resources=self.fixture_status_running_with_primitive
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env(), disabled=True)
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    report_codes.RESOURCE_RUNNING_ON_NODES,
                    resource_id="A",
                    roles_with_nodes={"Started": ["node1"]},
                )
            ]
        )

    def test_no_port_no_ip(self):
        resources_fixture = """
            <resources>
                <bundle id="B"/>
            </resources>
        """
        (
            self.config.runner.pcmk.load_agent().runner.cib.load(
                resources=resources_fixture
            )
        )
        self.env_assist.assert_raise_library_error(
            lambda: create_bundle(self.env_assist.get_env(), wait=False)
        )
        self.env_assist.assert_reports(
            [
                fixture.error(
                    # pylint: disable=line-too-long
                    report_codes.RESOURCE_IN_BUNDLE_NOT_ACCESSIBLE,
                    bundle_id="B",
                    inner_resource_id="A",
                    force_code=report_codes.FORCE_RESOURCE_IN_BUNDLE_NOT_ACCESSIBLE,
                )
            ]
        )

    def test_no_port_no_ip_forced(self):
        resources_fixture = """
            <resources>
                <bundle id="B"/>
            </resources>
        """
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=resources_fixture)
            .env.push_cib(
                resources=(
                    self.fixture_resource_post_simple_without_network.format(
                        network="", onfail=""
                    )
                )
            )
        )
        create_bundle(
            self.env_assist.get_env(),
            wait=False,
            allow_not_accessible_resource=True,
        )
        self.env_assist.assert_reports(
            [
                fixture.warn(
                    report_codes.RESOURCE_IN_BUNDLE_NOT_ACCESSIBLE,
                    bundle_id="B",
                    inner_resource_id="A",
                )
            ]
        )

    def _test_with_network_defined(self, network):
        resources_fixture = """
            <resources>
                <bundle id="B">
                    {network}
                </bundle>
            </resources>
        """.format(
            network=network
        )
        (
            self.config.runner.pcmk.load_agent()
            .runner.cib.load(resources=resources_fixture)
            .env.push_cib(
                resources=(
                    self.fixture_resource_post_simple_without_network.format(
                        network=network, onfail=""
                    )
                )
            )
        )
        create_bundle(self.env_assist.get_env(), wait=False)

    def test_port_defined(self):
        self._test_with_network_defined('<network control-port="12345"/>')

    def test_ip_range_defined(self):
        self._test_with_network_defined(
            '<network ip-range-start="192.168.100.200"/>'
        )
