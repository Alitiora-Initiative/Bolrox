"""BOLOROX main entry point. Skeleton runner."""
import argparse
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bolorox")

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="BOLOROX — autonomous forex analyst")
    parser.add_argument("command", nargs="?", default="STATUS", help="RUN ALL | RUN SYMBOL | STATUS | ...")
    args = parser.parse_args()

    config = load_config()
    logger.info(f"BOLOROX starting. Command: {args.command}")
    logger.info(f"Default symbols: {config['symbols']['default']}")
    logger.info(f"Timezone: {config['timezone']}")

    if args.command.upper() == "STATUS":
        print("BOLOROX Status")
        print("Sources: see sources.yaml")
        print("No open signals (journal empty on first run)")
        print("Ready for RUN ALL")
    elif args.command.upper().startswith("RUN"):
        print("Full analysis pipeline not yet implemented in this skeleton.")
        print("Next steps: implement Phase 0-11 in main loop using the src/ modules.")
        print("See README.md and the original specification for the complete workflow.")
    else:
        print(f"Command '{args.command}' recognized. Skeleton ready for extension.")

if __name__ == "__main__":
    main()
