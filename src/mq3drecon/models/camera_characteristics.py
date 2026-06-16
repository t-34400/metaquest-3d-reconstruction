from dataclasses import dataclass
import numpy as np


@dataclass
class CameraCharacteristics:
    width: int
    height: int

    fx: float
    fy: float
    cx: float
    cy: float
    
    transl: np.ndarray # head from camera
    rot_quat: np.ndarray # head from camera as quaternion
