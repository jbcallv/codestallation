import os
from typing import List
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message

from lib.dependency_parser import DependencyParser

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
    Provide a summary of the code chunk here: {code_text}. Relevant 
    dependency summary information is provided for context. Use it as necessary:

    {dependency_summaries}

    Return <your_summary_here> with NO other texts. Your summary 
    should be no longer than 3 sentences.
    your summary:
    """

    COMBINE_SUMMARIES_PROMPT: str = """
    Provide a single summary that captures all important
    information from the following list of code summaries:
    {summaries}
    Return <your_summary_here> with NO other texts. Your summary
    should be no longer than 4 sentences.
    your summary:
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dependency_graph = {}
        self.summaries = {}
        self.processing_stack = []
        self.CHUNK_SIZE = 100
        self.CHUNK_OVERLAP = 30

    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()
            
    @staticmethod
    def parse_imports(file, project_root):
        dependency_finder = DependencyParser()
        deps = dependency_finder.find_dependencies(file, project_root)
        
        return deps

    async def run(self, files, project_root):
        for file in files:
            dependencies = SummarizeCode.parse_imports(file, project_root)
            self.dependency_graph[file] = dependencies

        for file in files:
            if file not in self.summaries:
                await self.summarize_file(file)

        return self.dependency_graph, self.summaries

    async def generate_summary(self, file, dependency_summaries):
        code_text = self.get_code_text(file)

        # this is where we get the whole file for summarization
        chunks = self.create_chunks(file)

        dependency_summaries = "\n".join(dependency_summaries)
        for chunk in chunks:
            prompt = self.PROMPT_TEMPLATE.format(code_text=chunk["content"], dependency_summaries=dependency_summaries)
            rsp = await self._aask(prompt)
            chunk["summary"] = rsp


        # summarize whole file
        summaries = "\n".join([chunk["summary"] for chunk in chunks])
        prompt = self.COMBINE_SUMMARIES_PROMPT.format(summaries=summaries)
        rsp = await self._aask(prompt)

        # in db for tracking
        self.save_summary()
        return rsp

    def save_summary(self):
        # save summary to a db somewhere
        pass

    def create_chunks(self, file):
        chunks = []
        content = self.get_code_text(file)

        lines = content.split('\n')
        current_pos = 0

        while current_pos < len(lines):
            chunk_end = min(current_pos + self.CHUNK_SIZE, len(lines))
            chunk_content = '\n'.join(lines[current_pos:chunk_end])

            chunk = {
                'content': chunk_content,
                'chunk_number': len(chunks) + 1,
                'start_line': current_pos + 1,
                'end_line': chunk_end,
                'summary': "",
            }

            chunks.append(chunk)

            if chunk_end >= len(lines):
                break

            current_pos = chunk_end - self.CHUNK_OVERLAP

        return chunks

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
        summary = await self.generate_summary(file, [self.summaries[dep] for dep in file_dependencies if dep in self.summaries])
        self.summaries[file] = summary
        self.processing_stack.pop()
