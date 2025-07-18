import argparse
import os
import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
def run_remote(agent_engine_id: str, user_id: str):
    """Runs an interactive console session with a remote Vertex AI Agent Engine.
    This function initializes the Vertex AI SDK using environment variables,
    retrieves the specified remote agent engine, and then starts an interactive
    loop to query the agent.
    It creates a new session for the given user ID at the start and automatically
    deletes the session upon exiting the loop. The user can type "quit" to end
    the interactive session.
    The function streams responses from the agent and attempts to print raw events,
    extracted text content, and function call details.
    Relies on the following environment variables for Vertex AI initialization:
    *   ``GOOGLE_CLOUD_PROJECT``: The Google Cloud project ID.
    *   ``GOOGLE_CLOUD_LOCATION``: The Google Cloud location/region.
    :param agent_engine_id: The resource ID or identifier of the remote agent engine
        to interact with.
    :type agent_engine_id: str
    :param user_id: The unique identifier for the user interacting with the agent.
        This is used to create and manage the session.
    :type user_id: str
    :return:
    .. note::
        - This is an interactive function that runs until the user types ``quit``.
        - The session created at the start is automatically deleted when the function exits.
        - The parsing of streaming events (`content`, `function_call`) assumes
          a standard format returned by the agent engine API.
    """
    bucket = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}-staging"
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        staging_bucket="gs://test-data-source-for-agentspace",
    )
    agent = agent_engines.get(agent_engine_id)
    print(f"Found agent with resource ID: {agent_engine_id}")
    session = agent.create_session(user_id=user_id)
    print(f"Created session for user ID: {user_id}")
    print(f"Session state: {session['state']}")
    print("Type 'quit' to exit.")
    while True:
        user_input = input("Input: ")
        if user_input == "quit":
            break
        for event in agent.stream_query(user_id=user_id, session_id=session["id"], message=user_input):
            print(event)
            if "content" in event:
                if "parts" in event["content"]:
                    parts = event["content"]["parts"]
                    for part in parts:
                        if "text" in part:
                            text_part = part["text"]
                            print(f"Response: {text_part}")
            if "function_call" in event:
                function_call = event["function_call"]
                print(f"Called function {function_call['name']} with args {function_call['args']}")
    agent.delete_session(user_id=user_id, session_id=session["id"])
    print(f"Deleted session for user ID: {user_id}")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", type=str)
    parser.add_argument("-r", "--resource_id", type=str, default=None)
    parser.add_argument("-u", "--user_id", type=str, default="test_user")
    args = parser.parse_args()
    if args.mode == "remote":
        if args.resource_id is None:
            raise ValueError("resource_id must be passed when mode==remote")
        run_remote(args.resource_id, args.user_id)
    else:
        raise ValueError("Execution mode must be local or remote")
if __name__ == "__main__":
    # Setup
    load_dotenv()
    main()
