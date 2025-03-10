import os
import sys
from typing import List
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from pinecone import Pinecone

from lib.dependency_parser import DependencyParser

# action 1
class SplitProject(Action):
    name: str = "SplitProject"

    # consider using a tool to accomplish this
    async def run(self, directory, file_extensions):
        all_files = SplitProject.collect_files(directory)
        filtered_files = SplitProject.filter_by_extensions(all_files, file_extensions)

        if not filtered_files:
            print("Error: no relevant project files found.")
            sys.exit(0)

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


# action 2
class BuildDependencyGraph(Action):
    name: str = "BuildDependencyGraph"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dependency_graph = {}

    @staticmethod
    def parse_imports(file, project_root):
        dependency_finder = DependencyParser()
        deps = dependency_finder.find_dependencies(file, project_root)
        return deps

    async def run(self, files, project_root):
        for file in files:
            dependencies = BuildDependencyGraph.parse_imports(file, project_root)
            self.dependency_graph[file] = dependencies

        # store optimal processing order (files with no dependencies first)
        processing_order = self.determine_processing_order()

        return {
            "dependency_graph": self.dependency_graph,
            "processing_order": processing_order
        }

    def determine_processing_order(self):
        processed = set()
        order = []

        def process_file(file):
            if file in processed:
                return
            # Process dependencies first
            for dep in self.dependency_graph.get(file, []):
                # ensures we only process project files
                if dep in self.dependency_graph:
                    process_file(dep)

            processed.add(file)
            order.append(file)

        # process all files
        for file in self.dependency_graph:
            process_file(file)

        return order


# action 3
class SummarizeChunks(Action):
    name: str = "SummarizeChunks"
    PROMPT_TEMPLATE: str = """
    Provide a natural language summary of the code chunk here: 

    {code_text}

    Relevant dependency summary information is provided for context here (use it only as context, focus on summarizing the current chunk):

    {dependency_summaries}

    Return [your_summary_here] with NO other texts. Your summary 
    should be no longer than 3 sentences.

    Your summary:
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.CHUNK_SIZE = 1200
        self.CHUNK_OVERLAP = 50

    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()

    def create_chunks(self, file):
        chunks = []
        content = self.get_code_text(file)
        tokens = self._tokenize(content)

        current_pos = 0

        while current_pos < len(tokens):
            chunk_end = min(current_pos + self.CHUNK_SIZE, len(tokens))
            chunk_content = self._detokenize(tokens[current_pos:chunk_end])

            chunk = {
                'content': chunk_content,
                'chunk_number': len(chunks) + 1,
                'start_line': current_pos + 1,
                'end_line': chunk_end,
                'summary': "",
            }

            chunks.append(chunk)

            if chunk_end >= len(tokens):
                break

            current_pos = chunk_end - self.CHUNK_OVERLAP

        return chunks

    def format_dependency_context(self, dependency_summaries):
        if not dependency_summaries:
            return "No dependencies."

        formatted = "This file depends on:\n"
        for dep, summary in dependency_summaries.items():
            formatted += f"- {os.path.basename(dep)}: {summary}\n"

        return formatted


    async def run(self, file, dependency_summaries):
        chunks = self.create_chunks(file)
        
        # format dependency summaries for prompt
        dependency_context = self.format_dependency_context(dependency_summaries)
        
        for chunk in chunks:
            prompt = self.PROMPT_TEMPLATE.format(
                code_text=chunk["content"], 
                dependency_summaries=dependency_context
            )
            
            # summarize current chunk
            chunk_summary = await self._aask(prompt)
            chunk["summary"] = chunk_summary
        
        return chunks


# action 4
class CombineChunkSummaries(Action):
    name: str = "CombineChunkSummaries"
    COMBINE_SUMMARIES_PROMPT: str = """
    Provide a single natural language summary that captures all important
    information from the following list of code summaries:

    {summaries}

    Return [your_summary_here] with NO other texts. Your summary
    should be no longer than 4 sentences.

    your summary:
    """

    async def run(self, chunks):
        # extract chunk summaries
        chunk_summaries = [chunk["summary"] for chunk in chunks]
        summaries_text = "\n".join(chunk_summaries)
        
        # generate combined summary
        prompt = self.COMBINE_SUMMARIES_PROMPT.format(summaries=summaries_text)
        combined_summary = await self._aask(prompt)
        
        return combined_summary


# action 5
class FileSummarizer(Action):
    name: str = "FileSummarizer"
    FILE_SUMMARY_PROMPT: str = """
    Create a comprehensive summary for this file, using its combined chunk summary, the code itself, and relevant dependency information.

    File chunk summary:
    {file_summary}

    Relevant code sections:
    {code_sections}

    Dependency context (use only as context, focus on summarizing the current file):
    {dependency_context}

    Return [your_summary_here] with NO other texts. Your summary should clearly explain the purpose and functionality
    of this file, mentioning how it relates to its dependencies where relevant. Pay special attention to key classes,
    functions, and methods.

    Your summary:
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.MAX_RELEVANT_CODE_SECTIONS = 10
        self.FALLBACK_CHARACTER_COUNT = 600

        self.pc_namespace = "default"
        self.pc = Pinecone(api_key="pcsk_xn2YX_PrADNhizLCFVwYRrxx6Z488j1PLGKuXADxit5LGTHEbjnK97xrQRBiDt6SdT5JS")
        self.index = self.pc.Index("codestallation")


    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()

    def extract_key_code_sections(self, filepath):
        code_text = self.get_code_text(filepath)

        # TODO: enhance this function
        import re

        # class definitions
        class_defs = re.findall(r'class\s+\w+(?:\(.*?\))?\s*:.*?(?=\n\n|\Z)', code_text, re.DOTALL)

        # functions or methods
        func_defs = re.findall(r'def\s+\w+\(.*?\).*?:.*?(?=\n\n|\Z)', code_text, re.DOTALL)

        sections = class_defs + func_defs

        # plan b: return first part of file if nothing found
        if len("\n\n".join(sections)) < 200 and len(code_text) > 200:
            return code_text[:self.FALLBACK_CHARACTER_COUNT]

        return "\n\n".join(sections[:self.MAX_RELEVANT_CODE_SECTIONS])

    async def run(self, file, file_summary, dependency_summaries):
        # dependency context info
        dependency_context = self.format_dependency_context(dependency_summaries)

        # the key sections to focus on in the prompt
        code_sections = self.extract_key_code_sections(file)

        prompt = self.FILE_SUMMARY_PROMPT.format(
            file_summary=file_summary,
            code_sections=code_sections,
            dependency_context=dependency_context
        )

        final_summary = await self._aask(prompt)

        self.save_summary(file, final_summary)

        return final_summary

    def format_dependency_context(self, dependency_summaries):
        if not dependency_summaries:
            return "No dependencies."

        formatted = "This file depends on:\n"
        for dep, summary in dependency_summaries.items():
            formatted += f"- {os.path.basename(dep)}: {summary}\n"

        return formatted

    def save_summary(self, file_id, summary):
        embeddings = self.pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[summary if summary.strip() else "no summary was produced by the model"],
            parameters={"input_type": "passage"}
        )

        record = [{
            "id": file_id,
            "values": embeddings[0]["values"],
            "metadata": {"text": summary}
        }]

        self.index.upsert(
            vectors=record,
            namespace=self.pc_namespace
        )
