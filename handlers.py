from slack_bolt.async_app import AsyncApp
from logging import Logger
from slack_sdk import WebClient
from slack_bolt import Say, Ack, BoltContext
import os
import uuid
from a2a.client import A2AClient

async def invoke_a2a_agent(agent_url: str, input: str, logger: Logger):
    """
    Invokes the A2A agent and returns the response.
    """
    a2a_client = A2AClient(url=agent_url, timeout=600.0)
    task_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    payload = {
        "id": task_id,
        "sessionId": session_id,
        "acceptedOutputModes": ["text"],
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": input,
                }
            ]
        }
    }

    logger.info(f"Invoking the agent: {agent_url}")

    response = await a2a_client.send_task(payload)
    text = ""
    for artifact in response.result.artifacts:
        for part in artifact.parts:
            text += part.text
    return text



async def mykagent_command(
    client: WebClient, ack: Ack, command, say: Say, logger: Logger, context: BoltContext
):
    await ack()


    user_id = context["user_id"]
    channel_id = context["channel_id"]
    text = command.get("text")

    await client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text="Thinking...",
    )

    # Check if the KAGENT_A2A_URL environment variable is set
    kagent_a2a_url = os.getenv("KAGENT_A2A_URL")
    if not kagent_a2a_url:
        # TODO: Implement the logic for the /mykagent command
        await client.chat_postMessage(
            channel=channel_id,
            user=user_id,
            text="Hello! Once you set the KAGENT_A2A_URL environment variable, you can use the /aire command.",
        )
        return

    # Invoke the KAGENT A2A API
    try:
        response = await invoke_a2a_agent(kagent_a2a_url, text, logger)
        await client.chat_postMessage(
            channel=channel_id,
            user=user_id,
            text=response,
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await client.chat_postMessage(
            channel=channel_id,
            user=user_id,
            text=f"Occurred an error while talking to kagent: {e}",
        )


def register_handlers(app: AsyncApp):
    """
    Register all handlers for the bot.
    """

    # Commands
    app.command("/aire")(mykagent_command)