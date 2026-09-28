# Agent With RAG Specification V2
Build a web app to manage an AI Agent with RAG ability.

## 📂 Directory Architecture

## GUI
- Start with the login popup window. Prompt the user to enter the username and password
  - Display two text boxes for entering the username and password
  - Display three buttons:"Create New Account", “Cancel”, and "Ok"
  - If the user clicks “Create New Account”, open a popup window to create a new account
    - The popup window should display two text boxes for entering the username and password
    - Display two buttons: "Cancel" and "Add"
    - If the user clicks “Add”, sends the user name and password to the secrets_manager service to add to the user account storage.
    - If the user clicks “Cancel” button, close the login window and exit the app
  - If the user clicks “Ok” button, sends the user name and password to the secrets_manager service to validate
    - If the user name or password is invalid, display an error message "Invalid username or password." and prompt the user to enter the username and password again
    - If the user has status "Locked", display an error message "Account is Locked. Please contact the administrator." and prompt the user to enter the username and password again
    - If the login succeeds, close the login window and go to the main application window
  - If the user clicks “Cancel” button, display a message “Thank you for using the app”. Then close the login window and exit the app

The Main App window should have:
  - If the static/images folder have a file called tab-icon.gif, use it as the icon for the tab
  - If the static/images folder have a file called app-icon.gif, put it on the left side of the App name at the top left of the window
  - Six tabs with appropriate icon to the left of each tab name:
    1. Chat & Knowledge Mgnt
    2. VectorDB Mgnt
    3. Telemetry
    4. Log Viewer
    5. Container Mgr
    6. Password & API Mgnt
  - Add a button to the right of the six tabs called "Logout"
    - When the user clicks this button, close the current tab and go to the login window.
  - On the right side of the screen, put a button in the light red color “Shutdown” button
    - When the user clicks this button, open a dialog box warning the user that this will shutdown the app and all the services. All the users will be affected by this action. Confirm by typing “Shutdown the services” in the text box.
    - Show two buttons in the dialog box: Cancel, and Confirm. The confirm box should be disabled until the user typed the exact word in the text box.
    - When the user clicks “Confirm” shutdown all the services started by the app. If some of the supporting services were running before the app started, do not shut them down.
  
### 🗣️ First Page: "Chat & Knowledge Mgnt"
- Put a drop down box showing the currently selected model at the right side of the page title.
  - On start up, get the list of ONLY active LLM models for text generation from Google AI Studio API that are capable of synthesizing and outputting text then list them in the dropdown.
  - Use the GEMINI_MODEL as the default model. If the model is not available, select the first model in the list as the default model.
  - Include the option to select a Custom model. When the Custom model is selected, show a text box for the user to enter the API Endpoint of the model. The default text should be the last endpoint entered. If none exists, put “http://127.0.0.1:8010/v1/chat/completions”.
  - To the left of the model choice dropdown, add a box to allow the user to select the “Temperature” parameter to send to the model.
  - To the left of the temperature box, add a text box to allow the user to set the “Max Tokens” parameter to send to the model. Do not allow the user to set the number larger than the max tokens of the model selected.
    
#### Left Card: "Chat with the Agent"
- Add a drop down box called "Agent" on the right side of the card. The choices are: Custom Agent, Google ADK LlmAgent.
  - If the user selects Custom Agent, use the agent described in the Agent section of this document.
  - If the user selects Google ADK Agent, use the google ADK agent
- To the right of the "Agent" box, add a text box for the user to select the "Max Turns" the default is 3. Do not allow the user to set the number larger than 10. Use this as the maximum number of turns for the maximum Agent loop or number of turns.
- In the next row, add a dropbox called "Skill Selector" to allow the user to select the skills the agent can use.
  - The first option in the dropbox should be "Vector Store Selects" (default option). The Custom Agent will query the skills vector store to select the skills to use in the prompt to the model.
  - The second option should be "LLM Selects". The Custom Agent will ask the LLM to select the skills to use in the prompt to the model.
  - The remainder of the selection should be the list of skills in skills/ folder. The Custom Agent will use the skills selected in the prompt to the model.
- Add a text box "Skill Threshold" for the user to enter the threshold when the skill selection is "Vector Store Selects".
  - Use this number as the threshold when querying the vector store.
  - The default value is 0.2.
  - Remove this box if for other selection for "Skill Selector"
