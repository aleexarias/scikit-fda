# -*- coding: utf-8 -*-
"""Basis smoother.

This module contains the class for the basis smoothing.

"""
from __future__ import annotations

from typing import Optional

import numpy as np
from typing_extensions import Final

from ..._utils import _cartesian_product, _to_grid_points
from ...misc.lstsq import LstsqMethod, solve_regularized_weighted_lstsq
from ...misc.regularization import L2Regularization
from ...representation import FData, FDataBasis, FDataGrid, FDataIrregular
from ...representation.basis import Basis
from ...typing._base import GridPointsLike, GridPoints
from ...typing._numpy import NDArrayFloat
from ._linear import _LinearSmoother

#############################
# Auxiliary functions to treat with FDataGrid and FDataIrregular
#############################


def _eval_points(fd: FData) -> NDArrayFloat:
    """Get the eval points of a FDataGrid or FDataIrregular."""
    if isinstance(fd, FDataGrid):
        return _cartesian_product(_to_grid_points(fd.grid_points))
    if isinstance(fd, FDataIrregular):
        return fd.points
    raise ValueError("fd must be a FDataGrid or FDataIrregular")


def _input_points(fd: FData) -> GridPoints:
    """Get the input points of a FDataGrid or FDataIrregular."""
    if isinstance(fd, FDataGrid):
        return fd.grid_points
    if isinstance(fd, FDataIrregular):
        # There exists no equivalent in FDataIrregular to grid_points
        return fd.points  # type: ignore[return-value]
    raise ValueError("fd must be a FDataGrid or FDataIrregular")


def _function_values(fd: FData) -> NDArrayFloat:
    """Get the function values of a FDataGrid or FDataIrregular."""
    if isinstance(fd, FDataGrid):
        return fd.data_matrix.reshape((fd.n_samples, -1)).T
    if isinstance(fd, FDataIrregular):
        return fd.values
    raise ValueError("fd must be a FDataGrid or FDataIrregular")


#############################
# BasisSmoother
#############################

