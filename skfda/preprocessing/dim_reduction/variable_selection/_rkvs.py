import sklearn.utils.validation

import numpy as np
import numpy.linalg as linalg

from ....representation import FDataGrid


def _rkhs_vs(X, Y, n_components: int=1):
    '''
    Parameters
    ----------
    X
        Matrix of trajectories
    Y
        Vector of class labels
    n_components
        Number of selected components
    '''

    X = np.atleast_2d(X)
    assert n_components >= 1
    assert n_components <= X.shape[1]

    Y = np.asarray(Y)

    selected_features = np.zeros(n_components, dtype=int)
    score = np.zeros(n_components)
    indexes = np.arange(0, X.shape[1])

    # Calculate means and covariance matrix
    class_1_trajectories = X[Y.ravel() == 1]
    class_0_trajectories = X[Y.ravel() == 0]

    means = (np.mean(class_1_trajectories, axis=0) -
             np.mean(class_0_trajectories, axis=0))

    class_1_count = sum(Y)
    class_0_count = Y.shape[0] - class_1_count

    class_1_proportion = class_1_count / Y.shape[0]
    class_0_proportion = class_0_count / Y.shape[0]

    # The result should be casted to 2D because of bug #11502 in numpy
    variances = (
        class_1_proportion * np.atleast_2d(
            np.cov(class_1_trajectories, rowvar=False, bias=True)) +
        class_0_proportion * np.atleast_2d(
            np.cov(class_0_trajectories, rowvar=False, bias=True)))

    # The first variable maximizes |mu(t)|/sigma(t)
    mu_sigma = np.abs(means) / np.sqrt(np.diag(variances))

    selected_features[0] = np.argmax(mu_sigma)
    score[0] = mu_sigma[selected_features[0]]
    indexes = np.delete(indexes, selected_features[0])

    for i in range(1, n_components):
        aux = np.zeros_like(indexes, dtype=np.float_)

        for j in range(0, indexes.shape[0]):
            new_selection = np.concatenate([selected_features[0:i],
                                            [indexes[j]]])

            new_means = np.atleast_2d(means[new_selection])

            lstsq_solution = linalg.lstsq(
                variances[new_selection[:, np.newaxis], new_selection],
                new_means.T, rcond=None)[0]

            aux[j] = new_means @ lstsq_solution

        aux2 = np.argmax(aux)
        selected_features[i] = indexes[aux2]
        score[i] = aux[aux2]
        indexes = np.delete(indexes, aux2)

    return selected_features, score


class RKHSVariableSelection(sklearn.base.BaseEstimator,
                            sklearn.base.TransformerMixin):
    r'''
    Reproducing kernel variable selection.

    This is a variable selection method for homoscedastic binary
    classification problems. It aims to select the variables
    :math:`t_1, \ldots, t_d` which maximize the following quantity

    .. math::
        \phi(t_1, \ldots, t_d) = m_{t_1, \ldots, t_d}^T
        K_{t_1, \ldots, t_d}^{-1} m_{t_1, \ldots, t_d}

    where :math:`m_{t_1, \ldots, t_d}` is the difference of the mean
    functions of both classes evaluated at points :math:`t_1, \ldots, t_d`
    and :math:`K_{t_1, \ldots, t_d}` is the common covariance function
    evaluated at the same points.

    This method is optimal for variable selection in homoscedastic binary
    classification problems when all possible combinations of points are
    taken into account. That means that for all possible selections of
    :math:`t_1, \ldots, t_d`, the one in which :math:`\phi(t_1, \ldots, t_d)`
    is greater minimizes the optimal misclassification error of all the
    classification problems with the reduced dimensionality.

    In practice, however, the points are selected one at a time, using
    a greedy approach, so this optimality is not always guaranteed.

    Parameters:
        n_components (int): number of variables to select.

    Examples:

        >>> from skfda.preprocessing.dim_reduction import variable_selection
        >>> from skfda.datasets import make_gaussian_process
        >>> import skfda
        >>> import numpy as np

        We create trajectories from two classes, one with zero mean and the
        other with a peak-like mean. Both have Brownian covariance.

        >>> n_samples = 10000
        >>> n_features = 1000
        >>>
        >>> def mean_1(t):
        ...     return (np.abs(t - 0.25)
        ...             - 2 * np.abs(t - 0.5)
        ...             + np.abs(t - 0.75))
        >>>
        >>> X_0 = make_gaussian_process(n_samples=n_samples // 2,
        ...                             n_features=n_features,
        ...                             random_state=0)
        >>> X_1 = make_gaussian_process(n_samples=n_samples // 2,
        ...                             n_features=n_features,
        ...                             mean=mean_1,
        ...                             random_state=1)
        >>> X = skfda.concatenate((X_0, X_1))
        >>>
        >>> y = np.zeros(n_samples)
        >>> y [n_samples // 2:] = 1

        Select the relevant points to distinguish the two classes

        >>> rkvs = variable_selection.RKHSVariableSelection(n_components=3)
        >>> _ = rkvs.fit(X, y)
        >>> point_mask = rkvs.get_support()
        >>> points = X.sample_points[0][point_mask]
        >>> np.allclose(points, [0.25, 0.5, 0.75], rtol=1e-2)
        True

        Apply the learned dimensionality reduction

        >>> X_dimred = rkvs.transform(X)
        >>> len(X.sample_points[0])
        1000
        >>> X_dimred.shape
        (10000, 3)

    References:
        [1] J. R. Berrendero, A. Cuevas, y J. L. Torrecilla, «On the Use of
        Reproducing Kernel Hilbert Spaces in Functional Classification»,
        Journal of the American Statistical Association, vol. 113, n.º 523,
        pp. 1210-1218, jul. 2018, doi: 10.1080/01621459.2017.1320287.

    '''

    def __init__(self, n_components: int=1):
        self.n_components = n_components

    def fit(self, X: FDataGrid, y):

        n_unique_labels = len(np.unique(y))
        if n_unique_labels != 2:
            raise ValueError(f"RK-VS can only be used when there are only "
                             f"two different labels, but there are "
                             f"{n_unique_labels}")

        if X.dim_domain != 1 or X.dim_codomain != 1:
            raise ValueError("Domain and codomain dimensions must be 1")

        X, y = sklearn.utils.validation.check_X_y(X.data_matrix[..., 0], y)

        self._features_shape_ = X.shape[1:]

        self._features_, self._scores_ = _rkhs_vs(
            X=X,
            Y=y,
            n_components=self.n_components)

        return self

    def transform(self, X: FDataGrid, Y=None):

        sklearn.utils.validation.check_is_fitted(self)

        X_matrix = sklearn.utils.validation.check_array(X.data_matrix[..., 0])

        if X_matrix.shape[1:] != self._features_shape_:
            raise ValueError("The trajectories have a different number of "
                             "points than the ones fitted")

        return X_matrix[:, self._features_]

    def get_support(self, indices: bool=False):
        features = self._features_
        if indices:
            return features
        else:
            mask = np.zeros(self._features_shape_[0], dtype=bool)
            mask[features] = True
            return mask