- At the bottom of the card, put a text box for the user to enter the chat message.
  - Use a new conversation ID for each question
  - When the user clicks on the "Send" button or presses the Enter key, send the message to the agents container to process.
    - Use the Agents API key stored in the secrets manager
    - Include the Conversation ID of the message to the agent
    - Agent from the dropdown menu in the Chat Agent card
    - Max Turns from the text box in the Chat Agent card
    - Model Selection from the dropdown menu in the Chat page
    - Temperature from the text box in the Chat page
    - Max Tokens from the text box in the Chat page
    - Skill Selector from the dropdown menu in the Chat Agent card
    - Skill Threshold from the text box in the Chat Agent card
    - Doc Threshold from the text box in the Retrieved Context Evidence card
    - Max Chunks from the text box in the Retrieved Context Evidence card
- Use the typical chat user interface to display the chat messages and the agent's responses.
- Once the response is completed, display the response.
  - Add the detail box in the response with a button named “Show Logs”. Within the detail box, add bubbles showing the name of the components that generated the logs (such as Agent, Tools, RAG, Skills), icons appropriate for the components, and the elapse time of each step.
  - When the user clicks on the "Show Logs" button, the detail box should expand to show the full content of the step including the logs. Use the scroll area in the bubble if the content is too long.
  - Make the "Show Logs" button toggle between expand and collapse.
  - Anchor "Show Logs" button at the top-right corner of the detail box.

#### Right Card: "Retrieved Context Evidence"
- Add a box at the right side of the card named "Doc Threshold" for the user to set the threshold for the document retrieval.
  - The default value is 0.3.
  - Use this number as the minimum matching score the Document Vector Store should use to determine whether the text chunk should be returned in the query.
- To the left of "Doc Threshold", add a dropbox to allow the user to select the maximum number of RAG chunks to send to the model
  - Default value is 5.
  - Use this number to limit the number of text chunks to return from the Document Vector Store query.
- Display the contents of the information retrieved from the Document and Skill vector stores.
  - Pull the information from the Logging container related to the conversation ID for the specific chat message.
  - Group the results by the skills and documents.
  - Display the matching score from the vector store along with the name of the document.
- Allow the user to scroll through the data

### 🛢️ The second page: “VectorDB Mgnt”
- Display this page only if the user has editor or admin access
- At the same level as the page title at the right side of the page, put the statistics of the number of chunks, documents ingested, and the size of the DB in MByte. Retrieve this information from the Documents and SKills containers
- To the left of the statistic, add a button to “Update Skills Database”. When the button is selected, send the message to the Agent to load all the skills to the Documents and Skills container.

- To the left of the “Update Skills Database”, add a dropbox showing the list of Embedder that ollama can download.
  - Get the list of available models from ollama API, Display the currently running model.
  - If the user selects a different model, display a pop up window with a stern warning to the user that changing the model will delete all the data currently in the database.
    - Show two buttons: Cancel and Delete Data (initially disabled).
    - Ask the user to type the text to confirm they want to change the model.
    - When the user typed the exact text, enable the “Delete Data” button.
    - When the user clicks “Delete Data”, proceed to delete the data in the document and skill databases, then make ollama to load the new model selected.
    - After the ollama completes updating the model, scan the skills/ folder and import the skills to the skill database
    
#### Left Card: "Populate Vector Database"
- Takes a url or local directory, retrieves the documents, and sends it to the Documents & Skill containers via the Agents API to create a private vector database from documents.
  - Provide 5 buttons for the user to click with samples of web URL that can be imported into the database.
  - Add a sub card called “Advanced Chunking Parameters” to allow the user to select the Chunk size and Overlap in the number of characters. The sub card should be collapsed by default.
  - Add the button at the bottom to populate vector database
  - When loading the database, make sure there is no duplicated chunk
  - The card should be half of the page width

#### Right Card: “Vector Storage Status”.
- At the right side of the box put a button to allow the user to Reset the DB.
- The card should show if the ingestion is in progress
- It should also list the name of the document ingested and the number of chunks created and the total number of characters
- Allow the user to scroll through the list of ingested documents
- Allow the user to delete any document from the DB by using the Delete button on the right side of the document row
- The card should be half of the page width

