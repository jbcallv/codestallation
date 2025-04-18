import fire
import typer
from metagpt.logs import logger
from metagpt.team import Team
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.libs import repository_parser
from metagpt.strategy.task_type import TaskType
from model_configuration import get_chatgpt, get_claude, get_phi4, get_no_model, get_tinyllama

from agents import (
    ProjectSplitter, 
    DependencyGraphBuilder, 
    ChunkSummarizer, 
    ChunkSummaryCombiner, 
    FileLevelSummarizer
)

#phi4 = get_phi4()
c1 = get_claude()
c2 = get_claude()
c3 = get_claude()
no_model = get_no_model()

app = typer.Typer()

@app.command()
async def main(
    idea: str = typer.Argument("../MetaGPT", help="Directory with source code to summarize."), #"test/java/jenkins",  # directory with source code, ex. "../metagpt"
    investment: float = 5.0,
    n_round: int = 5,
    pinecone_api_key: str = None,
    pinecone_index: str = typer.Option("metagpt", help="Name of Pinecone index to use."),
    file_extensions: list = typer.Option(["python", "java"], help="File extensions to summarize."), # can add multiple
):
    team = Team()
    
    
    project_splitter = ProjectSplitter(config=no_model, file_extensions=file_extensions)
    dependency_builder = DependencyGraphBuilder(config=no_model)
    chunk_summarizer = ChunkSummarizer(config=c1)
    chunk_combiner = ChunkSummaryCombiner(config=c2)
    file_summarizer = FileLevelSummarizer(config=c3, pinecone_index=pinecone_index)
    
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
