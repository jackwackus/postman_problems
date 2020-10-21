#	File Created: 10/20/2020
#	Modifications and additions to code by brooksandrew

import itertools
import networkx as nx
import matplotlib.pyplot as plt
from postman_problems.turn_graph import turn_weight_function_distance, create_turn_weight_edge_attr
from postman_problems.graph import get_shortest_paths_distances, create_complete_graph, add_augmenting_path_to_graph

def create_pos_and_add_to_graph(g_full, complete_g):
    """
    Since g_full does not contain any position data,
    uses complete_g to create a position dictionary,
    and adds this data to g_full as node attributes
    Args:
        g_full (NetworkX MultiDiGraph): reconstituted graph of required and optional edges
            generated by postman_problems.graph.create_networkx_graph_from_edgelist
        complete_g (NetworkX MultiDiGraph): complete graph with all edge and node data
            generated by initialize_rpp.InnerAndOuterToEdgeListFile
    Returns:
        g_full (NetworkX MultiDiGraph): g_full with position data added to nodes
        pos (dict): node position dictionary
    """
    pos = {}
    g_full_copy = g_full.copy()
    for k in g_full.nodes():
        exec("pos[k] = (complete_g.nodes["+k+"].get('x'), complete_g.nodes["+k+"].get('y'))")
        g_full_copy.add_node(k, x = pos[k][0], y = pos[k][1])
    return g_full_copy, pos

def visualize_g_req(g_req, pos):
    """
    Plots g_req
    Args:
        g_req (NetworkX MultiDiGraph): required edge graph
            generated by postman_problems.graph.create_required_graph
        pos (dict): node position dictionary
            generated by create_pos_and_add_to_graph
    """
    fig, ax = plt.subplots()
    el = [e for e in g_req.edges(data=True)]
    nx.draw_networkx_edges(g_req, pos, edgelist=el, ax = ax)
    ax.set_xlim(left = min([pos[node][0] for node in g_req.nodes()]), right = max([pos[node][0] for node in g_req.nodes()]))
    ax.set_ylim(bottom = min([pos[node][1] for node in g_req.nodes()]), top = max([pos[node][1] for node in g_req.nodes()]))
    print('\nReconstituted Directed Graph in Solver, with Contracted Connector Edges')
    plt.show()

def make_graph_eulerian(g_req, g_full):
    """
    Directed graphs must satisfy 2 criteria to be eulerian
        strong connectivity
        in degree equals out degree for each node
    In a directed graph, the total in degree equals the total out degree
    This function augments g_req into an eulerian graph by adding edges that
    balance in degree and out degree of each node
    Args:
        g_req (NetworkX MultiDiGraph): required edge graph
            generated by postman_problems.graph.create_required_graph
        g_full (NetworkX MultiDiGraph): reconstituted graph of required and optional edges
            generated by postman_problems.graph.create_networkx_graph_from_edgelist
            augmented by create_pos_and_add_to_graph
    """
    asymmetric_nodes = []
    asymmetric_nodes_list = []
    for n in g_req.nodes():
        if g_req.in_degree(n) != g_req.out_degree(n):
            asymmetric_nodes += [(n, {'in_degree': g_req.in_degree(n), 'out_degree': g_req.out_degree(n)})]
            asymmetric_nodes_list += [n]
    nodes_to_add_out_edges = {}
    nodes_to_add_out_edges_list = []
    nodes_to_add_in_edges = {}
    nodes_to_add_in_edges_list = []
    for n in asymmetric_nodes:
        if n[1]['in_degree'] > n[1]['out_degree']:
            nodes_to_add_out_edges[n[0]] = {'edges_to_add': n[1]['in_degree']-n[1]['out_degree']}
            nodes_to_add_out_edges_list += [n[0]]
        else:
            nodes_to_add_in_edges[n[0]] = {'edges_to_add': n[1]['out_degree']-n[1]['in_degree']}
            nodes_to_add_in_edges_list += [n[0]]
    degree_matching = []
    degree_matching_depth = 1
    while len(asymmetric_nodes_list) > 0:
        degree_matching_depth += 1
        possible_degree_matching_node_pairs = []
        for (n1, n2) in itertools.combinations(asymmetric_nodes_list, 2):
            if (n1 in nodes_to_add_out_edges_list and n2 in nodes_to_add_in_edges_list) or (n1 in nodes_to_add_in_edges_list and n2 in nodes_to_add_out_edges_list):
                possible_degree_matching_node_pairs += [(n1, n2)]
        
        degree_matching_pairs_shortest_paths = get_shortest_paths_distances(g_full, possible_degree_matching_node_pairs, edge_weight_name=turn_weight_function_distance)
        g_degree_matching = create_complete_graph(degree_matching_pairs_shortest_paths, flip_weights=True)
        degree_matching_generator = list(nx.algorithms.max_weight_matching(g_degree_matching, True))
        for (n1, n2) in degree_matching_generator:
            if n1 in nodes_to_add_out_edges_list:
                degree_matching += [(n1, n2)]
                nodes_to_add_out_edges[n1]['edges_to_add']-=1
                nodes_to_add_in_edges[n2]['edges_to_add']-=1
            else:
                degree_matching += [(n2, n1)]
                nodes_to_add_out_edges[n2]['edges_to_add']-=1
                nodes_to_add_in_edges[n1]['edges_to_add']-=1
        print()
        for n in nodes_to_add_out_edges:
            if nodes_to_add_out_edges[n]['edges_to_add'] == 0 and n in nodes_to_add_out_edges_list:
                nodes_to_add_out_edges_list.remove(n)
                asymmetric_nodes_list.remove(n)
        for n in nodes_to_add_in_edges:
            if nodes_to_add_in_edges[n]['edges_to_add'] == 0 and n in nodes_to_add_in_edges_list:
                nodes_to_add_in_edges_list.remove(n)
                asymmetric_nodes_list.remove(n)
    print('Degree Matching Depth = {}'.format(degree_matching_depth))
    g_aug = add_augmenting_path_to_graph(g_req, g_full, degree_matching, edge_weight_name=turn_weight_function_distance)
    return g_aug

def is_graph_eulerian(g_aug):
    if nx.is_eulerian(g_aug):
        print('\nAugmented Graph is Eulerian\n')
    else:
        print('\nAugmented Graph is NOT Eulerian\n')
