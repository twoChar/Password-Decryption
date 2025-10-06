# Proposed Professional Directory Structure

## Current Issues
- Python modules mixed with data files in root
- Notebooks in root
- Multiple unorganized directories (Files, zOther, pcfg_cracker, pcfg_toplists, passTLS)
- Data files scattered (JSON, TSV in root)
- No clear separation of concerns

## Proposed Structure

```
PS-7/
├── src/                          # Source code (importable Python package)
│   ├── __init__.py
│   ├── config.py
│   ├── utils.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── pcfg_model.py
│   ├── generators/
│   │   ├── __init__.py
│   │   └── password_generator.py
│   ├── crackers/
│   │   ├── __init__.py
│   │   └── password_cracker.py
│   └── external/                 # External libraries/tools
│       ├── pcfg_cracker/        # Move from root
│       └── passtls/             # Move from root (PassTSL transformer)
│
├── scripts/                      # Executable scripts
│   └── pipeline.py              # Main CLI tool
│
├── notebooks/                    # Jupyter notebooks for exploration
│   ├── 01_training.ipynb        # main.ipynb renamed
│   ├── 02_model_analysis.ipynb  # a.ipynb renamed
│   ├── 03_generation.ipynb      # b.ipynb renamed
│   └── 04_cracking.ipynb        # c.ipynb renamed
│
├── data/                         # All data files
│   ├── training/
│   │   └── rockyou.txt          # Move from Data-Breach/
│   ├── models/                  # Move from output/models/
│   │   ├── pcfg_model_all_state.pkl
│   │   └── pcfg_model_ge6_state.pkl
│   ├── snapshots/               # JSON snapshots
│   │   ├── pcfg_all.json
│   │   └── pcfg_of_len6_or_more.json
│   └── tokens/                  # Token frequency files
│       ├── frag_tokens_all.tsv
│       └── frag_tokens_len6.tsv
│
├── generated/                    # Generated candidates
│   ├── candidates_det_ge6.txt
│   ├── candidates_sto_ge6.txt
│   └── candidates_combined_ge6.txt
│
├── tests/                        # Test files for cracking
│   ├── mock/                    # Mock files from competition
│   │   └── (50 files)
│   └── samples/                 # Sample test files
│
├── results/                      # Cracking results
│   ├── crack_results.csv
│   └── decrypted/
│
├── docs/                         # Documentation
│   ├── README.md                # Main README (move from root)
│   ├── PIPELINE.md              # README_PIPELINE.md renamed
│   ├── IMPROVEMENTS.md          # CODE_IMPROVEMENT_SUMMARY.md renamed
│   ├── CLEANUP.md               # CLEANUP_SUMMARY.md renamed
│   └── PS_7.pdf                 # Problem statement from zOther/
│
├── config/                       # Configuration files
│   └── requirements.txt
│
├── .gitignore
└── setup.py                      # Package setup (optional)
```

## Benefits

1. **src/ Package Structure**
   - Makes code importable as a proper Python package
   - Clear module hierarchy (models, generators, crackers)
   - External dependencies isolated in src/external/

2. **scripts/ for Executables**
   - pipeline.py in dedicated location
   - Can add more scripts without cluttering

3. **notebooks/ for Exploration**
   - All notebooks in one place
   - Numbered and descriptive names
   - Clear purpose

4. **data/ for All Data**
   - Training data organized
   - Models in data/models/
   - Snapshots and tokens separated

5. **generated/ for Output**
   - Clear distinction from input data
   - All generated candidates in one place

6. **tests/ for Test Files**
   - Mock files organized
   - Separate from production data

7. **results/ for Output**
   - Cracking results separate from candidates
   - Decrypted files organized

8. **docs/ for Documentation**
   - All documentation in one place
   - Cleaner root directory

## Migration Impact

**Files to Move:**
- 6 Python modules → src/
- 4 notebooks → notebooks/
- 5 data files → data/
- pipeline.py → scripts/
- 4 docs → docs/
- Mock/ → tests/mock/
- output/ → data/models/ + generated/

**Code Updates Needed:**
- Update imports (use src. prefix or adjust PYTHONPATH)
- Update config.py paths
- Update pipeline.py imports
- Test that everything works

**Benefits Worth the Effort:**
- ✅ Professional package structure
- ✅ Clear separation of concerns
- ✅ Easier to navigate
- ✅ Better for deployment
- ✅ Scalable for future growth
