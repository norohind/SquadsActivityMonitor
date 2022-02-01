"""
Features:
include files
insert variables from context dict
"""
from os.path import join
import re
templates_dir = 'templates'

variable_pattern: re.Pattern = re.compile(r'{{ .*? }}')
include_pattern: re.Pattern = re.compile(r'{{ @.*? }}')


def render(template_name: str, context: dict):
    template_path = join(templates_dir, template_name)
    template = get_file_content(template_path)

    including = True

    while including:
        including = False

        for include_statement in re.findall(include_pattern, template):
            including = True
            file_include = include_statement.split(' ')[1][1:]
            include_content = get_file_content(join(templates_dir, file_include))
            template = template.replace(include_statement, include_content)

    for var_to_replace in re.findall(variable_pattern, template):
        key = var_to_replace.split(' ')[1]
        template = template.replace(var_to_replace, context[key])

    return template


def get_file_content(filename: str) -> str:
    with open(filename, 'r', encoding='utf-8') as file:
        # it will throw exception if file doesn't exist
        return file.read()
