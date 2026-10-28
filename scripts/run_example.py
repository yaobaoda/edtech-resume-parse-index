import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.resume_service import main


if len(sys.argv) < 3:
    raise SystemExit("usage: python3 scripts/run_example.py PDF EMBEDDING...")

main(sys.argv[1], [float(value) for value in sys.argv[2:]])

