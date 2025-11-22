import asyncio
import logging
import time

from typing import NamedTuple, Dict, List, Union, Awaitable, Any, Optional

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from a2a.utils.message import new_agent_text_message
from google.adk import Runner
from google.adk.auth import AuthConfig, AuthCredential, AuthScheme
from google.adk.events import Event, EventActions
from google.adk.sessions import Session
from google.adk.tools.openapi_tool.openapi_spec_parser.tool_auth_handler import (
    ToolContextCredentialStore,
)
from google.genai import types


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Changed to INFO for general logging purposes


class ADKAuthDetails(NamedTuple):
    """Contains a collection of properties related to handling ADK authentication."""

    state: str
    uri: str
    future: asyncio.Future[str] # Explicitly hint the Future's result type
    auth_config: AuthConfig
    auth_request_function_call_id: str


class StoredCredential(NamedTuple):
    """Contains OAuth2 credentials."""

    key: str
    credential: AuthCredential


# 1 minute timeout to keep the demo moving.
auth_receive_timeout_seconds = 60


class ADKAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent."""

    _awaiting_auth: Dict[str, asyncio.Future[str]] # Explicit Dict and Future hint
    _credentials: Dict[str, StoredCredential] # Explicit Dict hint

    def __init__(self, runner: Runner, card: AgentCard):
        self.runner: Runner = runner # Add type hint
        self._card: AgentCard = card # Add type hint
        self._awaiting_auth = {}
        self._credentials = {}
        # Track active sessions for potential cancellation
        self._active_sessions: set[str] = set() # Add type hint

    async def _process_request(
        self,
        new_message: types.Content,
        context: RequestContext,
        task_updater: TaskUpdater,
    ) -> None:
        logger.info(f"Processing request for session '{context.context_id}' with message: '{new_message.parts[0].text if new_message.parts else ''}'")
        session: Session = await self._upsert_session(context)
        auth_details: Optional[ADKAuthDetails] = None
        async for event in self.runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=new_message,
        ):
            if auth_request_function_call := get_auth_request_function_call(event):
                auth_details = self._prepare_auth_request(auth_request_function_call)
                logger.info(f"Authorization required for session '{session.id}'. URI: '{auth_details.uri}'")
                await task_updater.update_status(
                    TaskState.auth_required,
                    message=new_agent_text_message(
                        f'Authorization is required to continue. Visit {auth_details.uri}'
                    ),
                )
                break
            if event.is_final_response():
                parts: List[Part] = convert_genai_parts_to_a2a(event.content.parts)
                logger.info(f"Final response for session '{session.id}': '{parts[0].root.text if parts and isinstance(parts[0].root, TextPart) else ''}'")
                await task_updater.add_artifact(parts)
                await task_updater.complete()
                break
            if not event.get_function_calls():
                logger.debug(f"Yielding update response for session '{session.id}'")
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(event.content.parts),
                    ),
                )
            else:
                logger.debug(f"Skipping event with function calls for session '{session.id}'")

        if auth_details:
            await self._complete_auth_processing(context, auth_details, task_updater)

    def _prepare_auth_request(
        self, auth_request_function_call: types.FunctionCall
    ) -> ADKAuthDetails:
        logger.info(f"Preparing auth request for function call ID: '{auth_request_function_call.id}'")
        if not (auth_request_function_call_id := auth_request_function_call.id):
            logger.error(f'Function call ID not found: {auth_request_function_call}')
            raise ValueError(
                f'Cannot get function call id from function call: {auth_request_function_call}'
            )
        auth_config: AuthConfig = get_auth_config(auth_request_function_call)
        if not auth_config:
            logger.error(f'Auth config not found from function call: {auth_request_function_call}')
            raise ValueError(
                f'Cannot get auth config from function call: {auth_request_function_call}'
            )
        oauth2_config = auth_config.exchanged_auth_credential.oauth2
        if not oauth2_config or not oauth2_config.auth_uri:
            logger.error(f'OAuth2 config or auth URI not found from auth config: {auth_config}')
            raise ValueError(
                f'Cannot get auth uri from auth config: {auth_config}'
            )
        
        base_auth_uri: str = oauth2_config.auth_uri
        redirect_uri: str = f'{self._card.url}authenticate'
        oauth2_config.redirect_uri = redirect_uri
        state_token: str = oauth2_config.state
        future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        self._awaiting_auth[state_token] = future
        auth_request_uri: str = base_auth_uri + f'&redirect_uri={redirect_uri}'
        logger.info(f"Auth request prepared. State: '{state_token}', Redirect URI: '{redirect_uri}'")
        return ADKAuthDetails(
            state=state_token,
            uri=auth_request_uri,
            future=future,
            auth_config=auth_config,
            auth_request_function_call_id=auth_request_function_call_id,
        )

    async def _complete_auth_processing(
        self,
        context: RequestContext,
        auth_details: ADKAuthDetails,
        task_updater: TaskUpdater,
    ) -> None:
        logger.info(f"Waiting for auth event for state: '{auth_details.state}'")
        try:
            auth_uri: str = await asyncio.wait_for(
                auth_details.future, timeout=auth_receive_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timed out waiting for auth for state: '{auth_details.state}'. Marking task as failed.")
            await task_updater.update_status(
                TaskState.failed,
                message=new_agent_text_message(
                    'Timed out waiting for authorization.',
                    context_id=context.context_id,
                ),
            )
            return
        logger.info(f"Auth received for state: '{auth_details.state}'. Continuing processing.")
        await task_updater.update_status(
            TaskState.working,
            message=new_agent_text_message(
                'Auth received, continuing...', context_id=context.context_id
            ),
        )
        del self._awaiting_auth[auth_details.state]
        oauth2_config = (
            auth_details.auth_config.exchanged_auth_credential.oauth2
        )
        if not oauth2_config:
            logger.error(f"OAuth2 config not found after auth for state: '{auth_details.state}'.")
            raise ValueError("OAuth2 config is missing after authentication.")

        oauth2_config.auth_response_uri = auth_uri
        auth_content: types.UserContent = types.UserContent(
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        id=auth_details.auth_request_function_call_id,
                        name='adk_request_credential',
                        response=auth_details.auth_config.model_dump(),
                    ),
                )
            ]
        )
        await self._process_request(auth_content, context, task_updater)
        # Extract the stored credential.
        if context.call_context and context.call_context.user.is_authenticated:
            logger.info(f"Storing user auth for user: '{context.call_context.user.user_name}'")
            await self._store_user_auth(
                context,
                auth_details.auth_config.auth_scheme,
                auth_details.auth_config.raw_auth_credential,
            )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info(f"Executing request for context ID: '{context.context_id}'")
        updater: TaskUpdater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            context,
            updater,
        )
        logger.info(f"Execution completed for context ID: '{context.context_id}'")

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"Cancellation requested for context ID: '{context.context_id}'")
        session_id: str = context.context_id
        if session_id in self._active_sessions:
            logger.info(
                f'Cancellation requested for active oauth session: {session_id}'
            )
            self._active_sessions.discard(session_id)
        else:
            logger.debug(
                f'Cancellation requested for inactive oauth session: {session_id}'
            )

        raise ServerError(error=UnsupportedOperationError())

    async def on_auth_callback(self, state: str, uri: str) -> None:
        logger.info(f"Auth callback received for state: '{state}'")
        if state in self._awaiting_auth:
            self._awaiting_auth[state].set_result(uri)
        else:
            logger.warning(f"Auth callback received for unknown state: '{state}'")

    async def _upsert_session(self, context: RequestContext) -> Session:
        user_id: str = 'anonymous'
        if context.call_context and context.call_context.user.is_authenticated:
            user_id = context.call_context.user.user_name
        logger.info(f"Upserting session for user '{user_id}' with context ID '{context.context_id}'")

        session: Optional[Session] = await self.runner.session_service.get_session(
            app_name=self.runner.app_name,
            user_id=user_id,
            session_id=context.context_id,
        )
        if session is None:
            logger.info(f"Creating new session for user '{user_id}' with context ID '{context.context_id}'")
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=context.context_id,
            )
        else:
            logger.info(f"Retrieved existing session for user '{user_id}' with context ID '{context.context_id}'")

        return await self._ensure_auth(session)

    async def _ensure_auth(self, session: Session) -> Session:
        logger.info(f"Ensuring auth for session '{session.id}'")
        if (
            stored_cred := self._credentials.get(session.user_id)
        ) and not session.state.get(stored_cred.key):
            logger.info(f"Loading stored credential for user '{session.user_id}'")
            event_action = EventActions(
                state_delta={
                    stored_cred.key: stored_cred.credential,
                }
            )
            event = Event(
                invocation_id='preload_auth',
                author='system',
                actions=event_action,
                timestamp=time.time(),
            )
            logger.debug('Loaded authorization state: %s', event)
            await self.runner.session_service.append_event(session, event)
        else:
            logger.debug(f"No stored credential to load or credential already in session state for user '{session.user_id}'")
        return session

    async def _store_user_auth(
        self,
        context: RequestContext,
        auth_scheme: AuthScheme,
        raw_credential: AuthCredential,
    ) -> None:
        logger.info(f"Storing user auth for context ID: '{context.context_id}'")
        session: Session = await self._upsert_session(context)
        tool_credential_store = ToolContextCredentialStore(None) # Consider if None is always appropriate here
        credential_key: str = tool_credential_store.get_credential_key(
            auth_scheme,
            raw_credential,
        )
        stored_credential: Optional[AuthCredential] = session.state.get(credential_key)
        if stored_credential and context.call_context and context.call_context.user.is_authenticated:
            user_name: str = context.call_context.user.user_name
            self._credentials[user_name] = (
                StoredCredential(
                    key=credential_key, credential=stored_credential
                )
            )
            logger.info(f"Credential stored for user: '{user_name}' with key: '{credential_key}'")
        else:
            logger.warning(f"Could not store credential for context ID: '{context.context_id}'. Stored credential: {stored_credential}, Authenticated: {context.call_context.user.is_authenticated if context.call_context else False}")


def convert_a2a_parts_to_genai(parts: List[Part]) -> List[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    part_root: Union[TextPart, FilePart] = part.root
    if isinstance(part_root, TextPart):
        return types.Part(text=part_root.text)
    if isinstance(part_root, FilePart):
        if isinstance(part_root.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=part_root.file.uri, mime_type=part_root.file.mime_type
                )
            )
        if isinstance(part_root.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=part_root.file.bytes, mime_type=part_root.file.mime_type
                )
            )
        logger.error(f'Unsupported file type in A2A Part: {type(part_root.file)}')
        raise ValueError(f'Unsupported file type: {type(part_root.file)}')
    logger.error(f'Unsupported part type in A2A Part: {type(part_root)}')
    raise ValueError(f'Unsupported part type: {type(part_root)}')


def convert_genai_parts_to_a2a(parts: List[types.Part]) -> List[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return TextPart(text=part.text)
    if part.file_data:
        return FilePart(
            file=FileWithUri(
                uri=part.file_data.file_uri,
                mime_type=part.file_data.mime_type,
            )
        )
    if part.inline_data:
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data,
                    mime_type=part.inline_data.mime_type,
                )
            )
        )
    logger.error(f'Unsupported part type in GenAI Part: {part}')
    raise ValueError(f'Unsupported part type: {part}')


def get_auth_request_function_call(event: Event) -> Optional[types.FunctionCall]:
    """Get the special auth request function call from the event."""
    if not (event.content and event.content.parts):
        return None
    for part in event.content.parts:
        if (
            part
            and part.function_call
            and part.function_call.name == 'adk_request_credential'
            and event.long_running_tool_ids
            and part.function_call.id in event.long_running_tool_ids
        ):
            return part.function_call
    return None


def get_auth_config(
    auth_request_function_call: types.FunctionCall,
) -> AuthConfig:
    """Extracts the AuthConfig object from the arguments of the auth request function call."""
    if not auth_request_function_call.args or not (
        auth_config_raw := auth_request_function_call.args.get('authConfig')
    ):
        logger.error(f'Auth config not found in function call arguments: {auth_request_function_call}')
        raise ValueError(
            f'Cannot get auth config from function call: {auth_request_function_call}'
        )
    return AuthConfig.model_validate(auth_config_raw)
