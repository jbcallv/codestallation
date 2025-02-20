import fire
import typer
from metagpt.logs import logger
from metagpt.team import Team
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.libs import repository_parser
from metagpt.strategy.task_type import TaskType

from agents import ProjectSplitter, Summarizer

from model_configuration import get_deepseek, get_tinyllama

## for customizing LLMs for each agent: https://docs.deepwisdom.ai/main/en/guide/tutorials/customize_llms_for_roles_or_actions.html
#deepseek = get_deepseek()
tinyllama = get_tinyllama()

app = typer.Typer()

@app.command()
async def main(
    idea: str = "../MetaGPT", # configured to be the directory with the source code
    investment: float = 5.0,
    n_round: int = 2
):

    #for tt in TaskType:
        #print(tt)

    # data interpreter for advanced NL -> action understanding
    """test_github_repo = "https://github.com/jbcallv/mixify-me"
    repo_parser = DataInterpreter(tools=["RepositoryParser"], config=tinyllama)
    await repo_parser.run(f"Clone the Github repository at the following URL to the projects directory: {test_github_repo}")"""

    project_splitter = ProjectSplitter(config=tinyllama, file_extensions=["py"])
    team = Team()
    team.hire(
        [
            project_splitter,
            Summarizer(config=tinyllama)
        ]
    )

    team.run_project(idea, send_to="ProjectSplitter") # initial agent to receive the first instruction
    await team.run(n_round=10)

if __name__ == "__main__":
    fire.Fire(main)