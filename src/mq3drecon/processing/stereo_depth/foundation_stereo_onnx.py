from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

from mq3drecon.config.foundation_stereo_config import FoundationStereoConfig
from mq3drecon.processing.stereo_depth.preprocessing import (
    image_to_model_tensor,
    resize_disparity_to_original,
    resize_pad_image,
)


class FoundationStereoOnnxModel:
    def __init__(self, model_path: Path, config: FoundationStereoConfig):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ImportError(
                "onnxruntime is required for FoundationStereo inference. "
                "Install mq3drecon[stereo] or install onnxruntime separately."
            ) from exc

        self.config = config
        self.session = ort.InferenceSession(str(model_path), providers=list(config.execution_providers))
        self.input_names = [input_meta.name for input_meta in self.session.get_inputs()]
        self.output_name = self.session.get_outputs()[0].name
        self.input_height, self.input_width = _resolve_input_size(self.session.get_inputs(), config)

    def predict_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        left_padded, pad_info = resize_pad_image(
            left_image,
            self.input_height,
            self.input_width,
            preserve_aspect_ratio=self.config.preserve_aspect_ratio,
            padding_value=self.config.padding_value,
        )
        right_padded, _ = resize_pad_image(
            right_image,
            self.input_height,
            self.input_width,
            preserve_aspect_ratio=self.config.preserve_aspect_ratio,
            padding_value=self.config.padding_value,
        )

        inputs = {
            self.input_names[0]: image_to_model_tensor(left_padded, self.config.normalize),
            self.input_names[1]: image_to_model_tensor(right_padded, self.config.normalize),
        }
        disparity = self.session.run([self.output_name], inputs)[0]
        return resize_disparity_to_original(np.asarray(disparity), pad_info)


def _resolve_input_size(input_meta: Sequence[object], config: FoundationStereoConfig) -> tuple[int, int]:
    shape = getattr(input_meta[0], "shape")
    height = shape[2]
    width = shape[3]

    if not isinstance(height, int):
        height = config.input_height
    if not isinstance(width, int):
        width = config.input_width

    if height is None or width is None:
        raise ValueError("Dynamic ONNX input shape requires input_height and input_width in FoundationStereoConfig")
    return int(height), int(width)
