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
    
    edge_pattern = re.compile(r'(\d+)\s*->\s*(\d+);')
    
    for line in text.split('\n'):
        line = line.strip()
        
        if 'shape=box' in line and '[label=' in line:
            id_match = re.match(r'(\d+)', line)
            if id_match:
                node_id = int(id_match.group(1))
                label_start = line.find('[label="') + 8
                label_end = line.rfind('" shape=box')
                if label_start > 7 and label_end > label_start:
                    label = line[label_start:label_end].replace('\\n', '\n')
                    nodes[node_id] = label
                    continue
        
        edge_match = edge_pattern.match(line)
        if edge_match:
            from_id = int(edge_match.group(1))
            to_id = int(edge_match.group(2))
            edges.append((from_id, to_id))
    
    return nodes, edges

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[32m"
ANSI_CYAN = "\033[36m"

TREE_VERTICAL = "│   "
TREE_BRANCH = "├── "
TREE_LAST = "└── "

def print_node(node_id, nodes, edges, prefix, is_last, prefixes, active_verticals):
    if node_id in prefixes:
        return
    prefixes.add(node_id)

    label = nodes[node_id]
    parts = label.split('\n')

    type_name = ""
    name_value = ""
    for part in parts:
        if ': ' in part:
            key, value = part.split(': ', 1)
            if key == 'type':
                type_name = value
            elif key == 'name' or key == 'value':
                name_value = value

    connector = TREE_LAST if is_last else TREE_BRANCH
    if name_value:
        print(f"{prefix}{connector}{ANSI_BOLD}{type_name}: {name_value}{ANSI_RESET}")
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
    parser.add_argument('--view', action='store_true',
                       help='Open the output file after rendering')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsing {args.input}...", file=sys.stderr)
    assembler_output = run_assembler(args.input)
    
    nodes, edges = parse_dot_format(assembler_output)
    print(f"Found {len(nodes)} nodes and {len(edges)} edges", file=sys.stderr)
    
    if not nodes:
        print("Error: No nodes found in assembler output", file=sys.stderr)
        sys.exit(1)
    
    if args.text:
        print_text_tree(nodes, edges)
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
