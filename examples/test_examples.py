#!/usr/bin/env python3
"""
Script to execute all Python files in subdirectories of the examples folder.
This will loop through each subdirectory and run each Python file in turn.
"""

import subprocess
import sys
from pathlib import Path

# TODO: Add in examples for all of the traits.

# Folder to start the search. Presently, any folder inside the directory containing this script.
root_folder = Path(__file__).parent

# Files with these names will not be processed
file_exclusion_list = [
    'a_template_game_loop.py'
]

folder_exclusion_list = [
    '__pycache__'
]

failures: int = 0


def execute_python_file(file_path):
    """Execute a Python file and capture its output."""
    global failures

    print(f"\n{'=' * 40}")
    print(f"Executing: {file_path.name}")
    print(f"{'=' * 40}")

    try:
        # Execute the Python file
        result = subprocess.run(
            [sys.executable, str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout per script
        )

        # Print stdout
        if result.stdout:
            print("StdOut:")
            print(result.stdout)

        # Print stderr if there are errors
        if result.stderr:
            print("StdErr:")
            print(result.stderr)

        # Print return code
        if result.returncode != 0:
            print(f"ERROR: Process exited with code: {result.returncode}")
            failures += 1
        else:
            print("Process completed successfully!")

    except subprocess.TimeoutExpired:
        print("ERROR: Script timed out!")
        failures += 1

    except Exception as e:
        print(f"ERROR: Failed to execute {file_path}: {e}")
        failures += 1


def get_folders(folder, exclusion_list: list[str] | None = None):
    """
    Locates all sub folders to process in folders. An exclusion list of folder names can
    be provided for folders to skip.
    """
    print(f"Looking for folders in: {folder}")

    # Get all folders, sorted for consistent execution order
    folders = []
    for item in folder.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if exclusion_list and item.name in exclusion_list:
                continue

            folders.append(item)

    # Sort folders by name to ensure consistent order
    folders.sort(key=lambda x: x.name)
    return folders


def get_files(folder, exclusion_list: list[str] | None = None):
    """
    Locates all files in a folder to process. An exclusion list of file names can
    be provided for files to skip.
    """
    python_files = []
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix == '.py':
            if exclusion_list and file_path.name in exclusion_list:
                continue

            python_files.append(file_path)

    # Sort Python files by name for consistent execution order
    python_files.sort(key=lambda x: x.name)

    return python_files


def main():
    files_processed: int = 0

    folders = get_folders(root_folder, folder_exclusion_list)

    if not folders:
        print("No folders found!")
        return

    print(f"Found {len(folders)} folders:")
    for folder in folders:
        print(f"  {folder.name}")

    for folder in folders:
        print(f"\n{'#' * 40}")
        print(f"Processing directory: {folder.name}")
        print(f"{'#' * 40}")

        files = get_files(folder, file_exclusion_list)
        files_processed += len(files)

        if not files:
            print(f"No files to process found in {folder.name}")
            continue

        print(f"Found {len(files)} files to process:")
        for file in files:
            print(f"  {file.name}")

        for file in files:
            execute_python_file(file)

    print(f"\n{'#' * 60}")
    print(f"Processed {len(folders)} folders, {files_processed} files, {failures} failures.")
    if failures > 0:
        print(f"FAILURE: There were {failures} failures!")
    else:
        print("SUCCESS: There were no failures.")
    print(f"{'#' * 60}")


def test_examples():
    """
    Run all the examples in the test framework.
    """
    main()
    assert failures == 0


if __name__ == "__main__":
    main()
