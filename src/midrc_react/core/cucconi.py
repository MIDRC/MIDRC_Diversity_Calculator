# Pulled from https://github.com/GrzegorzMika/NonParStat/blob/master/nonparstat/Cucconi.py
# Originally written by Grzegorz Mika (2020)

"""
This module contains functions for calculating the Cucconi test and distribution.
"""

from collections import namedtuple

from joblib import delayed, Parallel
import numpy as np
import numpy.typing as npt
from scipy.stats import rankdata

CucconiResult = namedtuple('CucconiResult', ('statistic', 'pvalue'))
CucconiMultisampleResult = namedtuple('CucconiMultisampleResult', ('statistic', 'pvalue'))


def _cucconi_test_statistic(a: npt.NDArray, b: npt.NDArray, ties: str = 'average') -> float:
    """
    Calculates the Cucconi test statistic for two arrays.
    Args:
        a:
        b:
        ties:

    Returns:

    """
    n1 = len(a)
    n2 = len(b)
    n = n1 + n2
    alldata = np.concatenate((a, b))
    ranked = rankdata(alldata, method=ties)
    a_ranks = ranked[:n1]

    rho = 2 * (n ** 2 - 4) / ((2 * n + 1) * (8 * n + 11)) - 1
    _u = (6 * np.sum(np.square(a_ranks)) - n1 * (n + 1) * (2 * n + 1)) / np.sqrt(
        n1 * n2 * (n + 1) * (2 * n + 1) * (8 * n + 11) / 5)
    _v = (6 * np.sum(np.square(n + 1 - a_ranks)) - n1 * (n + 1) * (2 * n + 1)) / np.sqrt(
        n1 * n2 * (n + 1) * (2 * n + 1) * (8 * n + 11) / 5)
    _c = (_u ** 2 + _v ** 2 - 2 * rho * _u * _v) / 2 * (1 - rho ** 2)

    return _c


def _cucconi_dist_permutation(a: npt.NDArray, b: npt.NDArray, replications: int = 1000,
                              ties: str = 'average', n_jobs: int = 1) -> npt.NDArray:
    """
    Calculates the Cucconi distribution using permutation.

    Args:
        a:
        b:
        replications:
        ties:
        n_jobs:

    Returns:

    """
    n1 = len(a)
    h0_data = np.concatenate([a, b])

    def permuted_test():
        permuted_data = np.random.permutation(h0_data)
        new_a = permuted_data[:n1]
        new_b = permuted_data[n1:]
        return _cucconi_test_statistic(a=new_a, b=new_b, ties=ties)

    return np.sort(
        Parallel(n_jobs=n_jobs)(delayed(permuted_test)() for _ in range(replications)))


def _cucconi_dist_bootstrap(a: npt.NDArray, b: npt.NDArray, replications: int = 1000,
                            ties: str = 'average', n_jobs: int = 1) -> npt.NDArray:
    """
    Calculates the Cucconi distribution using bootstrapping.

    Args:
        a:
        b:
        replications:
        ties:
        n_jobs:

    Returns:

    """
    n1 = len(a)
    n2 = len(b)
    h0_data = np.concatenate([a, b])

    def bootstrap_test():
        new_a = np.random.choice(h0_data, size=n1, replace=True)
        new_b = np.random.choice(h0_data, size=n2, replace=True)
        return _cucconi_test_statistic(new_a, new_b, ties=ties)

    return np.sort(
        Parallel(n_jobs=n_jobs)(delayed(bootstrap_test)() for _ in range(replications)))


