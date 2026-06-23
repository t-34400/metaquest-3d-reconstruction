#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-${PROJECT_DIR:-}}"
OUTPUT_ROOT="${2:-${OUTPUT_ROOT:-}}"
MODEL_PATH="${3:-${FOUNDATION_STEREO_MODEL_PATH:-}}"
CONFIG_PATH="${4:-${CONFIG_PATH:-config/pipeline_config_stereo.yml}}"

if [[ -z "${PROJECT_DIR}" || -z "${OUTPUT_ROOT}" || -z "${MODEL_PATH}" ]]; then
  echo "Usage: $0 <project_dir> <output_root> <foundation_stereo_onnx> [config_path]" >&2
  echo "Example: $0 data/projects/test output/test .local/models/foundation_stereo.onnx config/pipeline_config_stereo.yml" >&2
  exit 2
fi

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "Project directory does not exist: ${PROJECT_DIR}" >&2
  exit 2
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "FoundationStereo ONNX model does not exist: ${MODEL_PATH}" >&2
  exit 2
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "Pipeline config does not exist: ${CONFIG_PATH}" >&2
  exit 2
fi

mkdir -p "${OUTPUT_ROOT}"
COLMAP_OUTPUT_DIR="${OUTPUT_ROOT}/colmap_project"

echo "Project directory: ${PROJECT_DIR}"
echo "Output root: ${OUTPUT_ROOT}"
echo "FoundationStereo model: ${MODEL_PATH}"
echo "Pipeline config: ${CONFIG_PATH}"

mq3drecon foundation-stereo-depth \
  --project-dir "${PROJECT_DIR}" \
  --config "${CONFIG_PATH}" \
  --model-path "${MODEL_PATH}"

if [[ "${RUN_RECONSTRUCT:-1}" == "1" ]]; then
  mq3drecon reconstruct \
    --project-dir "${PROJECT_DIR}" \
    --config "${CONFIG_PATH}"
else
  echo "Skipping reconstruct: set RUN_RECONSTRUCT=1 to run reconstruction."
fi

if [[ "${RUN_EXPORT_COLMAP:-1}" == "1" ]]; then
  mq3drecon export-colmap \
    --project-dir "${PROJECT_DIR}" \
    --output-dir "${COLMAP_OUTPUT_DIR}" \
    --use-optimized-color-dataset \
    --interval "${COLMAP_INTERVAL:-1}"
else
  echo "Skipping export-colmap: set RUN_EXPORT_COLMAP=1 to export a COLMAP project."
fi

if [[ "${RUN_VISUALIZE:-0}" == "1" ]]; then
  mq3drecon visualize-cameras \
    --project-dir "${PROJECT_DIR}"
else
  echo "Skipping visualize-cameras: set RUN_VISUALIZE=1 to open the viewer."
fi

echo "Done. Output root: ${OUTPUT_ROOT}"
