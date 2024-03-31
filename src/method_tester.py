from src import graph, read_data
import experiments


# import graph_tool.all as gt
# from sklearn.cluster import SpectralClustering


def make_graph():
	eg1 = graph.LayeredGraph()
	eg1.add_nodes([(1,1), (2,2), (3,2), (4, 2), (5, 3), (6, 3), (7, 4), (8, 2), (9, 2), (10, 2), (11, 3)])
	eg1.add_edges([(1, 2), (1, 3), (1, 5), (4, 6), (4, 5), (5, 6), (2, 7), (6, 7), (1, 8), (8,11), (1,9), (9,11), (10, 5), (8, 6), (9, 6), (10, 11), (8,5)])
	return eg1


# def layered_graph_to_gtool(lg):
# 	new_g = gt.Graph(directed=False)
# 	new_g.add_vertex(len(lg.nodes))
# 	for edge in lg.edges:
# 		new_g.add_edge(edge.n1.name - 1, edge.n2.name - 1)
# 	return new_g


def adj_matrix(lg):
	new_matrix = [[0]*len(lg.nodes) for i in range(len(lg.nodes))]
	for v, l in lg.adj_list.items():
		for u in l:
			new_matrix[v-1][u-1] = 1
			new_matrix[u-1][v-1] = 1
	return new_matrix


if __name__ == '__main__':
	""" reopen all 60sec files and sort by total nodes """
	# with open(inp, 'r') as fd:
	# 	fdl = list(fd.readlines())
	# ghash = {}
	# for gfl in fdl:
	# 	lne = gfl.split(',')
	# 	if lne[3] not in ghash:
	# 		ghash[lne[3]] = []
	# 	ghash[lne[3]].append(lne[1])
	# all_g = experiments.get_all_graphs()
	# tnd = []
	# for i in range(3):
	# 	tnd.append([])
	# 	for gr in all_g[i]:
	# 		my_g = read_data.read(gr)
	# 		tnd[i].append((gr, len(my_g.nodes)))

	""" recalculate graphs """
	all_g = experiments.get_all_graphs()
	rome_g = []
	for gr in all_g[0]:
		my_g = read_data.read(gr)
		rome_g.append((gr, len(my_g.nodes)))
	rome_g.sort(key=lambda x: x[1])
	with open("../data storage/rome_sorted.txt", 'w') as fd:
		fd.write("Total nodes in [0,10):\n")
		for i in range(len(rome_g)):
			if i > 0 and rome_g[i][1]//10 > rome_g[i-1][1]//10:
				fd.write(f"Total nodes in [{rome_g[i][1]//10*10},{rome_g[i][1]//10*10+10}):\n")
			fd.write(f"{rome_g[i][0]},{rome_g[i][1]}\n")
	dagmar_g = []
	for gr in all_g[1]:
		my_g = read_data.read(gr)
		dagmar_g.append((gr, len(my_g.nodes)))
	dagmar_g.sort(key=lambda x: x[1])
	with open("../data storage/dagmar_sorted.txt", 'w') as fd:
		for i in range(len(dagmar_g)):
			if i > 0 and dagmar_g[i][1] // 10 > dagmar_g[i - 1][1] // 10:
				fd.write(f"Total nodes in [{dagmar_g[i][1] // 10 * 10},{dagmar_g[i][1] // 10 * 10 + 10}):\n")
			fd.write(f"{dagmar_g[i][0]},{dagmar_g[i][1]}\n")
	north_g = []
	for gr in all_g[0]:
		my_g = read_data.read(gr)
		north_g.append((gr, len(my_g.nodes)))
	north_g.sort(key=lambda x: x[1])
	with open("../data storage/north_sorted.txt", 'w') as fd:
		fd.write("Total nodes in [0,10):\n")
		for i in range(len(north_g)):
			if i > 0 and north_g[i][1] // 10 > north_g[i - 1][1] // 10:
				fd.write(f"Total nodes in [{north_g[i][1] // 10 * 10},{north_g[i][1] // 10 * 10 + 10}):\n")
			fd.write(f"{north_g[i][0]},{north_g[i][1]}\n")

	""" store all graphs in new file sorted by total nodes """
	# with open("../data storage/rome_sorted.txt", 'w') as fd:
	# 	fd.write("Total nodes in [0,10):\n")
	# 	for i in range(len(rome_g)):
	# 		if i > 0 and rome_g[i][1]//10 > rome_g[i-1][1]//10:
	# 			fd.write(f"Total nodes in [{rome_g[i][1]//10*10},{rome_g[i][1]//10*10+10}):\n")

	# g = make_graph()
	# g, tvert = read_rome_data.create_better_layered_graph("graficon80nodi/grafo5015.80", 4, 2)
	# g.adj_list = g.create_normal_adj_list()

	# vis.draw_graph(g, "example", nested=True)
	# reductions.kargers_algo_cut_finder(g)

	# g.y_val_setup()
	# vis.draw_graph(g, "example1", nested=True)
	# g.barycentric_reordering(5)
	# vis.draw_graph(g, "example2", nested=True)

	# g.add_anchors()

	# g_p = layered_graph_to_gtool(g)
	# state = gt.minimize_nested_blockmodel_dl(g_p)
	# state.draw_graph(output="testing.svg")
	# state.print_summary()

	# ebl = g.get_edge_ids_by_layer()
	# nbl = g.get_ids_by_layer()
	# x1 = reductions.normal_c_vars(ebl)
	# print([[a,b,c,d] for ((a, b), (c, d)) in x1])
	# x,y = reductions.c_vars_with_crossing_var_sum_reduction(g, nbl, ebl, 3)
	# print([[a,b,c,d] for ((a, b), (c, d)) in x])
	# print(y)

	# cluster = SpectralClustering(n_clusters=4, assign_labels="discretize", affinity="precomputed").fit(adj_matrix(g))
	# crosses = []
	# for edge in g.edges:
	# 	if cluster.labels_[edge.n1.name-1] != cluster.labels_[edge.n2.name-1]:
	# 		crosses.append(edge)
	# vis.draw_graph(g, "example00", nested=True, groups=cluster.labels_)
	# subgraphs = [set(node.name for node in g.nodes if cluster.labels_[node.name - 1] == i) for i in range(4)]
	# g.stack_entire_graph(subgraphs)
	# vis.draw_graph(g, "example000", nested=True)
