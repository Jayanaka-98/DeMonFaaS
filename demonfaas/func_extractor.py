import ast
import inspect
import os
import subprocess
from functools import wraps

def extract_function_to_file():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            function_name = func.__name__
            output_dir = "functions"
            output_file = f"{output_dir}/{function_name}.py"
            

            os.makedirs(output_dir, exist_ok=True)

            full_source_code = inspect.getsource(func)
            function_lines = full_source_code.splitlines()

            function_def_start = next(i for i, line in enumerate(function_lines) if line.strip().startswith("def "))
            function_code = "\n".join(function_lines[function_def_start:])

            func_module = inspect.getmodule(func)
            module_source = inspect.getsource(func_module)
            module_tree = ast.parse(module_source)

            import_statements = [node for node in module_tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]


            function_names = {node.id for node in ast.walk(ast.parse(function_code)) if isinstance(node, ast.Name)}

            additional_functions = []
            for node in module_tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in function_names and node.name != func.__name__:

                    if not node.decorator_list:
                        additional_functions.append(ast.unparse(node))

            minimal_imports = []
            for import_node in import_statements:
                if isinstance(import_node, ast.Import):
                    if any(alias.name.split('.')[0] in function_names for alias in import_node.names):
                        minimal_imports.append(ast.unparse(import_node))
                elif isinstance(import_node, ast.ImportFrom):
                    if import_node.module and any(alias.name in function_names for alias in import_node.names):
                        minimal_imports.append(ast.unparse(import_node))

            extracted_code = "\n".join(minimal_imports) + "\n\n" + "\n\n".join(additional_functions) + "\n\n" + function_code

            with open(output_file, "w") as f:
                f.write(extracted_code)

            result = subprocess.run(
                ["pylint", output_file, "--disable=all", "--enable=unused-import"],
                capture_output=True,
                text=True
            )

            if "unused-import" in result.stdout:
                print("Pylint identified unnecessary imports:")
                print(result.stdout)
            else:
                print(f"Minimal function extracted to {output_file}. No unnecessary imports detected.")
            
            return func(*args, **kwargs)

        return wrapper
    return decorator