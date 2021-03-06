# -*- coding: utf-8 -*-

import numpy as np
import graphviz
import pydotplus
import os
import sys

from time import time
from Join_Tool import get_join_order, join
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from IPython.display import Image
from Graph import Graphs

"""
解析数据
"""


def paserData(datafilePath):
    vtx = {}
    edge = {}
    label_set = []
    graphId = -1
    data = open(datafilePath)
    while True:
        line = data.readline().strip("\n")
        if not line: break
        if "#" in line:
            id = line.split(" ")[-1]
            graphId = int(id)
            if graphId not in vtx:
                vtx[graphId] = []
            if graphId not in edge:
                edge[graphId] = []
        if "v" in line:
            item = line.split(" ")[1:]
            vtx_item = [int(i) for i in item]
            vtx[graphId].append(vtx_item)
            label_set.append(vtx_item[1])
            # if vtx_item[1] == 51:
            #     print(graphId)
            #     print(vtx_item)
        if "e" in line:
            item = line.split(" ")[1:]
            edge_item = [int(i) for i in item]
            edge[graphId].append(edge_item)
    return vtx, edge, set(label_set)


# 获取图中所有顶点的label编码
def coding_label(label_set):
    max_label = max(label_set)
    label_list = [i for i in range(0, max_label + 1)]
    label_map = {}
    for label in label_list:
        coding = [0] * len(label_list)
        coding[label_list.index(label)] = 1
        label_map.update({label: coding})
    return label_map


# 计算顶点v的邻居节点
def get_graph_neb(edges, vtxs):
    vtxs = [vtx[0] for vtx in vtxs]
    graph = {}.fromkeys(vtxs)
    for vtx in vtxs:
        graph[vtx] = []
    for edge in edges:
        graph[edge[0]].append(edge[1])
    return graph


# 获取邻居N编码
def get_abj_coding(neb_nodes, label_codes, vtxs_label):
    coding_list = [0] * len(label_codes[0])
    for node in neb_nodes:
        node_label = vtxs_label[node]
        node_code = label_codes[node_label]
        for i in range(len(coding_list)):
            coding_list[i] = coding_list[i] + node_code[i]
    return coding_list


# 计算顶点特征值
def get_node_Eigenvalues(vtx_id, graph, n):
    seq_list = [vtx_id]
    nodes_set = [vtx_id]
    sub_graph = {}
    while n:
        tmp_nodes = []
        for node in seq_list:
            adj_node = list(graph[node])
            tmp_nodes.extend(adj_node)
            nodes_set.extend(adj_node)
            sub_graph[node] = adj_node
        seq_list = tmp_nodes
        n -= 1
    node_nub = len(nodes_set)
    adj_matrix = [[0] * node_nub] * node_nub
    for vtx in sub_graph.keys():
        i = nodes_set.index(vtx)
        adj_node = sub_graph[vtx]
        for node in adj_node:
            adj_matrix[i][nodes_set.index(node)] = 1
    R = np.array(adj_matrix)
    a, b = np.linalg.eig(R)
    a = sorted(a, reverse=True)
    if len(a) < 2: a.append(0.0)
    return a


# 获取图集中最大的图的id和顶点数量
def find_max_vtxs(dataVtx):
    max_vtx_mub = 0
    id = 0
    for key, value in dataVtx.iteritems():
        if max_vtx_mub < len(value):
            id = key
            max_vtx_mub = len(value)
    return id, max_vtx_mub
    pass


# def recurse(tree, node_id, vtx, parent=None, depth=0):
#     print "tree threshold"
#     print tree.threshold
#     print "tree feature"
#     print tree.feature
#     print "tree children_left"
#     print tree.children_left
#     print "tree children_right"
#     print tree.children_right
#     print "tree value in node"
#     print tree.value
#
#     if node_id == -1:
#         return tree.value[parent]
#     threshold = tree.threshold[node_id]
#     feature = tree.feature[node_id]
#     if feature < 51:
#         if vtx[feature] > threshold:
#             children = tree.children_right[node_id]
#         else:
#             children = tree.children_left[node_id]
#         recurse(tree, children, vtx, node_id, depth=depth + 1)
#     else:
#         if vtx[feature] > threshold:
#             children = tree.children_right[node_id]
#             recurse(tree, children, vtx, node_id, depth=depth + 1)
#         else:
#             recurse(tree, tree.children_right[node_id], vtx, node_id, depth=depth + 1)
#             recurse(tree, tree.children_left[node_id], vtx, node_id, depth=depth + 1)

def recurse(tree, node_id, vtx, parent=None, depth=0):
    if node_id == -1:
        yield tree.value[parent]
        return
    threshold = tree.threshold[node_id]
    feature = tree.feature[node_id]
    if feature < 60:
        if vtx[feature] > threshold:
            children = tree.children_right[node_id]
        else:
            children = tree.children_left[node_id]
        for item in recurse(tree, children, vtx, node_id, depth=depth + 1):
            yield item
    else:
        if vtx[feature] > threshold:
            children = tree.children_right[node_id]
            for item in recurse(tree, children, vtx, node_id, depth=depth + 1):
                yield item
        else:
            for item in recurse(tree, tree.children_right[node_id], vtx, node_id, depth=depth + 1):
                yield item
            for item in recurse(tree, tree.children_left[node_id], vtx, node_id, depth=depth + 1):
                yield item


