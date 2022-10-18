from pathlib import Path

import numpy as np
import pandas as pd
from feijoa.visualization.edf import plot_edf
from feijoa.visualization.evaluations import plot_evaluations
from feijoa.visualization.hist import plot_objective_hist
from feijoa.visualization.optimization_history import plot_optimization_history
from feijoa.visualization.parallel_coordinates import plot_parallel_coordinates
from fuzzywuzzy import fuzz
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import cross_val_score


def _subs_ratio(s1: str, s2: str) -> float:
    """
    Calculate the ratio of the number of words in common between two strings

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        The ratio of the number of words in common between two strings.
    """

    split_s1 = s1.split()
    split_s2 = s2.split()
    s1ins2 = [s1i in split_s2 for s1i in split_s1]
    s2ins1 = [s2i in split_s1 for s2i in split_s2]
    return (sum(s1ins2) + sum(s2ins1)) / (len(split_s1) + len(split_s2))


fuzz_ratio = np.vectorize(fuzz.ratio)
fuzz_partial_ratio = np.vectorize(fuzz.partial_ratio)
fuzz_token_sort_ratio = np.vectorize(fuzz.token_sort_ratio)
fuzz_token_set_ratio = np.vectorize(fuzz.token_set_ratio)
subs_ratio = np.vectorize(_subs_ratio)


# noinspection PyPep8Naming
class CNFuzzyClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        threshold=0.8,
        w_pred_ratio=0.2,
        w_pred_partial_ratio=0.2,
        w_pred_token_sort_ratio=0.2,
        w_pred_token_set_ratio=0.2,
        w_pred_subs_ratio=0.2,
    ):

        self.threshold = threshold

        self.w_pred_ratio = w_pred_ratio
        self.w_pred_partial_ratio = w_pred_partial_ratio
        self.w_pred_token_sort_ratio = w_pred_token_sort_ratio
        self.w_pred_token_set_ratio = w_pred_token_set_ratio
        self.w_pred_subs_ratio = w_pred_subs_ratio

    def fit(self, X, y):
        ...

    def _predict(self, X):
        assert X.shape[1] == 2

        X = transform_to_numpy(X)

        lhs, rhs = X[:, 0], X[:, 1]

        pred_ratio = fuzz_ratio(lhs, rhs) * self.w_pred_ratio
        pred_partial_ratio = fuzz_partial_ratio(lhs, rhs) * self.w_pred_partial_ratio
        pred_token_sort_ratio = (
            fuzz_token_sort_ratio(lhs, rhs) * self.w_pred_token_sort_ratio
        )
        pred_token_set_ratio = (
            fuzz_token_set_ratio(lhs, rhs) * self.w_pred_token_set_ratio
        )
        pred_subs_ratio = subs_ratio(lhs, rhs) * self.w_pred_subs_ratio

        pred = np.array(
            [
                pred_ratio,
                pred_partial_ratio,
                pred_token_sort_ratio,
                pred_subs_ratio,
                pred_token_set_ratio,
            ],
            dtype=np.float_,
        ).T

        pred = (pred - np.min(pred)) / (np.max(pred) - np.min(pred))
        return pred.mean(axis=1)

    def predict(self, X):
        """
        Predict the class of each sample.

        Args:
            X: Array-like of shape (n_samples, 2) containing the data to predict.

        Returns:
            Class of each sample.
        """

        pred = self.predict_proba(X) > self.threshold
        return pred.astype(np.int_)

    def predict_proba(self, X):
        """
        Predict the probability of each class.

        Args:
            X: Array-like of shape (n_samples, 2) containing the data to predict.

        Returns:
            Probability of each class.
        """

        return self._predict(X)


