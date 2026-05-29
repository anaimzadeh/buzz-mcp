from __future__ import annotations

import os
import sys
from collections.abc import Mapping


LIVE_TEST_ENABLE_ENV = "BUZZ_RUN_LIVE_TESTS"
SANDBOX_ACK_ENV = "BUZZ_TEST_SANDBOX_ACK"
REQUIRED_LIVE_ENV = (
    "BUZZ_USERNAME",
    "BUZZ_PASSWORD",
    "BUZZ_DOMAIN",
    "BUZZ_TEST_ENTITYID",
    "BUZZ_TEST_ITEMID",
    "BUZZ_TEST_ENROLLMENTID",
)
OPTIONAL_LIVE_ENV = (
    "BUZZ_BASE_URL",
    "BUZZ_TEST_ATTACHMENT_FILEPATH",
)


def missing_live_env(environ: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    missing: list[str] = []

    if env.get(LIVE_TEST_ENABLE_ENV) != "1":
        missing.append(f"{LIVE_TEST_ENABLE_ENV}=1")
    missing.extend(key for key in REQUIRED_LIVE_ENV if not env.get(key))
    if env.get(SANDBOX_ACK_ENV) != "1":
        missing.append(f"{SANDBOX_ACK_ENV}=1")
    return missing


def main() -> int:
    missing = missing_live_env()
    if not missing:
        print("Live Buzz sandbox environment is configured.")
        return 0

    print("Missing live Buzz sandbox configuration:", file=sys.stderr)
    for name in missing:
        print(f"- {name}", file=sys.stderr)
    print(
        "Set these as GitHub environment secrets or variables for the "
        "`buzz-sandbox` environment before running the live release gate.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
