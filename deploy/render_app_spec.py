"""Create a private App Platform spec with runtime secrets; does not deploy."""

import argparse
from getpass import getpass
import os
from pathlib import Path

from dotenv import dotenv_values
import yaml


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "var/deploy/app.yaml")
    parser.add_argument("--without-worker", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists. Choose a new --output path or edit the existing private spec.")
    spec = yaml.safe_load((ROOT / "deploy/digitalocean-app.yaml").read_text())
    local = dotenv_values(ROOT / ".env")
    aliases = {"ESPN_S2": "espn", "ESPN_SWID": "password"}
    secrets = {}
    for key in ["ESPN_S2", "ESPN_SWID", "ADMIN_TOKEN"]:
        value = os.environ.get(key) or local.get(key) or local.get(aliases.get(key, ""))
        if not value:
            value = getpass(f"{key}: ")
        if not value or (key == "ADMIN_TOKEN" and len(value.strip()) < 32):
            parser.error(f"{key} must be set; ADMIN_TOKEN must contain at least 32 characters")
        secrets[key] = value
    for entry in spec["envs"] + spec["services"][0]["envs"]:
        if entry["key"] in secrets:
            entry["value"] = secrets[entry["key"]]
    if args.without_worker:
        spec.pop("workers", None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        yaml.safe_dump(spec, output, sort_keys=False)
    print(f"Private deployment spec written to {args.output}. No cloud resources created.")


if __name__ == "__main__":
    main()
