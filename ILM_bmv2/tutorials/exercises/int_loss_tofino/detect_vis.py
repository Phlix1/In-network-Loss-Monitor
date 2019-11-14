import networkx as nx
import matplotlib.pyplot as plt
import json
import time
topo_file = "topology.json"
with open(topo_file, 'r') as f:
    topo = json.load(f)
hosts = topo['hosts']
switches = topo['switches']
links = topo['links']
pos = {}
G = nx.Graph()
hosts.sort()
G.add_nodes_from(hosts)
hostnum = len(hosts)
for i in range(hostnum):
    if hosts[i]=="h9":
        pos[hosts[i]] = ((80, 100))
    else:
        pos[hosts[i]] = ((10+i*10, 50))

switchlist = list(switches.keys())
switchnum = len(switchlist)
#G.add_nodes_from(switchlist)

control_switch = []
core_switch = []
edge_switch = []
access_switch = []
for i in range(switchnum):
    if switchlist[i] == "s0":
        control_switch.append(switchlist[i])
    elif len(switchlist[i])==2:
        core_switch.append(switchlist[i])
    elif switchlist[i][-1]=='1' or switchlist[i][-1]=='2':
        edge_switch.append(switchlist[i])
    elif switchlist[i][-1]=='3' or switchlist[i][-1]=='4':
        access_switch.append(switchlist[i])


control_switch.sort()
G.add_nodes_from(control_switch)
controlnum = len(control_switch)
for i in range(controlnum):
    pos[control_switch[i]] = ((40, 100))


core_switch.sort()
G.add_nodes_from(core_switch)
corenum = len(core_switch)
for i in range(corenum):
    pos[core_switch[i]] = ((30+i*10, 90))

access_switch.sort()
G.add_nodes_from(access_switch)
accessnum = len(access_switch)
for i in range(accessnum):
    pos[access_switch[i]] = ((10+i*10, 70))

edge_switch.sort()
G.add_nodes_from(edge_switch)
edgenum = len(edge_switch)
for i in range(edgenum):
    pos[edge_switch[i]] = ((10+i*10, 60))

link_index = {}
colors = []
linknum = len(links)
edgelist = []
for i in range(linknum):
    G.add_edge(links[i][0], links[i][1])
    edgelist.append((links[i][0], links[i][1]))
    link_index[(links[i][0], links[i][1])]=i
    link_index[(links[i][1], links[i][0])]=i
    colors.append(0)

#nx.draw(G, pos, node_color='#A0CBE2',edge_color=colors,
#        width=4, edge_cmap=plt.cm.cool, with_labels=True)
f = open("test.out","r")
linecount = 0
while True:
    line = f.readline()
    if line:
        paras = line[0:-1].split(" ")
        print(linecount, time.asctime( time.localtime(float(paras[0]))), paras[1], paras[2], str(round(float(paras[3][1:-1])*100, 2))+"%")
        linecount+=1
        colors[link_index[(paras[1],paras[2])]]=float(paras[3][1:-1])
    nx.draw_networkx_nodes(G, pos, node_color='#A0CBE2',node_size=400)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos, edgelist=edgelist,width=4,edge_color=colors,edge_cmap=plt.cm.Reds, edge_vmax=1, edge_vmin=0.0)
    plt.pause(0.001)
    plt.clf()
#plt.show()

'''
G = nx.Graph()
G.add_nodes_from([1, "s2", 3, 4])
G.add_edge(1, "s2")
G.add_edge(1, 3)
G.add_edge(1, 4)
pos = nx.spring_layout(G)
colors = [1,2,3]
while True:
    for i in range(3):
        colors[i] = 4-colors[i]
    nx.draw(G, pos, node_color='#A0CBE2', edge_color=colors,
            width=4, edge_cmap=plt.cm.Blues, with_labels=True)
    plt.pause(1)
'''
