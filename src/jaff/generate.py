"""
JAFF Code Generator CLI Interface.

This module provides the command-line interface for the JAFF (Just Another File Format)
code generator. It processes template files containing JAFF directives and generates
code for chemical reaction networks in various programming languages (C, C++, Fortran).

Usage:
    python -m jaff.generate --network <network_file> [--outdir <dir>] [--indir <dir>] [--files <file1> <file2> ...]

Example:
    python -m jaff.generate --network networks/react_COthin --indir templates/ --outdir output/
"""

import argparse
import warnings
from pathlib import Path

from jaff import Network
from jaff.file_parser import Fileparser


def main() -> None:
    """
    Main entry point for the JAFF code generator CLI.

    Parses command-line arguments, validates input files and directories, and processes
    template files to generate code based on the specified chemical reaction network.

    Command-line Arguments:
        --network: Path to the chemical reaction network file (required)
        --outdir: Output directory for generated files (optional, defaults to current directory)
        --indir: Input directory containing template files to process (optional)
        --files: Individual template files to process (optional)

    Raises:
        RuntimeError: If no network file is supplied or no valid input files are found
        FileNotFoundError: If network file or input files don't exist or are invalid
        NotADirectoryError: If the output path is not a directory
    """
    # Set up argument parser
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="JAFF code generator CLI interface"
    )
    parser.add_argument("--outdir", help="Output directory")
    parser.add_argument("--indir", help="Input directory")
    parser.add_argument("--files", nargs="+", help="Input files")
    parser.add_argument("--network", help="Network file")
    args: argparse.Namespace = parser.parse_args()

    # Extract command-line arguments
    output_dir: str | None = args.outdir
    input_dir: str | None = args.indir
    input_files: list[str] | None = args.files
    network_file: str | None = args.network

    # List to collect all files to process
    files: list[Path] = []

    # Validate network file is provided
    if network_file is None:
        raise RuntimeError("No network file supplied. Please enter a network file")

    # Resolve and validate network file path
    netfile: Path = Path(network_file).resolve()
    if not netfile.exists():
        raise FileNotFoundError(f"Unable to find network file: {netfile}")

    if not netfile.is_file():
        raise FileNotFoundError(f"{netfile} is not a valid file")

    # Handle output directory
    if output_dir is None:
        warnings.warn(
            "\n\nNo output directory has been supplied.\n"
            f"Files will be generated at {Path.cwd()}"
        )

    outdir: Path = Path(output_dir).resolve() if output_dir is not None else Path.cwd()
    if not outdir.exists():
        # Create output directory if it doesn't exist
        Path.mkdir(outdir)

    if not outdir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {outdir}")

    # Collect files from input directory if specified
    if input_dir is not None:
        indir: Path = Path(input_dir).resolve()
        files.extend([f for f in indir.iterdir() if f.is_file()])

    # Collect individual files if specified
    if input_files is not None:
        for file in input_files:
            infile: Path = Path(file).resolve()

            if not infile.exists():
                raise FileNotFoundError(f"Invalid file path {file}")

            if not infile.is_file():
                raise FileNotFoundError(f"{file} is not a file")

            files.append(infile)

    # Ensure at least one input file was provided
    if not files:
        raise RuntimeError("No valid input files have been supplied")

    # Process each template file
    for file in files:
        # Create a new network instance for each file
        net: Network = Network(str(netfile))

        # Initialize file parser for this template
        fparser: Fileparser = Fileparser(net, file)

        # Parse and generate code
        lines: str = fparser.parse_file()

        # Write generated code to output file
        outfile: Path = outdir / file.name
        with open(outfile, "w") as f:
            f.write(lines)


if __name__ == "__main__":
    main()
