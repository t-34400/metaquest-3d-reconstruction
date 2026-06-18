from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ResizePadInfo:
    original_height: int
    original_width: int
    resized_height: int
    resized_width: int
    target_height: int
    target_width: int
    pad_top: int
    pad_left: int
    scale_x: float
    scale_y: float


def resize_pad_image(
    image: np.ndarray,
    target_height: int,
    target_width: int,
    *,
    preserve_aspect_ratio: bool = True,
    padding_value: float = 0.0,
) -> tuple[np.ndarray, ResizePadInfo]:
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError(f"Expected HWC image with at least 3 channels, got shape {image.shape}")

    rgb = image[:, :, :3]
    original_height, original_width = rgb.shape[:2]

    if preserve_aspect_ratio:
        scale = min(target_width / original_width, target_height / original_height)
        resized_width = max(1, int(round(original_width * scale)))
        resized_height = max(1, int(round(original_height * scale)))
    else:
        resized_width = target_width
        resized_height = target_height

    resized = cv2.resize(rgb, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
    padded = np.full((target_height, target_width, 3), padding_value, dtype=resized.dtype)
    pad_top = (target_height - resized_height) // 2
    pad_left = (target_width - resized_width) // 2
    padded[pad_top:pad_top + resized_height, pad_left:pad_left + resized_width] = resized

    info = ResizePadInfo(
        original_height=original_height,
        original_width=original_width,
        resized_height=resized_height,
        resized_width=resized_width,
        target_height=target_height,
        target_width=target_width,
        pad_top=pad_top,
        pad_left=pad_left,
        scale_x=resized_width / original_width,
        scale_y=resized_height / original_height,
    )
    return padded, info


def resize_disparity_to_original(disparity: np.ndarray, info: ResizePadInfo) -> np.ndarray:
    if disparity.ndim == 4:
        disparity = disparity[0, 0]
    elif disparity.ndim == 3:
        disparity = disparity[0]
    if disparity.shape != (info.target_height, info.target_width):
        raise ValueError(
            f"Expected disparity shape {(info.target_height, info.target_width)}, got {disparity.shape}"
        )

    y0 = info.pad_top
    x0 = info.pad_left
    unpadded = disparity[y0:y0 + info.resized_height, x0:x0 + info.resized_width]
    restored = cv2.resize(
        unpadded,
        (info.original_width, info.original_height),
        interpolation=cv2.INTER_LINEAR,
    )
    return (restored / info.scale_x).astype(np.float32)


def image_to_model_tensor(image: np.ndarray, normalize: str) -> np.ndarray:
    tensor = image.astype(np.float32)
    if normalize == "0_1":
        tensor /= 255.0
    elif normalize == "imagenet":
        tensor /= 255.0
        mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
        tensor = (tensor - mean) / std
    elif normalize == "none":
        pass
    else:
        raise ValueError(f"Unsupported normalization mode: {normalize}")

    return np.transpose(tensor, (2, 0, 1))[None, :, :, :].astype(np.float32)
