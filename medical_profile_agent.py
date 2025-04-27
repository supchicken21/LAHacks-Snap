import os
from dotenv import load_dotenv
import json

# Third-party imports
from groq import Groq
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

# Load environment variables from .env file
load_dotenv()

# Open and load the JSON file with patient data
with open('medical_profile_data.json', 'r') as file:
    patient_dict = json.load(file)

# --- Agent Configuration ---

AGENT_SEED = "medical_seed" # Keep seed the same to maintain address
AGENT_PORT = 8008
AGENT_NAME = "medical_agent" # Renamed agent

# --- Models ---

class MedicalData(Model): # Renamed model
    message: str

# --- Groq API Call ---

# Initialize Groq Client (Loads API Key from Environment)
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"Error initializing Groq client: {e}. Make sure GROQ_API_KEY is set in .env")
    groq_client = None

async def fetch_medical_plan():
    """Calls the Groq API to generate a medical-profile-based plan."""
    if not groq_client:
        return "Error: Groq client not initialized."
    try:
        # Format patient data as a string for the prompt
        patient_data_str = json.dumps(patient_dict, indent=2)
        prompt_content = (
            f"You are a clinical assistant reviewing structured patient data for a patient with a neurodegenerative disorder. Based on the provided data, generate a full report in detail that includes a SOAP-style note, highlights relevant clinical red flags, tracks disease progression, suggests appropriate referrals or interventions, and identifies any care gaps. Also, convert complex clinical details into patient-friendly language where appropriate. Include recommendations for follow-up or care coordination tasks that a doctor might find useful. Your goal is to augment the physician's workflow, not replace their judgment—be clear, clinical, and actionable."
            f"{patient_data_str}"
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        # Log the specific error from Groq
        print(f"Error calling Groq API: {e}")
        return "Error generating plan via Groq."


# --- Agent Definition ---

# Create the medical Agent instance
medical_agent = Agent(
    name=AGENT_NAME,
    port=AGENT_PORT,
    seed=AGENT_SEED,
    endpoint=f"http://127.0.0.1:{AGENT_PORT}/submit",
    mailbox=True 
)

# --- Agent Event Handlers ---

@medical_agent.on_event("startup")
async def agent_startup(ctx: Context):
    """Logs agent startup"""
    ctx.logger.info(f"Agent {ctx.agent.name} starting up.")
    ctx.logger.info(f"Address: {ctx.agent.address}")
    if not groq_client:
         ctx.logger.error("Groq client failed to initialize. Check API key.")

@medical_agent.on_message(model=MedicalData)
async def handle_medical_request(ctx: Context, sender: str, msg: MedicalData):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    ctx.logger.info("Generating medical recovery plan...")
    plan = await fetch_medical_plan()
    ctx.logger.info("Sending plan back...")
    try:
        await ctx.send(sender, MedicalData(message=plan))
    except Exception as e:
         # Log error if sending fails (e.g., if sender endpoint cannot be resolved)
         ctx.logger.error(f"Failed to send plan back to {sender}: {e}")


# --- Run Agent ---

if __name__ == "__main__":
    medical_agent.run()
