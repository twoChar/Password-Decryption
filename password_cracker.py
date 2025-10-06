"""
Password Cracking Module for Office and PDF Files
Consolidated from c.ipynb
"""
import io
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass

import config
from utils import format_time, format_number, ensure_dir

logger = logging.getLogger(__name__)


@dataclass
class CrackResult:
    """Result of a cracking attempt."""
    filename: str
    password: Optional[str]
    attempts: int
    time_seconds: float
    success: bool

    def __str__(self):
        if self.success:
            return (f"✓ {self.filename}: password='{self.password}' "
                    f"(attempts={format_number(self.attempts)}, time={format_time(self.time_seconds)})")
        else:
            return (f"✗ {self.filename}: NOT FOUND "
                    f"(attempts={format_number(self.attempts)}, time={format_time(self.time_seconds)})")


class PasswordCracker:
    """Password cracker for Office and PDF files."""

    def __init__(self, candidates_file: Path, print_every: int = None, max_tries: int = None):
        """
        Initialize cracker.

        Args:
            candidates_file: Path to file with password candidates (one per line)
            print_every: Print progress every N attempts (None = use config)
            max_tries: Maximum attempts per file (None = try all)
        """
        self.candidates_file = candidates_file
        self.print_every = print_every or config.CRACK_PRINT_EVERY
        self.max_tries = max_tries or config.CRACK_MAX_TRIES

        if not self.candidates_file.exists():
            raise FileNotFoundError(f"Candidates file not found: {self.candidates_file}")

        # Count candidates
        with self.candidates_file.open("r", encoding="utf8") as f:
            self.num_candidates = sum(1 for line in f if line.strip())

        logger.info(f"Cracker initialized with {format_number(self.num_candidates)} candidates from {self.candidates_file.name}")

    def _iter_candidates(self) -> Iterator[str]:
        """Iterate over password candidates."""
        with self.candidates_file.open("r", encoding="utf8", errors="ignore") as f:
            for line in f:
                candidate = line.rstrip("\n\r")
                if candidate:
                    yield candidate

    def _try_office_password(self, file_path: Path, password: str) -> bool:
        """
        Try to decrypt an Office file with a password.

        Args:
            file_path: Path to Office file
            password: Password to try

        Returns:
            bool: True if password is correct
        """
        try:
            import msoffcrypto

            with file_path.open("rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=password)

                decrypted = io.BytesIO()
                office_file.decrypt(decrypted)

                # Verify decrypted data is non-empty
                data = decrypted.getvalue()
                return data and len(data) > 0

        except Exception:
            # Wrong password or other error
            return False

    def _try_pdf_password(self, file_path: Path, password: str) -> bool:
        """
        Try to decrypt a PDF file with a password.

        Args:
            file_path: Path to PDF file
            password: Password to try

        Returns:
            bool: True if password is correct
        """
        try:
            import pikepdf

            with pikepdf.open(file_path, password=password) as pdf:
                # If we can open it, password is correct
                return True

        except pikepdf.PasswordError:
            # Wrong password
            return False
        except Exception as e:
            # Other error
            logger.debug(f"PDF error for {file_path.name}: {e}")
            return False

    def crack_file(self, target_file: Path, output_decrypted: Path = None) -> CrackResult:
        """
        Attempt to crack a single file.

        Args:
            target_file: Path to password-protected file
            output_decrypted: Optional path to save decrypted file

        Returns:
            CrackResult: Result of cracking attempt
        """
        if not target_file.exists():
            raise FileNotFoundError(f"Target file not found: {target_file}")

        extension = target_file.suffix.lower()
        is_office = extension in config.OFFICE_EXTENSIONS
        is_pdf = extension in config.PDF_EXTENSIONS

        if not (is_office or is_pdf):
            raise ValueError(f"Unsupported file type: {extension}")

        logger.info(f"Cracking {target_file.name} ({extension})...")

        start_time = time.time()
        attempts = 0
        found_password = None

        for password in self._iter_candidates():
            if self.max_tries and attempts >= self.max_tries:
                logger.info(f"Reached max attempts limit ({self.max_tries})")
                break

            attempts += 1

            # Progress logging
            if attempts % self.print_every == 0:
                elapsed = time.time() - start_time
                rate = attempts / elapsed if elapsed > 0 else 0
                logger.info(f"[{format_number(attempts)}] attempts, "
                            f"elapsed {format_time(elapsed)}, "
                            f"rate {rate:.1f}/s, "
                            f"last: {password[:50]}")

            # Try the password
            try:
                if is_office:
                    success = self._try_office_password(target_file, password)
                else:  # PDF
                    success = self._try_pdf_password(target_file, password)

                if success:
                    found_password = password
                    break

            except Exception as e:
                logger.debug(f"Exception trying password: {e}")
                continue

        elapsed_time = time.time() - start_time

        # Create result
        result = CrackResult(
            filename=target_file.name,
            password=found_password,
            attempts=attempts,
            time_seconds=elapsed_time,
            success=found_password is not None
        )

        if result.success:
            logger.info(f"✓ SUCCESS: {result}")

            # Optionally save decrypted file
            if output_decrypted and is_office:
                self._save_decrypted_office(target_file, found_password, output_decrypted)

        else:
            logger.info(f"✗ FAILED: {result}")

        return result

    def _save_decrypted_office(self, input_file: Path, password: str, output_file: Path):
        """Save decrypted Office file."""
        try:
            import msoffcrypto

            with input_file.open("rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                office_file.load_key(password=password)

                decrypted = io.BytesIO()
                office_file.decrypt(decrypted)

                ensure_dir(output_file.parent)
                output_file.write_bytes(decrypted.getvalue())

            logger.info(f"Saved decrypted file: {output_file.resolve()}")

        except Exception as e:
            logger.error(f"Failed to save decrypted file: {e}")

    def crack_directory(self, target_dir: Path, results_file: Path = None) -> List[CrackResult]:
        """
        Crack all supported files in a directory.

        Args:
            target_dir: Directory containing password-protected files
            results_file: Optional path to save results CSV

        Returns:
            List[CrackResult]: Results for each file
        """
        if not target_dir.exists():
            raise FileNotFoundError(f"Target directory not found: {target_dir}")

        # Find all supported files
        target_files = []
        for pattern in ["*.docx", "*.pptx", "*.xlsx", "*.pdf"]:
            target_files.extend(target_dir.glob(pattern))

        if not target_files:
            logger.warning(f"No supported files found in {target_dir}")
            return []

        target_files.sort()
        logger.info(f"Found {len(target_files)} files to crack")

        results = []
        for i, target_file in enumerate(target_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"File {i}/{len(target_files)}: {target_file.name}")
            logger.info(f"{'='*60}")

            try:
                result = self.crack_file(target_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Error cracking {target_file.name}: {e}")
                results.append(CrackResult(
                    filename=target_file.name,
                    password=None,
                    attempts=0,
                    time_seconds=0,
                    success=False
                ))

        # Summary
        successes = sum(1 for r in results if r.success)
        total_attempts = sum(r.attempts for r in results)
        total_time = sum(r.time_seconds for r in results)

        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total files: {len(results)}")
        logger.info(f"Cracked: {successes} ({100*successes/len(results):.1f}%)")
        logger.info(f"Failed: {len(results) - successes}")
        logger.info(f"Total attempts: {format_number(total_attempts)}")
        logger.info(f"Total time: {format_time(total_time)}")

        # Save results
        if results_file:
            self._save_results_csv(results, results_file)

        return results

    def _save_results_csv(self, results: List[CrackResult], output_file: Path):
        """Save results to CSV file."""
        import csv

        ensure_dir(output_file.parent)

        with output_file.open("w", encoding="utf8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Password", "Attempts", "Time (s)", "Success"])

            for result in results:
                writer.writerow([
                    result.filename,
                    result.password or "",
                    result.attempts,
                    f"{result.time_seconds:.2f}",
                    "SUCCESS" if result.success else "FAILED"
                ])

        logger.info(f"Saved results to {output_file.resolve()}")


def crack_single_file(target_file: Path, candidates_file: Path,
                      output_decrypted: Path = None,
                      max_tries: int = None) -> CrackResult:
    """
    Convenience function to crack a single file.

    Args:
        target_file: Path to password-protected file
        candidates_file: Path to password candidates file
        output_decrypted: Optional path to save decrypted file
        max_tries: Maximum attempts (None = try all)

    Returns:
        CrackResult: Result of cracking attempt
    """
    cracker = PasswordCracker(candidates_file, max_tries=max_tries)
    return cracker.crack_file(target_file, output_decrypted)


def crack_directory(target_dir: Path, candidates_file: Path,
                    results_file: Path = None,
                    max_tries: int = None) -> List[CrackResult]:
    """
    Convenience function to crack all files in a directory.

    Args:
        target_dir: Directory containing password-protected files
        candidates_file: Path to password candidates file
        results_file: Optional path to save results CSV
        max_tries: Maximum attempts per file (None = try all)

    Returns:
        List[CrackResult]: Results for each file
    """
    cracker = PasswordCracker(candidates_file, max_tries=max_tries)
    return cracker.crack_directory(target_dir, results_file)
