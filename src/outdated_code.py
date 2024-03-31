def transitivity(model: gp.Model, x_var_layers, x, n_b_l):
	n_constr = 0
	for x_list in x_var_layers.values():
		if len(x_list) >= 3:
			for comb in itertools.combinations(x_list, 3):
				x2_rev, x3_rev = 1, 1
				if comb[0][1] == comb[1][0] or comb[0][1] == comb[1][1]:
					x2 = comb[1]
					x3 = comb[2]
					if comb[0][1] == comb[1][1]:
						x2_rev = -1
					if comb[0][0] == comb[2][1]:
						x3_rev = -1
				else:
					x2 = comb[2]
					x3 = comb[1]
					if comb[0][1] == comb[2][1]:
						x2_rev = -1
					if comb[0][0] == comb[1][1]:
						x3_rev = -1
				model.addConstr(x[comb[0]] + x2_rev * x[x2] - x3_rev * x[x3] + (1 - x2_rev) / 2 - (1 - x3_rev) / 2 >= 0,
								f"1t{comb[0]},{comb[1]},{comb[2]}")
				model.addConstr(
					-x[comb[0]] - x2_rev * x[x2] + x3_rev * x[x3] - (1 - x2_rev) / 2 + (1 - x3_rev) / 2 >= -1,
					f"2t{comb[0]},{comb[1]},{comb[2]}")
				n_constr += 2

	# def get_xval(i_x, j_x):
	# 	if i_x == j_x:
	# 		return 0
	# 	elif (i_x, j_x) in x:
	# 		return x[i_x, j_x]
	# 	return 1 - x[j_x, i_x]
	#
	# xsum_vars = []
	# xsum_checkvars = []
	# for name_list in n_b_l.values():
	# 	if len(name_list) > 2:
	# 		xsum_vars += name_list
	# 		xsum_checkvars += list(itertools.product(name_list, range(len(name_list))))
	# xsum = model.addVars(xsum_vars, vtype=GRB.INTEGER, name="xsum")
	# xsum_check = model.addVars(xsum_checkvars, vtype=GRB.BINARY, name="xsum_check")
	#
	# # new __transitivity
	# for node_list in n_b_l.values():
	# 	if len(node_list) >= 3:
	# 		for v in node_list:
	# 			model.addConstr(xsum[v] == sum((get_xval(v, ot) for ot in node_list)), f"2t{v}")
	# for i, x_list in n_b_l.items():
	# 	if len(x_list) >= 3:
	# 		for x_var in x_var_layers[i]:
	# 			model.addConstr(xsum[x_var[0]] != xsum[x_var[1]], f"23t{x_var}")
	return n_constr


def optimize_layout():
	if multiedge_reduction:
		c_vars, sp_c_vars = reductions.c_vars_with_crossing_var_sum_reduction(g, nodes_by_layer, edges_by_layer, 4)
		c_sp = m.addVars(sp_c_vars, vtype=GRB.BINARY, name="c_sp")
	if multiedge_reduction:
		m.setObjective(c.sum() + c_sp.sum(), GRB.MINIMIZE)

	if multiedge_reduction:
		n_constraints_generated[0] += add_multiedge_constraints(m, sp_c_vars, x, c_sp)

	if do_subg_reduction:
		cuts, crosses = reductions.kargers_algo_cut_finder(g, 50)
		contacts = []
		if not cuts:
			print("Failed to find large enough cutset for subgraph reduction")
			do_subg_reduction = False
		for i, cut in enumerate(cuts):
			contacts.append([])
			for cut_edge in crosses[i]:
				if cut_edge[0] in cut:
					contacts[i].append(cut_edge[0])
				else:
					contacts[i].append(cut_edge[1])
			g.stack_subgraph(set(cut), [g.edge_ids[ed[0], ed[1]] for ed in crosses[i]])

		gp_layers = g_prime.get_ids_by_layer()
		for node_list in gp_layers.values():
			for nn1, nn2 in itertools.combinations(node_list, 2):
				if g_prime.node_ids[nn1].y < g_prime.node_ids[nn2].y:
					x_vars_opt[nn1, nn2] = 1
				else:
					x_vars_opt[nn1, nn2] = 0
		for level, node_list in g.get_ids_by_layer().items():
			if level in gp_layers:
				stack_nodes = [node.id for node in g.big_stack_nodes[i] if node.layer == level]
				for stack_node in stack_nodes:
					for gp_node in gp_layers[level]:
						for node in node_list:
							if node != stack_node:
								if (stack_node, node) in x_vars_opt:
									x_vars_opt[gp_node, node] = x_vars_opt[stack_node, node]
								else:
									x_vars_opt[node, gp_node] = x_vars_opt[node, stack_node]
					for node in node_list:
						if node != stack_node:
							if (stack_node, node) in x_vars_opt:
								del x_vars_opt[stack_node, node]
							else:
								del x_vars_opt[node, stack_node]
		g.unstack_graph_nodes(i)
	g.unstack_all_graph_edges()


