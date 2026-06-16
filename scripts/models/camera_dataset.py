from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TypeVar, Type, Union, overload
import numpy as np

from models.transforms import Transforms, CoordinateSystem


T = TypeVar("T", bound="CameraDataset")


@dataclass
class CameraDataset:
    directory_relative_path: str
    image_file_names: np.ndarray

    timestamps: np.ndarray

    fx: np.ndarray
    fy: np.ndarray
    cx: np.ndarray
    cy: np.ndarray

    transforms: Transforms

    widths: np.ndarray
    heights: np.ndarray

    REQUIRED_KEYS = frozenset({
        "directory_relative_path",
        "image_file_names",
        "timestamps",
        "fx",
        "fy",
        "cx",
        "cy",
        "coordinate_system",
        "positions",
        "rotations",
        "widths",
        "heights",
    })

    def __post_init__(self):
        self._validate_lengths()

    def _validate_lengths(self) -> None:
        length = self.timestamps.shape[0]
        invalid_lengths = {
            key: value.shape[0]
            for key, value in self.to_dict().items()
            if isinstance(value, np.ndarray) and value.ndim > 0 and value.shape[0] != length
        }

        if invalid_lengths:
            raise ValueError(
                "CameraDataset arrays must have matching first dimensions: "
                f"expected {length}, got {invalid_lengths}"
            )

    @classmethod
    def _validate_required_keys(cls, data: dict) -> None:
        missing_keys = sorted(cls.REQUIRED_KEYS.difference(data.keys()))
        if missing_keys:
            raise ValueError(f"Missing required dataset keys: {missing_keys}")

    @overload
    def __getitem__(self: T, idx: int) -> dict[str, np.ndarray]: ... # type: ignore

    @overload
    def __getitem__(self: T, idx: Union[slice, list, np.ndarray]) -> T: ...

    def __getitem__(self: T, idx): # type: ignore
        data = self.to_dict()

        arrays = {k: v for k, v in data.items() if isinstance(v, np.ndarray) and v.ndim > 0}
        others = {k: v for k, v in data.items() if k not in arrays}

        if isinstance(idx, int):
            return {k: v[idx] for k, v in arrays.items()} | others

        elif isinstance(idx, slice) or isinstance(idx, (list, np.ndarray)):
            subset = {
                k: v[idx] if isinstance(v, np.ndarray) and v.ndim > 0 else v
                for k, v in data.items()
            }
            return self.__class__.from_dict(subset)

        else:
            raise TypeError(f"Unsupported index type: {type(idx)}")

    def __iter__(self) -> Iterator[dict[str, np.ndarray]]:
        for i in range(len(self)):
            yield self[i]

    def __len__(self) -> int:
        data = self.to_dict()

        for v in data.values():
            if isinstance(v, np.ndarray) and v.ndim > 0:
                return len(v)

        raise RuntimeError("No array data in dataset")

    def find_nearest_index(self, timestamp: int) -> int:
        i = np.searchsorted(self.timestamps, timestamp, side='left')
        if i == len(self.timestamps):
            return int(i - 1)
        elif i == 0:
            return 0
        elif abs(self.timestamps[i] - timestamp) < abs(self.timestamps[i - 1] - timestamp):
            return int(i)
        else:
            return int(i - 1)

    def get_intrinsic_matrices(self) -> np.ndarray:
        N = len(self.fx)
        intrinsic_matrices = np.zeros((N, 3, 3), dtype=np.float32)

        intrinsic_matrices[:, 0, 0] = self.fx
        intrinsic_matrices[:, 1, 1] = self.fy
        intrinsic_matrices[:, 2, 2] = 1.0

        intrinsic_matrices[:, 0, 2] = self.cx
        intrinsic_matrices[:, 1, 2] = self.cy

        return intrinsic_matrices

    def to_dict(self) -> dict:
        d = {
            "directory_relative_path": self.directory_relative_path,
            "image_file_names": self.image_file_names,
            "timestamps": self.timestamps,
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "coordinate_system": self.transforms.coordinate_system.name,
            "positions": self.transforms.positions,
            "rotations": self.transforms.rotations,
            "widths": self.widths,
            "heights": self.heights,
        }

        return d

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

        np.savez(
            path,
            **self.to_dict()
        )

    def split(self: T, fragment_size: int) -> list[T]:
        return [
            self[i:i + fragment_size]
            for i in range(0, len(self), fragment_size)
        ]

    @staticmethod
    def parse_transforms(data):
        try:
            coordinate_system = CoordinateSystem[str(data.pop('coordinate_system'))]
        except KeyError as exc:
            raise ValueError("Missing required transform key: coordinate_system") from exc

        try:
            positions = data.pop('positions')
            rotations = data.pop('rotations')
        except KeyError as exc:
            raise ValueError(f"Missing required transform key: {exc.args[0]}") from exc

        data['transforms'] = Transforms(
            coordinate_system=coordinate_system,
            positions=positions,
            rotations=rotations
        )

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if 'coordinate_system' in data:
            cls._validate_required_keys(data)
            cls.parse_transforms(data)

        return cls(**data)

    @classmethod
    def load(cls, path: Path):
        data = dict(np.load(path, allow_pickle=False))
        cls._validate_required_keys(data)

        return cls.from_dict(data=data)

    @classmethod
    def merge(cls: Type[T], datasets: list[T]) -> T:
        if not datasets:
            raise ValueError("Cannot merge an empty dataset list")

        dicts = [ds.to_dict() for ds in datasets]

        merged = {}
        keys = dicts[0].keys()

        for key in keys:
            values = [d[key] for d in dicts]
            types = {type(v) for v in values}

            if len(types) != 1:
                raise ValueError(f"Inconsistent types for key '{key}': {types}")

            v0 = values[0]
            if isinstance(v0, np.ndarray) and v0.ndim >= 1:
                shapes = {v.shape[1:] for v in values}
                if len(shapes) != 1:
                    raise ValueError(
                        f"Inconsistent shapes for key '{key}' (excluding first axis): {shapes}"
                    )

                merged[key] = np.concatenate(values, axis=0)

            else:
                all_equal = all(v == v0 for v in values)
                if not all_equal:
                    raise ValueError(f"Inconsistent scalar values for key '{key}': {set(values)}")

                merged[key] = v0

        return cls.from_dict(merged)


@dataclass
class DepthDataset(CameraDataset):
    nears: np.ndarray
    fars: np.ndarray

    REQUIRED_KEYS = CameraDataset.REQUIRED_KEYS | frozenset({"nears", "fars"})

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['nears'] = self.nears
        d['fars'] = self.fars

        return d

    @classmethod
    def load(cls, path: Path):
        data = dict(np.load(path, allow_pickle=False))
        cls._validate_required_keys(data)

        return cls.from_dict(data=data)
