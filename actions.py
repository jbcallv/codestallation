import re
from metagpt.actions import Action
from metagpt.logs import logger

class SummarizeCode(Action):
    PROMPT_TEMPLATE: str = """
    Provide a summary of the code here: {code_text}.
    Return ```<your_summary_here>``` with NO other texts,
    your summary:
    """

    name: str = "SummarizeCode"

    async def run(self, directory_name: str):

        code_file = SummarizeCode.find_code_file(directory_name)
        code_text = SummarizeCode.get_code_text(code_file)

        prompt = self.PROMPT_TEMPLATE.format(code_text=code_text)
        rsp = await self._aask(prompt)

        return code_text, rsp

    @staticmethod
    def find_code_file(directory):
        import os
        for file in os.listdir(directory):
            if file.endswith('.py'):
                return os.path.join(directory, file)

        return None
 
    @staticmethod
    def get_code_text(filepath):
        with open(filepath, 'r') as f:
            return f.read()


class ReviewCodeSummary(Action):
    PROMPT_TEMPLATE: str = """
    Given this code: {code}, evaluate the accuracy of the corresponding code summary {summary} in writing.
    Return ```<your_evaluation>``` with NO other texts,
    your evaluation:
    """

    name: str = "ReviewCodeSummary"

    async def run(self, summary: str):
        summary = tuple(summary)
        logger.info(summary)
        prompt = self.PROMPT_TEMPLATE.format(code=summary[0], summary=summary[1])
        rsp = await self._aask(prompt)

        return rsp