def cucconi_test(a: npt.NDArray, b: npt.NDArray, method: str = 'bootstrap', replications: int = 1000,
                 ties: str = 'average', n_jobs: int = 1) -> CucconiResult:
    """
    Method to perform a Cucconi scale-location test.
    Args:
        a (np.ndarray): vector of observations
        b (np.ndarray): vector of observations
        method (str): method for determining p-value,
            possible values are 'bootstrap' and 'permutation'
        replications (int): number of bootstrap replications
        ties (str): string specifying a method to deal with ties in data,
            possible values as for scipy.stats.rankdata
        n_jobs (int): the maximum number of concurrently running jobs. If -1 all CPUs are used. If 1 is given,
            no parallel computing code is used at all. For n_jobs below -1, (n_cpus + 1 + n_jobs) are used.
            None is a marker for ‘unset’ that will be interpreted as n_jobs=1 (sequential execution)

    Returns:
        tuple: namedtuple with test statistic value and the p-value

    Raises:
        ValueError: if 'method' parameter is not specified to 'bootstrap' or 'permutation'

    Examples:
        >>> np.random.seed(987654321) # set random seed to get the same result
        >>> sample_a = sample_b = np.random.normal(loc=0, scale=1, size=100)
        >>> cucconi_test(sample_a, sample_b, replications=10000)
        CucconiResult(statistic=3.7763314663244195e-08, pvalue=1.0)

        >>> np.random.seed(987654321)
        >>> sample_a = np.random.normal(loc=0, scale=1, size=100)
        >>> sample_b = np.random.normal(loc=10, scale=10, size=100)
        >>> cucconi_test(sample_a, sample_b, method='permutation')
        CucconiResult(statistic=2.62372293956099, pvalue=0.000999000999000999)

    """
    a, b = map(np.asarray, (a, b))

    test_statistics = _cucconi_test_statistic(a=a, b=b, ties=ties)

    if method == 'permutation':
        h0_distribution = _cucconi_dist_permutation(a=a, b=b, replications=replications, ties=ties,
                                                    n_jobs=n_jobs)
    elif method == 'bootstrap':
        h0_distribution = _cucconi_dist_bootstrap(a=a, b=b, replications=replications, ties=ties,
                                                  n_jobs=n_jobs)
    else:
        raise ValueError(
            f"Unknown method for constructing the distribution,"
            f" possible values are ['bootstrap', 'permutation'], but {method} was provided")

    p_value = (len(np.array(h0_distribution)[h0_distribution >= test_statistics]) + 1) / (
            replications + 1)

    return CucconiResult(statistic=test_statistics, pvalue=p_value)


def _cucconi_multisample_test_statistic(samples: list[npt.NDArray], ties: str = 'average') -> float:
    """
    Calculates the Cucconi multisample test statistic.

    Args:
        samples:
        ties:

    Returns:

    """
    lengths = np.cumsum([0] + [s.shape[0] for s in samples])
    ranked_data = rankdata(np.concatenate(samples), method=ties)
    samples_ranks = [ranked_data[lengths[k]:lengths[k + 1]] for k, _ in enumerate(lengths[:-1])]

    n_i = np.array([s.shape[0] for s in samples])
    n = sum(n_i)

    expected_values = n_i * (n + 1) * (2 * n + 1) / 6
    std_deviations = np.sqrt(n_i * (n - n_i) * (n + 1) * (2 * n + 1) * (8 * n + 11) / 180)
    correlation = -(30 * n + 14 * n ** 2 + 19) / ((8 * n + 11) * (2 * n + 1))

    _u = np.array(
        [(np.sum(sample ** 2) - expected_values[i]) / std_deviations[i] for i, sample in
         enumerate(samples_ranks)])
    _v = np.array(
        [(np.sum((n + 1 - sample) ** 2) - expected_values[i]) / std_deviations[i] for i, sample in
         enumerate(samples_ranks)])
    _mc = np.mean(_u ** 2 + _v ** 2 - 2 * _u * _v * correlation) / (2 - 2 * correlation ** 2)

    return _mc


def _cucconi_multisample_dist_bootstrap(samples: list[npt.NDArray], replications: int = 1000,
                                        ties: str = 'average', n_jobs: int = 1) -> npt.NDArray:
    """
    Calculates the Cucconi multisample distribution using bootstrapping.

    Args:
        samples:
        replications:
        ties:
        n_jobs:

    Returns:

    """
    lengths = [len(s) for s in samples]
    h0_data = np.concatenate(samples)

    def bootstrap_test():
        new_samples = [np.random.choice(h0_data, size=n, replace=True) for n in lengths]
        return _cucconi_multisample_test_statistic(samples=new_samples, ties=ties)

    return np.sort(
        Parallel(n_jobs=n_jobs)(delayed(bootstrap_test)() for _ in range(replications)))


