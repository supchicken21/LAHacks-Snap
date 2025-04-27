import os
import time
import asyncio # Import asyncio
from dotenv import load_dotenv
import google.generativeai as genai # ADD IMPORT

# Third-party imports
# from groq import Groq # Remove if not used elsewhere
from uagents import Agent, Context, Model

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
AGENT_SEED = "main_orchestrator_seed"
AGENT_PORT = 8006
AGENT_NAME = "main_orchestrator_agent" # Renamed agent

# Addresses of agents to contact (ensure these are correct based on seeds)
# Addresses are derived deterministically from the seeds used in the respective agent files
ADDRESS_BACKGROUND = "agent1qvxfehkpsetzsjjfcl8yr0jn3l8xms7eygdcjrhq63n7a2s6rmxlz8hjpf2" # From seed: "background_seed"
ADDRESS_MEDICAL = "agent1q2e74xhpyrm3vehhj4ztrjvf24sxgvcsfgrl9hdzrr5a75dn2jvzsj5y4al" # From seed: "medical_seed"
ADDRESS_GAME_DATA = "agent1q0entn3aqtwuqamq6c4v6dlujgdwd5rn5na3mzx08rj9986n6k52ggrrvqu" # From seed: "game_data_seed"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"
OUTPUT_FILE = './personalized_weekly_plan.txt'
RESPONSE_TIMEOUT = 30.0 # Wait up to 15 seconds for agent responses

# --- Models ---
# Models expected from other agents or for own use

class BackgroundData(Model): # Expecting this from background_analyzer
    message: str

class MedicalData(Model): # Expecting this from medical_profile_agent
    message: str

# Single model for Game Data Agent communication
class GameDataTransfer(Model):
    content: str

class CombinedPlan(Model): # Renamed for clarity
    combined_plan: str

# --- Agent State ---

# Dictionary to store responses from other agents
agent_responses = {
    "background": None,
    "medical": None, 
    "game_data": None,
}

# Dictionary to hold asyncio events for pending responses (transient)
response_events = {}

# --- Groq API Call ---