def add_multiedge_constraints(model: gp.Model, sp_c_vars, x, c_sp):
	n_constraints = 0
	for sp_c_var in sp_c_vars:
		n_val = len(sp_c_var[1])
		expr1 = gp.LinExpr(0)
		for edv in sp_c_var[1]:
			if sp_c_var[0][1] == edv[1]:
				expr1 -= 1
		expr2 = gp.LinExpr(0)
		for edge in sp_c_var[1]:
			if sp_c_var[0][1] != edge[1]:
				if (sp_c_var[0][0], sp_c_var[1][0][0]) in x:
					if (sp_c_var[0][1], edge[1]) in x:
						expr1 -= x[sp_c_var[0][1], edge[1]]
						expr2 += x[sp_c_var[0][1], edge[1]]
					else:
						expr1 -= 1 - x[edge[1], sp_c_var[0][1]]
						expr2 += 1 - x[edge[1], sp_c_var[0][1]]
				else:
					if (sp_c_var[0][1], edge[1]) in x:
						expr1 -= 1 - x[sp_c_var[0][1], edge[1]]
						expr2 += 1 - x[sp_c_var[0][1], edge[1]]
					else:
						expr1 -= x[edge[1], sp_c_var[0][1]]
						expr2 += x[edge[1], sp_c_var[0][1]]
		if (sp_c_var[0][0], sp_c_var[1][0][0]) in x:
			# print(f"{x[sp_c_var[0][0], sp_c_var[1][0][0]]} = 1 ==> c_sp[{sp_c_var}] >= {expr1}")
			# model.addGenConstrIndicator(x[sp_c_var[0][0], sp_c_var[1][0][0]], True, c_sp[sp_c_var] >= expr1)
			# model.addGenConstrIndicator(x[sp_c_var[0][0], sp_c_var[1][0][0]], False, c_sp[sp_c_var] >= expr2)
			expr1 += n_val * x[sp_c_var[0][0], sp_c_var[1][0][0]]
			expr2 -= n_val * x[sp_c_var[0][0], sp_c_var[1][0][0]]
		else:
			# model.addGenConstrIndicator(x[sp_c_var[1][0][0], sp_c_var[0][0]], False, c_sp[sp_c_var] >= expr1)
			# model.addGenConstrIndicator(x[sp_c_var[1][0][0], sp_c_var[0][0]], True, c_sp[sp_c_var] >= expr2)
			expr1 += n_val * x[sp_c_var[1][0][0], sp_c_var[0][0]]
			expr2 -= n_val * x[sp_c_var[1][0][0], sp_c_var[0][0]]
		model.addConstr(c_sp[sp_c_var] >= expr1)
		model.addConstr(c_sp[sp_c_var] >= expr2)
		# print(sp_c_var, expr1, expr2)
		n_constraints += 2
	return n_constraints


if m.IsMIP == 0:
	print('The model is not an integer program')

