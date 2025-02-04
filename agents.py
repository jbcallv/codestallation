from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

from actions import SummarizeCode, ReviewCodeSummary


# memory updated for each run of the individual agent's role. Not each action 

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
        code_text = await todo.run(msg.content)
        logger.info(code_text)
        msg = Message(content=str(code_text), role=self.profile, cause_by=type(todo), send_to="Reviewer")

        self.rc.memory.add(msg)

        return msg

class Reviewer(Role):
    name: str = "Reviewer"
    profile: str = "Reviewer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewCodeSummary])
        self._watch([Summarizer])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        context = self.get_memories(k=1)[0]  # find the most recent memory
        summary_evaluation = await todo.run(context)
        msg = Message(content=summary_evaluation, role=self.profile, cause_by=type(todo))

        self.rc.memory.add(msg)

        return msg




################# testing code
if __name__ == "__main__":
    import asyncio

    from metagpt.context import Context

    async def main():
        msg = "test" # project directory
        context = Context()
        role = Summarizer(context=context)
        logger.info(msg)

        result = await role.run(msg)
        logger.info(f"Result: {result}")

    asyncio.run(main())