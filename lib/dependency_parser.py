import sys
from abc import ABC, abstractmethod
from tree_sitter_languages.core import get_language
from tree_sitter_languages.core import get_parser
import os

class DependencyParser:
    def __init__(self):
        self._parsers = {
            '.py': PythonParser(),
            '.java': JavaParser(),
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust'
        }

    def find_dependencies(self, file_path, project_root):
        extension = os.path.splitext(file_path)[1].lower().strip()

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


class JavaParser(LanguageParser):
    def _initialize_parser(self):
        self.language = get_language("java")
        self.parser = get_parser("java")

    def parse_dependencies(self, file_path, project_root):
        with open(file_path) as f:
            tree = self.parser.parse(bytes(f.read(), "utf8"))
            
        query_string = """
            (import_declaration
                (scoped_identifier) @import)
            (import_declaration
                (scoped_identifier) @wildcard_import)
            (import_declaration
                (scoped_identifier) @static_import)
            (package_declaration 
                [(identifier) (scoped_identifier)] @package)

            (type_identifier) @type_usage
            (object_creation_expression
                [(type_identifier) (scoped_type_identifier)] @class_instantiation)
        """

        query = self.language.query(query_string)
        
        dependencies = []
        captures = query.captures(tree.root_node)
        for capture in captures:
            node, capture_name = capture  # capture is a tuple of (node, capture_name)
            import_path = node.text.decode('utf8')

                        
            if import_path.startswith('java.') or import_path.startswith('javax.'):
                continue

            if capture_name == "package":
                # get to package directory
                package_dir = os.path.join(project_root, import_path.replace('.', '/'))
                
                # 1. go through package directory
                # 2. find classes in package that are ACTUALLY USED by the file we're inspecting
                # 3. add the used classes to the dependency array
                package_deps = self.get_package_dependencies(package_dir, captures)
                dependencies += package_deps

            if capture_name == "static_import":
                import_path = '.'.join(import_path.split('.')[:-1]) # grab everything but the wildcard / method name / data type

            potential_dependency = os.path.join(project_root, import_path.replace('.', '/')) + '.java'

            if os.path.exists(potential_dependency):
                dependencies.append(potential_dependency)
            
        # deduplicate with set
        return list(set(dependencies))

    def get_package_dependencies(self, package_dir, captures):
        # we build a set so that lookups are done in O(1)
        class_names = {os.path.splitext(f)[0] for f in os.listdir(package_dir) if f.endswith('.java')}

        package_deps = []
        for capture in captures:
            node, capture_name = capture

            if capture_name in ("type_usage", "class_instantiation"):
                class_name = node.text.decode("utf8")

                if class_name in class_names:
                    package_deps.append(class_name)

        # now we need to add the file extensions back and return deduplicated copy
        return list(set([os.path.join(package_dir, class_name) + '.java' for class_name in package_deps]))

 

def main():
    finder = DependencyParser()
    
    #deps = finder.find_dependencies('../test/script.py', '../test')
    #print(f"Dependencies found: {deps}")

    deps = finder.find_dependencies('../test/java/netchat-java/ChatServer/src/chat/ChatServer.java', '../test/java/netchat-java/ChatServer/src')
    print(f"Dependencies found: {deps}")


if __name__ == '__main__':
    main()
