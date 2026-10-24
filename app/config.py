"""Central settings. Everything tunable lives here or in .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DOCS_DIR = DATA_DIR / "kb_docs"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
DB_PATH = DATA_DIR / "tickets.db"                 # orders + ticket log
CHECKPOINT_DB_PATH = DATA_DIR / "checkpoints.db"  # LangGraph pause/resume state
TESTS_DIR = BASE_DIR / "tests"

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.5-flash-lite",
    "nvidia": "nvidia/nemotron-3-nano-30b-a3b",
}  # model names change over time; override with LLM_MODEL if one is retired
LLM_MODEL = os.getenv("LLM_MODEL", "") or DEFAULT_MODELS.get(LLM_PROVIDER, "")
# Failover: comma-separated providers tried (in order) if the primary fails, e.g. "gemini,nvidia"
LLM_FALLBACKS = [p.strip().lower() for p in os.getenv("LLM_FALLBACKS", "").split(",") if p.strip()]
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))  # attempts per model before failing over
API_KEY_ENV = {"groq": "GROQ_API_KEY", "gemini": "GOOGLE_API_KEY", "nvidia": "NVIDIA_API_KEY"}

# Retrieval
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "support_kb"

# Business rules
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
REFUND_LIMIT = float(os.getenv("REFUND_LIMIT", "500"))
ORDER_CATEGORIES = {"ORDER", "REFUND", "DELIVERY", "CANCEL", "SHIPPING", "PAYMENT", "INVOICE"}

# Langfuse is on only when both keys exist
LANGFUSE_ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
