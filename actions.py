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
    PROMPT_TEMPLATE: str = """
    Provide a summary of the code here: {code_text}.
    Return ```<your_summary_here>``` with NO other texts,
    your summary:
    """

    name: str = "SummarizeCode"

    async def run(self, code_file: str):
        code_text = SummarizeCode.get_code_text(code_file)

        prompt = self.PROMPT_TEMPLATE.format(code_text=code_text)
        rsp = "This is your code summary" #await self._aask(prompt)

        return code_text, rsp

    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()


class ReviewCodeSummary(Action):
    PROMPT_TEMPLATE: str = """
    Given this code: ```{code}```, evaluate the accuracy of the corresponding code summary, '{summary}' in writing.
    Return ```<your_evaluation>``` with NO other texts,
    your evaluation:
    """

    name: str = "ReviewCodeSummary"

    async def run(self, summary_payload: List[Message]):
        prompt = self.PROMPT_TEMPLATE.format(code=summary_payload[0].content, summary=summary_payload[1].content)
        #rsp = await self._aask(prompt)

        return prompt#rsp