#### Bottom: "Available Embedding Models".
- Display the list of available Embedding Models for the embedding service. Briefly list the characteristics including the dimensions, context window, size, brief description, and status (Installed, Active, Available to Pull).

### 📊 The third page: “Telemetry”
- The Web UI queries the Logging container's statistics and query API to compute and display the telemetry counters and timeline graphs.
- On the right side of the page, put the button called “Refresh Telemetry” to allow the user to manually refresh the page.
- To the left of the “Refresh Telemetry” button, add a dropdown box to list the models that have been used. Filter the contents of the telemetry page based on the model selected. Include “All Models” as the default option.
- Next, shows Total Prompts, Total Response, Total Errors, Total Input Tokens, and Total Output Tokens sent to and received from the LLM models.

#### Top Card: "System Throughput & Token Velocity"
- Below the statistic, add a card that shows 2 graphs.
  - At the top of the box, there is a dropdown that selects the Aggregation/Refresh Interval with choices: 1 min, 15 min (default), 1 hr, and 1 day.
  - The second dropdown to the right allows the user to select the time range with options for: Last hr, 1 day (default), Week, Month and Custom. When Custom is selected, bring up two boxes with a dropdown calendar that allows the user to select the starting date and ending date.
  - Below the selection, the Left plot shows the line graphs of the number of prompts, responses and errors per Interval selected. The X-axis shows the time range selected.
  - The right plot shows the line graph of the number of input and output tokens per interval selected. The X-axis shows the time range selected.

#### Bottom Card: “Other Important Statistic not Available for Low-Performance Computer”
- Time to First Token (TTFT): The duration between a user sending a prompt and receiving the very first token. This is the most critical metric for perceived speed in streaming applications.
- Inter-Token Latency (ITL): The average time elapsed between generating each subsequent token.
- Tokens Per Second (TPS): The throughput speed of the model generation (often measured per request or aggregated across the server).
- Time Per Output Token (TPOT): The total time taken to generate the response divided by the number of output tokens.

### 📝 The fourth page: “Audit Logs & Events”
- Display this page only if the user has editor or admin access
- To the right side of the page, add a button called “Refresh” to allow the user to manually refresh the page.
- To the left of the “Refresh” button, add a button to allow the user to clear the logs. This will delete all the logs. When the user clicks on this box, open a pop up window asking the user to confirm.
- Next, display the statistics of the total user prompts logged, model calls, Ollama embeds, Avg call latency.

#### Top table: "User Conversations (Select a row to inspect associated events)"
- Display the list of all the user conversations in the log.
  - The following columns should be displayed: Timestamp (in local time), Conversation ID, User Query, Agent Response, Agent Type, Number of Events (occured during the conversation), etc.
- Only show 5 rows in the table
- There should be a scroll bar on the right side to allow the user to scroll through all the items.
- When the user clicks on a row, the next table should be populated with the logs associated with the conversation selected.
- The selected row should be highlighted.

#### Bottom table: "Events for Conversation <Conversation ID>
Display the logs associated with the conversation selected in the table above sorted by the ascending order based on the time. The table should have columns showing:
  - Time and Date (local time)
  - Event Type
  - Invoker
  - Target
  - Short Description
  - When the row is clicked, open a pop up window to show all the detailed logs including the JSON payload in human readable format
    - The popup window should show the text in the prompt and the response in a human readable format. If the text is JSON, display it in a JSON viewer format.

### Fifth page: "Container Mgr"
- Display this page only if the user has admin access
- Display a "Shutdown All" button at the top right corner.
  - Open a popup window asking the user to type "Shutdown System". The "Confirm Shutdown" button at the bottom right of the popup should be disabled until the exact phrase is typed.  
  - Add the "Cancel" button at the bottom of the popup window. When the user clicks the button, close the popup window.
  - When the user clicks on "Confirm Shutdown", shut down all the containers and close the application.
- Next to the "Shutdown All" button, there should be a "Restart All" button.
  - Open a popup window asking the user to type "Restart System". The "Confirm Restart" button at the bottom right of the popup should be disabled until the exact phrase is typed.  
  - Add the "Cancel" button at the bottom of the popup window. When the user clicks the button, close the popup window.
  - When the user clicks on "Confirm Restart", restart all the containers and close the application.
