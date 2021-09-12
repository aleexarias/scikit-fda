import unittest

import numpy as np

import skfda
from skfda.exploratory.stats import geometric_median, modified_epigraph_index


class TestGeometricMedian(unittest.TestCase):
    """Test the behavior of the geometric median."""

    def test_R_comparison(self) -> None:
        """
        Compare the results with real-world dataset with those in R.

        The R package used is the Gmedian package.

        """
        X, _ = skfda.datasets.fetch_tecator(return_X_y=True)

        r_res = [  # noqa: WPS317
            2.74083, 2.742715, 2.744627, 2.74659, 2.748656,
            2.750879, 2.753307, 2.755984, 2.758927, 2.762182,
            2.765724, 2.76957, 2.773756, 2.778333, 2.783346,
            2.788818, 2.794758, 2.801225, 2.808233, 2.815714,
            2.82351, 2.831355, 2.838997, 2.846298, 2.853295,
            2.860186, 2.867332, 2.875107, 2.883778, 2.893419,
            2.903851, 2.914717, 2.925698, 2.936765, 2.948293,
            2.960908, 2.97526, 2.991206, 3.008222, 3.02552,
            3.042172, 3.057356, 3.070666, 3.082351, 3.093396,
            3.105338, 3.119946, 3.139307, 3.164418, 3.196014,
            3.234248, 3.278306, 3.326051, 3.374015, 3.418148,
            3.455051, 3.483095, 3.502789, 3.515961, 3.524557,
            3.530135, 3.53364, 3.535369, 3.535305, 3.533326,
            3.529343, 3.523357, 3.51548, 3.5059, 3.494807,
            3.482358, 3.468695, 3.453939, 3.438202, 3.421574,
            3.404169, 3.386148, 3.367751, 3.349166, 3.330441,
            3.311532, 3.292318, 3.272683, 3.252482, 3.23157,
            3.2099, 3.187632, 3.165129, 3.14282, 3.121008,
            3.099793, 3.079092, 3.058772, 3.038755, 3.019038,
            2.99963, 2.980476, 2.961467, 2.94252, 2.923682,
        ]

        median_multivariate = geometric_median(X.data_matrix[..., 0])
        median = geometric_median(X)

        np.testing.assert_allclose(
            median.data_matrix[0, :, 0],
            median_multivariate,
            rtol=1e-4,
        )

        np.testing.assert_allclose(median_multivariate, r_res, rtol=1e-6)

    def test_big(self) -> None:
        """Test a bigger dataset."""
        X, _ = skfda.datasets.fetch_phoneme(return_X_y=True)

        res = np.array([  # noqa: WPS317
            10.87814495, 12.10539654, 15.19841961, 16.29929599, 15.52206033,
            15.35123923, 16.44119775, 16.92255038, 16.70263134, 16.62235371,
            16.76616863, 16.80691414, 16.67460045, 16.64628944, 16.60898231,
            16.64735698, 16.7749517, 16.84533289, 16.8134475, 16.69540395,
            16.56083649, 16.3716527, 16.13744993, 15.95246457, 15.78934047,
            15.64383354, 15.55120344, 15.4363593, 15.36998848, 15.35300094,
            15.23606121, 15.16001392, 15.07326127, 14.92863818, 14.77405828,
            14.63772985, 14.4496911, 14.22752646, 14.07162908, 13.90989422,
            13.68979176, 13.53664058, 13.45465055, 13.40192835, 13.39111557,
            13.32592256, 13.26068118, 13.2314264, 13.29364741, 13.30700552,
            13.30579737, 13.35277966, 13.36572257, 13.45244228, 13.50615096,
            13.54872786, 13.65412519, 13.74737364, 13.79203753, 13.87827636,
            13.97728725, 14.06989886, 14.09950082, 14.13697733, 14.18414727,
            14.1914785, 14.17973283, 14.19655855, 14.20551814, 14.23059727,
            14.23195262, 14.21091905, 14.22234481, 14.17687285, 14.1732165,
            14.13488535, 14.11564007, 14.0296303, 13.99540104, 13.9383672,
            13.85056848, 13.73195466, 13.66840843, 13.64387247, 13.52972191,
            13.43092629, 13.37470213, 13.31847522, 13.21687255, 13.15170299,
            13.15372387, 13.1059763, 13.09445287, 13.09041529, 13.11710243,
            13.14386673, 13.22359963, 13.27466107, 13.31319886, 13.34650331,
            13.45574711, 13.50415149, 13.53131719, 13.58150982, 13.65962685,
            13.63699657, 13.61248827, 13.60584663, 13.61072488, 13.54361538,
            13.48274699, 13.39589291, 13.33557961, 13.27237689, 13.15525989,
            13.0201153, 12.92930916, 12.81669859, 12.67134652, 12.58933066,
            12.48431933, 12.35395795, 12.23358723, 12.1604567, 12.02565859,
            11.92888167, 11.81510299, 11.74115444, 11.62986853, 11.51119027,
            11.41922977, 11.32781545, 11.23709771, 11.1553455, 11.06238304,
            10.97654662, 10.89217886, 10.837813, 10.76259305, 10.74123747,
            10.63519376, 10.58236217, 10.50270085, 10.43664285, 10.36198002,
            10.29128265, 10.27590625, 10.21337539, 10.14368936, 10.11450364,
            10.12276595, 10.0811153, 10.03603621, 10.00381717, 9.94299925,
            9.91830306, 9.90583771, 9.87254886, 9.84294024, 9.85472138,
            9.82047669, 9.8222713, 9.82272407, 9.78949033, 9.78038714,
            9.78720474, 9.81027704, 9.77565195, 9.80675363, 9.77084177,
            9.75289156, 9.75404079, 9.72316608, 9.7325137, 9.70562447,
            9.74528393, 9.70416261, 9.67298074, 9.6888954, 9.6765554,
            9.62346413, 9.65547732, 9.59897653, 9.64655533, 9.57719677,
            9.52660027, 9.54591084, 9.5389796, 9.53577489, 9.50843709,
            9.4889757, 9.46656255, 9.46875593, 9.48179707, 9.44946697,
            9.4798432, 9.46992684, 9.47672347, 9.50141949, 9.45946886,
            9.48043777, 9.49121177, 9.48771047, 9.51135703, 9.5309805,
            9.52914508, 9.54184114, 9.49902134, 9.5184432, 9.48091512,
            9.4951481, 9.51101019, 9.49815911, 9.48404411, 9.45754481,
            9.43717866, 9.38444679, 9.39625792, 9.38149371, 9.40279467,
            9.37378114, 9.31453485, 9.29494997, 9.30214391, 9.24839539,
            9.25834154, 9.24655115, 9.25298293, 9.22182526, 9.18142295,
            9.16692765, 9.1253291, 9.17396507, 9.11561516, 9.13792622,
            9.14151424, 9.10477211, 9.13132802, 9.10557653, 9.10442614,
            9.09571574, 9.13986784, 9.08555206, 9.11363748, 9.14300157,
            9.13020252, 9.15901185, 9.15329127, 9.19107506, 9.19507704,
            9.16421159, 9.18975673, 9.14399055, 9.15376256, 9.17409705,
            8.50360777,
        ])

        median_multivariate = geometric_median(X.data_matrix[..., 0])
        median = geometric_median(X)

        np.testing.assert_allclose(
            median.data_matrix[0, :, 0],
            median_multivariate,
            rtol=1e-2,
        )

        np.testing.assert_allclose(median_multivariate, res, rtol=1e-6)


class TestMEI(unittest.TestCase):
    """Test modified epigraph index."""

    def test_mei(self) -> None:
        """Test modified epigraph index."""
        fd, _ = skfda.datasets.fetch_weather(return_X_y=True)
        fd_temperatures = fd.coordinates[0]
        mei = modified_epigraph_index(fd_temperatures)
        np.testing.assert_allclose(
            mei,
            np.array([  # noqa: WPS317
                0.46272668, 0.27840835, 0.36268754, 0.27908676, 0.36112198,
                0.30802348, 0.82969341, 0.45904762, 0.53907371, 0.38799739,
                0.41283757, 0.20420091, 0.23564253, 0.14737117, 0.14379648,
                0.54035225, 0.43459883, 0.6378604, 0.86964123, 0.4421396,
                0.58906719, 0.75561644, 0.54982387, 0.46095238, 0.09969993,
                0.13166341, 0.18776256, 0.4831833, 0.36816699, 0.72962818,
                0.80313112, 0.79934768, 0.90643183, 0.90139596, 0.9685062,
            ]),
            rtol=1e-5,
        )
