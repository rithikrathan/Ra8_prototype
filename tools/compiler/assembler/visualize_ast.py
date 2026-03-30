#!/usr/bin/env python3
"""
Visualize the AST output from the assembler as a graph.

Usage:
    ./visualize_ast.py test.asm            # creates test.asm.dot
    ./visualize_ast.py test.asm -o out.pdf # renders to PDF (requires graphviz system package)
    ./visualize_ast.py test.asm -f svg     # creates test.asm.svg (requires graphviz)
    ./visualize_ast.py test.asm --text    # prints text tree to stdout
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
    
    node_pattern = re.compile(r'(\d+)\s*\[label="([^"]+)"\s*shape=box\];')
    edge_pattern = re.compile(r'(\d+)\s*->\s*(\d+);')
    
    for line in text.split('\n'):
        line = line.strip()
        
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

def build_tree(nodes, edges, root_id=0, parent=None, indent=0, visited=None):
    """Build tree representation as list of (indent, label) tuples."""
    if visited is None:
        visited = set()
    
    lines = []
    
    if root_id in visited:
        return lines
    
    if root_id not in nodes:
        return lines
    
    visited.add(root_id)
    label = nodes[root_id].split('\n')[0]
    lines.append((indent, label))
    
    children = [to_id for (fr, to_id) in edges if fr == root_id and to_id not in visited]
    for child_id in children:
        lines.extend(build_tree(nodes, edges, child_id, root_id, indent + 1, visited))
    
    return lines

def print_text_tree(nodes, edges):
    """Print tree as ASCII art."""
    lines = build_tree(nodes, edges)
    for indent, label in lines:
        prefix = "│   " * (indent - 1) + "├── " if indent > 0 else ""
        print(prefix + label)

def create_graphviz(nodes, edges):
    """Create a graphviz digraph from parsed nodes and edges."""
    try:
        from graphviz import Digraph
    except ImportError:
        return None
    
    dot = Digraph(comment='AST')
    dot.attr(rankdir='TB', splines='ortho')
    
    for node_id, label in nodes.items():
        if '\n' in label:
            label_html = '<BR/>'.join(label.split('\n'))
            dot.node(str(node_id), f'<{label_html}>', shape='box', style='rounded,filled', fillcolor='#f0f0f0')
        else:
            dot.node(str(node_id), label, shape='box', style='rounded,filled', fillcolor='#f0f0f0')
    
    for from_id, to_id in edges:
        dot.edge(str(from_id), str(to_id))
    
    return dot

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
    parser.add_argument('-f', '--format', default='dot', 
                       choices=['png', 'pdf', 'svg', 'dot'],
                       help='Output format (default: dot)')
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
    
    dot = create_graphviz(nodes, edges)
    
    if dot is None:
        print("Error: graphviz Python package not installed.", file=sys.stderr)
        print("Run: pip install graphviz", file=sys.stderr)
        print("\nFalling back to DOT format output:", file=sys.stderr)
        print(dot.source if dot else assembler_output)
        return
    
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    
    if args.output:
        output_path = args.output
    else:
        output_path = f"{base_name}.{args.format}"
    
    try:
        dot.render(output_path, format=args.format, cleanup=True)
        print(f"Written: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error rendering graph: {e}", file=sys.stderr)
        print("The graphviz system package may not be installed.", file=sys.stderr)
        print("Try: sudo apt install graphviz", file=sys.stderr)
        print("\nFalling back to DOT format:", file=sys.stderr)
        with open(output_path if args.output else f"{base_name}.dot", 'w') as f:
            f.write(dot.source)
        print(f"Written: {base_name}.dot", file=sys.stderr)
        return
    
    if args.view:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(output_path))

if __name__ == '__main__':
    main()
