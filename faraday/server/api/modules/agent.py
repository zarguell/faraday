"""
Faraday Penetration Test IDE
Copyright (C) 2019  Infobyte LLC (https://faradaysec.com/)
See the file 'doc/LICENSE' for the license information
"""

# Standard library imports
import logging
from datetime import datetime

# Related third party imports
import pyotp
import flask
from flask import Blueprint, abort, request, jsonify
import flask_login
from flask_classful import route
from marshmallow import fields, Schema, EXCLUDE
from sqlalchemy.orm.exc import NoResultFound
from faraday_agent_parameters_types.utils import type_validate, get_manifests

# Local application imports
from faraday.server.api.base import (
    AutoSchema,
    ReadWriteView, get_workspace
)
from faraday.server.models import (
    Agent,
    Executor,
    AgentExecution,
    Command,
    db
)
from faraday.server.schemas import PrimaryKeyRelatedField
from faraday.server.config import faraday_server
from faraday.server.events import changes_queue

agent_api = Blueprint('agent_api', __name__)
agent_creation_api = Blueprint('agent_creation_api', __name__)
logger = logging.getLogger(__name__)


class ExecutorSchema(AutoSchema):

    parameters_metadata = fields.Dict(
        dump_only=True
    )
    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    last_run = fields.DateTime(dump_only=True)

    class Meta:
        model = Executor
        fields = (
            'id',
            'name',
            'last_run',
            'parameters_metadata',
        )


class AgentSchema(AutoSchema):
    _id = fields.Integer(dump_only=True, attribute='id')
    status = fields.String(dump_only=True)
    creator = PrimaryKeyRelatedField('username', dump_only=True, attribute='creator')
    token = fields.String(dump_only=True)
    create_date = fields.DateTime(dump_only=True)
    update_date = fields.DateTime(dump_only=True)
    is_online = fields.Boolean(dump_only=True)
    executors = fields.Nested(ExecutorSchema(), dump_only=True, many=True)
    last_run = fields.DateTime(dump_only=True)

    class Meta:
        model = Agent
        fields = (
            'id',
            'name',
            'status',
            'active',
            'create_date',
            'update_date',
            'creator',
            'token',
            'is_online',
            'active',
            'executors',
            'last_run'
        )


class AgentCreationSchema(Schema):
    id = fields.Integer(dump_only=True)
    token = fields.String(dump_only=False, required=True)
    name = fields.String(required=True)

    class Meta:
        fields = (
            'id',
            'name',
            'token'
        )


class ExecutorDataSchema(Schema):
    executor = fields.String(default=None)
    args = fields.Dict(default=None)


