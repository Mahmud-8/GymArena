"""Generate durable local credentials without putting passwords in source or logs."""
import os
import re
import secrets
import tempfile
from pathlib import Path

CREDENTIALS = ("admin", "tracking", "membership", "session", "notification", "member", "recognition", "challenge", "scoring")


def initialize(root=Path("/credentials")):
    targets = [(service, "password") for service in CREDENTIALS]
    targets.extend([("member", "session_key"), ("member", "staff_key")])
    for service, filename in targets:
        directory = root / service
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        if destination.exists():
            if not re.fullmatch(r"[0-9a-f]{64}\n?", destination.read_text(encoding="ascii")):
                raise ValueError(f"Invalid credential file for {service}; existing credentials were preserved")
            continue
        # The next containers start only after this process completes successfully.
        # Atomic replacement avoids a truncated final file after an interrupted write.
        descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=".credential-")
        try:
            with os.fdopen(descriptor, "w", encoding="ascii") as stream:
                stream.write(secrets.token_hex(32) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o444)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print("Local credentials initialized or preserved; no credential values were logged.")


if __name__ == "__main__":
    initialize()
