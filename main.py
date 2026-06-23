"""SnapFlow entry point."""

import logging

from snapflow.ui.app import SnapFlowApp


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    SnapFlowApp().run()


if __name__ == "__main__":
    main()
