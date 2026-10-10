
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="langfuse-connection-test",
) as span:
    span.update(output="Local Langfuse connection successful")

langfuse.flush()
print("Trace sent. Check Langfuse for the test trace.")