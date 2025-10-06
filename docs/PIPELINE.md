# PS-7 Password Cracking System

AI/ML-driven password recovery system for PS-7 Stage 1 competition.

**Target:** Office 2013+, PDF 1.7+ with **6+ character** passwords.

## Architecture

The codebase has been refactored from Jupyter notebooks into a modular Python pipeline:

```
├── config.py              # Configuration parameters
├── utils.py               # Shared utilities (tokenization, normalization)
├── pcfg_model.py          # PCFG model implementation
├── password_generator.py  # Deterministic & stochastic generation
├── password_cracker.py    # Office & PDF cracking logic
├── pipeline.py            # Main CLI entry point
└── requirements.txt       # Python dependencies
```

### Key Components

1. **PCFG Model** - Probabilistic Context-Free Grammar for password structure learning
2. **Dual Generation** - Deterministic beam search + stochastic sampling
3. **Multi-format Cracking** - Office (docx/pptx/xlsx) and PDF support

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Full pipeline (train -> generate -> crack)
python pipeline.py full --data Data-Breach/rockyou.txt

# Or run individual steps:

# 1. Train models
python pipeline.py train --data Data-Breach/rockyou.txt

# 2. Generate candidates
python pipeline.py generate

# 3. Crack files
python pipeline.py crack Mock/
```

## Commands

### `train` - Train PCFG Models

Trains password models and extracts token frequencies from a password dataset.

```bash
python pipeline.py train --data rockyou.txt
```

**Outputs:**
- `output/models/pcfg_model_all_state.pkl` - Model trained on all passwords
- `output/models/pcfg_model_ge6_state.pkl` - Model trained on passwords ≥6 chars
- `pcfg_all.json` - Statistics snapshot (all)
- `pcfg_of_len6_or_more.json` - Statistics snapshot (≥6 chars)
- `frag_tokens_all.tsv` - Fragment token frequencies (all)
- `frag_tokens_len6.tsv` - Fragment token frequencies (≥6 chars)

**Training time:** ~5-10 minutes with rockyou.txt (~14M passwords)

### `generate` - Generate Password Candidates

Generates password candidates using trained models.

```bash
python pipeline.py generate
```

**Options:**
- `--skip-deterministic` - Skip deterministic beam search generation
- `--skip-stochastic` - Skip stochastic sampling generation

**Outputs:**
- `output/candidates/candidates_det_ge6.txt` - Deterministic candidates (~200k)
- `output/candidates/candidates_sto_ge6.txt` - Stochastic candidates (~100k)
- `output/candidates/candidates_combined_ge6.txt` - Combined & deduplicated

**Generation time:** ~2-5 minutes

### `crack` - Crack Password-Protected Files

Attempts to crack files using generated candidates.

```bash
# Crack directory
python pipeline.py crack Mock/

# Crack single file
python pipeline.py crack --target Mock/Gc_PS7_Mock_test1.docx

# With options
python pipeline.py crack Mock/ --max-tries 50000 --candidates custom_passwords.txt
```

**Options:**
- `--target` - File or directory to crack
- `--candidates` - Custom candidates file (default: uses generated)
- `--max-tries` - Maximum attempts per file (default: try all)
- `--save-decrypted` - Save decrypted files to output/results/

**Outputs:**
- `output/results/crack_results.csv` - Cracking results with passwords
- Progress logs with attempt rate and timing

**Supported formats:** .docx, .pptx, .xlsx, .pdf

### `full` - Run Full Pipeline

Runs all steps in sequence: train → generate → crack.

```bash
python pipeline.py full --data rockyou.txt --target Mock/
```

**Options:**
- `--data` - Password training file
- `--target` - Files to crack (default: Mock/)
- `--skip-training` - Skip training phase
- `--skip-generation` - Skip generation phase
- `--skip-cracking` - Skip cracking phase
- `--max-tries` - Max attempts per file

## Configuration

Edit `config.py` to customize:

```python
# Password length constraints
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 64

# Generation parameters
BEAM_MAX_TOTAL_CANDIDATES = 200000
STOCHASTIC_NUM_SAMPLES = 3000

# Cracking parameters
CRACK_MAX_TRIES = None  # None = try all
CRACK_PRINT_EVERY = 1000
```

## Methodology

### PCFG (Probabilistic Context-Free Grammar)

Passwords are parsed into templates using context-sensitive rules:

- **WORD**: Dictionary words (using NLTK vocabulary)
- **FRAG**: Non-dictionary fragments
- **DIGITS**: Numeric sequences
- **SYMBOL**: Special characters

Example: `Password123!` → Template: `WORD8|DIGITS3|SYMBOL`

### Generation Strategies

1. **Deterministic Beam Search**
   - Explores high-probability combinations
   - Prunes beam by frequency-based scores
   - Guarantees coverage of top patterns

2. **Stochastic Sampling**
   - Samples from empirical token distributions
   - Discovers diverse candidates
   - Complements deterministic coverage

### Leet-Speak Normalization

Normalizes l33t-speak during training:
- `P@ssw0rd` → `password` template
- Increases pattern generalization

## Performance

**Expected Results on Mock Files:**

| Metric | Value |
|--------|-------|
| Training time | ~5-10 min |
| Generation time | ~2-5 min |
| Candidates generated | ~300k unique |
| Crack rate (mock) | 30-60% |
| Speed | ~20-50 attempts/sec |

## Comparison with Notebooks

### Before (Notebooks)
- ❌ Scattered across 4 files (main, a, b, c)
- ❌ Duplicate code and imports
- ❌ Hard to configure and extend
- ❌ No CLI interface
- ❌ Difficult to test

### After (Pipeline)
- ✅ Modular architecture (6 focused modules)
- ✅ Single source of truth (config.py)
- ✅ Clean CLI interface
- ✅ Reusable components
- ✅ Easy to test and extend
- ✅ Production-ready structure

## Troubleshooting

### "Snapshot not found"
Run training first: `python pipeline.py train --data rockyou.txt`

### "No candidates file found"
Run generation first: `python pipeline.py generate`

### "NLTK words corpus not found"
The system will auto-download on first run, or manually:
```python
import nltk
nltk.download('words')
```

### Low crack rate
- Increase candidate generation (edit `config.py`)
- Use larger training dataset
- Combine multiple wordlists

## Future Enhancements

1. **Transformer Integration** - Integrate PassTSL model from `passTLS/` directory
2. **Multi-GPU Support** - Parallelize cracking across files
3. **Adaptive Generation** - Learn from cracked passwords during execution
4. **Hash Support** - Extend to raw hash cracking (Stage 2)

## License

Developed for PS-7 Password Cracking Challenge - Stage 1.
