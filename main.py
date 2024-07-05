import sys
import json
import os
from pathlib import Path


def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path) as f:
        spec = json.load(f)

    make_info_file(spec, output_path)
    for path, path_spec in spec["paths"].items():
        for method, method_spec in path_spec.items():
            make_operation_file(path, method, method_spec, spec, output_path)


def make_info_file(spec: dict, output_path: str):
    info = spec["info"]
    info_file = Path(os.path.join(output_path, "README.md"))
    info_file.parent.mkdir(exist_ok=True, parents=True)
    info_file.write_text(f"# {info['title']}\n\n{info['description']}\n\n```json\n{json.dumps(info, indent=4)}\n```")


def make_operation_file(path: str, method: str, method_spec: dict, spec: dict, output_path: str):
    if method != "get":
        return # We're only interested in read operations
    
    out = f"# {method_spec['summary']}\n\n`{method} {path}`\n\n{method_spec['description']}\n\n## Operation Object\n\n```json\n{json.dumps(method_spec, indent=4)}\n```"
    
    refs = get_references(method_spec, spec)
    if len(refs) > 0:
        out += "\n\n## References"
        for key, ref in refs:
            out += f"\n\n### `{key}`\n\n```json\n{json.dumps(ref, indent=4)}\n```"

    
    method_file = Path(os.path.join(output_path, path[1:], f"{method}.md"))
    method_file.parent.mkdir(exist_ok=True, parents=True)
    method_file.write_text(out)


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