import sys
from abc import ABC, abstractmethod
from tree_sitter_languages.core import get_language
from tree_sitter_languages.core import get_parser
import os

class DependencyParser:
    def __init__(self):
        self._parsers = {
            '.py': PythonParser(),
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust'
        }

    def find_dependencies(self, file_path, project_root):
        extension = os.path.splitext(file_path)[1].lower()

        if extension not in self._parsers:
            raise TypeError(f"Unsupported file type: {extension}")

        return self._parsers[extension].parse_dependencies(file_path, project_root)


class LanguageParser(ABC):
    def __init__(self):
        self.language = None
        self.parser = None
        self._initialize_parser()
    
    @abstractmethod
    def _initialize_parser(self):
        pass
    
    @abstractmethod
    def parse_dependencies(self, file_path, project_root):
        pass


class PythonParser(LanguageParser):
    def _initialize_parser(self):
        self.language = get_language("python")
        self.parser = get_parser("python")

    def parse_dependencies(self, file_path, project_root):
        with open(file_path) as f:
            tree = self.parser.parse(bytes(f.read(), "utf8"))
            
        query_string = """
            (import_statement 
                (dotted_name) @import)
            (import_from_statement
                module_name: (dotted_name) @from_import)
        """
        query = self.language.query(query_string)
        
        dependencies = []
        captures = query.captures(tree.root_node)
        for capture in captures:
            node = capture[0]  # capture is a tuple of (node, capture_name)
            import_path = node.text.decode('utf8')
            
            # remove base modules
            if import_path in sys.stdlib_module_names:
                continue

            # check if it's actually a file in the project
            potential_dependency = os.path.join(project_root, import_path.replace('.', '/')) + '.py'

            if os.path.exists(potential_dependency):
                dependencies.append(potential_dependency)
            
        # deduplicate with set
        return list(set(dependencies))


def main():
    finder = DependencyParser()
    
    deps = finder.find_dependencies('../test/script.py', '../test')
    print(f"Dependencies found: {deps}")


if __name__ == '__main__':
    main()