- Display the containers in the system in a drawing.
  - The user should be at the top of the drawing connecting to the web ui container.
  - The containers should be displayed in a way that the user can see the relationship between the containers.
    - Draw a line to show the Web UI container connects to Agent container and Documents & Skills container to upload documents.
    - Draw a line to show the Agent container connects to the Documents & Skills container, and Tools container.
    - Draw a line to show the Documents & Skills container connects to the Embedding container.
    - Draw a dash line to show all the containers connected to the Authentication and Logging containers.
  - The container should have light green when it is active and light red when it is stopped or failed to start.
  - When the user right click on any container, open a popup window with the following information:
    - Container name and Status
    - List of containers that the container accesses.
      - If the container is an active container, the list is read only.
      - If the container is inactive, the user can add the API key for each container in the list.
    - If the container is inactive, show a Start button in green color. If the container is active, there should be a Stop button. Show the button in red color. The button should be at the bottom right corner.
    - Add a "Close" button at the bottom left corner. Close the popup window when the user clicks the button.

The Agent container accesses:
  - Authentication service to authenticate the API key provided by the web ui
  - Documents and Skills container to request for documents or skills for a given query.
  - Tools container to access the tools for a given query.
  - Logging container to log the agent container's activity.

The Documents and Skills container accesses:
  - Authentication service to authenticate the API key provided by the web ui
  - Logging container to log the agent container's activity

### 🔑 Sixth page: “Passwords & API keys”
- If the user has editor or user access, only display the card showing the current user email address, role, and the storage backend
- If the user has admin access, display two sub-tabs: Passwords and API Keys
  - Passwords tab displays:
    - A table of all the users:
    - Add a button to generate a new API key
      - When clicked, a popup window open and display:
        - A text box to enter the User Name for the new user
        - A dropdown box with the list of all the containers 

      - The table should have columns showing:
        - User Name
        - Date/time when the account was created
        - Role (allow the admin to change the roles). The list includes: Admin, Editor, and User.
        - Add a button to reset the password of any user
        - Add a button to delete any user
      - Only show 5 rows in the table
      - There should be a scroll bar on the right side to allow the user to scroll through all the items

    - The second table displays the list of all user access and requests:
      - The table should have columns showing: Local Date/time, User Email, Request Type, and Status
      - The table should be sorted by the descending order based on the time
      - Include Login, Logout, New User Registration, and Password Reset requests
      - Only show 5 rows in the table
      - There should be a scroll bar on the right side to allow the user to scroll through all the items

  - API Keys tab displays:
    - Add a button to generate a new API key
      - When clicked, a popup window open and display:
        - A text box to enter the Key name for the API key
        - A dropdown box with the list of all the containers 
        - To the right of the container dropdown box is another dropdown box with the list of access levels for the API key.
          - The list includes: Read, Write, and Admin.
        - To the right of the access level dropdown box is the "Add" button. When clicked, the selected container and access level are added to the list of containers and access levels for the API key.
        - Below the container and access level dropdown boxes, display a list of all the configured containers and access levels for the API key.
        - A field to enter the expiry date/time of the API key. Default to 1 year from the date/time of generation.
        - A button "Proceed" to create the API key.
        - When the user clicks on the proceed button, generate the API key and display it in a popup window. The key should be displayed in a way that the user can copy it.
        - Notify the user that the API key will not be displayed again and they should save it in a safe place.
        - Show a button "Close" to allow the user to close the popup window. This will close the popup window and return to the previous screen.

    - A table listing the API keys:
      - The table should contain the following columns:
        - Key Name
        - API Key prefix
        - The user who created the key
        - Date/time when the key was generated
        - Expiry Date/time (1 year from generation date/time)
        - List of containers the key is valid for
        - List of access levels the key is valid for
        - The status of the key (active, inactive, and delete)
        - An "Edit" button to edit the API key details. When the button is clicked, open a popup window with the same layout as the "Add API key" popup window to edit the details of the API key
          - Each row of the existing access level in the popup should be a dropdown box with the list of access levels for the API key. The last item in the dropdown box is "Delete" to allow the user to delete the access level
          - At the bottom of the window, show:
            - A "Cancel" button. When the user clicks on this button, close the popup and return to the previous screen.
            - A "Delete" button to allow the user to delete the API key 
            - An "Update" button to allow the user to update the API key
            - When one of the last two buttons is clicked, bring a popup asking for confirmation from the user to delete or update the API key.
      - There should be a scroll bar on the right side to allow the user to scroll through all the items

