#!/usr/bin/env bash
set -euo pipefail

certificate_identity="${COSIGN_CERTIFICATE_IDENTITY:-https://github.com/YangchenxiWu/SkiLoadLab/.github/workflows/ci.yml@refs/heads/main}"
certificate_oidc_issuer="https://token.actions.githubusercontent.com"
provenance="${PROVENANCE_FILE:-provenance.json}"

if [ "$#" -eq 0 ]; then
  echo "usage: $0 dist/*.whl" >&2
  exit 2
fi

if [ ! -s "$provenance" ]; then
  echo "missing provenance file: $provenance" >&2
  exit 1
fi

python - "$provenance" "$@" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

provenance_path = Path(sys.argv[1])
artifacts = [Path(arg) for arg in sys.argv[2:]]
data = json.loads(provenance_path.read_text())

required = [
    "commit_sha",
    "timestamp",
    "artifact_sha256",
    "requirements_hash",
    "requirements_hash_summary",
    "ci_environment",
    "artifacts",
]
missing = [key for key in required if key not in data]
if missing:
    raise SystemExit(f"provenance missing required keys: {', '.join(missing)}")

if not data["requirements_hash_summary"]:
    raise SystemExit("provenance has no requirements hash summary")

requirements_digest = hashlib.sha256(
    json.dumps(
        data["requirements_hash_summary"],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()
if data["requirements_hash"] != requirements_digest:
    raise SystemExit("requirements_hash mismatch")

for artifact in artifacts:
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    direct_recorded = data["artifact_sha256"].get(str(artifact))
    if direct_recorded != digest:
        raise SystemExit(f"artifact_sha256 mismatch for {artifact}")
    recorded = data["artifacts"].get(str(artifact), {}).get("sha256")
    if recorded != digest:
        raise SystemExit(f"artifact hash mismatch for {artifact}")
PY

for artifact in "$@"; do
  cosign verify-blob \
    --bundle "${artifact}.sigstore.json" \
    --certificate-identity "$certificate_identity" \
    --certificate-oidc-issuer "$certificate_oidc_issuer" \
    "$artifact"

  cosign verify-blob-attestation \
    --certificate-oidc-issuer "$certificate_oidc_issuer" \
    --certificate-identity "$certificate_identity" \
    --type slsaprovenance \
    --bundle "${artifact}.attestation.json" \
    "$artifact"
done
