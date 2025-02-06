from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

from actions import SummarizeCode, ReviewCodeSummary


# note: memory updated for each run of the individual agent's role. Not each action 

# TODO: implement software parser
class SoftwareParser(Role):
    pass

class Summarizer(Role):
    name: str = "Summarizer"
    profile: str = "Summarizer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SummarizeCode])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text, code_summary = await todo.run(msg.content)

        code_msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        summary_msg = Message(content=code_summary, role=self.profile, cause_by=type(todo))

        # save memory for future use by summarizer agen
        self.rc.memory.add(code_msg)
        self.rc.memory.add(summary_msg)

        # publish message to reviewer role
        self.rc.env.publish_message(code_msg)
        self.rc.env.publish_message(summary_msg)

        return code_msg

class Reviewer(Role):
    name: str = "Reviewer"
    profile: str = "Reviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewCodeSummary])
        self._watch({SummarizeCode})

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        context = self.get_memories()  # find the most recent memory
        summary_evaluation = await todo.run(context)
        msg = Message(content=summary_evaluation, role=self.profile, cause_by=type(todo))

        self.rc.memory.add(msg)

        return msg