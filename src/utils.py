"""
Utility functions shared across the password cracking system
"""
import re
import logging
from typing import List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# VOCABULARY AND NORMALIZATION
# ============================================================================

# Leet-speak translation table
LEET_MAP = str.maketrans({
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's',
    '7': 't', '@': 'a', '$': 's', '!': 'i'
})

def leet_normalize(s: str) -> str:
    """Normalize leet-speak characters to standard characters."""
    return s.translate(LEET_MAP).lower()


def load_english_vocab() -> set:
    """Load English vocabulary from NLTK."""
    try:
        import nltk
        from nltk.corpus import words as nltk_words
        try:
            vocab = set(w.lower() for w in nltk_words.words())
        except LookupError:
            logger.info("Downloading NLTK words corpus...")
            nltk.download("words", quiet=True)
            vocab = set(w.lower() for w in nltk_words.words())
        logger.info(f"Loaded English vocab with {len(vocab)} words")
        return vocab
    except ImportError:
        logger.warning("NLTK not available, vocabulary-based detection disabled")
        return set()


# Global vocabulary (lazy loaded)
_ENGLISH_VOCAB = None

def get_english_vocab() -> set:
    """Get or initialize the English vocabulary."""
    global _ENGLISH_VOCAB
    if _ENGLISH_VOCAB is None:
        _ENGLISH_VOCAB = load_english_vocab()
    return _ENGLISH_VOCAB


# ============================================================================
# TOKENIZATION AND CLASSIFICATION
# ============================================================================

def classify_run(r: str, do_leet: bool = False, use_vocab: bool = True) -> Tuple[str, str, str]:
    """
    Classify a password run (consecutive chars of same type).

    Returns:
        tuple: (slot_type, token_for_counts, template_token)
            - slot_type: DIGITS, WORD, FRAG, or SYMBOL
            - token_for_counts: normalized token for frequency counting
            - template_token: token used in template (e.g., WORD4, DIGITS2)
    """
    if r.isdigit():
        return "DIGITS", r, f"DIGITS{len(r)}"

    if r.isalpha():
        token_norm = r.lower()
        if do_leet:
            token_norm = leet_normalize(token_norm)

        # Check if it's a dictionary word
        if use_vocab and len(token_norm) >= 3:
            vocab = get_english_vocab()
            if vocab and token_norm in vocab:
                return "WORD", token_norm, f"WORD{len(token_norm)}"

        return "FRAG", token_norm, "FRAG"

    # Symbols/special characters
    return "SYMBOL", r, "SYMBOL"


def tokenize(password: str, do_leet: bool = False, use_vocab: bool = True) -> Tuple[List[str], str]:
    """
    Tokenize a password into runs and generate template.

    Args:
        password: The password to tokenize
        do_leet: Whether to normalize leet-speak
        use_vocab: Whether to use vocabulary for word detection

    Returns:
        tuple: (tokens_list, template_string)
    """
    pw = password.strip()
    runs = re.findall(r'[A-Za-z]+|\d+|[^A-Za-z\d]+', pw)

    tokens_for_counts = []
    template_parts = []

    for r in runs:
        slot_type, token_for_counts, template_token = classify_run(r, do_leet=do_leet, use_vocab=use_vocab)
        tokens_for_counts.append(token_for_counts)
        template_parts.append(template_token)

    template = "|".join(template_parts)
    return tokens_for_counts, template


def parse_template(template: str) -> List[Tuple[str, int]]:
    """
    Parse a template string into slot components.

    Args:
        template: Template string like "WORD4|DIGITS2|SYMBOL"

    Returns:
        List of (slot_type, length) tuples
    """
    parts = template.split("|")
    slots = []

    for part in parts:
        if part.startswith("WORD"):
            n = int(part[4:]) if len(part) > 4 and part[4:].isdigit() else None
            slots.append(("WORD", n))
        elif part.startswith("DIGITS"):
            n = int(part[6:]) if len(part) > 6 and part[6:].isdigit() else None
            slots.append(("DIGITS", n))
        elif part == "SYMBOL":
            slots.append(("SYMBOL", None))
        elif part == "FRAG":
            slots.append(("FRAG", None))
        else:
            # Fallback: treat as FRAG
            slots.append(("FRAG", None))

    return slots


# ============================================================================
# FILE I/O UTILITIES
# ============================================================================

def iter_lines_from_file(filepath: Path, encoding: str = "latin-1", skip_empty: bool = True):
    """
    Generator to iterate lines from a file.

    Args:
        filepath: Path to the file
        encoding: File encoding
        skip_empty: Whether to skip empty lines

    Yields:
        str: Each line (stripped of newlines)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with filepath.open("r", encoding=encoding, errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if skip_empty and not line:
                continue
            yield line


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, create if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================================
# PROGRESS UTILITIES
# ============================================================================

def format_time(seconds: float) -> str:
    """Format seconds into human-readable time string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def format_number(num: int) -> str:
    """Format number with thousand separators."""
    return f"{num:,}"