class BasisSmoother(_LinearSmoother):
    r"""
    Transform raw data to a smooth functional form.

    Takes functional data in a discrete form and makes an approximates it
    to the closest function that can be generated by the basis.a.

    The fit is made so as to reduce the penalized sum of squared errors
    [RS05-5-2-6]_:

    .. math::

        PENSSE(c) = (y - \Phi c)' W (y - \Phi c) + \lambda c'Rc

    where :math:`y` is the vector or matrix of observations, :math:`\Phi`
    the matrix whose columns are the basis functions evaluated at the
    sampling points, :math:`c` the coefficient vector or matrix to be
    estimated, :math:`\lambda` a smoothness parameter and :math:`c'Rc` the
    matrix representation of the roughness penalty :math:`\int \left[ L(
    x(s)) \right] ^2 ds` where :math:`L` is a linear differential operator.

    Each element of :math:`R` has the following close form:

    .. math::

        R_{ij} = \int L\phi_i(s) L\phi_j(s) ds

    By deriving the first formula we obtain the closed formed of the
    estimated coefficients matrix:

    .. math::

        \hat{c} = \left( \Phi' W \Phi + \lambda R \right)^{-1} \Phi' W y

    The solution of this matrix equation is done using the cholesky
    method for the resolution of a LS problem. If this method throughs a
    rounding error warning you may want to use the QR factorisation that
    is more numerically stable despite being more expensive to compute.
    [RS05-5-2-8]_

    Args:
        basis: Basis used.
        weights: Matrix to weight the observations. Defaults to the identity
            matrix.
        smoothing_parameter: Smoothing parameter. Trying with several
            factors in a logarithm scale is suggested. If 0 no smoothing is
            performed. Defaults to 1.
        regularization: Regularization object. This allows the penalization of
            complicated models, which applies additional smoothing. By default
            is ``None`` meaning that no additional smoothing has to take
            place.
        method: Algorithm used for calculating the coefficients using
            the least squares method. The values admitted are 'cholesky', 'qr'
            and 'svd' for Cholesky, QR and SVD factorisation methods
            respectively, or a callable similar to the `lstsq` function. The
            default is 'svd', which is the most robust but less performant one.
        output_points: The output points. If ommited, the input points are
            used. If ``return_basis`` is ``True``, this parameter is ignored.
        return_basis: If ``False`` (the default) returns the smoothed
            data as an FDataGrid, like the other smoothers. If ``True`` returns
            a FDataBasis object.

    Examples:
        By default, this smoother returns a FDataGrid, like the other
        smoothers:

        >>> import numpy as np
        >>> import skfda
        >>> t = np.linspace(0, 1, 5)
        >>> x = np.sin(2 * np.pi * t) + np.cos(2 * np.pi * t) + 2
        >>> x
        array([ 3.,  3.,  1.,  1.,  3.])

        >>> fd = skfda.FDataGrid(data_matrix=x, grid_points=t)
        >>> basis = skfda.representation.basis.FourierBasis((0, 1), n_basis=3)
        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(basis)
        >>> fd_smooth = smoother.fit_transform(fd)
        >>> fd_smooth.data_matrix.round(2)
        array([[[ 3.],
                [ 3.],
                [ 1.],
                [ 1.],
                [ 3.]]])

        However, the parameter ``return_basis`` can be used to return the data
        in basis form, by default, without extra smoothing:

        >>> fd = skfda.FDataGrid(data_matrix=x, grid_points=t)
        >>> basis = skfda.representation.basis.FourierBasis((0, 1), n_basis=3)
        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='cholesky',
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.  , 0.71, 0.71]])

        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='qr',
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.  , 0.71, 0.71]])

        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='svd',
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.  , 0.71, 0.71]])
        >>> smoother.hat_matrix().round(2)
        array([[ 0.43,  0.14, -0.14,  0.14,  0.43],
               [ 0.14,  0.71,  0.29, -0.29,  0.14],
               [-0.14,  0.29,  0.71,  0.29, -0.14],
               [ 0.14, -0.29,  0.29,  0.71,  0.14],
               [ 0.43,  0.14, -0.14,  0.14,  0.43]])

        We can penalize approximations that are not smooth enough using some
        kind of regularization:

        >>> from skfda.misc.regularization import L2Regularization
        >>> from skfda.misc.operators import LinearDifferentialOperator
        >>>
        >>> fd = skfda.FDataGrid(data_matrix=x, grid_points=t)
        >>> basis = skfda.representation.basis.FourierBasis((0, 1), n_basis=3)
        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='cholesky',
        ...     regularization=L2Regularization(
        ...         LinearDifferentialOperator([0.1, 0.2]),
        ...     ),
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.04,  0.51,  0.55]])

        >>> fd = skfda.FDataGrid(data_matrix=x, grid_points=t)
        >>> basis = skfda.representation.basis.FourierBasis((0, 1), n_basis=3)
        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='qr',
        ...     regularization=L2Regularization(
        ...         LinearDifferentialOperator([0.1, 0.2]),
        ...     ),
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.04,  0.51,  0.55]])

        >>> fd = skfda.FDataGrid(data_matrix=x, grid_points=t)
        >>> basis = skfda.representation.basis.FourierBasis((0, 1), n_basis=3)
        >>> smoother = skfda.preprocessing.smoothing.BasisSmoother(
        ...     basis,
        ...     method='svd',
        ...     regularization=L2Regularization(
        ...         LinearDifferentialOperator([0.1, 0.2]),
        ...     ),
        ...     return_basis=True,
        ... )
        >>> fd_basis = smoother.fit_transform(fd)
        >>> fd_basis.coefficients.round(2)
        array([[ 2.04,  0.51,  0.55]])

    References:
        .. [RS05-5-2-6] Ramsay, J., Silverman, B. W. (2005). How spline
            smooths are computed. In *Functional Data Analysis*
            (pp. 86-87). Springer.

        .. [RS05-5-2-8] Ramsay, J., Silverman, B. W. (2005). HSpline
            smoothing as an augmented least squares problem. In *Functional
            Data Analysis* (pp. 86-87). Springer.

    """

    _required_parameters = ["basis"]

    def __init__(
        self,
        basis: Basis,
        *,
        smoothing_parameter: float = 1.0,
        weights: Optional[NDArrayFloat] = None,
        regularization: Optional[L2Regularization[FDataGrid]] = None,
        output_points: Optional[GridPointsLike] = None,
        method: LstsqMethod = 'svd',
        return_basis: bool = False,
    ) -> None:
        self.basis = basis
        self.smoothing_parameter = smoothing_parameter
        self.weights = weights
        self.regularization = regularization
        self.output_points = output_points
        self.method = method
        self.return_basis: Final = return_basis

    def _coef_matrix(
        self,
        eval_points: NDArrayFloat,
        *,
        function_values: NDArrayFloat | None = None,
    ) -> NDArrayFloat:
        """Get the matrix that gives the coefficients."""
        from ...misc.regularization import compute_penalty_matrix

        basis_values_input = self.basis(
            eval_points,
        ).reshape((self.basis.n_basis, -1)).T

        penalty_matrix = compute_penalty_matrix(
            basis_iterable=(self.basis,),
            regularization_parameter=self.smoothing_parameter,
            regularization=self.regularization,
        )

        # Get the matrix for computing the coefficients if no
        # function_values is passed
        if function_values is None:
            function_values = np.eye(basis_values_input.shape[0])

        return solve_regularized_weighted_lstsq(
            coefs=basis_values_input,
            result=function_values,
            weights=self.weights,
            penalty_matrix=penalty_matrix,
            lstsq_method=self.method,
        )

    def _hat_matrix(
        self,
        input_points: GridPointsLike,
        output_points: GridPointsLike,
    ) -> NDArrayFloat:
        basis_values_output = self.basis(
            _cartesian_product(
                _to_grid_points(output_points),
            ),
        ).reshape((self.basis.n_basis, -1)).T

        return basis_values_output @ self._coef_matrix(
            _cartesian_product(_to_grid_points(input_points)),
        )

    def fit(
        self,
        X: FDataGrid | FDataIrregular,
        y: object = None,
    ) -> BasisSmoother:
        """Compute the hat matrix for the desired output points.

        Args:
            X: The data whose points are used to compute the matrix.
            y: Ignored.

        Returns:
            self

        """
        self.input_points_ = _input_points(X)
        self.output_points_ = (
            _to_grid_points(self.output_points)
            if self.output_points is not None
            else self.input_points_
        )

        if not self.return_basis:
            super().fit(X, y)

        return self

    def transform(
        self,
        X: FDataGrid | FDataIrregular,
        y: object = None,
    ) -> FData:
        """
        Smooth the data.

        Args:
            X: The data to smooth.
            y: Ignored

        Returns:
            Smoothed data.

        """
        assert all(
            np.array_equal(i, s) for i, s in zip(
                self.input_points_,
                _input_points(X),
            )
        )

        if self.return_basis:
            coefficients = self._coef_matrix(
                eval_points=_eval_points(X),
                function_values=_function_values(X),
            ).T

            return FDataBasis(
                basis=self.basis,
                coefficients=coefficients,
                dataset_name=X.dataset_name,
                argument_names=X.argument_names,
                coordinate_names=X.coordinate_names,
                sample_names=X.sample_names,
            )

        return super().transform(X, y)
