"""The module never reads platform tables: platform facts come from the SDK."""

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
PLATFORM_TABLES = re.compile(
    r"\b(FROM|JOIN|INTO|UPDATE)\s+(public\.)?(tenants|tenant_installed_modules)\b", re.IGNORECASE
)


def test_code_does_not_name_platform_tables():
    offenders = [
        f"{path.relative_to(APP.parent)}:{n}"
        for path in APP.rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if PLATFORM_TABLES.search(line)
    ]
    assert not offenders, f"platform tables named in: {offenders}"
