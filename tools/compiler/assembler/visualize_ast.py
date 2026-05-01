#vibecoded
#!/usr/bin/env python3
"""
Visualize the AST output from the assembler as a graph using graphviz.

Usage:
    ./visualize_ast.py test.asm            # creates test.svg
    ./visualize_ast.py test.asm -f png     # creates test.png
    ./visualize_ast.py test.asm --text     # prints text tree to stdout

Requires: graphviz system package (sudo apt install graphviz)
"""

import subprocess
import sys
import os
import re
import argparse

def parse_dot_format(text):
    """Parse the DOT-like format output from assembler."""
    nodes = {}
    edges = []

    node_pattern = re.compile(r'\s*(\d+)\s*\[label="([^"]*)"')
    edge_pattern = re.compile(r'\s*(\d+)\s*->\s*(\d+)')

    for line in text.split('\n'):
        node_match = node_pattern.match(line)
        if node_match:
            node_id = int(node_match.group(1))
            label = node_match.group(2).replace('\\n', '\n')
            nodes[node_id] = label
            continue

        edge_match = edge_pattern.match(line)
        if edge_match:
            from_id = int(edge_match.group(1))
            to_id = int(edge_match.group(2))
            edges.append((from_id, to_id))

    return nodes, edges

def parse_node_format(text):
    """Parse the 'node: type (key: value)' format from assembler."""
    nodes = {}
    edges = []

    node_pattern = re.compile(r'node:\s*(\w+)\s*(?:\(([^)]*)\))?')

    for line in text.split('\n'):
        line = line.strip()
        if not line.startswith('node:'):
            continue

        match = node_pattern.match(line)
        if not match:
            continue

        node_type = match.group(1)
        attrs_str = match.group(2) or ""

        attrs = {}
        if attrs_str:
            for attr in attrs_str.split(','):
                attr = attr.strip()
                if ':' in attr:
                    key, value = attr.split(':', 1)
                    attrs[key.strip()] = value.strip()

    label = f"type: {node_type}"
    for key, value in attrs.items():
        label += f"\n{key}: {value}"

        node_id = len(nodes)
        nodes[node_id] = label

    section_parents = {}
    section_types = {'section': 'section'}

    for node_id, label in nodes.items():
        parts = label.split('\n')
        node_type = parts[0].replace('type: ', '')

        if node_type == 'section':
            section_parents[node_id] = None
        elif node_type == 'dataDeclaration':
            for sid in sorted(section_parents.keys(), reverse=True):
                if section_parents[sid] is None:
                    section_parents[sid] = node_id
                    edges.append((sid, node_id))
                    break
        elif node_type in ('instruction', 'labelDef'):
            for sid in sorted(section_parents.keys(), reverse=True):
                if 'inst' in nodes.get(sid, '').lower():
                    parent_id = sid
                    while parent_id is not None:
                        parent_label = nodes.get(parent_id, '')
                        parent_type = parent_label.split('\n')[0].replace('type: ', '')
                        if parent_type == 'section' and 'inst' in parent_label.lower():
                            break
                        parent_id = None
                        for eid, efrom in enumerate(edges):
                            if efrom[1] == sid and eid not in [0]:
                                parent_id = efrom[0]
                                break
                    if parent_id is not None:
                        edges.append((parent_id, node_id))
                        break
                    edges.append((sid, node_id))
                    break
        elif node_type in ('identifier', 'literal', 'reg'):
            for pid in range(node_id - 1, -1, -1):
                if pid in nodes:
                    pt = nodes[pid].split('\n')[0].replace('type: ', '')
                    if pt in ('dataDeclaration', 'instruction', 'labelDef', 'node'):
                        edges.append((pid, node_id))
                        break

    return nodes, edges

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[32m"
ANSI_CYAN = "\033[36m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"

def build_diff(pre_nodes, post_nodes, edges):
    changes = {}
    all_ids = set(post_nodes.keys())
    for nid in all_ids:
        if nid not in pre_nodes:
            continue
        pre = pre_nodes[nid]
        post = post_nodes[nid]
        if pre == post:
            continue
        pre_parts = pre.split('\n')
        post_parts = post.split('\n')
        diffs = []
        post_attrs = {}
        for part in post_parts:
            if ': ' in part:
                k, v = part.split(': ', 1)
                post_attrs[k] = v
        pre_attrs = {}
        for part in pre_parts:
            if ': ' in part:
                k, v = part.split(': ', 1)
                pre_attrs[k] = v
        for k in post_attrs:
            if k == 'type':
                continue
            if k == 'intValue' and pre_attrs.get(k, '0') != post_attrs.get(k, '0'):
                diffs.append(f"intValue={post_attrs[k]}")
            elif k in pre_attrs and pre_attrs[k] != post_attrs[k]:
                diffs.append(f"{k}={pre_attrs[k]}→{post_attrs[k]}")
        pre_type = pre_parts[0].replace('type: ', '')
        post_type = post_parts[0].replace('type: ', '')
        if pre_type != post_type:
            diffs.insert(0, f"{pre_type}→{post_type}")
        if diffs:
            changes[nid] = diffs
    return changes

TREE_VERTICAL = "│   "
TREE_BRANCH = "├── "
TREE_LAST = "└── "

def print_node_diff(node_id, nodes, edges, prefix, is_last, changes):
    if node_id not in nodes:
        return
    label = nodes[node_id]
    parts = label.split('\n')
    type_name = ""
    name_value = ""
    int_value = ""
    for part in parts:
        if ': ' in part:
            key, value = part.split(': ', 1)
            if key == 'type':
                type_name = value
            elif key == 'name' or key == 'value':
                name_value = value
            elif key == 'intValue':
                int_value = value

    connector = TREE_LAST if is_last else TREE_BRANCH
    change_str = ""
    if node_id in changes:
        diffs = changes[node_id]
        change_str = f" {ANSI_RED}[{ANSI_YELLOW}{', '.join(diffs)}{ANSI_RED}]{ANSI_RESET}"
    display = name_value
    if int_value and int_value.isdigit():
        v = int(int_value)
        if 0 <= v < 256:
            display += f" (resolved: {int_value})"
    print(f"{prefix}{connector}{ANSI_BOLD}{type_name}: {display}{ANSI_RESET}{change_str}")
    children = [to_id for (fr, to_id) in edges if fr == node_id]
    for i, child_id in enumerate(children):
        child_is_last = (i == len(children) - 1)
        new_prefix = prefix + (TREE_VERTICAL if not is_last else "    ")
        print_node_diff(child_id, nodes, edges, new_prefix, child_is_last, changes)

def print_diff_text_tree(pre_nodes, pre_edges, post_nodes, post_edges):
    print(f"\n{'='*50}")
    print("  AST BEFORE FIRST PASS")
    print(f"{'='*50}")
    print_node(0, pre_nodes, pre_edges, "", True, set(), [])

    print(f"\n{'='*50}")
    print("  AST AFTER FIRST PASS")
    print(f"{'='*50}")
    print_node(0, post_nodes, post_edges, "", True, set(), [])

    print(f"\n{'='*50}")
    print("  CHANGES (firstPass mutations)")
    print(f"{'='*50}")
    changes = build_diff(pre_nodes, post_nodes, post_edges)
    if not changes:
        print("No changes detected.")
        return
    print(f"Found {len(changes)} changed node(s)\n")
    print_node_diff(0, post_nodes, post_edges, "", True, changes)

def print_node(node_id, nodes, edges, prefix, is_last, prefixes, active_verticals):
    if node_id in prefixes:
        return
    prefixes.add(node_id)

    label = nodes[node_id]
    parts = label.split('\n')

    type_name = ""
    name_value = ""
    int_value = ""
    for part in parts:
        if ': ' in part:
            key, value = part.split(': ', 1)
            if key == 'type':
                type_name = value
            elif key == 'name' or key == 'value':
                name_value = value
            elif key == 'intValue':
                int_value = value

    connector = TREE_LAST if is_last else TREE_BRANCH
    display = name_value
    if int_value and int_value.isdigit() and int(int_value) >= 0 and int(int_value) < 256:
        display += f" (resolved: {int_value})"
    if display:
        print(f"{prefix}{connector}{ANSI_BOLD}{type_name}: {display}{ANSI_RESET}")
    else:
        print(f"{prefix}{connector}{ANSI_BOLD}{type_name}{ANSI_RESET}")

    children = [to_id for (fr, to_id) in edges if fr == node_id]
    for i, child_id in enumerate(children):
        child_is_last = (i == len(children) - 1)
        new_prefix = prefix + (TREE_VERTICAL if not is_last else "    ")
        new_active = active_verticals + [not is_last]
        print_node(child_id, nodes, edges, new_prefix, child_is_last, prefixes, new_active)

def print_text_tree(nodes, edges):
    """Print tree with proper box-drawing characters."""
    prefixes = set()
    print_node(0, nodes, edges, "", True, prefixes, [])

def get_display_label(label):
    """Extract display string from node label."""
    parts = label.split('\n')
    return '\n'.join(parts)

def generate_dot(nodes, edges):
    """Generate DOT digraph string from parsed nodes/edges."""
    lines = [
        'digraph AST {',
        '  rankdir=LR;',
        '  splines=ortho;',
        '  node [shape=box, style="rounded,filled", fillcolor="#e8f4f8", color="#2c3e50", fontname="Arial", fontsize="10"];',
        '  edge [color="#7f8c8d"];',
    ]

    for node_id, label in nodes.items():
        display = get_display_label(label)
        escaped = display.replace('"', '\\"').replace('\\', '\\\\')
        lines.append(f'  n{node_id} [label="{escaped}"];')

    for from_id, to_id in edges:
        lines.append(f'  n{from_id} -> n{to_id};')

    lines.append('}')
    return '\n'.join(lines)

def run_assembler(input_file):
    """Run the assembler and capture its output."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assembler_path = os.path.join(script_dir, 'assembler')

    if not os.path.exists(assembler_path):
        print(f"Error: assembler binary not found at {assembler_path}", file=sys.stderr)
        print("Run 'make' first to build the assembler.", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [assembler_path, input_file],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running assembler: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Visualize AST from assembler output')
    parser.add_argument('input', help='Input .asm file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-f', '--format', default='svg',
                       choices=['png', 'pdf', 'svg'],
                       help='Output format (default: svg)')
    parser.add_argument('--text', action='store_true',
                       help='Print text tree instead of graph')
    parser.add_argument('--dot', action='store_true',
                       help='Print DOT source to stdout')
    parser.add_argument('--compare', action='store_true',
                       help='Render both pre/post firstPass DOT files')
    parser.add_argument('--view', action='store_true',
                       help='Open the output file after rendering')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dot_files = [
        os.path.join(script_dir, 'out', 'ast_pre.dot'),
        os.path.join(script_dir, 'out', 'ast_post.dot'),
    ]

    if args.compare:
        for dot_path in dot_files:
            if not os.path.exists(dot_path):
                print(f"Error: {dot_path} not found. Run assembler first.", file=sys.stderr)
                sys.exit(1)

        with open(dot_files[0]) as f:
            pre_nodes, pre_edges = parse_dot_format(f.read())
        with open(dot_files[1]) as f:
            post_nodes, post_edges = parse_dot_format(f.read())

        if args.text:
            print_diff_text_tree(pre_nodes, pre_edges, post_nodes, post_edges)
            return

        base = os.path.splitext(dot_files[0])[0]
        for dot_path in dot_files:
            with open(dot_path) as f:
                dot_content = f.read()
            nodes, edges = parse_dot_format(dot_content)
            base = os.path.splitext(dot_path)[0]
            output_path = f"{base}.{args.format}"
            try:
                result = subprocess.run(
                    ['dot', '-T', args.format, '-o', output_path],
                    input=dot_content,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"Written: {output_path}", file=sys.stderr)
                if args.view:
                    import webbrowser
                    webbrowser.open('file://' + os.path.abspath(output_path))
            except FileNotFoundError:
                print("Error: graphviz 'dot' command not found.", file=sys.stderr)
                print("Install with: sudo apt install graphviz", file=sys.stderr)
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Error running dot: {e.stderr}", file=sys.stderr)
                sys.exit(1)
        return

    print(f"Parsing {args.input}...", file=sys.stderr)
    assembler_output = run_assembler(args.input)

    nodes, edges = parse_node_format(assembler_output)
    if not nodes:
        nodes, edges = parse_dot_format(assembler_output)
    print(f"Found {len(nodes)} nodes and {len(edges)} edges", file=sys.stderr)

    if not nodes:
        print("Error: No nodes found in assembler output", file=sys.stderr)
        sys.exit(1)

    if args.text:
        print_text_tree(nodes, edges)
        return

    dot_content = generate_dot(nodes, edges)

    if args.dot:
        print(dot_content)
        return

    base_name = os.path.splitext(os.path.basename(args.input))[0]

    if args.output:
        output_path = args.output
    else:
        output_path = f"{base_name}.{args.format}"

    dot_content = generate_dot(nodes, edges)

    try:
        result = subprocess.run(
            ['dot', '-T', args.format, '-o', output_path],
            input=dot_content,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Written: {output_path}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: graphviz 'dot' command not found.", file=sys.stderr)
        print("Install with: sudo apt install graphviz", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running dot: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    if args.view:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(output_path))

if __name__ == '__main__':
    main()
