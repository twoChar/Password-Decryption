#!/usr/bin/env python3
"""
PS-7 Password Cracking Pipeline
Main entry point for training, generation, and cracking

Stage 1: Office 2013+ and PDF 1.7+ with 6+ character passwords
"""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import config
from src.utils import ensure_dir
from src.models.pcfg_model import train_pcfg_model, extract_frag_tokens, save_snapshot, PCFGLite
from src.generators.password_generator import PasswordGenerator, combine_and_dedupe_candidates
from src.crackers.password_cracker import crack_directory, crack_single_file

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def cmd_train(args):
    """Train PCFG models from password data."""
    logger.info("="*60)
    logger.info("TRAINING PCFG MODELS")
    logger.info("="*60)

    data_path = Path(args.data) if args.data else config.DATA_PATH

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    ensure_dir(config.MODELS_DIR)

    # Train model on all passwords
    logger.info("\n[1/4] Training model on all passwords...")
    model_all = train_pcfg_model(
        data_path,
        min_len=None,
        output_path=config.MODELS_DIR / config.MODEL_ALL
    )
    save_snapshot(model_all, Path(config.SNAPSHOT_ALL))

    # Train model on passwords >= MIN_LENGTH
    logger.info(f"\n[2/4] Training model on passwords >= {config.MIN_PASSWORD_LENGTH} chars...")
    model_ge6 = train_pcfg_model(
        data_path,
        min_len=config.MIN_PASSWORD_LENGTH,
        output_path=config.MODELS_DIR / config.MODEL_GE6
    )
    save_snapshot(model_ge6, Path(config.SNAPSHOT_GE6),
                  filter_info={"min_len": config.MIN_PASSWORD_LENGTH})

    # Extract FRAG tokens (all)
    logger.info("\n[3/4] Extracting FRAG tokens from all passwords...")
    extract_frag_tokens(
        data_path,
        min_pw_len=None,
        min_token_len=config.MIN_TOKEN_LENGTH,
        output_path=Path(config.FRAG_TOKENS_ALL)
    )

    # Extract FRAG tokens (>= MIN_LENGTH)
    logger.info(f"\n[4/4] Extracting FRAG tokens from passwords >= {config.MIN_PASSWORD_LENGTH} chars...")
    extract_frag_tokens(
        data_path,
        min_pw_len=config.MIN_PASSWORD_LENGTH,
        min_token_len=config.MIN_TOKEN_LENGTH,
        output_path=Path(config.FRAG_TOKENS_GE6)
    )

    logger.info("\n✓ Training complete!")
    logger.info(f"  Model (all): {config.MODELS_DIR / config.MODEL_ALL}")
    logger.info(f"  Model (≥{config.MIN_PASSWORD_LENGTH}): {config.MODELS_DIR / config.MODEL_GE6}")
    logger.info(f"  Snapshot (all): {config.SNAPSHOT_ALL}")
    logger.info(f"  Snapshot (≥{config.MIN_PASSWORD_LENGTH}): {config.SNAPSHOT_GE6}")


def cmd_generate(args):
    """Generate password candidates."""
    logger.info("="*60)
    logger.info("GENERATING PASSWORD CANDIDATES")
    logger.info("="*60)

    # Check required files
    snapshot_path = Path(config.SNAPSHOT_GE6)
    frag_path = Path(config.FRAG_TOKENS_ALL)

    if not snapshot_path.exists():
        logger.error(f"Snapshot not found: {snapshot_path}")
        logger.error("Run 'pipeline.py train' first")
        sys.exit(1)

    if not frag_path.exists():
        logger.error(f"FRAG tokens not found: {frag_path}")
        logger.error("Run 'pipeline.py train' first")
        sys.exit(1)

    # Initialize generator
    generator = PasswordGenerator(snapshot_path, frag_path)

    ensure_dir(config.CANDIDATES_DIR)

    # Generate deterministic candidates
    if args.skip_deterministic:
        logger.info("\n[1/3] Skipping deterministic generation...")
    else:
        logger.info("\n[1/3] Generating deterministic candidates...")
        generator.generate_candidates_deterministic(config.CANDIDATES_DET)

    # Generate stochastic candidates
    if args.skip_stochastic:
        logger.info("\n[2/3] Skipping stochastic generation...")
    else:
        logger.info("\n[2/3] Generating stochastic candidates...")
        generator.generate_candidates_stochastic(config.CANDIDATES_STO)

    # Combine and dedupe
    logger.info("\n[3/3] Combining and deduplicating candidates...")
    input_files = []
    if config.CANDIDATES_DET.exists():
        input_files.append(config.CANDIDATES_DET)
    if config.CANDIDATES_STO.exists():
        input_files.append(config.CANDIDATES_STO)

    if input_files:
        combine_and_dedupe_candidates(input_files, config.CANDIDATES_COMBINED)

    logger.info("\n✓ Generation complete!")
    if config.CANDIDATES_COMBINED.exists():
        logger.info(f"  Combined candidates: {config.CANDIDATES_COMBINED}")


