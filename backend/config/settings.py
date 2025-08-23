import os
from dotenv import load_dotenv
import dspy

# Load environment variables
load_dotenv()

# OpenAI Configuration
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )

# Initialize DSPy with OpenAI
gpt4o_mini = dspy.LM("openai/gpt-4o-mini", max_tokens=8192, api_key=openai_api_key)
dspy.configure(lm=gpt4o_mini)

# Export for use in other modules
__all__ = ["openai_api_key", "gpt4o_mini"]
