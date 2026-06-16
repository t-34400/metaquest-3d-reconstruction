from dataclasses import dataclass

import numpy as np


@dataclass
class ConfidenceMap:
    confidence_map: np.ndarray
    valid_count: np.ndarray

    @property
    def width(self) -> int:
        return self.confidence_map.shape[1]
    
    @property
    def height(self) -> int:
        return self.confidence_map.shape[0]
    
    @property
    def size(self) -> int:
        return self.width * self.height
    
    @property
    def shape(self) -> tuple[int, int]:
        return self.confidence_map.shape


    def __post_init__(self):
        if self.confidence_map.shape != self.valid_count.shape:
            raise ValueError("Confidence map and valid mask must have the same shape.")
        if self.confidence_map.ndim != 2:
            raise ValueError("Confidence map must be a 2D array.")
