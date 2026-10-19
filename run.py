#!/usr/bin/env python3
"""Tek giriş noktası — uygulama src/cli.py'de. Örnek: python3 run.py stem --text "Kitapları okuyordum."  (python3 run.py -h)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from cli import main  # noqa: E402

if __name__ == "__main__":
    main()
