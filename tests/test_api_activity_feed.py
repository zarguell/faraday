'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
import datetime
import pytest

from tests.factories import (WorkspaceFactory,
                             VulnerabilityFactory,
                             CommandFactory,
                             EmptyCommandFactory,
                             HostFactory,
                             CommandObjectFactory)


@pytest.mark.usefixtures('logged_user')
class TestActivityFeed:

    @pytest.mark.usefixtures('ignore_nplusone')
    def test_activity_feed(self, test_client, session):
        ws = WorkspaceFactory.create(name="abc")
        command = CommandFactory.create(workspace=ws, tool="nessus")
        session.add(ws)
        session.add(command)
        session.commit()

        res = test_client.get(f'/v3/ws/{ws.name}/activities')

        assert res.status_code == 200
        activities = res.json['activities'][0]
        assert activities['hosts_count'] == 1
        assert activities['vulnerabilities_count'] == 1
        assert activities['tool'] == 'nessus'

    def test_load_itime(self, test_client, session):
        ws = WorkspaceFactory.create(name="abc")
        command = CommandFactory.create(workspace=ws)
        session.add(ws)
        session.add(command)
        session.commit()

        new_start_date = command.end_date - datetime.timedelta(days=1)
        data = {
            'command': command.command,
            'tool': command.tool,
            'itime': new_start_date.timestamp()

        }

        res = test_client.put(f'/v3/ws/{ws.name}/activities/{command.id}',
                data=data,
            )
        assert res.status_code == 200

        # Changing res.json['itime'] to timestamp format of itime
        res_itime = res.json['itime'] / 1000.0
        assert res.status_code == 200
        assert datetime.datetime.fromtimestamp(res_itime) == new_start_date

    @pytest.mark.usefixtures('ignore_nplusone')
    def test_verify_correct_severities_sum_values(self, session, test_client):
        workspace = WorkspaceFactory.create()
        command = EmptyCommandFactory.create(workspace=workspace)
        host = HostFactory.create(workspace=workspace)
        vuln_critical = VulnerabilityFactory.create(severity='critical', workspace=workspace, host=host, service=None)
        vuln_high = VulnerabilityFactory.create(severity='high', workspace=workspace, host=host, service=None)
        vuln_med = VulnerabilityFactory.create(severity='medium', workspace=workspace, host=host, service=None)
        vuln_med2 = VulnerabilityFactory.create(severity='medium', workspace=workspace, host=host, service=None)
        vuln_low = VulnerabilityFactory.create(severity='low', workspace=workspace, host=host, service=None)
        vuln_info = VulnerabilityFactory.create(severity='informational', workspace=workspace, host=host, service=None)
        vuln_info2 = VulnerabilityFactory.create(severity='informational', workspace=workspace, host=host, service=None)
        vuln_unclassified = VulnerabilityFactory.create(severity='unclassified', workspace=workspace, host=host, service=None)
        session.flush()
        CommandObjectFactory.create(
            command=command,
            object_type='host',
            object_id=host.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_critical.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_high.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_med.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_med2.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_low.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_info.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_info2.id,
            workspace=workspace
        )
        CommandObjectFactory.create(
            command=command,
            object_type='vulnerability',
            object_id=vuln_unclassified.id,
            workspace=workspace
        )
        session.commit()
        res = test_client.get(f'/v3/ws/{command.workspace.name}/activities')
        assert res.status_code == 200
        assert res.json['activities'][0]['vulnerabilities_count'] == 8
        assert res.json['activities'][0]['criticalIssue'] == 1
        assert res.json['activities'][0]['highIssue'] == 1
        assert res.json['activities'][0]['mediumIssue'] == 2
        assert res.json['activities'][0]['lowIssue'] == 1
        assert res.json['activities'][0]['infoIssue'] == 2
        assert res.json['activities'][0]['unclassifiedIssue'] == 1