# Set a 2 second time limit
m.Params.TimeLimit = 20

# Now solve the model with different values of MIPFocus
m.optimize()
best_gap = m.MIPGap
best_focus = 0
print(m.MIPGap)
for i in range(1, 4):
	m.reset()
	m.Params.MIPFocus = i
	m.optimize()
	print(m.MIPGap)
	if m.MIPGap < best_gap:
		best_gap = m.MIPGap
		best_focus = i
m.Params.TimeLimit = float('inf')
m.Params.MIPFocus = best_focus
m.optimize()
print('Solved with MIPFocus: %d' % m.Params.MIPFocus)


""" ALTAIR CHART STUFF """
def make_altair_chart_for_ind_var():
    data = experiments.read_data_from_file("independent_var_study.csv", ',')
    data = [dat for dat in data if dat["opttime"] < 120 and dat["iterations"] > 0]
    print(len(data))
    for dat in data:
        dat['file'] = dat['file'][:dat['file'].index('/')]
        dat['xpc'] = dat['xvars'] + dat['cvars']
    vis.draw_altair_scatter(data, "xpc", "opttime", "file", "X-vars + c-vars", "Time (s)", "Decision variables vs time to optimize")
    vis.draw_altair_scatter(data, "xpc", "iterations", "file", "X-vars + c-vars", "Simplex iterations", "Decision variables vs iterations")

def make_altair_chart_all_three(experiment_name):
    full_data = []
    for formulation in ["junger_basic", "vertical_transitivity", "redundancy"]:
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        data = [dat for dat in data if dat["Opttime"] > 0]
        tag_data(data, "formulation", formulation)
        full_data.extend(data)
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    for data_pt in full_data:
        data_pt["Total nodes"] = info[data_pt["Index"] - 1]["Total Nodes"]
    vis.draw_altair_scatter(data, x_axis="Total nodes", y_axis="Opttime", color_field="formulation", x_title="Nodes", y_title="Time (s)", chart_name="Total nodes vs. time to optimize", log_y_scale=True, plot_loess=True, loess_features=["junger_basic", "vertical_transitivity", "redundancy"])

    data_pt["L2 constant"] = info[data_pt["Index"] - 1]["L2 constant"]
    vis.draw_altair_scatter(full_data, x_axis="Total nodes", y_axis="Opttime", color_field="formulation", x_title="L2",
                        y_title="Time (s)", chart_name="Total nodes vs. time to optimize", log_y_scale=True,
                        plot_loess=True, loess_features=["junger_basic", "vertical_transitivity", "redundancy"])


