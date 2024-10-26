from pathlib import Path
from itertools import chain
import tempfile
import nbformat
import networkx as nx

from .nb_utils import parse_hash, find_tagged_cell, find_section

def search_node(G, node_query, first_only=True):
  nodes = []
  for node in G.nodes:
    if node_query.lower() in node.lower():
      nodes.append(node)
  
  if nodes and first_only:
    return nodes[0]
  else:
    return nodes

def build_full_graph(repo_dir=None):
  if repo_dir is None:
    import subprocess
    repo_dir = subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
    repo_dir = repo_dir.decode("utf-8").strip()
  nb_paths = Path(repo_dir).rglob("*.ipynb")  
  G = nx.DiGraph(repo_dir=repo_dir)


  for nb_path in nb_paths:      
    nb = nbformat.read(nb_path, as_version=4)
    nb_cells = nb.cells
    input_cells = []
    output_cells = []

    # find the input and output cells
    input_cells = find_tagged_cell(nb_cells, "indata")
    if not input_cells:
      input_cells= find_section(nb_cells, "data")
    
    output_cells = find_tagged_cell(nb_cells, "outdata")
    if not output_cells:
      output_cells = find_section(nb_cells, "export")

    # only add node to graph if it has input OR output cells
    if not input_cells and not output_cells:
      continue
    
    nb_label = nb_path.stem
    G.add_node(nb_label, node_type="nb")
    # parse the input and output cells
    input_hashes = list(chain.from_iterable(map(parse_hash, input_cells)))
    output_hashes = list(chain.from_iterable(map(parse_hash, output_cells)))

    for input_hash, input_path in input_hashes:
      ihash = input_hash[:7]
      if not G.has_node(ihash):
        G.add_node(ihash, file_path=input_path, node_type="data", sha1=input_hash)
      G.add_edge(ihash, nb_label)
    
    for output_hash, output_path in output_hashes:
      ohash = output_hash[:7]
      if not G.has_node(ohash):
        G.add_node(ohash, file_path=output_path, node_type="data", sha1=output_hash)
      G.add_edge(nb_label, ohash)
    
  return G

def build_subgraph(G, target: str, depth=None):
  tgt_node = None
  for node_x in G.nodes:
    if target in node_x:
      tgt_node = node_x
      break  
  
  if not tgt_node:
    raise ValueError(f"Node {target} not found in graph")
  
  rev_edges = nx.bfs_edges(G, tgt_node, reverse=True, depth_limit=depth)
  fwd_edges = nx.bfs_edges(G, tgt_node, reverse=False, depth_limit=depth)
  visited_edges = [(x[1], x[0]) for x in rev_edges] + list(fwd_edges)  
  sG = G.edge_subgraph([(x[0], x[1]) for x in visited_edges])
  return sG

def visualize(G, hide_label=True):
  import pydot
  pydot_G = pydot.Dot()
  pydot_G.set_edge_defaults(arrowsize=.2)
  
  for node_x in G.nodes:
    node_data = G.nodes[node_x]

    if node_data["node_type"] == "nb":
      pydot_node = pydot.Node(node_x, color="red", shape="ellipse")
    else:
      pydot_node = pydot.Node(node_x, color="blue", shape="box")
    
    if hide_label:
      pydot_node.set_label("") # type: ignore

    pydot_G.add_node(pydot_node)

  for edge_x in G.edges:
    pydot_edge = pydot.Edge(edge_x[0], edge_x[1])
    pydot_G.add_edge(pydot_edge)

  fd, path = tempfile.mkstemp(suffix=".png")
  pydot_G.write_png(path)  # type: ignore
  return path

def data_deps(G, target: str, depth=None):
  sG = build_subgraph(G, target, depth)
  vpath = visualize(sG, hide_label=False)
  return vpath, sG