def cmd_crack(args):
    """Crack password-protected files."""
    logger.info("="*60)
    logger.info("CRACKING PASSWORD-PROTECTED FILES")
    logger.info("="*60)

    # Check candidates file
    if args.candidates:
        candidates_file = Path(args.candidates)
    elif config.CANDIDATES_COMBINED.exists():
        candidates_file = config.CANDIDATES_COMBINED
    elif config.CANDIDATES_STO.exists():
        candidates_file = config.CANDIDATES_STO
    elif config.CANDIDATES_DET.exists():
        candidates_file = config.CANDIDATES_DET
    else:
        logger.error("No candidates file found")
        logger.error("Run 'pipeline.py generate' first")
        sys.exit(1)

    logger.info(f"Using candidates: {candidates_file}")

    # Single file or directory
    target_path = Path(args.target)

    if not target_path.exists():
        logger.error(f"Target not found: {target_path}")
        sys.exit(1)

    ensure_dir(config.RESULTS_DIR)

    max_tries = args.max_tries if args.max_tries else config.CRACK_MAX_TRIES

    if target_path.is_file():
        # Single file
        output_decrypted = config.RESULTS_DIR / f"decrypted_{target_path.name}" if args.save_decrypted else None
        result = crack_single_file(target_path, candidates_file, output_decrypted, max_tries)
        logger.info(f"\n{result}")

    else:
        # Directory
        results_file = config.RESULTS_DIR / "crack_results.csv"
        results = crack_directory(target_path, candidates_file, results_file, max_tries)

        # Print summary
        logger.info("\nCracked passwords:")
        for result in results:
            if result.success:
                logger.info(f"  {result.filename}: {result.password}")


def cmd_full(args):
    """Run full pipeline: train -> generate -> crack."""
    logger.info("="*60)
    logger.info("RUNNING FULL PIPELINE")
    logger.info("="*60)

    # Training
    if args.skip_training:
        logger.info("\nSkipping training phase...")
    else:
        cmd_train(args)

    # Generation
    if args.skip_generation:
        logger.info("\nSkipping generation phase...")
    else:
        cmd_generate(args)

    # Cracking
    if args.skip_cracking:
        logger.info("\nSkipping cracking phase...")
    else:
        # Set default target if not specified
        if not hasattr(args, 'target') or not args.target:
            args.target = str(config.MOCK_DIR)
        cmd_crack(args)

    logger.info("\n" + "="*60)
    logger.info("PIPELINE COMPLETE!")
    logger.info("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PS-7 Password Cracking Pipeline (Stage 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python pipeline.py full --data rockyou.txt

  # Individual steps
  python pipeline.py train --data rockyou.txt
  python pipeline.py generate
  python pipeline.py crack Mock/

  # Crack single file
  python pipeline.py crack --target Mock/Gc_PS7_Mock_test1.docx --max-tries 10000
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train PCFG models')
    train_parser.add_argument('--data', type=str, help='Path to password file (default: from config)')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate password candidates')
    gen_parser.add_argument('--skip-deterministic', action='store_true', help='Skip deterministic generation')
    gen_parser.add_argument('--skip-stochastic', action='store_true', help='Skip stochastic generation')

    # Crack command
    crack_parser = subparsers.add_parser('crack', help='Crack password-protected files')
    crack_parser.add_argument('target', type=str, nargs='?', help='File or directory to crack')
    crack_parser.add_argument('--candidates', type=str, help='Path to candidates file')
    crack_parser.add_argument('--max-tries', type=int, help='Maximum attempts per file')
    crack_parser.add_argument('--save-decrypted', action='store_true', help='Save decrypted files')

    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run full pipeline')
    full_parser.add_argument('--data', type=str, help='Path to password file')
    full_parser.add_argument('--target', type=str, help='Target to crack (default: Mock/)')
    full_parser.add_argument('--skip-training', action='store_true', help='Skip training phase')
    full_parser.add_argument('--skip-generation', action='store_true', help='Skip generation phase')
    full_parser.add_argument('--skip-cracking', action='store_true', help='Skip cracking phase')
    full_parser.add_argument('--max-tries', type=int, help='Maximum attempts per file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    if args.command == 'train':
        cmd_train(args)
    elif args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'crack':
        if not args.target:
            logger.error("Error: target argument is required for crack command")
            crack_parser.print_help()
            sys.exit(1)
        cmd_crack(args)
    elif args.command == 'full':
        cmd_full(args)


if __name__ == "__main__":
    main()
