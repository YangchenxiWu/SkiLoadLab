#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# SkiLoadLab: Reproducible Demo Benchmark
# Runs the demo pipeline N times and writes median wall-clock time.
#
# Usage:
#   ./scripts/benchmark_demo.sh [runs_csv_rel] [alpha] [repeats]
# Example:
#   ./scripts/benchmark_demo.sh data/example/runs_final_example.csv 0.5 3
# ==============================================================================

RUNS_CSV_REL="${1:-data/example/runs_final_example.csv}"
ALPHA="${2:-0.5}"
REPEATS="${3:-3}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_CSV_ABS="$REPO_ROOT/$RUNS_CSV_REL"

if [[ ! -f "$RUNS_CSV_ABS" ]]; then
  echo "[ERR] Missing file: $RUNS_CSV_REL (resolved to $RUNS_CSV_ABS)" >&2
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Export environment for Python blocks
export REPO_ROOT
export RUNS_CSV_ABS
export RUNS_CSV_REL
export ALPHA
export REPEATS
export PY_VER="$("$PYTHON_BIN" --version 2>&1 | tr -d '\r')"
export SYS_INFO="$(uname -smp | tr -d '\r')"
export OS_VER="$(sw_vers 2>/dev/null | tr '\n' ';' | sed 's/;*$//' || echo "N/A")"
export GIT_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
export DIRTY_FILES="$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"

echo "[INFO] Starting Benchmark..."
echo "[INFO] repo: $REPO_ROOT (commit $GIT_COMMIT, dirty_files=$DIRTY_FILES)"
echo "[INFO] runs_csv: $RUNS_CSV_REL"
echo "[INFO] alpha: $ALPHA  repeats: $REPEATS"
echo

times=()

for i in $(seq 1 "$REPEATS"); do
  export OUT_CSV="$TMPDIR/demo_out_${i}.csv"
  export OUT_JSON="$TMPDIR/demo_report_${i}.json"
  export FIG_DIR="$TMPDIR/figs_${i}"
  mkdir -p "$FIG_DIR"

  t=$("$PYTHON_BIN" - <<'PY'
import os, sys, time, subprocess

def run_step(cmd):
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.environ["REPO_ROOT"],
    )
    if r.returncode != 0:
        print("SUBPROCESS FAILED:", file=sys.stderr)
        print("CMD:", " ".join(cmd), file=sys.stderr)
        print("STDERR:", r.stderr, file=sys.stderr)
        print("STDOUT:", r.stdout, file=sys.stderr)
        sys.exit(r.returncode)
    return r

t0 = time.perf_counter()

run_step([
    sys.executable, "src/model/combined_load.py",
    "--in", os.environ["RUNS_CSV_ABS"],
    "--out", os.environ["OUT_CSV"],
    "--report", os.environ["OUT_JSON"],
    "--alpha", os.environ["ALPHA"],
])

run_step([
    sys.executable, "scripts/make_figures.py",
    "--runs", os.environ["RUNS_CSV_ABS"],
    "--out", os.environ["FIG_DIR"],
])

t1 = time.perf_counter()
print(f"{t1 - t0:.6f}")
PY
)
  echo "[RUN $i] ${t}s"
  times+=("$t")
done

# Build a Python-list literal like [1.234, 1.111, 1.222]
py_list_str=$(printf ", %s" "${times[@]}")
py_list_str="[${py_list_str:2}]"
export PY_TIMES_LIST="$py_list_str"

echo
echo "========================================"
"$PYTHON_BIN" - <<'PY'
import os, json, statistics, datetime, ast, sys

times_raw = os.environ.get("PY_TIMES_LIST", "[]")
try:
    times = ast.literal_eval(times_raw)
except Exception as e:
    print(f"[ERR] Could not parse times list: {e}", file=sys.stderr)
    sys.exit(1)

if not times:
    print("[ERR] No timing results collected.", file=sys.stderr)
    sys.exit(1)

times_sorted = sorted(float(x) for x in times)
median_val = statistics.median(times_sorted)

ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

result = {
  "timestamp_utc": ts,
  "median_s": float(median_val),
  "times_s": [float(x) for x in times_sorted],
  "python": os.environ["PY_VER"],
  "platform": os.environ["SYS_INFO"],
  "os": os.environ["OS_VER"],
  "git_commit": os.environ["GIT_COMMIT"],
  "dirty_files": int(os.environ["DIRTY_FILES"]),
  "runs_csv": os.environ["RUNS_CSV_REL"],  # <-- record REL path (portable)
  "alpha": float(os.environ["ALPHA"]),
  "repeats": int(os.environ["REPEATS"]),
}

out_dir = os.path.join(os.environ["REPO_ROOT"], "paper", "bench")
os.makedirs(out_dir, exist_ok=True)

json_path = os.path.join(out_dir, "benchmark_demo.json")
md_path = os.path.join(out_dir, "benchmark_demo.md")

with open(json_path, "w") as f:
    json.dump(result, f, indent=2)

with open(md_path, "w") as f:
    f.write("# Benchmark Results (demo mode)\n")
    f.write(f"- Timestamp (UTC): {ts}\n")
    f.write(f"- Median wall time (s): {median_val:.4f}\n")
    f.write(f"- Trials (s): {', '.join([f'{x:.4f}' for x in times_sorted])}\n")
    f.write(f"- Runs table: {os.environ['RUNS_CSV_REL']}\n")
    f.write(f"- Alpha: {os.environ['ALPHA']}\n")
    f.write(f"- Repeats: {os.environ['REPEATS']}\n")
    f.write(f"- Python: {os.environ['PY_VER']}\n")
    f.write(f"- Git commit: {os.environ['GIT_COMMIT']}\n")
    f.write(f"- Dirty files: {os.environ['DIRTY_FILES']}\n")

print("BENCHMARK COMPLETED")
print(f"Median Time : {median_val:.4f}s")
print(f"[OK] wrote: {json_path}")
print(f"[OK] wrote: {md_path}")
PY
echo "========================================"
