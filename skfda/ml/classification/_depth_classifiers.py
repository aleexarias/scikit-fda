"""Depth-based models for supervised classification."""

from typing import List

import numpy as np
from sklearn.base import (
    BaseEstimator,
    ClassifierMixin,
    TransformerMixin,
    clone,
)
from sklearn.utils.validation import check_is_fitted as sklearn_check_is_fitted

from ..._utils import _classifier_get_classes
from ...exploratory.depth import Depth, IntegratedDepth, ModifiedBandDepth


class MaximumDepthClassifier(BaseEstimator, ClassifierMixin):
    """Maximum depth classifier for functional data.

    Test samples are classified to the class where they are deeper.

    Parameters:
        depth_method (Depth, default
            :class:`ModifiedBandDepth <skfda.depth.ModifiedBandDepth>`):
            The depth class to use when calculating the depth of a test
            sample in a class. See the documentation of the depths module
            for a list of available depths. By default it is ModifiedBandDepth.
    Examples:
        Firstly, we will import and split the Berkeley Growth Study dataset

        >>> from skfda.datasets import fetch_growth
        >>> from sklearn.model_selection import train_test_split
        >>> dataset = fetch_growth()
        >>> fd = dataset['data']
        >>> y = dataset['target']
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     fd, y, test_size=0.25, stratify=y, random_state=0)

        We will fit a Maximum depth classifier

        >>> from skfda.ml.classification import MaximumDepthClassifier
        >>> clf = MaximumDepthClassifier()
        >>> clf.fit(X_train, y_train)
        MaximumDepthClassifier(...)

        We can predict the class of new samples

        >>> clf.predict(X_test) # Predict labels for test samples
        array([1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1,
               1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1])

        Finally, we calculate the mean accuracy for the test data

        >>> clf.score(X_test, y_test)
        0.875

    See also:
        :class:`~skfda.ml.classification.DDClassifier`
        :class:`~skfda.ml.classification.DTMClassifier`

    References:
        Ghosh, A. K. and Chaudhuri, P. (2005b). On maximum depth and
        related classifiers. Scandinavian Journal of Statistics, 32, 327–350.
    """

    def __init__(self, depth_method: Depth = None):
        if depth_method is None:
            self.depth_method = ModifiedBandDepth()
        else:
            self.depth_method = depth_method

    def fit(self, X, y):
        """Fit the model using X as training data and y as target values.

        Args:
            X (:class:`FDataGrid`): FDataGrid with the training data.
            y (array-like): Target values of shape = (n_samples).

        Returns:
            self (object)
        """
        classes_, y_ind = _classifier_get_classes(y)

        self.classes_ = classes_
        self.distributions_ = [
            clone(self.depth_method).fit(X[y_ind == cur_class])
            for cur_class in range(self.classes_.size)
        ]

        return self

    def predict(self, X):
        """Predict the class labels for the provided data.

        Args:
            X (:class:`FDataGrid`): FDataGrid with the test samples.

        Returns:
            y (np.array): array of shape (n_samples) with class labels
                for each data sample.
        """
        sklearn_check_is_fitted(self)

        depths = [
            distribution.predict(X)
            for distribution in self.distributions_
        ]

        return self.classes_[np.argmax(depths, axis=0)]


class DDTransform(BaseEstimator, TransformerMixin):
    r"""Depth-versus-depth (DD) transformer for functional data.

    This transformer takes a list of k depths and performs the following map:

    .. math::
        \mathcal{X} &\rightarrow \mathbb{R}^G \\
        x &\rightarrow \textbf{d} = (D_1^1(x),...,D_g^k(x))

    Where :math:`D_i^j(x)` is the depth of the point :math:`x` with respect to
    the data in the :math:`i`-th group using the :math:`j`-th depth of the
    provided list.

    Note that :math:`\mathcal{X}` is possibly multivariate, that is,
    :math:`\mathcal{X} = \mathcal{X}_1 \times ... \times \mathcal{X}_p`.

    Parameters:
        depth_methods (default
            :class:`ModifiedBandDepth <skfda.depth.ModifiedBandDepth>`):
            List of depth classes to use when calculating the depth of a test
            sample in a class. See the documentation of the depths module
            for a list of available depths. By default it is the list
            containing ModifiedBandDepth.

    Examples:
        Firstly, we will import and split the Berkeley Growth Study dataset

        >>> from skfda.datasets import fetch_growth
        >>> from sklearn.model_selection import train_test_split
        >>> dataset = fetch_growth()
        >>> fd = dataset['data']
        >>> y = dataset['target']
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     fd, y, test_size=0.25, stratify=y, random_state=0)

        >>> from skfda.ml.classification import DDTransform
        >>> from sklearn.pipeline import make_pipeline
        >>> from sklearn.neighbors import KNeighborsClassifier

        We classify by first transforming our data using the defined map
        and then using KNN

        >>> pipe = make_pipeline(DDTransform(), KNeighborsClassifier())
        >>> pipe.fit(X_train, y_train)
        Pipeline(steps=[('ddtransform',
                         DDTransform(depth_methods=[ModifiedBandDepth(),
                                                    IntegratedDepth()])),
                        ('kneighborsclassifier', KNeighborsClassifier())])

        We can predict the class of new samples

        >>> pipe.predict(X_test)
        array([1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1,
               1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1])

        Finally, we calculate the mean accuracy for the test data

        >>> pipe.score(X_test, y_test)
        0.875

    See also:
        :class:`~skfda.ml.classification.DTMClassifier`
        :class:`~skfda.ml.classification.MaximumDepthClassifier`

    References:
        Li, J., Cuesta-Albertos, J. A., and Liu, R. Y. (2012). DD-classifier:
        Nonparametric classification procedure based on DD-plot. Journal of
        the American Statistical Association, 107(498):737-753.

        Cuesta-Albertos, J.A., Febrero-Bande, M. and Oviedo de la Fuente, M.
        (2017) The DDG-classifier in the functional setting. TEST, 26. 119-142.
    """

    def __init__(self, depth_methods: List[Depth] = None):  # FIXME
        if depth_methods is None:
            self.depth_methods = [ModifiedBandDepth(), IntegratedDepth()]
        else:
            self.depth_methods = depth_methods

    def fit(self, X, y):  # FIXME
        """Fit the model using X as training data and y as target values.

        Args:
            X (:class:`FDataGrid`): FDataGrid with the training data.
            y (array-like): Target values of shape = (n_samples).

        Returns:
            self (object)
        """
        classes_, y_ind = _classifier_get_classes(y)

        self.classes_ = classes_
        self.distributions_ = [
            clone(depth_method).fit(X[y_ind == cur_class])
            for cur_class in range(self.classes_.size)
            for depth_method in self.depth_methods
        ]

        return self

    def transform(self, X):  # FIXME
        """Transform the provided data using the defined map.

        Args:
            X (:class:`FDataGrid`): FDataGrid with the test samples.

        Returns:
            X_new (array-like): array of shape (n_samples, G). FIXME
        """
        sklearn_check_is_fitted(self)

        return np.transpose([
            distribution.predict(X)
            for distribution in self.distributions_
        ])