## Container Requirements
- The project should be run using Docker.
- Create a docker-compose.yml file to run all the containers.
- All the files created for the container should be in the container's own folder
- Use Python as the default language for all the code in the containers
- All containers should use API keys for authentication and determine what they are allowed to do.
- Use TCP port 8000 for the Web UI container.
- Use TCP port 8001 for the Authentication Service container.
- Use TCP port 8002 for the Agent container.
- Use TCP port 8003 for the Documents and Skills Vector Store container.
- Use TCP port 11434 for the Ollama Vector Embedding container.
- Use TCP port 8005 for the Tools container.
- Use TCP port 8006 for the Logging container.
- All of the containers should send all the logs to the Logging container using the Logging service API.

### Web UI
- Create a soft link from the ./.env file to the web_ui/secrets/.env file
- Create a container for the web UI in the web_ui/ folder for all files related to this web UI
  - Mount a volume to persist all the contents in the ./web_ui/secrets/ folder on the host to the secrets/ folder in the container. This folder will be used to store the API keys used by the web UI.
  - Import GEMINI_MODEL from the secrets/.env file and use it as the default model to make the request to the agent
  - Mount the host Docker socket /var/run/docker.sock to /var/run/docker.sock inside the web_ui container so that the Container Manager can monitor container health/resources and trigger Start/Stop/Restart actions using the Python docker SDK
  - Provide the access to the UI described above.
  - Create a unique Conversation ID for each chat message.
  - When sending a request to the Agent container, include the API key that was provided by the user on the login page in the web UI.
  - Log when the user:
    - Logs into and out of the system with:
      - the user name
      - IP address
      - time of login and logout
    - Views different pages in the web UI with:
      - the user name
      - IP address
      - time the page was viewed
      - page name

### Authentication Service
- Create a container for the authentication & authorization services in the auth_service/ folder
  - Persist user accounts and API keys in an SQLite database mounted to host ./auth_service/data/ volume.
  - Seed a default initial Admin account on first startup: username: admin, password: admin123
  - Manages user accounts and API keys as described in the "Passwords & API keys" page in the web UI.
  - When a new user account is created, it is initially set to "Locked" status. The administrator can unlock the account via the UI.
  - Allows the containers to authenticate and get the permissions of the API key provided when the container gets the request from the other containers or from the web UI.
  - Create a log of API key access from each container and user, and send them to the Logging container using the Logging service API. The API key access log should contain the following information:
    - Container name
    - User name (if from the Web UI) or API key name (if from other containers)
    - IP address
    - Type of request (for example, chat, tool, etc.)
    - Date/time of request
    - The result of the request (success or failure)
    - The full payload of the request and response

### Agents
- Create a container for the agent in the agents/ folder.
  - Use FastMCP server with async HTTP transport as an interface to provide access to all the services. 
  - Link the .env from the root folder to the agents/secrets folder
  - The secrets/ folder in the container should map to the agents/secrets/ folder on the host. Use volume to persist the secrets/ on the host.
  - Upon start up:
    - import GEMINI_API_KEY from the .env file
    - import API keys that had been previously configured for the agent services from the secrets/keys file
    - The app should scan the skills/ folder and load the skills that are not currently in the skills vector database.
  - Store all API keys configured in the keys file in the secrets/keys file
  - Use GEMINI_API_KEY to make the LLM calls using Google genai library


  - The skills folder structure should as follow:
  ```
  ├── skills/
  │   ├── <skill_name>/          # Skill folder (e.g., time-weather-skill)
  │   │   ├── SKILL.md            # Skill metadata and SOP
  │   │   └── scripts/            # Python scripts for tools
  │   │       └── tool_*.py       # Tool scripts (e.g., env_tools.py)
  │   └── <another_skill>/       # Another skill folder
  │       ├── SKILL.md            # Skill metadata and SOP
  │       └── scripts/            # Python scripts for tools
  │           └── tool_*.py       # Tool scripts
  ```

  - Create two agents: Custom agent and Google genai agent.
    - All Custom agents should be in the agents/custom_agent/ folder
    - All Google genai agents should be in the agents/genai/ folder

