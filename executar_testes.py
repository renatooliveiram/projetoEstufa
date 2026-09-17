"""Abra este arquivo e clique em Executar Arquivo Python no VS Code."""
import sys
import unittest
from pathlib import Path


if __name__ == '__main__':
    raiz = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(raiz / 'tests'), pattern='test_*.py', top_level_dir=str(raiz)
    )
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if resultado.wasSuccessful() else 1)
