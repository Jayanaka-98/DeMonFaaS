# decorator_scanner.py
import ast
import sys

def get_decorated_functions(filename, decorator_name="DeMonFaaS"):
    with open(filename, "r") as file:
        tree = ast.parse(file.read())

    functions_with_decorator = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                    functions_with_decorator.append(node.name)
                elif isinstance(decorator, ast.Attribute) and decorator.attr == decorator_name:
                    functions_with_decorator.append(node.name)
    return functions_with_decorator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decorator_scanner.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    decorated_functions = get_decorated_functions(filename)
    for func_name in decorated_functions:
        print(func_name)