class AgentRunSchema(Schema):
    executor_data = fields.Nested(
        ExecutorDataSchema(unknown=EXCLUDE),
        required=True
    )
    workspaces_names = fields.List(fields.String, required=True)
    ignore_info = fields.Boolean(required=False)
    resolve_hostname = fields.Boolean(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unknown = EXCLUDE


class AgentView(ReadWriteView):
    route_base = 'agents'
    model_class = Agent
    schema_class = AgentSchema
    get_joinedloads = [Agent.creator, Agent.executors]

    def _perform_create(self, data, **kwargs):
        data = self._parse_data(AgentCreationSchema(unknown=EXCLUDE), request)
        token = data.pop('token')
        if not faraday_server.agent_registration_secret:
            # someone is trying to use the token, but no token was generated yet.
            abort(401, "Invalid Token")
        if not pyotp.TOTP(faraday_server.agent_registration_secret,
                          interval=int(faraday_server.agent_token_expiration)
                          ).verify(token, valid_window=1):
            abort(401, "Invalid Token")
        agent = super()._perform_create(data, **kwargs)
        return agent

    @route('/<int:agent_id>/run', methods=['POST'])
    def run_agent(self, agent_id):
        """
        ---
          tags: ["Agent"]
          description: Runs an agent
          responses:
            400:
              description: Bad request
            201:
              description: Ok
              content:
                application/json:
                  schema: AgentSchema
        """
        if flask.request.content_type != 'application/json':
            abort(400, "Only application/json is a valid content-type")
        username = flask_login.current_user.username
        data = self._parse_data(AgentRunSchema(unknown=EXCLUDE), request)
        agent = self._get_object(agent_id)
        executor_data = data['executor_data']
        ignore_info = data.get('ignore_info', False)
        resolve_hostname = data.get('resolve_hostname', True)
        workspaces = [get_workspace(workspace_name=workspace) for workspace in data['workspaces_names']]

        try:
            executor = Executor.query.filter(Executor.name == executor_data['executor'],
                                             Executor.agent_id == agent_id).one()

            # VALIDATE
            errors = {}
            for param_name, param_data in executor_data["args"].items():
                if executor.parameters_metadata.get(param_name):
                    val_error = type_validate(executor.parameters_metadata[param_name]['type'], param_data)
                    if val_error:
                        errors[param_name] = val_error
                else:
                    errors['message'] = f'"{param_name}" not recognized as an executor argument'

            for param_name, _ in executor.parameters_metadata.items():
                if executor.parameters_metadata[param_name]['mandatory'] and param_name not in executor_data['args']:
                    errors['message'] = f'Mandatory argument {param_name} not passed to {executor.name} executor.'

            if errors:
                response = jsonify(errors)
                response.status_code = 400
                abort(response)

            params = ', '.join([f'{key}={value}' for (key, value) in executor_data["args"].items()])
            commands = [
                Command(
                    import_source="agent",
                    tool=agent.name,
                    command=executor.name,
                    user=username,
                    hostname='',
                    params=params,
                    start_date=datetime.utcnow(),
                    workspace=workspace
                )
                for workspace in workspaces
            ]

            agent_executions = [
                AgentExecution(
                    running=None,
                    successful=None,
                    message='',
                    executor=executor,
                    workspace_id=workspace.id,
                    parameters_data=executor_data["args"],
                    command=command
                )
                for workspace, command in zip(workspaces, commands)
            ]
            executor.last_run = datetime.utcnow()
            for agent_execution in agent_executions:
                db.session.add(agent_execution)
            db.session.commit()

            changes_queue.put({
                'execution_ids': [agent_execution.id for agent_execution in agent_executions],
                'agent_id': agent.id,
                'workspaces': [workspace.name for workspace in workspaces],
                'action': 'RUN',
                "executor": executor_data.get('executor'),
                "args": executor_data.get('args'),
                "plugin_args": {
                    "ignore_info": ignore_info,
                    "resolve_hostname": resolve_hostname,
                    "vuln_tag": None,
                    "service_tag": None,
                    "host_tag": None
                }
            })
            logger.info("Agent executed")
        except NoResultFound as e:
            logger.exception(e)
            abort(400, "Can not find an agent execution with that id")
        else:
            return flask.jsonify({
                'commands_id': [command.id for command in commands]
            })

    @route('/active_agents', methods=['GET'])
    def active_agents(self, **kwargs):
        """
        ---
        get:
          tags: ["Agent"]
          summary: Get all manifests, Optionally choose latest version with parameter
          parameters:
          - in: version
            name: agent_version
            description: latest version to request

          responses:
            200:
              description: Ok
        """
        try:
            objects = self.model_class.query.filter(self.model_class.active).all()
            return self._envelope_list(self._dump(objects, kwargs, many=True))
        except ValueError as e:
            flask.abort(400, e)

    @route('/get_manifests', methods=['GET'])
    def manifests_get(self):
        """
        ---
        get:
          tags: ["Agent"]
          summary: Get all manifests, Optionally choose latest version with parameter
          parameters:
          - in: version
            name: agent_version
            description: latest version to request

          responses:
            200:
              description: Ok
        """
        try:
            return flask.jsonify(get_manifests(request.args.get("agent_version")))
        except ValueError as e:
            flask.abort(400, e)


AgentView.register(agent_api)
