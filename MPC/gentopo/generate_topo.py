  
#!/usr/bin/env python

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import random


def fattree_topo(pods):
    num_hosts         = int((pods ** 3)/4)
    num_agg_switches  = int(pods * pods)
    num_core_switches = int((pods * pods)/4)

    hosts = [('h' + str(i), {'type':'host'})
             for i in range (1, num_hosts + 1)]

    core_switches = [('s' + str(i), {'type':'core_switch','id':i})
                       for i in range(1,num_core_switches + 1)]

    agg_switches = [('s' + str(i), {'type':'switch','id':i})
                    for i in range(num_core_switches + 1,num_core_switches + num_agg_switches+ 1)]

    g = nx.DiGraph()
    g.add_nodes_from(hosts)
    g.add_nodes_from(core_switches)
    g.add_nodes_from(agg_switches)

    host_offset = 0
    for pod in range(pods): # pods for completed graph and 1 for speed up
        core_offset = 0
        for sw in range(int(pods/2)):
            switch = agg_switches[(pod*pods) + sw][0]
            # Connect to core switches
            for port in range(int(pods/2)):
                core_switch = core_switches[core_offset][0]
                g.add_edge(switch,core_switch)
                #g.add_edge(core_switch,switch)
                core_offset += 1

            # Connect to aggregate switches in same pod
            for port in range(int(pods/2),pods):
                lower_switch = agg_switches[(pod*pods) + port][0]
                #g.add_edge(switch,lower_switch)
                g.add_edge(lower_switch,switch)

        for sw in range(int(pods/2),pods):
            switch = agg_switches[(pod*pods) + sw][0]
            # Connect to hosts
            for port in range(int(pods/2),pods): # First k/2 pods connect to upper layer
                host = hosts[host_offset][0]
                # All hosts connect on port 0
                g.node[switch]['type'] = 'access_switch'
                #g.add_edge(switch,host)
                g.add_edge(host,switch) 
                host_offset += 1

    return g

def vl2_topo(port_num_of_aggregation_switch=20, port_num_of_intermediate_switch=12,
    port_num_of_tor_for_server=20):
    """Standard vl2 topology
    total port_num_of_aggregation_switch^2 / 4 * port_num_of_tor_for_server servers
    """
    topo = nx.Graph()
    num_of_aggregation_switches = port_num_of_intermediate_switch
    num_of_intermediate_switches = port_num_of_aggregation_switch // 2
    num_of_tor_switches = (port_num_of_intermediate_switch * 
                                port_num_of_aggregation_switch) // 4

    # create intermediate switch
    for i in range(num_of_intermediate_switches):
        topo.add_node("IntermediateSwitch{}".format(i), type='core_switch')

    # create aggregation switch
    for i in range(num_of_aggregation_switches):
        topo.add_node("AggregationSwitch{}".format(i), type='agg_switch')
        for j in range(num_of_intermediate_switches):
            topo.add_edge("AggregationSwitch{}".format(i),
                          "IntermediateSwitch{}".format(j))

    # create ToR switch
    num_of_tor_switches_per_aggregation_switch_can_connect = num_of_aggregation_switches // 2
    for i in range(num_of_tor_switches):
        topo.add_node("ToRSwitch{}".format(i), type='access_switch')
        # For speed up
        if i>=num_of_tor_switches_per_aggregation_switch_can_connect:
            continue
        # every ToR only need to connect 2 aggregation switch
        aggregation_index = (
            i % num_of_tor_switches_per_aggregation_switch_can_connect) * 2
        
        topo.add_edge("ToRSwitch{}".format(i),
                      "AggregationSwitch{}".format(aggregation_index))
        aggregation_index += 1  # The second aggregation switch
        topo.add_edge("ToRSwitch{}".format(i),
                      "AggregationSwitch{}".format(aggregation_index))
        # add server to ToR
        for j in range(port_num_of_tor_for_server):
            topo.add_node("host{}ToRSwitch{}".format(j, i), type='host')
            # speed up
            #topo.add_edge("host{}ToRSwitch{}".format(j, i),
            #              "ToRSwitch{}".format(i))
    topo.name = 'VL2'
    return topo

