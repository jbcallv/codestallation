from metagpt.roles import Role
from metagpt.logs import logger
from metagpt.schema import Message
from typing import Dict, List, Any

from actions import (
    SplitProject, 
    BuildDependencyGraph, 
    SummarizeChunks, 
    CombineChunkSummaries, 
    FileSummarizer
)

class ProjectSplitter(Role):
    name: str = "ProjectSplitter"
    profile: str = "ProjectSplitter"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_extensions = kwargs.get("file_extensions", ["py", "java"])
        self.set_actions([SplitProject])
        
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        root_directory = self.get_memories(k=1)[0].content
        code_files = await todo.run(root_directory, self.file_extensions)
        
        msg_content = ",".join(code_files)
        code_files_msg = Message(content=msg_content, role=self.profile, cause_by=type(todo))
        project_root_msg = Message(content=root_directory, role=self.profile, cause_by=type(todo))
        
        self.rc.env.publish_message(code_files_msg)
        self.rc.env.publish_message(project_root_msg)
        
        return code_files_msg


class DependencyGraphBuilder(Role):
    name: str = "DependencyGraphBuilder"
    profile: str = "DependencyGraphBuilder"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([BuildDependencyGraph])
        self._watch({SplitProject})  # Watch for SplitProject completion
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        # extract information for building the graph
        message_queue = self.get_memories(k=2)
        files_msg = message_queue[0]
        project_root = message_queue[1].content
        code_files = files_msg.content.split(",")
        
        result = await todo.run(code_files, project_root)
        dependency_graph = result["dependency_graph"]
        processing_order = result["processing_order"]
        
        graph_msg = Message(
            content="dependency_graph", 
            role=self.profile, 
            cause_by=type(todo),
            metadata={"dependency_graph": dependency_graph}
        )
        
        order_msg = Message(
            content="processing_order", 
            role=self.profile, 
            cause_by=type(todo),
            metadata={"processing_order": processing_order}
        )
        
        #self.rc.memory.add(graph_msg)
        #self.rc.memory.add(order_msg)
        self.rc.env.publish_message(graph_msg)
        self.rc.env.publish_message(order_msg)
        
        return graph_msg


class ChunkSummarizer(Role):
    name: str = "ChunkSummarizer"
    profile: str = "ChunkSummarizer"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SummarizeChunks])
        self._watch({BuildDependencyGraph})
        self.file_chunks = {}  # keep track of chunk summaries for each file
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        memories = self.get_memories()
        
        # optimal processing order extraction
        dependency_graph = None
        processing_order = None
        project_root = None
        
        #TODO: fix this mess
        for mem in memories:
            if hasattr(mem, 'metadata') and mem.metadata:
                if 'dependency_graph' in mem.metadata:
                    dependency_graph = mem.metadata['dependency_graph']
                elif 'processing_order' in mem.metadata:
                    processing_order = mem.metadata['processing_order']

            if mem.content and not mem.content.startswith('{') and ',' not in mem.content:
                project_root = mem.content
        
        if not dependency_graph or not processing_order or not project_root:
            logger.error("Missing required information for chunk summarization.")
            return Message(content="error", role=self.profile)
        
        # for in case we need these later
        summaries = {}
        
        for file in processing_order:
            dependency_summaries = []
            # use dependencies for context if they exist
            for dep in dependency_graph.get(file, []):
                if dep in summaries:
                    dependency_summaries.append(summaries[dep])
            
            # summarize the chunks
            chunks = await todo.run(file, dependency_summaries)
            self.file_chunks[file] = chunks
            
            # publish chunks and summaries to be joined by the next agent
            chunks_msg = Message(
                content=f"chunks_{file}", 
                role=self.profile, 
                cause_by=type(todo),
                send_to={"ChunkSummaryCombiner"},
                metadata={"file": file, "chunks": chunks}
            )
            
            self.rc.memory.add(chunks_msg)
            # maybe don't want this
            self.rc.env.publish_message(chunks_msg)

        
        # completed message
        summary_msg = Message(
            content="all_chunks_summarized", 
            role=self.profile, 
            cause_by=type(todo),
            metadata={"file_chunks": self.file_chunks}
        )
        
        self.rc.env.publish_message(summary_msg)
        return summary_msg


class ChunkSummaryCombiner(Role):
    name: str = "ChunkSummaryCombiner"
    profile: str = "ChunkSummaryCombiner"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CombineChunkSummaries])
        self._watch({SummarizeChunks})  
        self.file_summaries = {}

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        memories = self.get_memories()
        
        # process each chunk as it comes in
        for mem in memories:
            if hasattr(mem, 'metadata') and mem.metadata and 'chunks' in mem.metadata:
                file = mem.metadata['file']
                chunks = mem.metadata['chunks']
                
                # form the file summary by combining prompts
                file_summary = await todo.run(chunks)
                self.file_summaries[file] = file_summary
                
                # publish the full file summary
                summary_msg = Message(
                    content=f"file_summary_{file}", 
                    role=self.profile, 
                    cause_by=type(todo),
                    send_to={"FileLevelSummarizer"},
                    metadata={"file": file, "summary": file_summary}
                )
                
                self.rc.memory.add(summary_msg)
                self.rc.env.publish_message(summary_msg)
        
        # completed notification message
        all_summaries_msg = Message(
            content="all_file_summaries", 
            role=self.profile, 
            cause_by=type(todo),
            metadata={"file_summaries": self.file_summaries}
        )

        self.rc.env.publish_message(all_summaries_msg)
        return all_summaries_msg


class FileLevelSummarizer(Role):
    name: str = "FileLevelSummarizer"
    profile: str = "FileLevelSummarizer"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([FileSummarizer])
        #self._watch({CombineChunkSummaries})
        
        self.pc_index = kwargs.get("pinecone_index", "metagpt")
        self.final_summaries = {}
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        # get existing summaries and dependency graph
        memories = self.get_memories()
        
        file_summaries = {}
        dependency_graph = None
        
        for mem in memories:
            if hasattr(mem, 'metadata') and mem.metadata:
                if 'file_summaries' in mem.metadata:
                    file_summaries = mem.metadata['file_summaries']
                elif 'dependency_graph' in mem.metadata:
                    dependency_graph = mem.metadata['dependency_graph']
        
        if not file_summaries or not dependency_graph:
            logger.error("Missing required information for file-level summarization")
            return Message(content="error", role=self.profile)
        
        # process each file
        for file, summary in file_summaries.items():
            dependency_summaries = {}
            for dep in dependency_graph.get(file, []):
                if dep in file_summaries:
                    dependency_summaries[dep] = file_summaries[dep]
            
            # finalize the current file's summary
            final_summary = await todo.run(
                file, 
                summary, 
                dependency_summaries,
                self.pc_index
            )
            
            self.final_summaries[file] = final_summary
            
            summary_msg = Message(
                content=f"final_summary_{file}", 
                role=self.profile, 
                cause_by=type(todo),
                metadata={"file": file, "summary": final_summary}
            )
            
            self.rc.memory.add(summary_msg)
            self.rc.env.publish_message(summary_msg)
        
        # publish finalized summary
        final_msg = Message(
            content="documentation_complete", 
            role=self.profile, 
            cause_by=type(todo),
            metadata={"final_summaries": self.final_summaries}
        )
        
        self.rc.env.publish_message(final_msg)
        return final_msg
