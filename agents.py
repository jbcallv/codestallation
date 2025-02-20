from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

from actions import SplitProject, SummarizeCode


# note: memory updated for each run of the individual agent's role. Not each action 

# TODO: implement software parser to pull repository and enter relevant files for summarization into test/ dir
class SoftwareParser(Role):
    pass

class ProjectSplitter(Role):
    name: str = "ProjectSplitter"
    profile: str = "ProjectSplitter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_extensions = kwargs.get("file_extensions", ["*"])
        self.set_actions([SplitProject])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # get the directory containing the code - currently hardcoded; eventually model figures this out
        root_directory = self.get_memories(k=1)[0].content
        code_files = await todo.run(root_directory, self.file_extensions)

        # can only store messages in memory
        msg_content = ",".join(code_files)
        code_files_msg = Message(content=msg_content, role=self.profile, cause_by=type(todo))
        project_root_msg = Message(content=root_directory, role=self.profile, cause_by=type(todo))

        self.rc.memory.add(code_files_msg)
        self.rc.env.publish_message(code_files_msg)
        self.rc.env.publish_message(project_root_msg)
        
        return code_files_msg


# project level summarizer
class Summarizer(Role):
    name: str = "Summarizer"
    profile: str = "Summarizer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SummarizeCode])
        self._watch({SplitProject})

        # TODO: add to shared memory pool later? Or during construction...
        self.dependency_graph = {}
        self.summaries = {}

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # should get the code files relevant for summarization
        message_queue = self.get_memories(k=2)

        files_msg = message_queue[0]

        project_root = message_queue[1].content
        code_files = files_msg.content.split(",")
        print(project_root)

        # should return a dictionary: pass
        self.dependency_graph, self.summaries = await todo.run(code_files, project_root)
        print()
        for key, value in self.summaries.items():
            print(value)
        
        print()

        #code_msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        #summary_msg = Message(content=code_summary, role=self.profile, cause_by=type(todo))

        #print(code_msg, summary_msg)

        # save memory for future use by summarizer agen
        #self.rc.memory.add(code_msg)
        #self.rc.memory.add(summary_msg)

        # publish message for watchers to read
        #self.rc.env.publish_message(code_msg)
        #self.rc.env.publish_message(summary_msg)

        #return code_msg