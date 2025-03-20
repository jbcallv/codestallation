import fire
import typer
from metagpt.logs import logger
from metagpt.team import Team
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.libs import repository_parser
from metagpt.strategy.task_type import TaskType
from model_configuration import get_phi4, get_no_model

from agents import (
    ProjectSplitter, 
    DependencyGraphBuilder, 
    ChunkSummarizer, 
    ChunkSummaryCombiner, 
    FileLevelSummarizer
)

phi4_contextual = get_phi4()
#no_model = get_no_model()

app = typer.Typer()

@app.command()
async def main(
    idea: str = "../metagpt",  # directory with source code
    investment: float = 5.0,
    n_round: int = 2,
    pinecone_api_key: str = None,
    pinecone_index: str = "codestallation",
    file_extensions: list = ["py", "java"]
):
    team = Team()
    
    
    project_splitter = ProjectSplitter(config=phi4_contextual, file_extensions=file_extensions)
    dependency_builder = DependencyGraphBuilder(config=phi4_contextual)
    chunk_summarizer = ChunkSummarizer(config=phi4_contextual)
    chunk_combiner = ChunkSummaryCombiner(config=phi4_contextual)
    file_summarizer = FileLevelSummarizer(config=phi4_contextual)
    
    team.hire([
        project_splitter,
        dependency_builder,
        chunk_summarizer, 
        chunk_combiner,
        file_summarizer
    ])
    
    team.run_project(idea, send_to="ProjectSplitter")
    
    # run the team for the specified number of rounds
    await team.run(n_round=n_round)
    
    # print final summaries
    if hasattr(file_summarizer, 'final_summaries') and file_summarizer.final_summaries:
        print("\n=== DOCUMENTATION COMPLETE ===\n")
        for file, summary in file_summarizer.final_summaries.items():
            print(f"\n--- {file} ---\n")
            print(summary)
            print("\n" + "-" * 40)

if __name__ == "__main__":
    fire.Fire(main)
