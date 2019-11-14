#!/usr/bin/env python
import sys
import struct
from scapy.all import *
from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr, bind_layers
from scapy.all import Packet, IPOption
from scapy.all import IP, UDP, Raw, Ether
from scapy.layers.inet import _IPOption_HDR
from scapy.all import IntField, FieldListField, FieldLenField, ShortField, PacketListField
from scapy.layers.inet import _IPOption_HDR
from scapy.fields import *
import time

paths = {}
#paths[1] = ["h1","s11","s13","s1"]
#paths[2] = ["h1","s11","s14","s3"]
#paths[3] = ["h2","s12","s14","s3"]
failure = {}

def write_cap(pkgs):
    wrpcap("pingpkg.pcap",pkgs)

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface
linecount = 0
printtick = 0
pretime = time.time()
def handle_pkt(pkt):
    f = open("test.out","a+")
    #print "current state:"
    pkt.show2()
    #write_cap([pkt])
    scount = len(pkt[IP].options[0].swtraces)
    pcount = pkt[IP].options[0].pcount
    global linecount
    global printtick
    printtick = printtick + 1
    for i in range(scount):
        pcount += pkt[IP].options[0].swtraces[i].loss 
        #print pcount, pkt[IP].options[0].pathid, pkt[IP].options[0].swtraces[i].hop, float(pkt[IP].options[0].swtraces[i].loss)/pcount
        if (pkt[IP].options[0].pathid, pkt[IP].options[0].swtraces[i].hop) not in failure.keys():
            failure[(pkt[IP].options[0].pathid, pkt[IP].options[0].swtraces[i].hop)] = (float(pkt[IP].options[0].swtraces[i].loss)/pcount,0,0)
        else:
            key = (pkt[IP].options[0].pathid, pkt[IP].options[0].swtraces[i].hop)
            if pcount-failure[key][1]>50:
                lossrate = (float(pkt[IP].options[0].swtraces[i].loss)-failure[key][2])/(pcount-failure[key][1])
                if pkt[IP].options[0].pcount%100==0:
                    failure[key] = (lossrate,pcount,float(pkt[IP].options[0].swtraces[i].loss))
                else:
                    failure[key] = (lossrate,failure[key][1],failure[key][2])
    global pretime
    currenttime = time.time()
    if currenttime-pretime>0.1:
        pretime = currenttime
        for key in failure.keys():
            f.write(str(currenttime)+" "+paths[key[0]][key[1]]+" "+paths[key[0]][key[1]-1]+" "+str(failure[key])+"\n")
            print(linecount)
            linecount = linecount+1
    sys.stdout.flush()


class SwitchTrace(Packet):
    fields_desc = [ IntField("hop", 0),
                  IntField("loss", 0)]
    def extract_padding(self, p):
                return "", p

class IPOption_MRI(IPOption):
    name = "MRI"
    option = 31
    fields_desc = [ _IPOption_HDR,
                    FieldLenField("length", None, fmt="B",
                                  length_of="swtraces",
                                  adjust=lambda pkt,l:l*2+4),
                    ShortField("count", 0),
                    IntField("pathid", 0),
                    IntField("pcount", 0),
                    PacketListField("swtraces",
                                   [],
                                   SwitchTrace,
                                   count_from=lambda pkt:(pkt.count*1)) ]

def main():
    f = open("pinglist.txt", "r")
    line = f.readline()
    while line:
        line = line[0:-1]
        paras = line.split(" ")
        paths[int(paras[0])]=paras[1].split(",")
        line = f.readline()
    f.close()    
    iface = 'h2-eth0'
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(filter="udp and port 4321", iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()
