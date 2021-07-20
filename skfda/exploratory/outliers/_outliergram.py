from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, OutlierMixin

from ...representation import FDataGrid
from ..depth._depth import ModifiedBandDepth
from ..stats import modified_epigraph_index


class OutliergramOutlierDetector(
    BaseEstimator,  # type: ignore
    OutlierMixin,  # type: ignore
):
    r"""Outlier detector using the relation between MEI and MBD.

    Detects as outliers functions that have one or more points outside
    ``factor`` times the interquartile range plus or minus the central
    envelope, given a functional depth measure. This corresponds to the
    points selected as outliers by the functional boxplot.

    Parameters:
        depth_method (Callable): The functional depth measure used.
        factor (float): The number of times the IQR is multiplied.

    Example:
        Function :math:`f : \mathbb{R}\longmapsto\mathbb{R}`.

        >>> import skfda
        >>> data_matrix = [[1, 1, 2, 3, 2.5, 2],
        ...                [0.5, 0.5, 1, 2, 1.5, 1],
        ...                [-1, -1, -0.5, 1, 1, 0.5],
        ...                [-0.5, -0.5, -0.5, -1, -1, -1]]
        >>> grid_points = [0, 2, 4, 6, 8, 10]
        >>> fd = skfda.FDataGrid(data_matrix, grid_points)
        >>> out_detector = IQROutlierDetector()
        >>> out_detector.fit_predict(fd)
        array([-1, 1, 1, -1])

    """

    def __init__(self, *, factor: float = 1.5) -> None:
        self.factor = factor

    def _compute_parabola(self, X: FDataGrid) -> np.ndarray:
        """Compute the parabola in which pairs (mei, mbd) should lie."""
        a_0 = -2 / (X.n_samples * (X.n_samples - 1))
        a_1 = (2 * (X.n_samples + 1)) / (X.n_samples - 1)
        a_2 = a_0

        return (
            a_0 + a_1 * self.mei_
            + X.n_samples**2 * a_2 * self.mei_**2
        )

    def _compute_maximum_inlier_distance(self, distances: np.ndarray) -> float:
        """Compute the distance above which data are considered outliers."""
        first_quartile = np.percentile(distances, 25)  # noqa: WPS432
        third_quartile = np.percentile(distances, 75)  # noqa: WPS432
        iqr = third_quartile - first_quartile
        return third_quartile + self.factor * iqr

    def fit(self, X: FDataGrid, y: None = None) -> OutliergramOutlierDetector:
        self.mbd_ = ModifiedBandDepth()(X)
        self.mei_ = modified_epigraph_index(X)
        self.parabola_ = self._compute_parabola(X)
        self.distances_ = self.parabola_ - self.mbd_
        self.max_inlier_distance_ = self._compute_maximum_inlier_distance(
            self.distances_,
        )

        return self

    def fit_predict(self, X: FDataGrid, y: None = None) -> np.ndarray:
        self.fit(X, y)

        outliers = self.distances_ > self.max_inlier_distance_

        # Predict as scikit-learn outlier detectors
        predicted = ~outliers + outliers * -1

        return predicted