"""
Password Candidate Generation Module
Consolidated from b.ipynb with deterministic and stochastic methods
"""
import json
import math
import random
import logging
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Dict, Generator

from utils import parse_template, ensure_dir
import config

logger = logging.getLogger(__name__)

# Set random seed
random.seed(config.RANDOM_SEED)


class PasswordGenerator:
    """Generate password candidates using PCFG statistics."""

    def __init__(self, snapshot_path: Path, frag_tsv_path: Path):
        """
        Initialize generator from snapshot and FRAG tokens.

        Args:
            snapshot_path: Path to PCFG snapshot JSON
            frag_tsv_path: Path to FRAG tokens TSV file
        """
        self.snapshot = self._load_snapshot(snapshot_path)
        self.frag_counter = self._load_frag_tokens(frag_tsv_path)
        self.count_map = self._build_count_map()

        # Extract top lists
        self.top_templates = [tpl for tpl, _ in self.snapshot.get("top_templates", [])]
        self.top_words = [w for w, _ in self.snapshot.get("top_words", [])][:config.GEN_TOP_WORDS]
        self.top_digits = [d for d, _ in self.snapshot.get("top_digits", [])][:config.GEN_TOP_DIGITS]
        self.top_frags = [f for f, _ in self.frag_counter.most_common(config.GEN_TOP_FRAGS)]

        logger.info(f"Generator initialized: {len(self.top_templates)} templates, "
                    f"{len(self.top_words)} words, {len(self.top_digits)} digits, "
                    f"{len(self.top_frags)} frags")

    def _load_snapshot(self, path: Path) -> Dict:
        """Load PCFG snapshot JSON."""
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {path}")
        return json.loads(path.read_text(encoding="utf8"))

    def _load_frag_tokens(self, path: Path) -> Counter:
        """Load FRAG tokens from TSV file."""
        if not path.exists():
            raise FileNotFoundError(f"FRAG tokens file not found: {path}")

        frag_counter = Counter()
        with path.open("r", encoding="utf8") as f:
            next(f)  # Skip header
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) == 2:
                    token, count = parts
                    frag_counter[token] = int(count)

        logger.info(f"Loaded {len(frag_counter):,} FRAG tokens from {path.name}")
        return frag_counter

    def _build_count_map(self) -> Dict[Tuple[str, str], int]:
        """Build a map of (slot_type, token) -> count for scoring."""
        count_map = {}

        for word, count in self.snapshot.get("top_words", []):
            count_map[("WORD", word)] = count

        for digit, count in self.snapshot.get("top_digits", []):
            count_map[("DIGITS", digit)] = count

        for frag, count in self.frag_counter.items():
            count_map[("FRAG", frag)] = count

        return count_map

    def _partial_score(self, prefix_score: float, slot_type: str, token: str) -> float:
        """Calculate incremental score for beam search."""
        count = self.count_map.get((slot_type, token), 1)
        return prefix_score + math.log(count + 1)

    def _get_slot_choices(self, slot_type: str, topk: int) -> List[str]:
        """Get top K choices for a slot type."""
        if slot_type == "WORD":
            return self.top_words[:topk]
        elif slot_type == "FRAG":
            return self.top_frags[:topk]
        elif slot_type == "DIGITS":
            return self.top_digits[:topk]
        elif slot_type == "SYMBOL":
            return config.COMMON_SYMBOLS
        return []

    def estimate_template_length(self, template: str) -> Tuple[int, int]:
        """
        Estimate min and max length for a template.

        Returns:
            tuple: (min_length, max_length)
        """
        slots = parse_template(template)
        min_len = 0
        max_len = 0

        for slot_type, n in slots:
            if slot_type == "DIGITS":
                if n:
                    min_len += n
                    max_len += n
                else:
                    min_len += 1
                    max_len += (len(self.top_digits[0]) if self.top_digits else 4)

            elif slot_type == "WORD":
                if n:
                    min_len += n
                    max_len += n
                else:
                    min_len += 3
                    max_len += (len(self.top_words[0]) if self.top_words else 12)

            elif slot_type == "SYMBOL":
                min_len += 1
                max_len += 4

            elif slot_type == "FRAG":
                min_len += 3
                max_len += (len(self.top_frags[0]) if self.top_frags else 12)

        return min_len, max_len

    def generate_deterministic(self, template: str, topk_per_slot: int = 300,
                                prune_beam: int = 2000, min_len: int = 6,
                                max_out: int = 5000) -> Generator[Tuple[str, float], None, None]:
        """
        Generate passwords deterministically using beam search.

        Args:
            template: Template string (e.g., "WORD4|DIGITS2")
            topk_per_slot: Top K tokens to consider per slot
            prune_beam: Beam size (keep top N partial candidates)
            min_len: Minimum password length
            max_out: Maximum candidates to yield

        Yields:
            tuple: (password, score)
        """
        slots = parse_template(template)

        # Initialize beam with empty string
        beam = [("", 0.0)]

        for slot_type, _ in slots:
            new_beam = []
            choices = self._get_slot_choices(slot_type, topk_per_slot)

            for prefix, prefix_score in beam:
                for token in choices:
                    candidate = prefix + token

                    # Skip if too long
                    if len(candidate) > config.MAX_PASSWORD_LENGTH:
                        continue

                    new_score = self._partial_score(prefix_score, slot_type, token)
                    new_beam.append((candidate, new_score))

            # Prune beam
            new_beam.sort(key=lambda x: x[1], reverse=True)
            beam = new_beam[:prune_beam]

            if not beam:
                break

        # Filter by min length and yield top results
        final = [(cand, score) for cand, score in beam if len(cand) >= min_len]
        final.sort(key=lambda x: x[1], reverse=True)

        for cand, score in final[:max_out]:
            yield cand, score

    def generate_stochastic(self, template: str, n_samples: int = 3000,
                            min_len: int = 6) -> List[Tuple[str, float]]:
        """
        Generate passwords stochastically by sampling.

        Args:
            template: Template string
            n_samples: Number of samples to generate
            min_len: Minimum password length

        Returns:
            List of (password, score) tuples sorted by score
        """
        slots = parse_template(template)
        results = {}

        # Prepare weighted token lists
        word_choices = [(w, self.count_map.get(("WORD", w), 1)) for w in self.top_words]
        frag_choices = [(f, self.count_map.get(("FRAG", f), 1)) for f in self.top_frags]
        digit_choices = [(d, self.count_map.get(("DIGITS", d), 1)) for d in self.top_digits]

        def sample_from_choices(choices):
            if not choices:
                return ""
            tokens, counts = zip(*choices)
            total = sum(counts)
            weights = [c / total for c in counts]
            return random.choices(tokens, weights=weights, k=1)[0]

        for _ in range(n_samples):
            parts = []

            for slot_type, _ in slots:
                if slot_type == "WORD":
                    token = sample_from_choices(word_choices)
                elif slot_type == "FRAG":
                    token = sample_from_choices(frag_choices)
                elif slot_type == "DIGITS":
                    token = sample_from_choices(digit_choices)
                else:  # SYMBOL
                    token = random.choice(config.COMMON_SYMBOLS)

                parts.append(token)

            candidate = "".join(parts)

            if len(candidate) < min_len:
                continue

            # Calculate score
            score = 0.0
            for part, (slot_type, _) in zip(parts, slots):
                count = self.count_map.get((slot_type, part), 1)
                score += math.log(count + 1)

            # Keep best score per candidate
            if candidate not in results or results[candidate] < score:
                results[candidate] = score

        # Return sorted by score
        return sorted(results.items(), key=lambda x: x[1], reverse=True)

    def generate_candidates_deterministic(self, output_path: Path,
                                          num_templates: int = None,
                                          max_total: int = None) -> int:
        """
        Generate deterministic candidates and write to file.

        Args:
            output_path: Output file path
            num_templates: Number of templates to use (None = use config)
            max_total: Maximum total candidates (None = use config)

        Returns:
            int: Number of candidates generated
        """
        num_templates = num_templates or config.BEAM_NUM_TEMPLATES
        max_total = max_total or config.BEAM_MAX_TOTAL_CANDIDATES

        # Filter templates capable of reaching min length
        capable_templates = []
        for tpl in self.top_templates:
            min_l, max_l = self.estimate_template_length(tpl)
            if max_l >= config.MIN_PASSWORD_LENGTH:
                capable_templates.append(tpl)

        logger.info(f"Generating deterministic candidates from {len(capable_templates)} templates...")

        ensure_dir(output_path.parent)
        written = 0

        with output_path.open("w", encoding="utf8") as f:
            for tpl in capable_templates[:num_templates]:
                for cand, score in self.generate_deterministic(
                        tpl,
                        topk_per_slot=config.BEAM_TOPK_PER_SLOT,
                        prune_beam=config.BEAM_PRUNE_SIZE,
                        min_len=config.MIN_PASSWORD_LENGTH,
                        max_out=config.BEAM_MAX_OUTPUT_PER_TEMPLATE):
                    f.write(cand + "\n")
                    written += 1

                    if max_total and written >= max_total:
                        break

                if max_total and written >= max_total:
                    break

        logger.info(f"Generated {written:,} deterministic candidates -> {output_path.name}")
        return written

    def generate_candidates_stochastic(self, output_path: Path,
                                       num_templates: int = None) -> int:
        """
        Generate stochastic candidates and write to file.

        Args:
            output_path: Output file path
            num_templates: Number of templates to use (None = use config)

        Returns:
            int: Number of candidates generated
        """
        num_templates = num_templates or config.STOCHASTIC_NUM_TEMPLATES

        # Filter templates
        capable_templates = []
        for tpl in self.top_templates:
            min_l, max_l = self.estimate_template_length(tpl)
            if max_l >= config.MIN_PASSWORD_LENGTH:
                capable_templates.append(tpl)

        logger.info(f"Generating stochastic candidates from {len(capable_templates)} templates...")

        ensure_dir(output_path.parent)
        written = 0

        with output_path.open("w", encoding="utf8") as f:
            for tpl in capable_templates[:num_templates]:
                candidates = self.generate_stochastic(
                    tpl,
                    n_samples=config.STOCHASTIC_NUM_SAMPLES,
                    min_len=config.MIN_PASSWORD_LENGTH
                )

                for cand, score in candidates[:config.STOCHASTIC_MAX_OUTPUT_PER_TEMPLATE]:
                    f.write(cand + "\n")
                    written += 1

        logger.info(f"Generated {written:,} stochastic candidates -> {output_path.name}")
        return written


def combine_and_dedupe_candidates(input_files: List[Path], output_path: Path) -> int:
    """
    Combine multiple candidate files and remove duplicates.

    Args:
        input_files: List of input candidate file paths
        output_path: Output combined file path

    Returns:
        int: Number of unique candidates
    """
    unique_candidates = set()

    for input_file in input_files:
        if not input_file.exists():
            logger.warning(f"Input file not found: {input_file}")
            continue

        with input_file.open("r", encoding="utf8") as f:
            for line in f:
                candidate = line.strip()
                if candidate:
                    unique_candidates.add(candidate)

        logger.info(f"Loaded {len(unique_candidates):,} unique candidates from {input_file.name}")

    # Write unique candidates
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf8") as f:
        for candidate in sorted(unique_candidates):  # Sort for consistency
            f.write(candidate + "\n")

    logger.info(f"Combined {len(unique_candidates):,} unique candidates -> {output_path.name}")
    return len(unique_candidates)