def paser_DT(id, vtx_nub, graph_vtxs_coding):
    # id = 0
    graph_0 = graph_vtxs_coding[id]
    Y = [i[0] for i in graph_0]
    X = []
    for item in graph_0:
        tmp = []
        for i in range(1, len(item)):
            tmp.extend(item[i])
        X.append(tmp)
    a = [len(i) for i in X]
    model_tree = DecisionTreeClassifier()
    model_tree.fit(X, Y)
    dot_data = tree.export_graphviz(model_tree, out_file=None)
    print(dot_data)
    graph = pydotplus.graph_from_dot_data(dot_data)
    graph_name = "ID_%s_%s.pdf" % (str(id), str(vtx_nub))
    graph.write_pdf('./DT-PDF/' + graph_name)
    pass


def coding_graph(dataVtx, dataEdge, label_codes):
    graph_vtxs_coding = {}
    for key in dataVtx.keys():
        vtxs_coding = []
        vtxs = dataVtx[key]
        edges = dataEdge[key]
        vtxs_label = {vtx[0]: vtx[1] for vtx in vtxs}
        neb_dict = get_graph_neb(edges, vtxs)
        graph = get_graph_neb(edges, vtxs)
        for vtx in vtxs:
            vtx_id = vtx[0]
            vtx_label = vtx[1]
            neb_nodes = neb_dict[vtx_id]
            node_L = label_codes[vtx_label]
            node_N = get_abj_coding(neb_nodes, label_codes, vtxs_label)
            node_Eigenvalues = get_node_Eigenvalues(vtx_id, graph, 1)
            vtxs_coding.append([vtx[0], node_L, node_N, node_Eigenvalues[0:2]])
        graph_vtxs_coding[key] = vtxs_coding
    return graph_vtxs_coding


"""
aggregation garph conding ,{id,[X,Y]}
"""


def agg_garph_coding(data_graph_vtxs_coding):
    graph_X_Y = {}
    for key, value in data_graph_vtxs_coding.iteritems():
        Y = [i[0] for i in value]
        X = []
        for item in value:
            tmp = []
            for i in range(1, len(item)):
                tmp.extend(item[i])
            X.append(tmp)
        graph_X_Y[key] = [X, Y]
    return graph_X_Y


"""
get DT of every graph in dataset
sort in map{id,DT}
"""


def get_dt_index(data_graph_vtxs_coding):
    DT_indexes = {}
    graphs_X_Y = agg_garph_coding(data_graph_vtxs_coding)
    for key, value in graphs_X_Y.iteritems():
        X = value[0]
        Y = value[1]
        model_tree = DecisionTreeClassifier()
        model_tree.fit(X, Y)
        DT_indexes[key] = model_tree.tree_
    return DT_indexes


def index(tree, query_graph_x):
    # for X in queryX:
    #     tmp = []
    #     pre_y = recurse(model_tree.tree_,0,X)
    #     for y in pre_y:
    #         tmp.append(y[0])
    #     queryY.append(np.sum(tmp,axis=0))
    queryY = []
    for vtx in query_graph_x:
        tmp = []
        pre_y = recurse(tree, 0, vtx)
        for y in pre_y:
            tmp.append(y[0])
        l = np.sum(tmp, axis=0)
        if l.sum() > 0:
            queryY.append(l)
        else:
            return []
    return queryY


def query(DT_indexes, query_graph_x):
    graph_match_results = {}
    for index_key, tree in DT_indexes.iteritems():
        graph_match_result = index(tree, query_graph_x)
        graph_match_results[index_key] = graph_match_result
    return graph_match_results


def query_Matching(DT_indexes, query_graphs_X, query_graphs):
    matching_results = {}
    for key, value in query_graphs_X.iteritems():
        graph_id = key
        query_graph = query_graphs[key]
        matching_vtx = query_graph.keys()
        query_graph_x = [value[vtx] for vtx in matching_vtx]  # 过滤出度为1的顶点
        graph_match_result = query(DT_indexes, query_graph_x)
        matching_results[graph_id] = graph_match_result

    return matching_results, matching_vtx


def getsize(DT_indexes):
    sizeB = sys.getsizeof(DT_indexes)
    sizeM = float(sizeB) / 1024 / 1024
    return sizeM


