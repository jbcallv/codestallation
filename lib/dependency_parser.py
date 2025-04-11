import sys
from abc import ABC, abstractmethod
from tree_sitter_languages.core import get_language
from tree_sitter_languages.core import get_parser
import os

class DependencyParser:
    def __init__(self):
        self._parsers = {
            '.py': PythonParser(),
            '.java': JavaParser2(),
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
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = self.parser.parse(bytes(content, "utf8"))
            
        query_string = """
            (import_declaration
                (scoped_identifier) @import)
            (import_declaration
                (scoped_identifier 
                    _ @wildcard_import))
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
        
        # Extract the package of the current file
        current_package = None
        for capture in captures:
            node, capture_name = capture
            if capture_name == "package":
                current_package = node.text.decode('utf8')
                break
        
        for capture in captures:
            node, capture_name = capture
            import_path = node.text.decode('utf8')
            
            # Skip standard Java libraries
            if import_path.startswith('java.') or import_path.startswith('javax.'):
                continue
                
            if capture_name == "import":
                # Direct path resolution based on project_root (src directory)
                potential_dependency = os.path.join(project_root, import_path.replace('.', '/')) + '.java'
                if os.path.exists(potential_dependency):
                    dependencies.append(potential_dependency)
                
            elif capture_name == "static_import" or capture_name == "wildcard_import":
                # Handle static imports and wildcard imports
                if '.*' in import_path:
                    # Wildcard import
                    base_path = import_path.replace('.*', '')
                    package_dir = os.path.join(project_root, base_path.replace('.', '/'))
                    if os.path.exists(package_dir) and os.path.isdir(package_dir):
                        # Add all .java files in this package
                        for file in os.listdir(package_dir):
                            if file.endswith('.java'):
                                dependencies.append(os.path.join(package_dir, file))
                else:
                    # Static import of a specific method/field
                    class_path = '.'.join(import_path.split('.')[:-1])
                    potential_dependency = os.path.join(project_root, class_path.replace('.', '/')) + '.java'
                    if os.path.exists(potential_dependency):
                        dependencies.append(potential_dependency)
            
            elif capture_name in ("type_usage", "class_instantiation"):
                class_name = node.text.decode("utf8")
                
                # Check if it could be a class from the same package
                if current_package:
                    same_package_path = os.path.join(
                        project_root, 
                        current_package.replace('.', '/'), 
                        f"{class_name}.java"
                    )
                    if os.path.exists(same_package_path):
                        dependencies.append(same_package_path)
                
                # If we don't find it in the same package, we need to check imported packages
                # but we'll need to track which imports are used for this to be accurate

        # Deduplicate
        return list(set(dependencies))

    def parse_dependencies_old(self, file_path, project_root):
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

class JavaParser2:
    def __init__(self):
        self.language = get_language("java")
        self.parser = get_parser("java")

    def parse_dependencies(self, file_path, project_root):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = self.parser.parse(bytes(content, "utf8"))

        query_string = """
            (import_declaration
                (scoped_identifier) @import)
            (import_declaration
                (scoped_identifier
                    _ @wildcard_import))
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

        # Extract the package of the current file
        current_package = None
        for capture in captures:
            node, capture_name = capture
            if capture_name == "package":
                current_package = node.text.decode('utf8')
                break

        # Determine the directory structure pattern used in this project
        file_dir = os.path.dirname(file_path)

        for capture in captures:
            node, capture_name = capture
            import_path = node.text.decode('utf8')

            # Skip standard Java libraries
            if import_path.startswith('java.') or import_path.startswith('javax.'):
                continue

            if capture_name == "import":
                # Try to find the Java file for this import
                dependency_path = self.find_dependency_file(import_path, project_root)
                if dependency_path:
                    dependencies.append(dependency_path)

            elif capture_name == "static_import" or capture_name == "wildcard_import":
                if '.*' in import_path:
                    # Wildcard import
                    package_name = import_path.replace('.*', '')
                    package_dir = self.find_package_dir(package_name, project_root)
                    if package_dir:
                        for file in os.listdir(package_dir):
                            if file.endswith('.java'):
                                dependencies.append(os.path.join(package_dir, file))
                else:
                    # Static import
                    class_path = '.'.join(import_path.split('.')[:-1])
                    dependency_path = self.find_dependency_file(class_path, project_root)
                    if dependency_path:
                        dependencies.append(dependency_path)

        # Deduplicate
        return list(set(dependencies))

    def find_dependency_file(self, import_path, project_root):
        """
        Find a Java file for a given import path by checking multiple common directory patterns.
        """
        class_name = import_path.split('.')[-1]
        package_parts = import_path.split('.')
        package_path = '/'.join(package_parts[:-1])
        file_name = f"{class_name}.java"

        # Check common directory patterns
        patterns = [
            # Standard pattern
            os.path.join(project_root, package_path, file_name),

            # With src directory
            os.path.join(project_root, 'src', package_path, file_name),

            # With src/main
            os.path.join(project_root, 'src', 'main', package_path, file_name),

            # With src/main/java (Maven convention)
            os.path.join(project_root, 'src', 'main', 'java', package_path, file_name)
        ]

        # Check each pattern
        for pattern in patterns:
            #print(pattern)
            if os.path.exists(pattern):
                return pattern

        # If not found with standard patterns, search the project
        # (limit depth to reduce computational cost)
        max_depth = 5
        for root, dirs, files in os.walk(project_root):
            # Calculate depth
            rel_path = os.path.relpath(root, project_root)
            if rel_path == '.':
                depth = 0
            else:
                depth = len(rel_path.split(os.sep))

            if depth > max_depth:
                dirs[:] = []  # Stop going deeper
                continue

            # Skip build outputs and VCS directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'target', 'build', 'bin', 'out']]

            # Check if this directory ends with the package path
            if root.endswith(package_path):
                potential_path = os.path.join(root, file_name)
                if os.path.exists(potential_path):
                    return potential_path

        return None

    def find_package_dir(self, package_name, project_root):
        """Find the directory for a package."""
        package_path = package_name.replace('.', '/')

        # Check common patterns
        patterns = [
            os.path.join(project_root, package_path),
            os.path.join(project_root, 'src', package_path),
            os.path.join(project_root, 'src', 'main', package_path),
            os.path.join(project_root, 'src', 'main', 'java', package_path)
        ]

        for pattern in patterns:
            if os.path.isdir(pattern):
                return pattern

        # Search the project with depth limit
        max_depth = 5
        for root, dirs, files in os.walk(project_root):
            # Calculate depth
            rel_path = os.path.relpath(root, project_root)
            if rel_path == '.':
                depth = 0
            else:
                depth = len(rel_path.split(os.sep))

            if depth > max_depth:
                dirs[:] = []  # Stop going deeper
                continue

            # Skip build outputs and VCS directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'target', 'build', 'bin', 'out']]

            # Check if this is our package directory
            if root.endswith(package_path):
                return root

        return None

def main():
    finder = DependencyParser()
    
    #deps = finder.find_dependencies('../test/script.py', '../test')
    #print(f"Dependencies found: {deps}")

    deps = finder.find_dependencies('../test/java/ant/src/main/org/apache/tools/ant/AntClassLoader.java', '../test/java/ant/')
    print(f"Dependencies found: {deps}")


if __name__ == '__main__':
    main()