def _cucconi_multisample_dist_permutation(samples: list[npt.NDArray], replications: int = 1000,
                                          ties: str = 'average', n_jobs: int = 1) -> npt.NDArray:
    """
    Calculates the Cucconi multisample distribution using permutation.

    Args:
        samples:
        replications:
        ties:
        n_jobs:

    Returns:

    """
    lengths = lengths = np.cumsum([0] + [s.shape[0] for s in samples])
    h0_data = np.concatenate(samples)

    def permuted_test():
        permuted_data = np.random.permutation(h0_data)
        new_samples = [permuted_data[lengths[k]:lengths[k + 1]] for k, _ in enumerate(lengths[:-1])]
        return _cucconi_multisample_test_statistic(samples=new_samples, ties=ties)

    return np.sort(
        Parallel(n_jobs=n_jobs)(delayed(permuted_test)() for _ in range(replications)))


def cucconi_multisample_test(samples: list[npt.NDArray], method: str = 'bootstrap',
                             replications: int = 1000,
                             ties: str = 'average', n_jobs: int = 1) -> CucconiMultisampleResult:
    """
    Method to perform a multisample Cucconi scale-location test.
    Args:
        samples (List[numpy.ndarray]): list of observation vectors
        method (str): method for determining p-value,
            possible values are 'bootstrap' and 'permutation'
        replications (int): number of bootstrap replications
        ties (str): string specifying a method to deal with ties in data,
            possible values as for scipy.stats.rankdata
        n_jobs (int): the maximum number of concurrently running jobs. If -1 all CPUs are used. If 1 is given,
            no parallel computing code is used at all. For n_jobs below -1, (n_cpus + 1 + n_jobs) are used.
            None is a marker for ‘unset’ that will be interpreted as n_jobs=1 (sequential execution)

    Returns:
        tuple: namedtuple with test statistic value and the p-value

    Raises:
        ValueError: if 'method' parameter is not specified to 'bootstrap' or 'permutation'

    Examples:
        >>> np.random.seed(987654321) # set random seed to get the same result
        >>> sample_a = sample_b = np.random.normal(loc=0, scale=1, size=100)
        >>> cucconi_multisample_test([sample_a, sample_b], replications=100000)
        CucconiMultisampleResult(statistic=6.996968353551774e-07, pvalue=1.0)

        >>> np.random.seed(987654321)
        >>> sample_a = np.random.normal(loc=0, scale=1, size=100)
        >>> sample_b = np.random.normal(loc=10, scale=10, size=100)
        >>> cucconi_multisample_test([sample_a, sample_a, sample_b], method='permutation')
        CucconiMultisampleResult(statistic=45.3891929069273, pvalue=0.000999000999000999)

    """
    samples = list(map(np.asarray, samples))

    test_statistics = _cucconi_multisample_test_statistic(samples=samples, ties=ties)

    if method == 'permutation':
        h0_distribution = _cucconi_multisample_dist_bootstrap(samples=samples, replications=replications,
                                                              ties=ties,
                                                              n_jobs=n_jobs)
    elif method == 'bootstrap':
        h0_distribution = _cucconi_multisample_dist_permutation(samples=samples,
                                                                replications=replications, ties=ties,
                                                                n_jobs=n_jobs)
    else:
        raise ValueError(
            f"Unknown method for constructing the distribution, "
            f"possible values are ['bootstrap', 'permutation'], but {method} was provided")

    p_value = (len(np.array(h0_distribution)[h0_distribution >= test_statistics]) + 1) / (
            replications + 1)

    return CucconiMultisampleResult(statistic=test_statistics, pvalue=p_value)
