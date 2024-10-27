import ast
import inspect
import os
import subprocess

class ExtractFunctionToFile:
    def __init__(self, func):
        self.func = func
        self.extract_and_save()

    def extract_and_save(self):
        function_name = self.func.__name__
        output_dir = "functions"
        output_file = f"{output_dir}/{function_name}.py"
        
        os.makedirs(output_dir, exist_ok=True)
        
        func_module = inspect.getmodule(self.func)
        module_source = inspect.getsource(func_module)
        module_tree = ast.parse(module_source)

        # Locate the target function node
        function_node = next(
            (node for node in module_tree.body if isinstance(node, (ast.FunctionDef,ast.AsyncFunctionDef)) and node.name == function_name), None
        )

        if not function_node:
            print(f"Could not find the function {function_name}.")
            return

        # Collect initial dependencies from decorators, ignoring `ExtractFunctionToFile`
        function_node.decorator_list = [
            decorator for decorator in function_node.decorator_list
            if not (isinstance(decorator, ast.Name) and decorator.id == "ExtractFunctionToFile")
        ]

        # Convert the modified function node back to source code
        function_code = ast.unparse(function_node)

        # Identify dependencies within the function code
        function_tree = ast.parse(function_code)
        all_dependencies = gather_all_dependancies(function_tree, module_tree)
        minimal_imports = []
        for node in module_tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if any(alias.name.split('.')[0] in all_dependencies for alias in node.names):
                    minimal_imports.append(ast.unparse(node))

        # Gather definitions of dependent functions, classes, and variables
        additional_definitions = gather_all_definitions(all_dependencies, module_tree)

        # Combine imports, additional definitions, and function code
        extracted_code = "\n".join(minimal_imports) + "\n\n" + "\n\n".join(additional_definitions) + "\n\n" + function_code

        # Write the final code to the output file
        with open(output_file, "w") as f:
            f.write(extracted_code)

        # Run pylint to check for any unnecessary imports
        result = subprocess.run(
            ["pylint", output_file, "--disable=all", "--enable=unused-import"],
            capture_output=True,
            text=True
        )

        # Clean up any unnecessary imports identified by pylint
        clean_imports(output_file)

        print(f"Minimal function extracted to {output_file}.")

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def gather_all_definitions(dependencies, module_tree):
    definitions = []
    seen_dependencies = set()

    while dependencies:
        dependency = dependencies.pop()
        if dependency in seen_dependencies:
            continue
        seen_dependencies.add(dependency)

        for node in module_tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef ,ast.ClassDef)) and node.name == dependency:
                node.decorator_list = []
                definitions.append(ast.unparse(node))

                new_dependencies = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                dependencies.update(new_dependencies - seen_dependencies)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == dependency:
                        definitions.append(ast.unparse(node))
                        new_dependencies = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
                        dependencies.update(new_dependencies - seen_dependencies)

    return definitions

def gather_all_dependancies(function_tree, module_tree, dependencies=set()):
    old_dependencies = dependencies.copy()

    for node in ast.walk(function_tree):
        if isinstance(node, ast.Name):
            dependencies.add(node.id)

    for node in module_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom,ast.Assign)):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef)) and node.name in dependencies:
                dependencies.update({n.id for n in ast.walk(node) if isinstance(n, ast.Name)})
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in dependencies:
                        dependencies.update({n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)})
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name.split('.')[0] in dependencies:
                        dependencies.add(alias.name.split('.')[0])
    while True :
        if old_dependencies == dependencies:
            dependencies = gather_all_dependancies(function_tree, module_tree,dependencies)
        else:
            break
        
    return dependencies

def find_unused_imports(tree):
    imported_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)

    return imported_names - used_names

def remove_unused_imports(tree, unused_imports):
    class RemoveUnusedImports(ast.NodeTransformer):
        def visit_Import(self, node):
            node.names = [alias for alias in node.names if alias.name.split('.')[0] not in unused_imports]
            if not node.names:
                return None
            return node

        def visit_ImportFrom(self, node):
            node.names = [alias for alias in node.names if alias.name not in unused_imports]
            if not node.names:
                return None
            return node

    return RemoveUnusedImports().visit(tree)

def clean_imports(filename):
    with open(filename, "r") as file:
        tree = ast.parse(file.read(), filename)

    unused_imports = find_unused_imports(tree)
    if not unused_imports:
        print("No unused imports found.")
        return
    
    new_tree = remove_unused_imports(tree, unused_imports)
    new_code = ast.unparse(new_tree)

    with open(filename, "w") as file:
        file.write(new_code)

    print(f"Removed unused imports: {', '.join(unused_imports)}")