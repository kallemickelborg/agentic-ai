import os
from dotenv import load_dotenv
import dspy
import litellm

# Load environment variables
load_dotenv()

# Configure litellm for gpt-5-mini compatibility
# gpt-5 models only support temperature=1, so we drop unsupported params
litellm.drop_params = True

# OpenAI Configuration
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )

# Initialize DSPy with OpenAI
# gpt-5-mini requires temperature=1 (cannot be 0.0)
gpt5_mini = dspy.LM(
    "openai/gpt-5-mini",
    max_tokens=8192,
    api_key=openai_api_key,
    temperature=1,
    reasoning_effort="minimal",
)
dspy.configure(lm=gpt5_mini)

# Export for use in other modules
__all__ = ["openai_api_key", "gpt5_mini"]
