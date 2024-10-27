import ast
import inspect
import os
import subprocess
from functools import wraps

from demonfaas.func_extractor import ExtractFunctionToFile

# Example usage
@ExtractFunctionToFile
def hello():
    helper()
    print("Hello, World!")

# @extract_function_to_file()
def helper():
    print("This is a helper function.")

# # Run the function
# hello()
