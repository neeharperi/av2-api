"""PyTorch data-loader for 3D object detection task."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from torch.utils.data import Dataset

import av2._r as rust
from av2.utils.typing import PathType

from ..structures.sweep import Sweep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DetectionDataLoader(Dataset[Sweep]):  # type: ignore
    """PyTorch data-loader for the sensor dataset.

    The sensor dataset should exist somewhere such as `~/data/datasets/{dataset_name}/{dataset_type}/{split_name}`,
    where
        dataset_name = "av2",
        dataset_type = "sensor,
        split_name = "train".

    This data-loader backend is implemented in Rust for speed. Each iteration will yield a new sweep.

    Args:
        root_dir: Path to the dataset directory.
        dataset_name: Dataset name (e.g., "av2").
        split_name: Name of the dataset split (e.g., "train").
        num_accumulated_sweeps: Number of temporally accumulated sweeps (accounting for ego-vehicle motion).
        memory_mapped: Boolean flag indicating whether to memory map the dataframes.
    """

    root_dir: PathType
    dataset_name: str
    split_name: str
    num_accumulated_sweeps: int = 1
    memory_mapped: bool = False

    _backend: rust.DataLoader = field(init=False)
    _current_idx: int = 0

    def __post_init__(self) -> None:
        """Initialize Rust backend."""
        self._backend = rust.DataLoader(
            str(self.root_dir),
            self.dataset_name,
            "sensor",
            self.split_name,
            self.num_accumulated_sweeps,
            self.memory_mapped,
        )

    def __getitem__(self, index: int) -> Sweep:
        """Get a sweep from the sensor dataset."""
        sweep = self._backend.get(index)
        return Sweep.from_rust(sweep)

    def __len__(self) -> int:
        """Length of the sensor dataset (number of sweeps)."""
        return self._backend.__len__()

    def __iter__(self) -> DetectionDataLoader:
        """Iterate method for the data-loader."""
        return self

    def __next__(self) -> Sweep:
        """Return the next sweep."""
        if self._current_idx >= self.__len__():
            raise StopIteration
        datum = self.__getitem__(self._current_idx)
        self._current_idx += 1
        return datum