#### The Custom Agent
The Custom Agent should operate as follow:
  - When it receives the message from the user, check the Skills selection in the request:
    - If it is "Vector Store Selects" use the skills vector store to find the skills that have a higher matching score than the minimum threshold set by the user.
    - If it is "Use AI Agent with Tools" send the name and description of all skills to the LLM and use the simple system prompt asking the LLM to determine if it should use any of the skills to answer the question.
    - If it is "Skill: xxxxxx", then send the user message and the skill description to the LLM to get the instruction or plan for the tool execution.
  - If no skill is found, send the user query to the LLM using the simple system prompt as an assistant to answer the question.
  - If there are multiple skills found, send the user message and the 2 highest matching skills to the LLM to get the instruction or plan for the tool execution.
  - The system prompt should ask the LLM to determine if any of the tools should be invoked to gather more information to answer the question.
  - The system prompt should ask the LLM to respond with JSON format indicating the tool to be executed and the arguments to be passed to the tool. For example:
  ```
    {
      "tool": "person_search.query_person_registry",
      "arguments": {
        "keyword": "Lucas Dubois",
        "field": "name"
      }
    }
  ```
  - If the LLM determines that a procedural tool should be executed, execute the tool to obtain the needed information. Send a prompt to the LLM with the results from the tool. Repeat until the final answer is received. Limit the number of loops no more than MAX_LLM_TURNS.
  - Minimize skill-specific code in the orchestrator
  - The last llm call should use a typical system prompt as an assistant to answer the question. The final output of the agent is the response from this last LLM call.
  - Only perform vector search for documents when the skill search result and the model direct the Agent to perform the search.
  - Minimize the number of loops to obtain the final answer. The maximum number of loops should be Max turns configured in the GUI.
  - Format the final output to make it easy for human reading and understanding.

#### Google ADK Agent
- Create a python code in agents/genai/ folder to use LlmAgent from Google ADK.
- Use the model selected in the Chat & Knowledge Synthesis page.
- Set the agent_type to "Google ADK Agent" and add it to the log record.
- Use the skills and tools available in the skills/ folder.
- Create logs for all the invocations and responses when the Agent is invoked.
  - Include all the details needed to show in the Audit Log & Event page.
  - Create logs when the Agent invokes and receives response from the model. Include the actual payload.

#### Logs
- Create logs for all the calls / invocations and responses between the following components. The log should include the actual details of the payloads passed to and from the components. 
  - agent - log the complete messages including actual payload:
    - Sent to the agent
    - sent/calls from the agent to: tools, ollama, vector store, MCP, and LLM.
    - All the responses received from the calls and the LLM
  - LLM - prompts sent to and response received from the model include the FULL payload. Log the model invocation and response. Include the FULL PAYLOAD.
  - In all of the logs, include the time of the call, the type of the call, the invoker, the recipient, and all the raw payload passed in the message.

#### Sample Skills and Tools
- Create the following skills using the skills folder structure. The skills should at least have the name, description, Trigger Queries, etc:
  - Write the SKILL.md file to get the time and weather of the city in the query.
    - Create the python code in the skills/<skill_name>/scripts/ folder that will get the time and weather of the city in the query. Use a site that doesn't require API key to get the data
  - Write the SKILL.md file to get the list of stocks with the highest percentage increase or lowest percentage decrease based on the chat question.
    - Create the python code in the skills/<skill_name>/scripts/ folder that will get the list of stocks with the highest percentage increase or lowest percentage decrease based on the chat question. Call the tools container to get the response.
  - Write the SKILL.md file to get the list of top k text chunks from the document vector database.
    - Call the tools container to get the response.
  - Write the SKILL.md file to get the name, city, country, or job title of the person in the CSV file.
    - Call the tools container to get the response.

