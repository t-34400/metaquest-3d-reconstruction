# Models

## Supported Stereo Models

MQ3DRecon supports ONNX models derived from the following upstream projects.

### FoundationStereo

- Original FoundationStereo model from NVIDIA
- Higher computational cost
- Commercially usable checkpoints are available from the upstream project
- Suitable when reconstruction quality is the primary goal

### Fast-FoundationStereo

- Lightweight FoundationStereo variant
- Faster inference and lower resource requirements
- Convenient for development, testing, and rapid iteration

## Model Comparison

| Model | Relative Size | Notes |
|---------|---------|---------|
| FoundationStereo | Larger | Commercial checkpoints available |
| Fast-FoundationStereo | Smaller | Faster inference |

## ONNX Models

MQ3DRecon does not require a specific checkpoint.

Any FoundationStereo or Fast-FoundationStereo checkpoint may be used after exporting the model to ONNX.

## Configuration Compatibility

The pipeline configuration must be compatible with the exported ONNX model.

In particular, the configured inference resolution should match the resolution used when the ONNX model was exported.

## Upstream Projects

- FoundationStereo: https://github.com/NVlabs/FoundationStereo
- Fast-FoundationStereo: https://github.com/NVlabs/Fast-FoundationStereo
