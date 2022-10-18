import click
import pandas as pd

from fuzzy_clf import tune_cn_fuzzy_clf


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dataset", "-d", type=click.Path(exists=True), required=True)
@click.option("--n-trials", "-n", type=int, default=10)
@click.option("--n-jobs", "-j", type=int, default=1)
@click.option("--n-points-iter", "-p", type=int, default=1)
@click.option("--save-visualization", "-s", type=bool, default=True)
def example(dataset, n_trials, n_jobs, n_points_iter, save_visualization):
    df = pd.read_csv(dataset)
    X, y = df[["name_1", "name_2"]], df["is_duplicate"]

    tune_cn_fuzzy_clf(
        X,
        y,
        n_trials=n_trials,
        n_jobs=n_jobs,
        n_points_iter=n_points_iter,
        save_visualization=save_visualization,
    )


cli.add_command(example)

if __name__ == "__main__":
    cli()
