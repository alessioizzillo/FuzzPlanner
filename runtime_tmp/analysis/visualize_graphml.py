import sys
import networkx as nx
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print("Usage: python3 visualize_graphml.py <graphml file>")
    sys.exit(1)

graphml_file = sys.argv[1]

try:
    G = nx.read_graphml(graphml_file)
except FileNotFoundError:
    sys.exit(1)

pos = nx.spring_layout(G, k=1000, iterations=100000)

nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=12, font_weight='bold')

edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

plt.tight_layout()

plt.show()