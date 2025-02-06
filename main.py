import fire
import typer
from metagpt.logs import logger
from metagpt.team import Team

from agents import Summarizer, Reviewer

from model_configuration import get_deepseek, get_tinyllama

## for customizing LLMs for each agent: https://docs.deepwisdom.ai/main/en/guide/tutorials/customize_llms_for_roles_or_actions.html
deepseek = get_deepseek()
tinyllama = get_tinyllama()

app = typer.Typer()

@app.command()
async def main(
    idea: str = "test", # configured to be the directory with the source code
    investment: float = 5.0,
    n_round: int = 2
):
    team = Team()
    team.hire(
        [
            Summarizer(config=deepseek),
            Reviewer(config=tinyllama),
        ]
    )

    team.run_project(idea, send_to="Summarizer") # initial agent to receive the first instruction
    await team.run(n_round=10)

if __name__ == "__main__":
    fire.Fire(main)