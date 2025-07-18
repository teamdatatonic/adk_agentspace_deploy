import json
import os

import requests
from absl import app, flags
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request as GoogleAuthRequest


USE_CASE_NAME = "weather-agent-1"

# --- absl.flags definitions ---
FLAGS = flags.FLAGS

flags.DEFINE_string("as_project_id", None, "Agentspace GCP project ID.")
flags.DEFINE_string("ae_project_id", None, "Agent Engine GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("company_name", "Datatonic", "Weather agent description.")
flags.DEFINE_bool("list", False, "List all AS agents.")
flags.DEFINE_bool("link", False, "Link an AE agent to AS app.")
flags.DEFINE_bool("delete", False, "Delete an existing AS agent.")

flags.DEFINE_string(
    "resource_id",
    None,
    "The resource ID of the agent engine to delete or update.",
    short_name="r",
)

flags.DEFINE_string(
    "as_agent_id",
    None,
    "The resource ID of the AgentSpace agent to delete",
    short_name="a",
)


# TODO: change and use oauth to authenticate
def get_gcloud_access_token():
    """Retrieves the gcloud access token using the command line."""
    try:
        credentials, project = default()
        auth_req = GoogleAuthRequest()
        credentials.refresh(auth_req)
        access_token = credentials.token
        return access_token
    except Exception as e:
        print(f"Error getting access token: {e}")
        print("Please ensure you are authenticated with 'gcloud auth application-default login'")
        exit(1)


def discovery_engine_url() -> str:
    """Constructs the base URL for AgentSpace (Discovery Engine) API calls.

    The URL is built using the GCP project ID, AgentSpace application ID,
    and AgentSpace location, retrieved from command-line flags (``FLAGS.project_id``)
    or environment variables (``AS_GOOGLE_CLOUD_PROJECT``, ``AGENT_SPACE_APP_ID``,
    ``AGENT_SPACE_LOCATION``). The hostname is adjusted based on the specified location.

    :returns: The constructed base URL for AgentSpace API interactions.
    :rtype: str
    """
    project_id = FLAGS.as_project_id if FLAGS.as_project_id else os.getenv("AS_GOOGLE_CLOUD_PROJECT")
    agentspace_app_id = os.getenv("AGENT_SPACE_APP_ID")
    as_location_id = os.getenv("AGENT_SPACE_LOCATION")
    hostname = "discoveryengine.googleapis.com"
    if as_location_id != "global":
        hostname = f"{as_location_id}-{hostname}"
    url = f"https://{hostname}/v1alpha/projects/{project_id}/locations/{as_location_id}/collections/default_collection/engines/{agentspace_app_id}/assistants/default_assistant/agents"
    return url


def link_agent_to_agentspace(agent_engine_id: str):
    """
     Links an existing Agent Engine (AE) agent to the configured AgentSpace application

     :param agent_engine_id: The resource ID of the Agent Engine to link, e.g., ``my-agent-engine-id``.
     :return:
     :raises ValueError: If authentication fails to retrieve an access token.
    :raises requests.exceptions.RequestException: For any HTTP or connection errors during the API call.
    """
    as_project_id = os.getenv("AS_GOOGLE_CLOUD_PROJECT")
    ae_project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    ae_location_id = FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION")
    # The URL for the POST request
    url = discovery_engine_url()

    # Retrieve the access token
    access_token = get_gcloud_access_token()

    if access_token:
        # Set the headers for the request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": as_project_id,
        }

        # The JSON data payload for the request
        ae_url = f"projects/{ae_project_id}/locations/{ae_location_id}/reasoningEngines/{agent_engine_id}"
        payload = {
            "displayName": USE_CASE_NAME,
            "description": f"Weather agent that provides weather information for {FLAGS.company_name}.",
            "adk_agent_definition": {
                "tool_settings": {
                    "tool_description": "This agent provides weather information for a given location."
                },
                "provisioned_reasoning_engine": {"reasoning_engine": ae_url},
            },
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            print("\nAPI Response:")
            print(json.dumps(response.json(), indent=2))
            print(f"\nSuccessfully created agent: {response.json().get('name', 'N/A')}")

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response Content: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
    else:
        raise ValueError("Authentication failed")


def list_as_agents():
    """
     Lists all agents currently linked within the configured AgentSpace application.

     :raises ValueError: If authentication fails to retrieve an access token.
    :raises requests.exceptions.RequestException: For any HTTP or connection errors during the API call.
     :return:
    """
    project_id = FLAGS.as_project_id if FLAGS.as_project_id else os.getenv("AS_GOOGLE_CLOUD_PROJECT")
    url = discovery_engine_url()

    # Retrieve the access token
    access_token = get_gcloud_access_token()

    if access_token:
        # Set the headers for the request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id,
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            print("\nAPI Response:")
            print(json.dumps(response.json(), indent=2))

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response Content: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
    else:
        raise ValueError("Authentication failed")


def delete_as_agent(as_agent_id: str):
    """
     Deletes a specific AgentSpace agent from the configured AgentSpace application.

     :param as_agent_id: The resource ID of the AgentSpace agent to delete. This typically includes the full path, e.g.,
     ``projects/.../locations/.../agents/my-agent-id``.
     :raises ValueError: If authentication fails to retrieve an access token.
    :raises requests.exceptions.RequestException: For any HTTP or connection errors during the API call.
     :return:
    """
    project_id = FLAGS.as_project_id if FLAGS.as_project_id else os.getenv("AS_GOOGLE_CLOUD_PROJECT")
    url = discovery_engine_url()
    agent_url = os.path.join(url, as_agent_id)

    # Retrieve the access token
    access_token = get_gcloud_access_token()

    if access_token:
        # Set the headers for the request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id,
        }
        try:
            response = requests.delete(agent_url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            print("\nAPI Response:")
            print(json.dumps(response.json(), indent=2))
            print(f"\nSuccessfully deleted agent: {response.json().get('name', 'N/A')}")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response Content: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
    else:
        raise ValueError("Authentication failed")


def main(argv: list[str]):
    del argv
    load_dotenv()

    if FLAGS.link and FLAGS.resource_id:
        link_agent_to_agentspace(FLAGS.resource_id)
    elif FLAGS.list:
        list_as_agents()
    elif FLAGS.delete and FLAGS.as_agent_id:
        delete_as_agent(FLAGS.as_agent_id)
    else:
        raise ValueError("Execution mode must be deploy, list or delete. If deploy, a resource-id must be provided")


if __name__ == "__main__":
    app.run(main)
