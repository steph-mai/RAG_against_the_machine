import sys
import fire
from src.core.logger import logger
from src.core.cli import RAGCli


def main() -> None:
    try:
        fire.Fire(RAGCli)
    except KeyboardInterrupt:
        logger.warning("Interruption of the process (Ctrl C).")
        sys.exit(0)


if __name__ == "__main__":
    main()