def random_topo(node_num, link_pr, access_per=20, core_per=20):
    topo = nx.erdos_renyi_graph(node_num, link_pr)
    
    for n in topo.nodes:
        access = random.randint(0,100)   
        if access<access_per:        
            topo.node[n]['type'] = 'access_switch'
        else:
            core = random.randint(0,100)   
            if core<core_per:
                topo.node[n]['type'] = 'core_switch'
            else:
                topo.node[n]['type'] = 'switch'
    return topo
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--pods',type=int,action='store',dest='pods',
                        default=8,
                        help='number of pods (parameter k in the paper)')
    parser.add_argument('-f','--files',type=str,action='store',dest='file',
                        default="test.txt",
                        help='out file name')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    #topo = fattree_topo(args.pods)
    #topo = vl2_topo(40,24,40)
    topo = random_topo(100, 0.4)
    nodenames = list(topo.nodes)
    nodenum = len(nodenames)
    edges = list(topo.edges)
    print(nodenum, len(edges))
    
    # For fattree
    accessnodes = []
    corenodes = []
    vaild_nodenum = 0
    vaild_node = ""
    with open(args.file,'w') as f:
        for nname in nodenames:
            if topo.degree(nname)>0:
                vaild_nodenum += 1
                vaild_node += (str(nname)+" ")
            if topo.node[nname]['type']=='access_switch':
                accessnodes.append(nname)
            if topo.node[nname]['type']=='core_switch':
                corenodes.append(nname)
        f.write(str(vaild_nodenum)+"\n")
        f.write(vaild_node)            
        f.write("\n")
        for e in edges:
            f.write(str(e[0])+" "+str(e[1])+"\n")
        f.write("#\n")
        f.write(str(len(accessnodes))+"\n")
        for h in accessnodes:
            f.write(str(h)+" ")
        f.write("\n")
        f.write(str(len(corenodes))+"\n")
        for c in corenodes:
            f.write(str(c)+" ")
        f.write("\n")  
     
    '''
    # For VL2
    accessnodes = []
    corenodes = []
    vaild_nodenum = 0
    vaild_node = ""
    with open(args.file,'w') as f:
        for nname in nodenames:
            if topo.degree(nname)>0:
                vaild_nodenum += 1
                vaild_node += (nname+" ")
                if "host" in nname:
                    pass
                elif "ToRSwitch" in nname:
                    accessnodes.append(nname)
                elif "IntermediateSwitch" in nname:
                    corenodes.append(nname)
        f.write(str(vaild_nodenum)+"\n")
        f.write(vaild_node)            
        f.write("\n")
        for e in edges:
            f.write(e[0]+" "+e[1]+"\n")
        f.write("#\n")
        f.write(str(len(accessnodes))+"\n")
        for h in accessnodes:
            f.write(h+" ")
        f.write("\n")
        f.write(str(len(corenodes))+"\n")
        for c in corenodes:
            f.write(c+" ")
        f.write("\n")    
    '''
    '''
    # For random network
    accessnodes = []
    corenodes = []  
    vaild_nodenum = 0
    vaild_node = ""
    with open(args.file,'w') as f:
        for nname in nodenames:
            if topo.degree(nname)>0:
                vaild_nodenum += 1
                vaild_node += (nname+" ")
            if topo.node[nname]['type']=='access_switch':
                accessnodes.append(nname)
            if topo.node[nname]['type']=='core_switch':
                corenodes.append(nname)
        f.write(str(vaild_nodenum)+"\n")
        f.write(vaild_node)            
        f.write("\n")
        for e in edges:
            f.write(e[0]+" "+e[1]+"\n")
        f.write("#\n")
        f.write(str(len(accessnodes))+"\n")
        for h in accessnodes:
            f.write(h+" ")
        f.write("\n")
        f.write(str(len(corenodes))+"\n")
        for c in corenodes:
            f.write(c+" ")
        f.write("\n")            
    '''  
    nx.draw(topo, with_labels=True, font_weight='bold')
    plt.show()
