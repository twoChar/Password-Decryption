"""
Configuration file for PS-7 Password Cracking System
Stage 1: Office 2013+ and PDF 1.7+ with 6+ character passwords
"""
from pathlib import Path

# ============================================================================
# DATA PATHS
# ============================================================================
# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "training" / "rockyou.txt"
MOCK_DIR = PROJECT_ROOT / "tests" / "mock"

# Output directories
MODELS_DIR = PROJECT_ROOT / "data" / "models"
CANDIDATES_DIR = PROJECT_ROOT / "generated"
RESULTS_DIR = PROJECT_ROOT / "results"

# ============================================================================
# TRAINING PARAMETERS
# ============================================================================
MIN_PASSWORD_LENGTH = 6  # Stage 1 requirement updated from 12 to 6
MAX_PASSWORD_LENGTH = 64
MIN_TOKEN_LENGTH = 3

# PCFG Model parameters
PCFG_ALPHA = 1.0  # Smoothing parameter
PCFG_DO_LEET = True  # Enable leet-speak normalization
PCFG_TRIM_TOP_N = 250000  # Keep top N tokens per slot to manage memory

# Snapshot parameters
TOP_TEMPLATES_N = 1000
TOP_WORDS_N = 2000
TOP_DIGITS_N = 500
TOP_FRAGS_N = 200000

# ============================================================================
# PASSWORD GENERATION PARAMETERS
# ============================================================================
# Deterministic beam search
BEAM_TOPK_PER_SLOT = 300
BEAM_PRUNE_SIZE = 2000
BEAM_MAX_OUTPUT_PER_TEMPLATE = 2000
BEAM_NUM_TEMPLATES = 40
BEAM_MAX_TOTAL_CANDIDATES = 200000

# Stochastic sampling
STOCHASTIC_NUM_SAMPLES = 3000
STOCHASTIC_MAX_OUTPUT_PER_TEMPLATE = 1000
STOCHASTIC_NUM_TEMPLATES = 60

# Token pool sizes for generation
GEN_TOP_WORDS = 2000
GEN_TOP_FRAGS = 2000
GEN_TOP_DIGITS = 500

# Common symbols for password generation
COMMON_SYMBOLS = ["!", "@", "#", "$", "%", "&", "!!", "##"]

# ============================================================================
# PASSWORD CRACKING PARAMETERS
# ============================================================================
CRACK_PRINT_EVERY = 1000  # Print progress every N attempts
CRACK_MAX_TRIES = None  # None = try all candidates
CRACK_TIMEOUT_PER_FILE = 3600  # Timeout in seconds (1 hour)

# File type extensions to crack
OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
PDF_EXTENSIONS = {".pdf"}

# ============================================================================
# MODEL FILE NAMES
# ============================================================================
MODEL_ALL = "pcfg_model_all_state.pkl"
MODEL_GE6 = "pcfg_model_ge6_state.pkl"

SNAPSHOT_ALL = PROJECT_ROOT / "data" / "snapshots" / "pcfg_all.json"
SNAPSHOT_GE6 = PROJECT_ROOT / "data" / "snapshots" / "pcfg_of_len6_or_more.json"

FRAG_TOKENS_ALL = PROJECT_ROOT / "data" / "tokens" / "frag_tokens_all.tsv"
FRAG_TOKENS_GE6 = PROJECT_ROOT / "data" / "tokens" / "frag_tokens_len6.tsv"

CANDIDATES_DET = CANDIDATES_DIR / "candidates_det_ge6.txt"
CANDIDATES_STO = CANDIDATES_DIR / "candidates_sto_ge6.txt"
CANDIDATES_COMBINED = CANDIDATES_DIR / "candidates_combined_ge6.txt"

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# RANDOM SEED
# ============================================================================
RANDOM_SEED = 42
