"""Entry point for PGP Sentence Lab.

Usage:
    python sentence_generation.py            # interactive CLI
    python sentence_generation.py --web      # web server (default: 127.0.0.1:5000)
    python sentence_generation.py --version
"""
from __future__ import annotations

import argparse
import logging

VERSION = "2503.26-alpha"


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    _configure_logging()

    cli = argparse.ArgumentParser(
        description="PGP Sentence Lab — pregroup grammar parser and web app."
    )
    cli.add_argument("--web", action="store_true", help="Run the web server.")
    cli.add_argument("--host", default="127.0.0.1", help="Web host (default: 127.0.0.1).")
    cli.add_argument("--port", type=int, default=5000, help="Web port (default: 5000).")
    cli.add_argument("--version", action="version", version=f"sentence-lab {VERSION}")
    args = cli.parse_args()

    if args.web:
        from pgp.web import create_app
        app = create_app()
        app.run(host=args.host, port=args.port, debug=False)
    else:
        from pgp.cli import run_cli
        run_cli()


if __name__ == "__main__":
    main()
