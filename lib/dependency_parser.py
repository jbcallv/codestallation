from tree_sitter import Language, Parser
#from tree_sitter_languages import get_language, get_parser
from tree_sitter_languages.core import get_language as get_lang
from tree_sitter_languages.core import get_parser as get_pars
import os
from typing import List, Dict, Optional

class DependencyFinder:
    def __init__(self, language_options):
        """
        Initialize the DependencyFinder with path to tree-sitter language definitions.
        
        Args:
            language_dir: Directory containing tree-sitter language .so files
        """
        self.languages: Dict[str, Language] = {}
        self.parsers: Dict[str, Parser] = {}

        for lang_name in language_options:
            self.languages[lang_name] = get_lang(lang_name)
            self.parsers[lang_name] = get_pars(lang_name)

        print(self.languages, self.parsers)

    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect the programming language based on file extension.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Language name if detected, None otherwise
        """
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext_to_lang.get(ext)

    def find_dependencies(self, file_path: str) -> List[str]:
        """
        Find all imported/referenced dependencies in the given file.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            List of dependency names/paths found
        """
        # Detect language
        lang = self.detect_language(file_path)
        if not lang or lang not in self.parsers:
            raise ValueError(f"Unsupported language for file: {file_path}")

        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Parse the file
        tree = self.parsers[lang].parse(bytes(content, 'utf8'))
        
        # Find import/require nodes based on language
        dependencies = []
        
        def visit_node(node):
            # Common import patterns across languages
            if node.type in ('import_statement', 'import_from_statement',  # Python
                           'import_declaration', 'require_call',           # JavaScript/TypeScript
                           'use_declaration', 'include_statement',         # Rust/C++
                           'package_clause', 'import_spec'):              # Go
                
                # Extract the imported module/package name
                for child in node.children:
                    print(child.text, child.type)
                    if child.type in ('string', 'identifier', 'string_literal', 'dotted_name'):
                        print("here", child.type)
                        dep = content[child.start_byte:child.end_byte].strip('"\'')
                        if dep not in dependencies:
                            dependencies.append(dep)
            
            # Recursively visit child nodes
            for child in node.children:
                visit_node(child)
                
        visit_node(tree.root_node)
        return dependencies

def main():
    # Example usage
    language_options = ["python", "java"]
    finder = DependencyFinder(language_options)
    
    # Find dependencies in a Python file
    deps = finder.find_dependencies('../test/script.py')
    print(f"Dependencies found: {deps}")

if __name__ == '__main__':
    main()