def altair_windowed_median(experiment_name, chart_name):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    # clean_names = {"junger_basic": "Junger", "vertical_transitivity": "Stratisfimal"}
    for formulation in ["junger_basic", "vertical_transitivity", "redundancy"]:
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        # data = [dat for dat in data if dat["Opttime"] > 0]
        new_data = [{"noderange": i, "times": [], "formulation": formulation} for i in range(0, 301, 25)]
        for data_pt in data:
            new_data[info[data_pt["Index"] - 1]["Total Nodes"] // 25]["times"].append(data_pt["Opttime"])
        removals = []
        for i in range(13):
            if len(new_data[i]["times"]) > 0:
                optt_s = sorted(new_data[i]["times"])
                new_data[i]["median"] = optt_s[len(optt_s) // 2]
                # new_data[i]["median"] = sum(optt_s)/len(optt_s)
            else:
                removals.append(i)
        new_data = [nd for idx, nd in enumerate(new_data) if idx not in removals]
        full_data.extend(new_data)
    vis.draw_altair_line_chart(full_data, x_axis="noderange", y_axis="median", color_field="formulation", x_title="Nodes", y_title="Time (s)", chart_name=chart_name, log_y_scale=True)


def altair_windowed_median_paper_forms(chart_name):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    clean_names = {"junger": "Junger", "strat": "Stratisfimal", "sankey": "Sankey", "my_form": "Our Formulation"}
    for formulation in ["junger", "strat", "sankey", "my_form"]:
        data = read_data_from_file(f"{formulation}_actual.csv", ',')
        # data = [dat for dat in data if dat["Opttime"] > 0]
        new_data = [{"noderange": i, "times": [], "Formulation": clean_names[formulation]} for i in range(0, 301, 25)]
        for data_pt in data:
            new_data[info[data_pt["Index"] - 1]["Total Nodes"] // 25]["times"].append(data_pt["Opttime"])
        removals = []
        for i in range(13):
            if len(new_data[i]["times"]) > 0:
                optt_s = sorted(new_data[i]["times"])
                new_data[i]["median"] = optt_s[len(optt_s) // 2]
                # new_data[i]["median"] = sum(optt_s)/len(optt_s)
            else:
                removals.append(i)
        new_data = [nd for idx, nd in enumerate(new_data) if idx not in removals]
        full_data.extend(new_data)
    vis.draw_altair_line_chart(full_data, x_axis="noderange", y_axis="median", color_field="Formulation", x_title="Nodes", y_title="Time (s)", chart_name=chart_name, log_y_scale=True)


def compare_to_baseline(experiment_name, chart_name, just_two=True):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    clean_names = {"junger_basic": "Junger", "vertical_transitivity": "Stratisfimal", "redundancy": "Redundant"}
    if just_two:
        formulations = ["junger_basic", "vertical_transitivity"]
    else:
        formulations = ["junger_basic", "vertical_transitivity", "redundancy"]
    for formulation in formulations:
        b_data = read_data_from_file(f"{formulation}/baseline.csv", ',')
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        keepers = [i for i, v in enumerate(b_data) if 0 < v["Opttime"] < 300]
        keepers = [i for i in keepers if data[i]["Opttime"] > 0]
        data = [dat for i, dat in enumerate(data) if i in keepers]
        b_data = [dat for i, dat in enumerate(b_data) if i in keepers]
        for i, data_pt in enumerate(data):
            data_pt["speedup"] = 100 * round(b_data[i]["Opttime"] / data_pt["Opttime"], 3)
            data_pt["Formulation"] = clean_names[formulation]
        full_data.extend(data)
    for data_pt in full_data:
        data_pt["Total nodes"] = info[data_pt["Index"] - 1]["Total Nodes"]
    vis.draw_altair_line_compare(full_data, x_axis="Total nodes", y_axis="speedup", facet_field="Formulation",
                                 x_title="Nodes", y_title="Speedup (% of baseline)", chart_name=chart_name,
                                 log_y_scale=False, experiment_name=experiment_name)


def compare_to_baseline_percent_solved(experiment_name, chart_name, just_two=True):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    clean_names = {"junger_basic": "Junger", "vertical_transitivity": "Stratisfimal"}
    if just_two:
        formulations = ["junger_basic", "vertical_transitivity"]
    else:
        formulations = ["junger_basic", "vertical_transitivity", "redundancy"]
    for formulation in formulations:
        b_data = read_data_from_file(f"{formulation}/baseline.csv", ',')
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        keepers = [i for i, v in enumerate(b_data) if
                   0 < v["Opttime"] and info[v["Index"] - 1]["Default #crossings"] != info[v["Index"] - 1]["Crossing#"]]
        keepers = [i for i in keepers if data[i]["Opttime"] > 0]
        data = [dat for i, dat in enumerate(data) if i in keepers]
        b_data = [dat for i, dat in enumerate(b_data) if i in keepers]
        for i, data_pt in enumerate(data):
            data_pt["Percent"] = 100 * (info[data_pt["Index"] - 1]["Default #crossings"] - data_pt["Crossings"]) / (
                        info[data_pt["Index"] - 1]["Default #crossings"] - info[data_pt["Index"] - 1]["Crossing#"])
            data_pt["Formulation"] = clean_names[formulation]
            data_pt["Experiment"] = experiment_name
            b_data[i]["Percent"] = 100 * (info[data_pt["Index"] - 1]["Default #crossings"] - b_data[i]["Crossings"]) / (
                        info[data_pt["Index"] - 1]["Default #crossings"] - info[data_pt["Index"] - 1]["Crossing#"])
            b_data[i]["Formulation"] = clean_names[formulation]
            b_data[i]["Experiment"] = "baseline"
        full_data.extend(data)
        full_data.extend(b_data)
    for data_pt in full_data:
        data_pt["Total nodes"] = info[data_pt["Index"] - 1]["Total Nodes"]
    vis.draw_altair_colored_line_compare(full_data, x_axis="Total nodes", y_axis="Percent", facet_field="Formulation",
                                         color_field="Experiment", x_title="Nodes", y_title="% Solved",
                                         chart_name=chart_name)


def compare_to_baseline_butterfly_colored(experiment_name, chart_name):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    clean_names = {"junger_basic": "Junger", "vertical_transitivity": "Stratisfimal"}
    for formulation in ["junger_basic", "vertical_transitivity"]:
        b_data = read_data_from_file(f"{formulation}/baseline.csv", ',')
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        keepers = [i for i, v in enumerate(b_data) if 0 < v["Opttime"] < 300]
        keepers = [i for i in keepers if data[i]["Opttime"] > 0]
        data = [dat for i, dat in enumerate(data) if i in keepers]
        b_data = [dat for i, dat in enumerate(b_data) if i in keepers]
        for i, data_pt in enumerate(data):
            data_pt["speedup"] = 100 * round(b_data[i]["Opttime"] / data_pt["Opttime"], 3)
            data_pt["Formulation"] = clean_names[formulation]
        full_data.extend(data)
    for data_pt in full_data:
        data_pt["Total nodes"] = info[data_pt["Index"] - 1]["Total Nodes"]
        data_pt["Has butterfly"] = "Yes" if info[data_pt["Index"] - 1]["Butterflies"] > 0 else "No"
    vis.draw_altair_colored_line_compare(full_data, x_axis="Total nodes", y_axis="speedup", facet_field="Formulation",
                                         color_field="Has butterfly", x_title="Nodes",
                                         y_title="Speedup (% of baseline)", chart_name=chart_name)


def compare_to_baseline_presolve_colored(experiment_name, chart_name):
    full_data = []
    info = read_data_from_file("experiment_set_50_info.csv", ',')
    clean_names = {"junger_basic": "Junger", "vertical_transitivity": "Stratisfimal"}
    for formulation in ["junger_basic", "vertical_transitivity"]:
        b_data = read_data_from_file(f"{formulation}/baseline.csv", ',')
        data = read_data_from_file(f"{formulation}/{experiment_name}.csv", ',')
        keepers = [i for i, v in enumerate(b_data) if 0 < v["Opttime"] < 300]
        keepers = [i for i in keepers if data[i]["Opttime"] > 0]
        data = [dat for i, dat in enumerate(data) if i in keepers]
        b_data = [dat for i, dat in enumerate(b_data) if i in keepers]
        for i, data_pt in enumerate(data):
            data_pt["speedup"] = 100 * round(b_data[i]["Opttime"] / data_pt["Opttime"], 3)
            data_pt["Formulation"] = clean_names[formulation]
            data_pt["Solved at Root Node"] = "Both" if b_data[i]["Nodes visited"] == 1.0 and data_pt[
                "Nodes visited"] == 1.0 else "Just Presolve Version" if data_pt["Nodes visited"] == 1.0 else "Neither"
        full_data.extend(data)
    for data_pt in full_data:
        data_pt["Total nodes"] = info[data_pt["Index"] - 1]["Total Nodes"]
    vis.draw_altair_colored_line_compare(full_data, x_axis="Total nodes", y_axis="speedup", facet_field="Formulation",
                                         color_field="Solved at Root Node", x_title="Nodes",
                                         y_title="Speedup (% of baseline)", chart_name=chart_name)


