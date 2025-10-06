# PS-7 Password Cracking System

AI/ML-based password recovery for forensic evidence (Stage 1: Office 2013+ and PDF 1.7+).

## Quick Start

```bash
# Run full pipeline
python scripts/pipeline.py full --data data/training/rockyou.txt

# Or run individual steps
python scripts/pipeline.py train --data data/training/rockyou.txt
python scripts/pipeline.py generate
python scripts/pipeline.py crack tests/mock/
```

## Directory Structure

```
Pd/
├── src/                          # Source code (Python package)
│   ├── config.py                 # Configuration settings
│   ├── utils.py                  # Shared utilities
│   ├── models/
│   │   └── pcfg_model.py        # PCFG training and scoring
│   ├── generators/
│   │   └── password_generator.py # Password candidate generation
│   └── crackers/
│       └── password_cracker.py   # File decryption
│
├── scripts/                      # Executable scripts
│   └── pipeline.py              # Main CLI tool
│
├── notebooks/                    # Jupyter notebooks
│   ├── 01_training.ipynb        # Model training demo
│   ├── 02_model_analysis.ipynb  # PCFG analysis
│   ├── 03_generation.ipynb      # Candidate generation
│   └── 04_cracking.ipynb        # Password cracking demo
│
├── data/                         # Data files
│   ├── training/                # Training data (rockyou.txt)
│   ├── models/                  # Trained PCFG models
│   ├── snapshots/               # JSON snapshots
│   └── tokens/                  # Token frequency files
│
├── generated/                    # Generated password candidates
├── tests/mock/                   # Test files for cracking
├── results/                      # Cracking results
├── docs/                         # Documentation
└── config/                       # Configuration files

```

## Documentation

- **[docs/PIPELINE.md](docs/PIPELINE.md)** - Complete pipeline usage guide
- **[docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md)** - Code quality improvements
- **[docs/CLEANUP.md](docs/CLEANUP.md)** - Data generation and cleanup
- **[docs/PROPOSED_STRUCTURE.md](docs/PROPOSED_STRUCTURE.md)** - Directory structure design
- **[docs/PS_7.pdf](docs/PS_7.pdf)** - Problem statement

## Requirements

```bash
pip install -r config/requirements.txt
```

## Usage Examples

### Training

```bash
# Train on custom dataset
python scripts/pipeline.py train --data path/to/passwords.txt
```

### Generation

```bash
# Generate candidates
python scripts/pipeline.py generate

# Skip deterministic or stochastic
python scripts/pipeline.py generate --skip-deterministic
```

### Cracking

```bash
# Crack single file
python scripts/pipeline.py crack --target tests/mock/file.docx --max-tries 10000

# Crack directory
python scripts/pipeline.py crack tests/mock/ --max-tries 10000

# Use custom candidates
python scripts/pipeline.py crack tests/mock/ --candidates path/to/candidates.txt
```

## Features

- **PCFG-based password modeling** - Probabilistic Context-Free Grammar analysis
- **Dual generation strategies** - Deterministic beam search + stochastic sampling
- **Multi-format support** - Office 2013+ (.docx, .xlsx, .pptx) and PDF 1.7+
- **Modular architecture** - Clean separation of training, generation, and cracking
- **Interactive notebooks** - Jupyter notebooks for exploration and analysis

## Stage 1 Requirements

- Minimum password length: **6 characters**
- Target formats: **Office 2013+, PDF 1.7+**
- Training data: **rockyou.txt** (14M passwords)
- Generated candidates: **65,613 unique passwords**

## Project Status

✅ Models trained on 6+ character passwords
✅ 65,613 unique candidates generated
✅ Clean modular codebase
✅ Professional directory structure
⏭️ Ready for Stage 1 evaluation
