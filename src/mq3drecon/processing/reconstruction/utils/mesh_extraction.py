from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

_CUDA_ASSISTANCE_MESH_ALLOCATION_ERROR = "Unable to allocate assistance mesh structure for Marching Cubes"


def extract_triangle_mesh_with_cpu_fallback(vbg: Any, **kwargs: Any) -> Any:
    try:
        return vbg.extract_triangle_mesh(**kwargs)
    except RuntimeError as exc:
        if _CUDA_ASSISTANCE_MESH_ALLOCATION_ERROR not in str(exc):
            raise
        LOGGER.warning("GPU mesh extraction failed; retrying mesh extraction on CPU")
        return vbg.cpu().extract_triangle_mesh(**kwargs)