def main(datafilePath, queryfilePath):
    datafilePath = datafilePath
    queryfilePath = queryfilePath
    """
    paser data graph and query graph
    """

    dataVtx, dataEdge, label_set = paserData(datafilePath)
    queryVtxs, queryEdges, q_label_set = paserData(queryfilePath)

    label_codes = coding_label(label_set)
    # begin conding vtx , get L,N,Eigenvalues [[L],[N],[Eigenvalues]]
    query_garph_vtx_coding = coding_graph(queryVtxs, queryEdges, label_codes)

    query_graphs_X = {}
    for key, value in query_garph_vtx_coding.iteritems():
        query_graph_X = []
        for item in value:
            tmp = []
            for i in range(1, len(item)):
                tmp.extend(item[i])
            query_graph_X.append(tmp)
        query_graphs_X[key] = query_graph_X

    # """
    # 测试查询
    # """
    # graph_0 = data_graph_vtxs_coding[0]
    # query_graph = query_garph_vtx_coding[0]
    # Y = [i[0] for i in graph_0]
    # X = []
    # for item in graph_0:
    #     tmp = []
    #     for i in range(1, len(item)):
    #         tmp.extend(item[i])
    #     X.append(tmp)
    # model_tree = DecisionTreeClassifier()
    # model_tree.fit(X, Y)
    #
    # queryX=[]
    # for item in query_graph:
    #     tmp = []
    #     for i in range(1, len(item)):
    #         tmp.extend(item[i])
    #     queryX.append(tmp)
    # queryY=[]
    # for X in queryX:
    #     tmp = []
    #     pre_y = recurse(model_tree.tree_,0,X)
    #     for y in pre_y:
    #         tmp.append(y[0])
    #     queryY.append(np.sum(tmp,axis=0))
    #
    # for y in queryY:
    #     print(y)

    # pre = model_tree.predict(queryX)
    # print(pre)
    query_graph_list = Graphs(queryEdges)
    data_graph_list = Graphs(dataEdge)

    # building index
    print("begin building index...")
    building_index_start = time()
    data_graph_vtxs_coding = coding_graph(dataVtx, dataEdge, label_codes)
    DT_indexes = get_dt_index(data_graph_vtxs_coding)
    building_index_stop = time()
    print("finish building index...")

    dome_query_graph_X = {0: query_graphs_X[0]}
    query_graphs = {0: query_graph_list[0]}

    # query
    print("begin query...")
    begin_query = time()
    query_matching_result, query_matching_vtx = query_Matching(DT_indexes, dome_query_graph_X, query_graphs)
    finish_query = time()
    print("finish query ...")

    # sample = query_matching_result[0][0]
    # print "query_matching_vtx: ", query_matching_vtx
    #
    # for i in sample:
    #     s = ""
    #     for index in range(len(i)):
    #         if i[index] == 1:
    #             s += (str(index) + ",")
    #     print(s)

    # join
    print("begin join...")
    begin_join = time()
    sum_join_garph = {}
    for qgraph_id in query_matching_result:  # query_matching_result:{query graph id:{data graph id :[matching result]}}
        matching_results = query_matching_result[qgraph_id]
        query_graph = query_graph_list[qgraph_id]
        query_vtx_label = {item[0]: item[1] for item in queryVtxs[qgraph_id]}
        JoinGraph = []
        for dgarph_id in matching_results:
            data_graph = data_graph_list[dgarph_id]
            matching_result = matching_results[dgarph_id]
            data_vtx_label = {item[0]: item[1] for item in dataVtx[dgarph_id]}
            join_order = get_join_order(matching_result, query_graph, query_matching_vtx)
            partJoinGraph = join(join_order, query_matching_vtx, matching_result, data_graph, query_graph,
                                 query_vtx_label, data_vtx_label)
            JoinGraph.append({"dgarph_id": dgarph_id, "partJoinGraph": partJoinGraph})
        sum_join_garph[qgraph_id] = JoinGraph
    finish_join = time()
    print("finish join...")

    for q_id in range(len(sum_join_garph)):
        joined_graphs = sum_join_garph[q_id]
        graph_sum = [len(item["partJoinGraph"]) for item in joined_graphs]
        sum = np.sum(np.array(graph_sum))
        q_size = len(queryVtxs[q_id])

        print("--------------------------Summary--------------------------")
        print("query graph %i ,size %i ,result count: %i" % (q_id, q_size, sum))
        print("index size: %f MB" % (getsize(DT_indexes)))
        print("index builded time: %f s" % (building_index_stop - building_index_start))
        print("graph query time: %f s" % (finish_query - begin_query))
        print("join time: %f s" % (finish_join - begin_join))
        print("------------------------------------------------------------")
    # id, vtx_nub = find_max_vtxs(dataVtx)
    # paser_DT(id, vtx_nub, data_graph_vtxs_coding)

    pass


if __name__ == '__main__':
    datafilePath = "./data/sample/dataset"
    Q4 = "./data/sample/Q4"
    Q8 = "./data/sample/Q8"
    Q12 = "./data/sample/Q12"
    Q16 = "./data/sample/Q16"
    Q20 = "./data/sample/Q20"
    Q24 = "./data/sample/Q24"
    queryfilePaths = [Q4, Q8, Q12, Q16, Q20, Q24]
    for queryfilePath in queryfilePaths:
        main(datafilePath, queryfilePath)
