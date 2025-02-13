import os
from typing import List
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message

class CloneRepository(Action):
    name: str = "CloneRepository"

    # consider using a tool to accomplish this
    async def run(self, repo_url: str):
        pass

class SplitProject(Action):
    name: str = "SplitProject"

    # consider using a tool to accomplish this
    async def run(self, directory, file_extensions):
        all_files = SplitProject.collect_files(directory)
        filtered_files = SplitProject.filter_by_extensions(all_files, file_extensions)

        return filtered_files

    @staticmethod
    def collect_files(directory: str):
        found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                found_files.append(os.path.join(root, file))
        return found_files

    @staticmethod
    def filter_by_extensions(files: list[str], extensions: list[str]) -> list[str]:
        return [f for f in files if any(f.endswith(ext) for ext in extensions)]


class SummarizeCode(Action):
    name: str = "BuildDependencyGraph"
    PROMPT_TEMPLATE: str = """
    Provide a summary of the code here: {code_text}.
    Return ```<your_summary_here>``` with NO other texts,
    your summary:
    """

    # currently python only
    import_keywords: list = ["import"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dependency_graph = {}
        self.summaries = {}
        self.processing_stack = []

    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()
            
    @staticmethod
    def parse_imports(file):
        SummarizeCode.get_code_text(file)

        # TODO: parse imports language agnostic

        # temp for testing
        if "dependency" in file:
            return []
        
        return ["test/dependency.py"]

        

    async def run(self, files):
        for file in files:
            dependencies = SummarizeCode.parse_imports(file)
            self.dependency_graph[file] = dependencies


        print(self.dependency_graph)
        for file in files:
            if file not in self.summaries:
                await self.summarize_file(file)

        return self.dependency_graph, self.summaries, self.processing_stack

    def generate_summary(self, file, dependency_summaries):
        code_text = self.get_code_text(file)
        prompt = self.PROMPT_TEMPLATE.format(code_text=code_text)
        rsp = f"<{file} code summary/prompt>" #await self._aask(prompt)
        return rsp

    async def summarize_file(self, file):
        if file in self.processing_stack:
            return # avoid unnecessary cycles
        
        self.processing_stack.append(file)

        # handle dependencies before the actual file
        for dependency in self.dependency_graph[file]:
            if dependency not in self.summaries:
                await self.summarize_file(dependency)

        file_dependencies = self.dependency_graph[file]
        # add await when you send to model
        summary = self.generate_summary(file, [self.summaries[dep] for dep in file_dependencies])
        self.summaries[file] = summary
        self.processing_stack.pop()