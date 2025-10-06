"""
PCFG (Probabilistic Context-Free Grammar) Model for Password Analysis
Consolidated from a.ipynb and main.ipynb
"""
import re
import math
import json
import pickle
import logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import Union, List, Tuple, Dict, Any

from utils import tokenize, classify_run, iter_lines_from_file, ensure_dir
import config

logger = logging.getLogger(__name__)


class PCFGLite:
    """
    Lightweight PCFG model for password probability estimation.

    Uses template-based parsing with smoothed frequency estimation.
    """

    def __init__(self, alpha: float = 1.0, do_leet: bool = False):
        """
        Initialize PCFG model.

        Args:
            alpha: Smoothing parameter (Laplace smoothing)
            do_leet: Whether to normalize leet-speak during parsing
        """
        self.template_counts = Counter()
        self.slot_counts = defaultdict(Counter)  # slot_type -> Counter(token)
        self.total_templates = 0
        self.alpha = float(alpha)
        self.do_leet = do_leet

    def __repr__(self):
        return f"PCFGLite(total_templates={self.total_templates}, unique_templates={len(self.template_counts)}, do_leet={self.do_leet})"

    def trim_slot_counts(self, top_n: int = 100000):
        """
        Trim each slot Counter to top N entries to manage memory.

        Args:
            top_n: Number of top tokens to keep per slot
        """
        for slot_type in list(self.slot_counts.keys()):
            self.slot_counts[slot_type] = Counter(dict(self.slot_counts[slot_type].most_common(top_n)))
        logger.info(f"Trimmed slot counts to top {top_n} per slot")

    def fit_list(self, pw_list, max_samples: int = None, verbose: bool = True,
                 use_vocab: bool = True, trim_top_n: int = None):
        """
        Train model from a list/iterable of passwords.

        Args:
            pw_list: Iterable of password strings
            max_samples: Maximum number of passwords to process (None = all)
            verbose: Whether to log progress
            use_vocab: Whether to use vocabulary for word detection
            trim_top_n: Periodically trim slot counts to top N (memory optimization)
        """
        processed = 0

        for i, pw in enumerate(pw_list):
            if max_samples and i >= max_samples:
                break
            if not pw:
                continue

            # Tokenize and count template
            tokens, template = tokenize(pw, do_leet=self.do_leet, use_vocab=use_vocab)
            self.template_counts[template] += 1
            self.total_templates += 1

            # Count tokens for each slot
            runs = re.findall(r'[A-Za-z]+|\d+|[^A-Za-z\d]+', pw)
            for r in runs:
                slot_type, token_for_counts, _ = classify_run(r, do_leet=self.do_leet, use_vocab=use_vocab)
                self.slot_counts[slot_type][token_for_counts] += 1

            processed += 1

            # Progress logging
            if verbose and (processed % 100000 == 0):
                logger.info(f"Processed {processed:,} passwords...")

            # Periodic trimming to control memory
            if trim_top_n and (processed % 500000 == 0):
                self.trim_slot_counts(trim_top_n)

        if verbose:
            logger.info(f"Training complete: {self.total_templates:,} templates, {len(self.template_counts):,} unique")

    def fit_file(self, filepath: Union[str, Path], max_lines: int = None,
                 use_vocab: bool = True, trim_top_n: int = None):
        """
        Train model from a password file.

        Args:
            filepath: Path to password file (one per line)
            max_lines: Maximum lines to read (None = all)
            use_vocab: Whether to use vocabulary for word detection
            trim_top_n: Periodically trim slot counts to top N
        """
        filepath = Path(filepath)
        logger.info(f"Training model from {filepath.name}...")

        def iter_lines():
            for i, line in enumerate(iter_lines_from_file(filepath)):
                if max_lines and i >= max_lines:
                    break
                yield line

        self.fit_list(iter_lines(), max_samples=None, verbose=True,
                      use_vocab=use_vocab, trim_top_n=trim_top_n)

    def template_prob(self, template: str) -> float:
        """Calculate probability of a template with smoothing."""
        V = len(self.template_counts)
        return (self.template_counts[template] + self.alpha) / (self.total_templates + self.alpha * (V + 1))

    def slot_token_prob(self, slot_type: str, token: str) -> float:
        """Calculate probability of a token given its slot type."""
        counter = self.slot_counts.get(slot_type, Counter())
        total = sum(counter.values())
        V = len(counter)
        return (counter[token] + self.alpha) / (total + self.alpha * (V + 1))

    def score(self, password: str, use_vocab: bool = True) -> float:
        """
        Calculate log-probability score for a password.

        Args:
            password: Password to score
            use_vocab: Whether to use vocabulary for word detection

        Returns:
            float: Log-probability (higher = more likely)
        """
        tokens, template = tokenize(password, do_leet=self.do_leet, use_vocab=use_vocab)
        logp = math.log(self.template_prob(template))

        runs = re.findall(r'[A-Za-z]+|\d+|[^A-Za-z\d]+', password)
        for r in runs:
            slot_type, token_for_counts, _ = classify_run(r, do_leet=self.do_leet, use_vocab=use_vocab)
            p = self.slot_token_prob(slot_type, token_for_counts)
            logp += math.log(p)

        return logp

    def top_templates(self, n: int = 30) -> List[Tuple[str, int]]:
        """Get top N most common templates."""
        return self.template_counts.most_common(n)

    def top_tokens(self, slot_type: str, n: int = 30) -> List[Tuple[str, int]]:
        """Get top N most common tokens for a slot type."""
        return self.slot_counts.get(slot_type, Counter()).most_common(n)

    def snapshot(self, top_templates_n: int = 200, top_words_n: int = 500,
                 top_digits_n: int = 200) -> Dict[str, Any]:
        """
        Create a snapshot of model statistics.

        Returns:
            dict: Summary statistics
        """
        return {
            "total_templates": self.total_templates,
            "unique_templates": len(self.template_counts),
            "top_templates": self.top_templates(top_templates_n),
            "top_words": self.top_tokens("WORD", top_words_n),
            "top_digits": self.top_tokens("DIGITS", top_digits_n),
        }

    def save(self, path: Union[str, Path], state_only: bool = True):
        """
        Save model to disk.

        Args:
            path: Output file path
            state_only: If True, save as dict (portable); if False, pickle full object
        """
        path = Path(path)
        ensure_dir(path.parent)

        if state_only:
            data = {
                "template_counts": dict(self.template_counts),
                "slot_counts": {k: dict(v) for k, v in self.slot_counts.items()},
                "total_templates": int(self.total_templates),
                "alpha": float(self.alpha),
                "do_leet": bool(self.do_leet),
            }
            with path.open("wb") as f:
                pickle.dump({"__pcfg_state_v1": True, "data": data}, f, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with path.open("wb") as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"Saved model to {path.resolve()} (state_only={state_only})")

    @classmethod
    def load(cls, path: Union[str, Path], state_only: bool = True) -> 'PCFGLite':
        """
        Load model from disk.

        Args:
            path: Input file path
            state_only: If True, load from dict; if False, unpickle object

        Returns:
            PCFGLite: Loaded model
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        with path.open("rb") as f:
            data = pickle.load(f)

        if state_only:
            # Handle wrapped state format
            if isinstance(data, dict) and data.get("__pcfg_state_v1"):
                st = data["data"]
            else:
                st = data

            model = cls(alpha=st.get("alpha", 1.0), do_leet=st.get("do_leet", False))
            model.template_counts = Counter(st.get("template_counts", {}))
            model.slot_counts = defaultdict(Counter, {k: Counter(v) for k, v in st.get("slot_counts", {}).items()})
            model.total_templates = int(st.get("total_templates", 0))
            logger.info(f"Loaded model from {path.resolve()}")
            return model
        else:
            if not isinstance(data, cls):
                raise TypeError("Unpickled object is not a PCFGLite instance")
            logger.info(f"Loaded model from {path.resolve()}")
            return data


def train_pcfg_model(data_path: Path, min_len: int = None, output_path: Path = None) -> PCFGLite:
    """
    Train a PCFG model from a password file.

    Args:
        data_path: Path to password file
        min_len: Minimum password length filter (None = no filter)
        output_path: Path to save model (None = don't save)

    Returns:
        PCFGLite: Trained model
    """
    model = PCFGLite(alpha=config.PCFG_ALPHA, do_leet=config.PCFG_DO_LEET)

    def iter_filtered():
        for pw in iter_lines_from_file(data_path):
            if min_len is None or len(pw) >= min_len:
                yield pw

    model.fit_list(iter_filtered(), verbose=True, use_vocab=True,
                   trim_top_n=config.PCFG_TRIM_TOP_N)

    if output_path:
        model.save(output_path, state_only=True)

    return model


def extract_frag_tokens(data_path: Path, min_pw_len: int = None,
                        min_token_len: int = 3, output_path: Path = None) -> Counter:
    """
    Extract FRAG tokens from password file.

    Args:
        data_path: Path to password file
        min_pw_len: Minimum password length filter
        min_token_len: Minimum token length
        output_path: Path to save TSV file (None = don't save)

    Returns:
        Counter: FRAG token frequencies
    """
    frag_counter = Counter()
    processed = 0

    for pw in iter_lines_from_file(data_path):
        if min_pw_len and len(pw) < min_pw_len:
            continue

        runs = re.findall(r'[A-Za-z]+|\d+|[^A-Za-z\d]+', pw)
        for r in runs:
            slot_type, token_for_counts, _ = classify_run(r, do_leet=config.PCFG_DO_LEET, use_vocab=True)
            if slot_type == "FRAG" and len(token_for_counts) >= min_token_len:
                frag_counter[token_for_counts] += 1

        processed += 1
        if processed % 1_000_000 == 0:
            logger.info(f"Processed {processed:,} passwords...")

    logger.info(f"Extracted {len(frag_counter):,} unique FRAG tokens from {processed:,} passwords")

    if output_path:
        ensure_dir(output_path.parent)
        with output_path.open("w", encoding="utf8") as f:
            f.write("token\tcount\n")
            for token, cnt in frag_counter.most_common(config.TOP_FRAGS_N):
                f.write(f"{token}\t{cnt}\n")
        logger.info(f"Saved FRAG tokens to {output_path.resolve()}")

    return frag_counter


def save_snapshot(model: PCFGLite, output_path: Path, filter_info: Dict = None):
    """
    Save model snapshot as JSON.

    Args:
        model: PCFG model
        output_path: Output JSON file path
        filter_info: Optional filter metadata to include
    """
    ensure_dir(output_path.parent)

    snapshot = model.snapshot(
        top_templates_n=config.TOP_TEMPLATES_N,
        top_words_n=config.TOP_WORDS_N,
        top_digits_n=config.TOP_DIGITS_N
    )

    if filter_info:
        snapshot["filter"] = filter_info

    output_path.write_text(json.dumps(snapshot, ensure_ascii=False))
    logger.info(f"Saved snapshot to {output_path.resolve()}")
