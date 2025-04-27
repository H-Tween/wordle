from prefect import flow
from prefect.runner.storage import GitRepository


def deploy_flow():
    # Define the Git source (GitHub repo)
    # Credentials aren't required because the repository is public
    source = GitRepository(
        url="https://github.com/H-Tween/wordle.git",
    )

    # Deploy the flow from the source
    flow.from_source(
        source=source,
        entrypoint="wordle/flows/daily_word_prefect_script.py:daily_word_update"
    ).deploy(
        name="github-deployV2",
        work_pool_name="wordle",
    )


if __name__ == "__main__":
    deploy_flow()