# Initialize Gemini Client (REPLACE BLOCK)
try:
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        gemini_model = None # Indicate model is unavailable
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print("Gemini client configured successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    gemini_model = None

async def generate_final_plan_with_groq(ctx: Context) -> str:
    """Generates the combined plan using Gemini, using stored responses."""
    # Check if Gemini model is available (REPLACE CHECK)
    if not gemini_model:
        return "Error: Gemini client not initialized or configured."

    # Construct prompt using responses, handling None values
    prompt_content = (
        f"Background Info Plan: {agent_responses['background'] or 'Not Available'}\n\n"
        f"Medical Info Plan: {agent_responses['medical'] or 'Not Available'}\n\n"
        f"AI Analysis of Game Data: {agent_responses['game_data'] or 'Not Available'}\n\n"
        f"Combine the patient's Background Information, Medical History, and AI-Analyzed Game Data into a comprehensive, evidence-based report that offers detailed insights into their neurodegenerative disease. The report should include a summary of the patient's clinical history, key diagnoses, treatments, and disease progression, as well as insights from the AI analysis of game data that identify specific functional impairments, movement patterns, or cognitive challenges. Additionally, incorporate relevant scientific insights from the latest research on neurodegenerative diseases, physical rehabilitation, and cognitive function, and provide personalized treatment recommendations for physicians and physical therapists to optimize care and improve patient outcomes."
    )

    ctx.logger.info("Generating combined plan with Gemini...") # Update log
    try:
        # Call Gemini API (REPLACE CALL)
        chat_completion = await asyncio.to_thread(
            gemini_model.generate_content,
            prompt_content
        )
        # Extract Gemini response (REPLACE EXTRACTION)
        final_plan = chat_completion.text
        ctx.logger.info("Combined plan generated.")

        # Write plan to file
        try:
            with open(OUTPUT_FILE, 'w') as f:
                f.write(final_plan)
            ctx.logger.info(f"Plan saved to {OUTPUT_FILE}")
        except IOError as e:
            ctx.logger.error(f"Error writing plan to file {OUTPUT_FILE}: {e}")

        return final_plan
    except Exception as e:
        ctx.logger.error(f"Error calling Gemini API: {e}") # Update log
        return "Error generating final plan via Gemini."

# --- Agent Definition ---
orchestrator_agent = Agent(
    name=AGENT_NAME,
    port=AGENT_PORT,
    seed=AGENT_SEED,
    endpoint=f"http://127.0.0.1:{AGENT_PORT}/submit",
    mailbox=True
)

# --- Agent Logic: Requesting Data ---

async def request_data_from_all(ctx: Context, current_request_events: dict):
    """Sends requests to all required agents and sets up events to wait for."""
    ctx.logger.info("Requesting data from all agents...")
    active_events = []
    # Clear previous responses
    for key in agent_responses:
        agent_responses[key] = None

    # Background Agent Request
    event_background = asyncio.Event()
    current_request_events['background'] = event_background # Store event for this request
    active_events.append(event_background.wait()) # Add wait() coroutine to list
    await ctx.send(ADDRESS_BACKGROUND, BackgroundData(message="Request background info plan"))

    event_medical = asyncio.Event()
    current_request_events['medical'] = event_medical # Store event for this request
    active_events.append(event_medical.wait()) # Add wait() coroutine to list
    await ctx.send(ADDRESS_MEDICAL, MedicalData(message="Request medical info plan"))

    # Game Data Agent Request (Use GameDataTransfer)
    try:
        event_game_data = asyncio.Event()
        current_request_events['game_data'] = event_game_data
        active_events.append(event_game_data.wait())
        # Send using the single model
        await ctx.send(ADDRESS_GAME_DATA, GameDataTransfer(content="Request AI game data analysis")) 
        ctx.logger.info(f"Sent request to Game Data agent: {ADDRESS_GAME_DATA}")
    except Exception as e:
        ctx.logger.error(f"Failed to send request to Game Data agent ({ADDRESS_GAME_DATA}): {e}")

    ctx.logger.info("Finished sending all active requests.")
    return active_events

# --- Agent Logic: Handling Responses ---

@orchestrator_agent.on_message(model=BackgroundData)
async def handle_background_data_response(ctx: Context, sender: str, msg: BackgroundData):
    ctx.logger.info(f"Received Background response from {sender}")
    agent_responses["background"] = msg.message
    # Signal that the background response has been received for the current request
    if 'background' in response_events and response_events['background']:
        response_events['background'].set()
        response_events['background'] = None # Clear event for this specific request cycle

@orchestrator_agent.on_message(model=MedicalData)
async def handle_background_data_response(ctx: Context, sender: str, msg: MedicalData):
    ctx.logger.info(f"Received Medical response from {sender}")
    agent_responses["medical"] = msg.message
    # Signal that the background response has been received for the current request
    if 'medical' in response_events and response_events['medical']:
        response_events['medical'].set()
        response_events['medical'] = None # Clear event for this specific request cycle

# Remove any old/incorrect game data handlers first

# Handler for Game Data Agent Response (Using GameDataTransfer)
@orchestrator_agent.on_message(model=GameDataTransfer) # Use the single model
async def handle_game_data_transfer_response(ctx: Context, sender: str, msg: GameDataTransfer): # Renamed function
    # Check if the sender is the game agent to avoid confusion
    if sender == ADDRESS_GAME_DATA: 
        ctx.logger.info(f"Received Game Data Analysis response from {sender}")
        agent_responses["game_data"] = msg.content # Store the content
        # Signal that the game data response has been received
        if 'game_data' in response_events and response_events['game_data']:
            response_events['game_data'].set()
            response_events['game_data'] = None # Clear event
    else:
        # Optional: Log if message came from unexpected sender
        ctx.logger.warning(f"Received GameDataTransfer message from unexpected sender: {sender}")

# --- Agent Logic: REST Endpoint and Startup ---

@orchestrator_agent.on_event("startup")
async def agent_startup(ctx: Context):
    """Logs agent startup"""
    ctx.logger.info(f"Agent {ctx.agent.name} starting up.")
    ctx.logger.info(f"Address: {ctx.agent.address}")
    ctx.logger.info(f"Waiting for POST requests on /generate_plan")
    if not gemini_model:
         ctx.logger.error("Gemini client failed to initialize. Check API key.")

@orchestrator_agent.on_rest_post("/generate_plan", None, CombinedPlan)
async def handle_plan_generation_request(ctx: Context):
    """Handles external request to generate the combined plan using async wait."""
    ctx.logger.info("Received /generate_plan request.")
    global response_events # Use the global dict for this request cycle
    response_events = {} # Clear events for this new request cycle

    try:
        active_wait_coroutines = await request_data_from_all(ctx, response_events)

        if not active_wait_coroutines:
             ctx.logger.warning("No active agent requests were sent.")
        else:
            ctx.logger.info(f"Waiting up to {RESPONSE_TIMEOUT}s for {len(active_wait_coroutines)} agent response(s)...")
            try:
                # Wait for all event.wait() coroutines concurrently with a timeout
                await asyncio.wait_for(asyncio.gather(*active_wait_coroutines), timeout=RESPONSE_TIMEOUT)
                ctx.logger.info("All expected agent responses received.")
            except asyncio.TimeoutError:
                ctx.logger.warning(f"Timed out waiting for agent responses after {RESPONSE_TIMEOUT}s.")
            except Exception as e:
                ctx.logger.error(f"Error waiting for agent responses: {e}")

    except Exception as e:
        ctx.logger.error(f"Error occurred during request_data_from_all: {e}")
        # If sending fails (e.g., endpoint resolution), log it but continue

    # Proceed to generate plan regardless of wait outcome, using whatever arrived
    received_count = sum(1 for resp in agent_responses.values() if resp is not None)
    ctx.logger.info(f"Proceeding to generate plan with {received_count} received response(s).")

    combined_plan_text = await generate_final_plan_with_groq(ctx)
    # Clear events dictionary after processing is complete for this request
    response_events = {}
    return CombinedPlan(combined_plan=combined_plan_text)

# --- Run Agent ---
if __name__ == "__main__":
    orchestrator_agent.run()
