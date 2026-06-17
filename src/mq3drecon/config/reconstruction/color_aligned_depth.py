from dataclasses import dataclass


@dataclass
class ColorAlignedDepthRenderingConfig:
    weight_threshold: float = 3.0
    estimated_vertex_number: int = -1
    only_use_optimized_dataset: bool = True
