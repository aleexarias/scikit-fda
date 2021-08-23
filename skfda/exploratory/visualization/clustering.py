"""Clustering Plots Module."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted
from typing_extensions import Protocol

from ..._utils import _check_compatible_fdata
from ...representation import FData, FDataGrid
from ...representation._typing import NDArrayFloat, NDArrayInt
from ._baseplot import BasePlot
from ._utils import ColorLike, _darken, _set_labels


class ClusteringEstimator(Protocol):

    @property
    def n_clusters(self) -> int:
        pass

    @property
    def cluster_centers_(self) -> FDataGrid:
        pass

    @property
    def labels_(self) -> NDArrayInt:
        pass

    def fit(self, X: FDataGrid) -> ClusteringEstimator:
        pass

    def predict(self, X: FDataGrid) -> NDArrayInt:
        pass


class FuzzyClusteringEstimator(ClusteringEstimator, Protocol):

    def predict_proba(self, X: FDataGrid) -> NDArrayFloat:
        pass


def _plot_clustering_checks(
    estimator: ClusteringEstimator,
    fdata: FData,
    sample_colors: Optional[Sequence[ColorLike]],
    sample_labels: Optional[Sequence[str]],
    cluster_colors: Optional[Sequence[ColorLike]],
    cluster_labels: Optional[Sequence[str]],
    center_colors: Optional[Sequence[ColorLike]],
    center_labels: Optional[Sequence[str]],
) -> None:
    """Check the arguments."""
    if (
        sample_colors is not None
        and len(sample_colors) != fdata.n_samples
    ):
        raise ValueError(
            "sample_colors must contain a color for each sample.",
        )

    if (
        sample_labels is not None
        and len(sample_labels) != fdata.n_samples
    ):
        raise ValueError(
            "sample_labels must contain a label for each sample.",
        )

    if (
        cluster_colors is not None
        and len(cluster_colors) != estimator.n_clusters
    ):
        raise ValueError(
            "cluster_colors must contain a color for each cluster.",
        )

    if (
        cluster_labels is not None
        and len(cluster_labels) != estimator.n_clusters
    ):
        raise ValueError(
            "cluster_labels must contain a label for each cluster.",
        )

    if (
        center_colors is not None
        and len(center_colors) != estimator.n_clusters
    ):
        raise ValueError(
            "center_colors must contain a color for each center.",
        )

    if (
        center_labels is not None
        and len(center_labels) != estimator.n_clusters
    ):
        raise ValueError(
            "centers_labels must contain a label for each center.",
        )


def _get_labels(
    x_label: Optional[str],
    y_label: Optional[str],
    title: Optional[str],
    xlabel_str: str,
) -> Tuple[str, str, str]:
    """
    Get the axes labels.

    Set the arguments *xlabel*, *ylabel*, *title* passed to the plot
    functions :func:`plot_cluster_lines
    <skfda.exploratory.visualization.clustering_plots.plot_cluster_lines>` and
    :func:`plot_cluster_bars
    <skfda.exploratory.visualization.clustering_plots.plot_cluster_bars>`,
    in case they are not set yet.

    Args:
        x_label: Label for the x-axes.
        y_label: Label for the y-axes.
        title: Title for the figure where the clustering results are
            ploted.
        xlabel_str: In case xlabel is None, string to use for the labels
            in the x-axes.

    Returns:
        xlabel: Labels for the x-axes.
        ylabel: Labels for the y-axes.
        title: Title for the figure where the clustering results are
            plotted.
    """
    if x_label is None:
        x_label = xlabel_str

    if y_label is None:
        y_label = "Degree of membership"

    if title is None:
        title = "Degrees of membership of the samples to each cluster"

    return x_label, y_label, title


class ClusterPlot(BasePlot):
    """
    ClusterPlot class.

    Args:
        estimator: estimator used to calculate the
            clusters.
        X: contains the samples which are grouped
            into different clusters.
        fig: figure over which the graphs are plotted in
            case ax is not specified. If None and ax is also None, the figure
            is initialized.
        axes: axis over where the graphs are plotted.
            If None, see param fig.
        n_rows: designates the number of rows of the figure to plot the
            different dimensions of the image. Only specified if fig and
            ax are None.
        n_cols: designates the number of columns of the figure to plot
            the different dimensions of the image. Only specified if fig
            and ax are None.
        sample_labels: contains in order the labels of each
        sample of the fdatagrid.
        cluster_colors: contains in order the colors of each
            cluster the samples of the fdatagrid are classified into.
        cluster_labels: contains in order the names of each
            cluster the samples of the fdatagrid are classified into.
        center_colors: contains in order the colors of each
            centroid of the clusters the samples of the fdatagrid are
            classified into.
        center_labels: contains in order the labels of each
            centroid of the clusters the samples of the fdatagrid are
            classified into.
        center_width: width of the centroid curves.
        colormap: colormap from which the colors of the plot are
            taken. Defaults to `rainbow`.
    """

    def __init__(
        self,
        estimator: ClusteringEstimator,
        fdata: FDataGrid,
        chart: Union[Figure, Axes, None] = None,
        fig: Optional[Figure] = None,
        axes: Union[Axes, Sequence[Axes], None] = None,
        n_rows: Optional[int] = None,
        n_cols: Optional[int] = None,
        sample_labels: Optional[Sequence[str]] = None,
        cluster_colors: Optional[Sequence[ColorLike]] = None,
        cluster_labels: Optional[Sequence[str]] = None,
        center_colors: Optional[Sequence[ColorLike]] = None,
        center_labels: Optional[Sequence[str]] = None,
        center_width: int = 3,
        colormap: matplotlib.colors.Colormap = None,
    ) -> None:

        if colormap is None:
            colormap = plt.cm.get_cmap('rainbow')

        super().__init__(
            chart,
            fig=fig,
            axes=axes,
        )
        self.fdata = fdata
        self.estimator = estimator
        self.sample_labels = sample_labels
        self.cluster_colors = cluster_colors
        self.cluster_labels = cluster_labels
        self.center_colors = center_colors
        self.center_labels = center_labels
        self.center_width = center_width
        self.colormap = colormap
        self._set_figure_and_axes(chart, fig=fig, axes=axes)

    def n_samples(self) -> int:
        return self.fdata.n_samples

    def _plot_clusters(self) -> Figure:
        """Implement the plot of the FDataGrid samples by clusters."""
        _plot_clustering_checks(
            estimator=self.estimator,
            fdata=self.fdata,
            sample_colors=None,
            sample_labels=self.sample_labels,
            cluster_colors=self.cluster_colors,
            cluster_labels=self.cluster_labels,
            center_colors=self.center_colors,
            center_labels=self.center_labels,
        )

        if self.sample_labels is None:
            self.sample_labels = [
                f'$SAMPLE: {i}$' for i in range(self.fdata.n_samples)
            ]

        if self.cluster_colors is None:
            self.cluster_colors = self.colormap(
                np.arange(self.estimator.n_clusters)
                / (self.estimator.n_clusters - 1),
            )

        if self.cluster_labels is None:
            self.cluster_labels = [
                f'$CLUSTER: {i}$' for i in range(self.estimator.n_clusters)
            ]

        if self.center_colors is None:
            self.center_colors = [_darken(c, 0.5) for c in self.cluster_colors]

        if self.center_labels is None:
            self.center_labels = [
                f'$CENTER: {i}$' for i in range(self.estimator.n_clusters)
            ]

        colors_by_cluster = self.cluster_colors[self.labels]

        patches = [
            mpatches.Patch(
                color=self.cluster_colors[i],
                label=self.cluster_labels[i],
            )
            for i in range(self.estimator.n_clusters)
        ]

        artists = [
            self.axes[j].plot(
                self.fdata.grid_points[0],
                self.fdata.data_matrix[i, :, j],
                c=colors_by_cluster[i],
                label=self.sample_labels[i],
            )
            for j in range(self.fdata.dim_codomain)
            for i in range(self.fdata.n_samples)
        ]

        self.artists = np.array(artists)

        for j in range(self.fdata.dim_codomain):

            for i in range(self.estimator.n_clusters):
                self.axes[j].plot(
                    self.fdata.grid_points[0],
                    self.estimator.cluster_centers_.data_matrix[i, :, j],
                    c=self.center_colors[i],
                    label=self.center_labels[i],
                    linewidth=self.center_width,
                )
            self.axes[j].legend(handles=patches)

        _set_labels(self.fdata, self.fig, self.axes)

        return self.fig

    def plot(self) -> Figure:
        """
        Plot of the FDataGrid samples by clusters.

        The clusters are calculated with the estimator passed as a parameter.
        If the estimator is not fitted, the fit method is called.
        Once each sample is assigned a label the plotting can be done.
        Each group is assigned a color described in a legend.

        Returns:
            Plotted figure.

        """
        self.artists = np.array([])

        try:
            check_is_fitted(self.estimator)
            _check_compatible_fdata(
                self.estimator.cluster_centers_,
                self.fdata,
            )
        except NotFittedError:
            self.estimator.fit(self.fdata)

        self.labels = self.estimator.labels_

        return self._plot_clusters()


class ClusterMembershipLinesPlot(BasePlot):
    """
    Class ClusterMembershipLinesPlot.

    Args:
        estimator: estimator used to calculate the
            clusters.
        X: contains the samples which are grouped
            into different clusters.
        fig: figure over which the graph is
            plotted in case ax is not specified. If None and ax is also None,
            the figure is initialized.
        axes: axis over where the graph is  plotted.
            If None, see param fig.
        sample_colors: contains in order the colors
            of each sample of the fdatagrid.
        sample_labels: contains in order the labels
            of each sample  of the fdatagrid.
        cluster_labels: contains in order the names of
            each cluster the samples of the fdatagrid are classified into.
        colormap: colormap from which the colors of the
            plot are taken.
        x_label: Label for the x-axis. Defaults to "Cluster".
        y_label: Label for the y-axis. Defaults to
            "Degree of membership".
        title: Title for the figure where the clustering
            results are ploted.
            Defaults to "Degrees of membership of the samples to each cluster".
    """

    def __init__(
        self,
        estimator: FuzzyClusteringEstimator,
        fdata: FDataGrid,
        chart: Union[Figure, Axes, None] = None,
        fig: Optional[Figure] = None,
        axes: Union[Axes, Sequence[Axes], None] = None,
        sample_colors: Optional[Sequence[ColorLike]] = None,
        sample_labels: Optional[Sequence[str]] = None,
        cluster_labels: Optional[Sequence[str]] = None,
        colormap: matplotlib.colors.Colormap = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:

        if colormap is None:
            colormap = plt.cm.get_cmap('rainbow')

        super().__init__(
            chart,
            fig=fig,
            axes=axes,
        )
        self.fdata = fdata
        self.estimator = estimator
        self.sample_labels = sample_labels
        self.sample_colors = sample_colors
        self.cluster_labels = cluster_labels
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.colormap = colormap
        self._set_figure_and_axes(chart, fig=fig, axes=axes)

    def n_samples(self) -> int:
        return self.fdata.n_samples

    def plot(self) -> Figure:
        """
        Plot cluster membership.

        A kind of Parallel Coordinates plot is generated in this function with
        the membership values obtained from the algorithm. A line is plotted
        for each sample with the values for each cluster. See
        `Clustering Example <../auto_examples/plot_clustering.html>`_.

        Returns:
            Plotted figure.

        """
        self.artists = np.array([])

        try:
            check_is_fitted(self.estimator)
            _check_compatible_fdata(
                self.estimator.cluster_centers_,
                self.fdata,
            )
        except NotFittedError:
            self.estimator.fit(self.fdata)

        membership = self.estimator.predict_proba(self.fdata)

        _plot_clustering_checks(
            estimator=self.estimator,
            fdata=self.fdata,
            sample_colors=self.sample_colors,
            sample_labels=self.sample_labels,
            cluster_colors=None,
            cluster_labels=self.cluster_labels,
            center_colors=None,
            center_labels=None,
        )

        self.x_label, self.y_label, self.title = _get_labels(
            self.x_label,
            self.y_label,
            self.title,
            "Cluster",
        )

        if self.sample_colors is None:
            self.cluster_colors = self.colormap(
                np.arange(self.estimator.n_clusters)
                / (self.estimator.n_clusters - 1),
            )
            labels_by_cluster = self.estimator.labels_
            self.sample_colors = self.cluster_colors[labels_by_cluster]

        if self.sample_labels is None:
            self.sample_labels = [
                f'$SAMPLE: {i}$'
                for i in range(self.fdata.n_samples)
            ]

        if self.cluster_labels is None:
            self.cluster_labels = [
                f'${i}$'
                for i in range(self.estimator.n_clusters)
            ]

        self.axes[0].get_xaxis().set_major_locator(MaxNLocator(integer=True))
        self.artists = np.array([
            self.axes[0].plot(
                np.arange(self.estimator.n_clusters),
                membership[i],
                label=self.sample_labels[i],
                color=self.sample_colors[i],
            )
            for i in range(self.fdata.n_samples)
        ])

        self.axes[0].set_xticks(np.arange(self.estimator.n_clusters))
        self.axes[0].set_xticklabels(self.cluster_labels)
        self.axes[0].set_xlabel(self.x_label)
        self.axes[0].set_ylabel(self.y_label)

        self.fig.suptitle(self.title)
        return self.fig


class ClusterMembershipPlot(BasePlot):
    """
    Class ClusterMembershipPlot.

    Args:
        estimator: estimator used to calculate the
            clusters.
        X: contains the samples which are grouped
            into different clusters.
        fig: figure over which the graph is
            plotted in case ax is not specified. If None and ax is also None,
            the figure is initialized.
        axes: axis over where the graph is  plotted.
            If None, see param fig.
        sample_colors: contains in order the colors
            of each sample of the fdatagrid.
        sample_labels: contains in order the labels
            of each sample  of the fdatagrid.
        cluster_labels: contains in order the names of
            each cluster the samples of the fdatagrid are classified into.
        colormap: colormap from which the colors of the
            plot are taken.
        x_label: Label for the x-axis. Defaults to "Cluster".
        y_label: Label for the y-axis. Defaults to
            "Degree of membership".
        title: Title for the figure where the clustering
            results are ploted.
            Defaults to "Degrees of membership of the samples to each cluster".
    """

    def __init__(
        self,
        estimator: FuzzyClusteringEstimator,
        fdata: FData,
        chart: Union[Figure, Axes, None] = None,
        fig: Optional[Figure] = None,
        axes: Union[Axes, Sequence[Axes], None] = None,
        sort: int = -1,
        sample_labels: Optional[Sequence[str]] = None,
        cluster_colors: Optional[Sequence[ColorLike]] = None,
        cluster_labels: Optional[Sequence[str]] = None,
        colormap: matplotlib.colors.Colormap = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:

        if colormap is None:
            colormap = plt.cm.get_cmap('rainbow')

        super().__init__(
            chart,
            fig=fig,
            axes=axes,
        )
        self.fdata = fdata
        self.estimator = estimator
        self.sample_labels = sample_labels
        self.cluster_colors = cluster_colors
        self.cluster_labels = cluster_labels
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.colormap = colormap
        self.sort = sort
        self._set_figure_and_axes(chart, fig=fig, axes=axes)

    def n_samples(self) -> int:
        return self.fdata.n_samples

    def plot(self) -> Figure:
        """
        Plot cluster membership.

        A kind of barplot is generated in this function with the membership
        values obtained from the algorithm. There is a bar for each sample
        whose height is 1 (the sum of the membership values of a sample add
        to 1), and the part proportional to each cluster is coloured with
        the corresponding color. See
        `Clustering Example <../auto_examples/plot_clustering.html>`_.

        Returns:
            Plotted figure.

        """
        self.artists = np.array([])

        try:
            check_is_fitted(self.estimator)
            _check_compatible_fdata(
                self.estimator.cluster_centers_,
                self.fdata,
            )
        except NotFittedError:
            self.estimator.fit(self.fdata)

        membership = self.estimator.predict_proba(self.fdata)

        if self.sort < -1 or self.sort >= self.estimator.n_clusters:
            raise ValueError(
                "The sorting number must belong to "
                "the interval [-1, n_clusters)",
            )

        _plot_clustering_checks(
            estimator=self.estimator,
            fdata=self.fdata,
            sample_colors=None,
            sample_labels=self.sample_labels,
            cluster_colors=self.cluster_colors,
            cluster_labels=self.cluster_labels,
            center_colors=None,
            center_labels=None,
        )

        self.x_label, self.y_label, self.title = _get_labels(
            self.x_label,
            self.y_label,
            self.title,
            "Sample",
        )

        if self.sample_labels is None:
            self.sample_labels = np.arange(self.fdata.n_samples)

        if self.cluster_colors is None:
            self.cluster_colors = self.colormap(
                np.arange(self.estimator.n_clusters)
                / (self.estimator.n_clusters - 1),
            )

        if self.cluster_labels is None:
            self.cluster_labels = [
                f'$CLUSTER: {i}$'
                for i in range(self.estimator.n_clusters)
            ]

        patches = [
            mpatches.Patch(
                color=self.cluster_colors[i],
                label=self.cluster_labels[i],
            )
            for i in range(self.estimator.n_clusters)
        ]

        if self.sort == -1:
            labels_dim = membership
        else:
            sample_indices = np.argsort(-membership[:, self.sort])
            self.sample_labels = np.copy(self.sample_labels[sample_indices])
            labels_dim = np.copy(membership[sample_indices])

            temp_labels = np.copy(labels_dim[:, 0])
            labels_dim[:, 0] = labels_dim[:, self.sort]
            labels_dim[:, self.sort] = temp_labels

            temp_color = np.copy(self.cluster_colors[0])
            self.cluster_colors[0] = self.cluster_colors[self.sort]
            self.cluster_colors[self.sort] = temp_color

        conc = np.zeros((self.fdata.n_samples, 1))
        labels_dim = np.concatenate((conc, labels_dim), axis=-1)
        for i in range(self.estimator.n_clusters):
            self.x = self.axes[0].bar(
                np.arange(self.fdata.n_samples),
                labels_dim[:, i + 1],
                bottom=np.sum(labels_dim[:, :(i + 1)], axis=1),
                color=self.cluster_colors[i],
            )

        self.axes[0].set_xticks(np.arange(self.fdata.n_samples))
        self.axes[0].set_xticklabels(self.sample_labels)
        self.axes[0].set_xlabel(self.x_label)
        self.axes[0].set_ylabel(self.y_label)
        self.axes[0].legend(handles=patches)

        self.fig.suptitle(self.title)
        return self.fig
