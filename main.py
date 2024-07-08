import sys
import json
import os
from pathlib import Path


def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path) as f:
        spec = json.load(f)

    for path, path_spec in spec["paths"].items():
        for method, method_spec in path_spec.items():
            make_operation_file(path, method, method_spec, spec, output_path)


def make_operation_file(path: str, method: str, method_spec: dict, spec: dict, output_path: str):
    if method != "get":
        return # We're only interested in read operations
    
    out = [
        f"# {method_spec['summary']}",
        "",
        f"`{method.upper()} {path}`",
        "",
        f"{method_spec['description']}",
        "",
        f'[{method_spec["externalDocs"]["description"]}]({method_spec["externalDocs"]["url"]})',
        "",
    ] + params_section(method_spec, spec)
    
    method_file = Path(os.path.join(output_path, path[1:], f"{method}.md"))
    method_file.parent.mkdir(exist_ok=True, parents=True)
    method_file.write_text("\n".join(out))


def params_section(method_spec: dict, spec: dict):
    if "parameters" not in method_spec:
        return []
    
    path_list_items = []
    query_list_items = []

    for parameter in method_spec["parameters"]:
        if "$ref" in parameter:
            parameter = get_reference(parameter["$ref"], spec)

        param_type = ""
        if "schema" in parameter and "type" in parameter["schema"]:
            param_type = parameter["schema"]["type"]

        if 'required' in parameter and parameter['required']:
            param_type += ", required"

        list_item = f"- `{parameter['name']}`"

        if param_type:
            list_item += f" ({param_type})"

        if "description" in parameter:
            list_item += ": " + parameter["description"]

        if "in" in parameter and parameter["in"] == "path":
            path_list_items.append(list_item)
        else:
            query_list_items.append(list_item)

    out = [
        f"## All Parameters for \"{method_spec['summary']}\"", 
        ""
    ]

    if len(path_list_items) > 0:
        out += ["### Path Parameters", ""] + path_list_items

    if len(query_list_items) > 0:
        out += ["### Query Parameters", ""] + query_list_items

    return out


def get_references(method_spec: dict, spec: dict):
    refs = []

    for key, value in traverse_json(method_spec):
        if key == "$ref":
            ref  = get_reference(value, spec)
            refs.append((value, ref))

            refs += get_references(value, spec)

    return refs


def get_reference(key: str, spec: dict):
    pieces = key.split("/")[1:]
    target = spec
    for piece in pieces:
        target = target[piece]

    return target


def traverse_json(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            for inner_k, inner_v in traverse_json(v):
                yield inner_k, inner_v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield i, v
            for inner_k, inner_v in traverse_json(v):
                yield inner_k, inner_v


if __name__ == "__main__":
    main()