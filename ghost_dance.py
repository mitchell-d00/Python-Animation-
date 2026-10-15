#!/usr/bin/env python3
"""Compatibility entry point: python ghost_dance.py [output.gif] [--preview]."""
from ghost_party.cli import main
if __name__=='__main__':
    raise SystemExit(main())
