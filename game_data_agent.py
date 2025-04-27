import os
import json
# import requests # No longer needed
from dotenv import load_dotenv
import logging # Import logging
import asyncio

# Third-party imports
from groq import Groq # Re-add Groq import
from uagents import Agent, Context, Model
# from uagents.setup import fund_agent_if_low # Not used

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
AGENT_SEED = "game_data_seed" # Keep seed the same
AGENT_PORT = 8004
AGENT_NAME = "game_data_agent" # Renamed agent

# Path to the data file written by the receiver server
# Assumes agent script runs from project root and receiver server runs in its subdir
EXTERNAL_DATA_FILE = 'received_game_data.json' # Correct path

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-8b-8192" # Or choose another suitable model like "gemma-7b-it"

# --- Models ---
# Single model for communication
class GameDataTransfer(Model):
    content: str

# --- Groq Client Initialization ---
try:
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in environment variables.")
        groq_client = None
    else:
        groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    groq_client = None

# --- Analysis Function ---

async def read_and_analyze_external_game_data(ctx: Context) -> str:
    """Reads all game data entries and uses Groq to generate insights."""
    ctx.logger.info(f"Attempting to read game data from: {os.path.abspath(EXTERNAL_DATA_FILE)}")
    game_data_list = []
    try:
        if os.path.exists(EXTERNAL_DATA_FILE) and os.path.getsize(EXTERNAL_DATA_FILE) > 0:
            with open(EXTERNAL_DATA_FILE, 'r', encoding='utf-8') as f:
                content = json.load(f)
            if isinstance(content, list):
                game_data_list = content
                ctx.logger.info(f"Successfully read {len(game_data_list)} entries from {EXTERNAL_DATA_FILE}")
            else:
                 ctx.logger.warning(f"Content in {EXTERNAL_DATA_FILE} is not a list.")
                 return "Error: Game data file does not contain a valid list."
        else:
            ctx.logger.warning(f"External data file not found or empty: {EXTERNAL_DATA_FILE}")
            return "Error: External game data file not found or empty."

    except json.JSONDecodeError as e:
        ctx.logger.error(f"Error decoding JSON from {EXTERNAL_DATA_FILE}: {e}")
        return f"Error: Invalid JSON format in {EXTERNAL_DATA_FILE}."
    except IOError as e:
        ctx.logger.error(f"Error reading file {EXTERNAL_DATA_FILE}: {e}")
        return f"Error: Could not read file {EXTERNAL_DATA_FILE}."
    except Exception as e:
        ctx.logger.error(f"Unexpected error reading external data: {e}")
        return "Error: Unexpected error reading external game data."

    # Proceed to analysis if data was read successfully
    if not game_data_list:
        return "Error: No game data available to analyze."

    if not groq_client:
        ctx.logger.error("Groq client not available for analysis.")
        return "Error: Analysis service not configured."

    try:
        # Convert the list of game data entries to a string for the prompt
        game_data_str = json.dumps(game_data_list, indent=2)

        # Construct the prompt for the LLM
        prompt = (
            f"You are an AI assistant analyzing game performance data for a user potentially recovering from a neurodegenerative disease. "
            f"Review the following time-ordered list of game data entries (the game is a dodging game in Augmented Reality, the user is a character in the game, and the game is tracking their performance seeing how many collisions they can avoid) (most recent last):\n\n{game_data_str}\n\n"
            f"Provide a full report including:\n" 
            f"1. A brief summary of the most recent game session's performance.\n" 
            f"2. Any noticeable trends or significant changes in performance metrics (e.g., score, accuracy, level reached) over the sessions.\n" 
            f"3. Any potential areas of concern or positive developments based *only* on this data.\n" 
            f"Keep the report clear and actionable, suitable for integration into a broader wellness plan."
        )

        ctx.logger.info("Sending game data analysis request to Groq...")
        chat_completion = await asyncio.to_thread( # Run blocking call in thread
             groq_client.chat.completions.create,
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        report = chat_completion.choices[0].message.content
        ctx.logger.info("Received analysis report from Groq.")
        return report
    except Exception as e:
        ctx.logger.error(f"Error calling Groq API for analysis: {e}")
        return "Error generating analysis report via Groq."

# --- Agent Definition ---
# Remove endpoint= argument
game_data_agent = Agent(
    name=AGENT_NAME,
    port=AGENT_PORT,
    seed=AGENT_SEED,
    endpoint=f"http://127.0.0.1:{AGENT_PORT}/submit",
    mailbox=True
)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# --- Agent Event Handlers ---

@game_data_agent.on_event("startup")
async def agent_startup(ctx: Context):
    """Logs agent startup"""
    ctx.logger.info(f"Agent {ctx.agent.name} starting up.")
    ctx.logger.info(f"Address: {ctx.agent.address}")
    ctx.logger.info(f"Will read external game data from: {os.path.abspath(EXTERNAL_DATA_FILE)}")
    if not groq_client:
        ctx.logger.error("Groq client failed to initialize during startup! Check API key.")

@game_data_agent.on_message(model=GameDataTransfer)
async def handle_game_data_request(ctx: Context, sender: str, msg: GameDataTransfer):
    """Handles requests by reading game data file and generating AI analysis."""
    # msg.content might contain the request text, e.g., "Request AI game data analysis"
    ctx.logger.info(f"Received analysis request from orchestrator ({sender}): {msg.content}") 
    analysis_report = await read_and_analyze_external_game_data(ctx)
    ctx.logger.info("Sending analysis report back to orchestrator...")
    try:
        # Send response using the single model
        await ctx.send(sender, GameDataTransfer(content=analysis_report))
    except Exception as e:
        ctx.logger.error(f"Failed to send analysis report back to {sender}: {e}")

# --- Run Agent ---
if __name__ == "__main__":
    game_data_agent.run()