# noinspection PyPep8Naming
def transform_to_numpy(X):
    """
    Transform the input to a numpy array.

    Args:
        X: Array-like of shape (n_samples, 2) containing the data to predict.

    Returns:
        A numpy array.
    """

    if isinstance(X, np.ndarray):
        return X

    if isinstance(X, pd.DataFrame):
        return X.to_numpy()
    if isinstance(X, pd.Series):
        return X.to_numpy().reshape(-1, 1)

    if isinstance(X, (list, tuple, set)):
        return np.array(X)

    raise TypeError(
        f"X must be a numpy array, pandas DataFrame,"
        f" pandas Series, or generic sequence, not {type(X)}"
    )


def _get_last_tuning_number():
    """
    Get the last tuning number.

    Returns:
        The last tuning number.
    """

    tuning_folder = Path(__file__).parent.parent.joinpath("tuning")
    tuning_sessions = tuning_folder.glob("tuning_*")
    last_session = sorted(tuning_sessions, key=lambda x: int(x.stem[-1]))

    return int(last_session[-1].stem[-1]) if last_session else 0


def tune_cn_fuzzy_clf(
    X,
    y,
    n_trials=100,
    n_jobs=1,
    n_points_iter=1,
    save_visualization=True,
):
    """
    Tune the weights of the company names fuzzy classifier.

    Args:
        X: Array-like of shape (n_samples, 2) containing the data to predict.
        y: Array-like of shape (n_samples,) containing the true class of each sample.
        n_trials: Number of trials to run.
        n_jobs: Number of jobs to run in parallel.
        n_points_iter: Number of points to evaluate in each iteration.
        save_visualization: Whether to save the visualization.

    Returns:
        A dictionary containing the weights of the fuzzy classifier.
    """

    from feijoa import Real, SearchSpace, create_job
    from pymoo.config import Config

    # ignore pymoo warnings
    Config.warnings["not_compiled"] = False

    # find all w_* field, assume they are all weights
    clf_weights = [
        field for field in dir(CNFuzzyClassifier()) if field.startswith("w_")
    ]
    search_space = SearchSpace()

    # need to insert threshold manually
    search_space.insert(Real("threshold", low=0.2, high=1.0))
    for clf_weight in clf_weights:
        search_space.insert(Real(clf_weight, low=0.0, high=1.0))

    # create a job
    tuning_folder = Path(__file__).parent.parent.joinpath("tuning")
    if not tuning_folder.exists():
        tuning_folder.mkdir()

    last_session_number = _get_last_tuning_number()
    name = f"tuning_{last_session_number + 1}"
    Path.mkdir(tuning_folder.joinpath(name), exist_ok=True)

    job = create_job(
        search_space=search_space,
        storage=f"sqlite:///{tuning_folder.joinpath(name, 'tuning.db')}",
    )

    # define the objective function
    def objective(experiment):
        clf = CNFuzzyClassifier(**experiment.params)
        return 1 - cross_val_score(clf, X, y, cv=5).mean()

    job.do(
        objective,
        n_trials=n_trials,
        optimizer="bayesian",
        n_jobs=n_jobs,
        n_points_iter=n_points_iter,
    )

    print(f"Best parameters: {job.best_parameters}")
    print(f"Best score: {1 - job.best_value}")

    if save_visualization:
        # save the plotly image reports
        plot_edf(job).write_html(tuning_folder.joinpath(name, "edf.html"))
        plot_objective_hist(job).write_html(
            tuning_folder.joinpath(name, "objective_hist.html")
        )
        plot_evaluations(job).write_html(
            tuning_folder.joinpath(name, "evaluations.html")
        )
        plot_parallel_coordinates(job).write_html(
            tuning_folder.joinpath(name, "parallel_coordinates.html")
        )
        plot_optimization_history(job).write_html(
            tuning_folder.joinpath(name, "optimization_history.html")
        )

    return CNFuzzyClassifier(**job.best_parameters)


if __name__ == "__main__":
    df = pd.read_csv(
        Path(__file__).parent.parent.joinpath("data", "1-train-balanced-3600.csv"),
        index_col=0,
    )

    X, y = df[["name_1", "name_2"]], df["is_duplicate"]
    clf = tune_cn_fuzzy_clf(X, y, n_trials=10)
