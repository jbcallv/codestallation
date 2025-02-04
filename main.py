import fire
import typer
from metagpt.logs import logger
from metagpt.team import Team

from agents import Summarizer, Reviewer

## for customizing LLMs for each agent: https://docs.deepwisdom.ai/main/en/guide/tutorials/customize_llms_for_roles_or_actions.html

app = typer.Typer()

@app.command()
async def main(
    idea: str = "test",
    investment: float = 5.0,
    n_round: int = 1
):
    logger.info(idea)

    team = Team()
    team.hire(
        [
            Summarizer(),
            Reviewer(),
        ]
    )

    team.invest(investment=investment)
    team.run_project(idea, send_to="Summarizer")
    await team.run(n_round=n_round)

if __name__ == "__main__":
    fire.Fire(main)