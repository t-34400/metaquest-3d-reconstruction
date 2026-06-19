#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-${PROJECT_DIR:-}}"
OUTPUT_ROOT="${2:-${OUTPUT_ROOT:-}}"

if [[ -z "${PROJECT_DIR}" || -z "${OUTPUT_ROOT}" ]]; then
  echo "Usage: $0 <project_dir> <output_root>" >&2
  echo "Example: $0 data/projects/test_output output/test_output" >&2
  exit 2
fi

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "Project directory does not exist: ${PROJECT_DIR}" >&2
  exit 2
fi

mkdir -p "${OUTPUT_ROOT}"
COLMAP_OUTPUT_DIR="${OUTPUT_ROOT}/colmap_project"

CAPTURE_BACKEND="NativeCamera2"
if [[ -f "${PROJECT_DIR}/session_info.json" ]]; then
  CAPTURE_BACKEND=$(python - "${PROJECT_DIR}/session_info.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    session_info = json.load(f)
print(session_info.get("captureBackend", "NativeCamera2"))
PY
)
fi

has_files() {
  local pattern="$1"
  compgen -G "${pattern}" > /dev/null
}

echo "Project directory: ${PROJECT_DIR}"
echo "Output root: ${OUTPUT_ROOT}"
echo "Capture backend: ${CAPTURE_BACKEND}"

if [[ "${CAPTURE_BACKEND}" == "NativeCamera2" ]] && \
   has_files "${PROJECT_DIR}/left_camera_raw/*.yuv" && \
   has_files "${PROJECT_DIR}/right_camera_raw/*.yuv"; then
  mq3drecon yuv-to-rgb \
    --project-dir "${PROJECT_DIR}"
else
  echo "Skipping yuv-to-rgb: not required for this capture or no YUV frames were found."
fi

if has_files "${PROJECT_DIR}/left_depth/*.raw" && has_files "${PROJECT_DIR}/right_depth/*.raw"; then
  mq3drecon depth-to-linear \
    --project-dir "${PROJECT_DIR}"

  if [[ "${RUN_RECONSTRUCT:-0}" == "1" ]]; then
    mq3drecon reconstruct \
      --project-dir "${PROJECT_DIR}"
  else
    echo "Skipping reconstruct: set RUN_RECONSTRUCT=1 to run Open3D reconstruction."
  fi
else
  echo "Skipping depth-to-linear and reconstruct: no raw depth frames were found."
fi

mq3drecon export-colmap \
  --project-dir "${PROJECT_DIR}" \
  --output-dir "${COLMAP_OUTPUT_DIR}" \
  --interval "${COLMAP_INTERVAL:-1}"

if [[ "${RUN_VISUALIZE:-0}" == "1" ]]; then
  mq3drecon visualize-cameras \
    --project-dir "${PROJECT_DIR}"
else
  echo "Skipping visualize-cameras: set RUN_VISUALIZE=1 to open the viewer."
fi

echo "Done. COLMAP output: ${COLMAP_OUTPUT_DIR}"