### Documents and Skills
- Create a doc_RAG container in the doc_RAG/ folder.
  - Use FastMCP server with async HTTP transport as an interface to provide access to query the documents and skills vector store databases.
  - Use the API key sent in the request to check with the Authorization Service whether the service has the authority to access the embedding service
  - All the query calls must include Conversation ID to allow the logging service to track the calls

  - The vector store database has the following services:
    - All the requests to the vector store must include the database type: "document" or "skill"
    - Add New Document. Only allow users with edit or admin permission to add new documents. The request must contain:
      - the name of the document or skill
      - the complete text of the document or skill
      - for skill, the "vector_text" that should be used to create the vector for this skill
    - Delete Document or the skill. Only allow users with edit or admin permission to delete documents. The request must contain:
      - the name of the document or skill
    - Query the vector database. The request must contain:
      - the Conversation ID
      - the query text
      - the matching threshold
      - the number of text chunks to return
      - Return the text chunks that have the highest similarity scores above the matching threshold to the query.
        - Sort by descending order of the similarity scores
        - Return no more than the number of text chunks specified.

  - Use chromadb to store the documents and skills vector database
  - Create two databases: one for the document and another for the skill storage
  - Each record should contain:
    - name of the document or skill
    - the text chunk or complete text of the skill
    - the vector of the text chunk or complete text of the skill

  - For skill database:
    - To add skill into the vector database:
      - Use the embedding container to create the vector for the text in the "vector_text" of the skill.
      - Store the skill name, vector, and the complete text of the skill in the vector database

  - For document database:
    - Split the complete text of the document into chunks using the Chunk size and Overlap parameter sent in the request
    - Generate vectors for each chunk via the embedding container
    - Store each chunk record (document name, chunk text, chunk index, vector) in ChromaDB.

  - Create logs of all the communication between the request container and the vector store container. Include the Conversation ID (if available), the invoker, the recipient (Vector Store Service), date and time of the call, the request, and the full payload of the request and response.
  - Create a log for all the API requests and responses between the vector store container and the embedding container. Include the following information:
    - invoker
    - recipient (Embedding Service)
    - date and time of the call
    - the request
    - the response

### Embedding
- Create an embedding container in the embedding/ folder.
  - Use the embedding container from ollama
  - Provide the API access to query the embedding service for:
    - The model that is currently loaded to embed the documents and skills
    - The list of available embed models in ollama
  - If the API key used for the service has edit or admin permission, allows the following:
    - Change or update the model used to embed the documents and skills


### Tools
- Create a tools container in the tools/ folder.
  - Use FastMCP with async HTTP transport to serve all the access to the tools in the container. 
  - Use the API key sent in the request to check with the Authorization Service whether the service has the authority to access the tools
  - All the calls must include Conversation ID to allow the logging service to track the calls
  - The container should have a volume data/ mounted to ./tools/data/ on the host hard drive to persist any data
  - The first tool provides the information about the employee from the csv file. The tool can search the employee by name, city, country, or job title.
    - Create 30 random employee records with name, city, country, and job title in a csv file. Store the data in the data/employee_database.csv file.
  - The second tool gets the list of stocks with the highest percentage increase or lowest percentage decrease based on criteria from the arguments in the function call.
  - Create logs of all the calls to the tools service. Include: 
    - Conversation ID
    - invoker
    - tool name
    - date and time of the call
    - arguments
    - complete request and response payload.

### Logging
- Create a logging service container in the logging/ folder to store logs from all the entities that interact with the system.
  - The logs should be stored in the logs/ folder that maps to the logging/logs/ on the host. Use volume to persist the logs on the host.
  - Keep the statistics of the Total number of logs, number of logs from each entity, and the size of the log files and save it into the logs/ folder

  - Provide the following APIs:
    - Accepts logs from all the entities in the system and stores them in the logs/ folder
    - Retrieve the logs based on the criteria from the arguments in the function call
      - Entity name
      - Conversation ID
      - Date range
      - Fields to return or statistics

## Sample Documents
- Create 3 sample documents in the sample_docs/ folder
  - One document should be about Agent and RAG technology, around 3000 words.
  - The second document should be a sample of a company marketing strategy. It should be around 3000 words.
  - The third document should be a sample of the financial report for the company. It should be around 3000 words.

## Misc
- Create a README.md with a brief description about:
  - what this system does
  - how to install the components needed
  - how to start all the services
  - how to shutdown all the services
  - user guide with information on how to use the system

- Create a requirements.txt and put all the libraries used by the app
