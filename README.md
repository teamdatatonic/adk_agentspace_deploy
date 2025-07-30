# Custom ADK Agent Deployment to Agentspace via Agent Engine

This project demonstrates how to create a custom AI agent using Google's Agent Development Kit (ADK) and then deploy it into an Agentspace application, via Vertex AI Agent Engine

## Project Overview

This repository provides a concrete example of integrating custom ADK agents into the Google Cloud Agentspace ecosystem. The core components are:

  * **`weather_agent`**: A simple ADK agent that provides weather and time information for a specified city (currently mocked for "New York").
  * **Deployment Scripts**: Python scripts (`deploy.py`, `test_deploy.py`, `as_deploy.py`) to automate the deployment process from local development to Agent Engine, and subsequently to an Agentspace application.

N.B. Direct deployment of custom ADK agents to Agentspace via the Google Cloud Console is not currently available.

## Prerequisites

Before you begin, ensure you have the following:

  * **Python 3.8+**

  * **Poetry** (for dependency management): [Here](https://python-poetry.org/docs/#installing-with-the-official-installer) are some installation instructions

  * **Google Cloud SDK (gcloud CLI)**: Authenticate with `gcloud auth application-default login`

  * **A Google Cloud Project**: With the necessary APIs enabled (e.g., Vertex AI, Agent Engine, Agentspace).

  * **Configured `.env` file**: Populate the `.env` file with your Google Cloud project details, storage bucket, and Agentspace application IDs. N.B. Your GOOGLE_CLOUD_PROJECT and AS_GOOGLE_CLOUD_PROJECT variables are likely to be the same.

    ```
    # Example .env content
    # Vertex AI backend config, uncomment and use
    GOOGLE_GENAI_USE_VERTEXAI=1 
    GOOGLE_CLOUD_PROJECT=dt-agentspace-emea-dev
    GOOGLE_CLOUD_LOCATION=us-central1 # this location works well for deploying into global agentspace app
    GOOGLE_CLOUD_STORAGE_BUCKET=test-data-source-for-agentspace # staging bucket

    # AgentSpace application configuration
    AS_GOOGLE_CLOUD_PROJECT=dt-agentspace-emea-dev
    AGENT_SPACE_LOCATION=global
    AGENT_SPACE_APP_ID=custom-agent-demo_1752590746685	
    ```

## Setup

1.  **Clone the repository**:
    ```bash
    git clone [repo-url]
    ```
2.  **Install project dependencies**:
    ```bash
    poetry install
    ```
    This command will install all required Python packages for the agent and deployment scripts, as specified in `pyproject.toml`.

## Understanding the Custom ADK Agent

The core logic for our custom agent resides in the `weather_agent` directory.

  * **`weather_agent/weather_agent/agent.py`**:
    This file contains the definition of our `weather_time_agent`. It implements two simple tools:

      * `get_weather(city: str)`: Provides mock weather information.
      * `get_current_time(city: str)`: Provides mock time information.
        The `root_agent` instance is configured here, specifying a name, the LLM model to use, description, instructions, and the tools it can access.

  * **`weather_agent/weather_agent/__init__.py`**:
    This file contains `from . import agent`, as reccomended in Google's [Quickstart Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-development-kit/quickstart) on how to build an ADK agent.  

## Deployment Steps

The deployment process involves two main stages: first to Agent Engine, then to Agentspace.

### 1\. Package the Agent (Create Wheel File)

Before deployment, your ADK agent needs to be packaged into a Python wheel (`.whl`) file. This self-contained archive includes all your agent's code and its dependencies.

```bash
poetry build --format=wheel --output=deployment
```

This command will create a file similar to `weather_agent-0.1.0-py3-none-any.whl` in the `deployment/` directory. This wheel file will be referenced by the deployment scripts.

### 2\. Deploy your ADK agent to Agent Engine

The `deploy.py` script is responsible for deploying your packaged ADK agent to Google Cloud's Agent Engine.

```bash
poetry run python deployment/deploy.py
```

Upon successful execution, you will see output indicating the agent has been deployed. **Crucially, note down the `reasoningEngine` ID** from the output. This ID is essential for the next step, linking your agent to Agentspace. You can also find this ID by navigating to **Vertex AI -\> Agent Engine** in the Google Cloud Console, selecting the `us-central1` region (or your configured region), and inspecting the "Deployment Details" of your newly deployed agent. It will also appear in the terminal output.

**Example `reasoningEngine` ID format:** `projects/your-gcp-project-id/locations/us-central1/reasoningEngines/6311399053573750784`
*(The number at the end is your specific agent ID for Agent Engine)*  amongst text like this `projects/your-gcp-project-id/locations/us-central1/reasoningEngines/6311399053573750784`, where the agent id is `6311399053573750784`

In your env file, the location you have for the `GOOGLE_CLOUD_LOCATION` variable will be where your agent is deployed in agent engine. We found that if you have a global agentspace app, using `europe-west2`, might not work and using a region like `us-central1` instead does work.

### 3\. Test Agent Engine Deployment

To verify that your agent has been deployed correctly to Agent Engine and is responsive, you can run the `test_deploy.py` script.

```bash
poetry run python deployment/test_deploy.py -m remote -r [YOUR_AGENT_ENGINE_ID]
```

**Example:**

```bash
poetry run python deployment/test_deploy.py -m remote -r 6311399053573750784
```

Replace `[YOUR_AGENT_ENGINE_ID]` with the ID obtained in the previous step. This will create a remote session allowing you to interact with your agent running in Agent Engine.

### 4\. Deploy to Agentspace App

The `as_deploy.py` script links your agent from Agent Engine into your Agentspace application, making it accessible for conversational AI experiences within Agentspace.

```bash
poetry run python deployment/as_deploy.py --link -r [YOUR_AGENT_ENGINE_ID]
```

**Example:**

```bash
poetry run python deployment/as_deploy.py --link -r 6311399053573750784
```

Replace `[YOUR_AGENT_ENGINE_ID]` with the Agent Engine ID you noted earlier. This command establishes the connection, and your custom agent should now appear in your Agentspace application.

## Managing Agentspace Deployments

The `as_deploy.py` script also provides utility commands for managing your Agentspace deployments.

### List Agentspace Agents

To see a list of all custom agents currently linked to your Agentspace project:

```bash
poetry run python deployment/as_deploy.py --list
```

This will output details of your Agentspace agents, including their unique IDs.

### Delete Agentspace Agents

If you need to remove an agent from your Agentspace application, use the `--delete` command with its Agentspace ID.

**Example Agentspace Agent ID format:** `projects/468940617625/locations/global/collections/default_collection/engines/custom-agent-demo_175259074665/assistants/default_assistant/agents/17672033777203492998`
*(The last numeric part is the specific Agentspace Agent ID.)*

```bash
poetry run python deployment/as_deploy.py --delete -a [YOUR_AGENTSPACE_AGENT_ID]
```

**Example:**

```bash
poetry run python deployment/as_deploy.py --delete -a 17672033777203492998
```

Replace `[YOUR_AGENTSPACE_AGENT_ID]` with the ID you want to delete, obtained from the `--list` command.
