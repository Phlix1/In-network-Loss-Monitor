#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct
import datetime

import psutil
from scapy.all import *
from scapy.all import sendp, send, get_if_list, get_if_hwaddr, bind_layers
from scapy.all import Packet, IPOption
from scapy.all import Ether, IP, UDP
from scapy.fields import *
from scapy.all import IntField, FieldListField, FieldLenField, ShortField, PacketListField
from scapy.layers.inet import _IPOption_HDR
import readline

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

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

def write_cap(pkgs):
    wrpcap("pingpkg.pcap",pkgs)

def main():
    pathIDs = []
    portpaths = []
    info = psutil.net_if_addrs()
    for cname in info.keys():
        if cname!='lo':
            hostname = cname.split('-')[0]
    print hostname
    #if len(sys.argv)<5:
    #    print 'pass 5 arguments: <destination> <num> <pathID> <path>'
    #    exit(1)
    f = open("pinglist.txt", "r")
    line = f.readline()
    while line:
        line = line[0:-1]
        paras = line.split(" ")
        if hostname==paras[1].split(",")[0]:
            #pathID = int(paras[0])
            pathIDs.append(int(paras[0]))
            #s = paras[2]
            portpaths.append(paras[2])
        line = f.readline()
    addr = socket.gethostbyname("10.0.3.2")
    num = 0
    #pathID = int(sys.argv[3])
    #s=sys.argv[4]
    iface = get_if()
    #print "sending on interface %s to %s" % (iface, str(addr))
    pathnum = len(pathIDs)
    begin_time = datetime.datetime.now()
    

    probepkts = []
    for j in range(pathnum):
        pathID = pathIDs[j]
        s = portpaths[j]
        i=0
        pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
        pkt = pkt / IP(dst=addr, options = IPOption_MRI(count=0, pathid=pathID, swtraces=[])) / UDP(dport=4321, sport=1234)
        probepkts.append(pkt)

    write_cap(probepkts)
    packet_size = len(probepkts[0])


    while True:
        #pathID = pathIDs[num%pathnum]
        #s=portpaths[num%pathnum]
        num = num + 1    
        '''
        i = 0
        pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
        for p in s.split(","):
            try:
                pkt = pkt / SourceRoute(bos=0, port=int(p))
                i = i+1
            except ValueError:
                pass
        if pkt.haslayer(SourceRoute):
            pkt.getlayer(SourceRoute, i).bos = 1

        pkt = pkt / IP(dst=addr, options = IPOption_MRI(count=0, pathid=pathID, swtraces=[])) / UDP(dport=4321, sport=1234)
        #print len(pkt)
        #pkt.show2()
        '''
        #probepkts[num%pathnum].show2()
        sendp(probepkts[num%pathnum], iface=iface, verbose=False)
        end_time = datetime.datetime.now()
        
        total_bytes = packet_size * num
        total_time = (end_time - begin_time).total_seconds()
        if total_time == 0:
            total_time = 2.23E-308
        bytes_per_second = total_bytes / total_time / 1024
        print str(bytes_per_second)+"Bps"
    #pkt = pkt / SourceRoute(bos=0, port=2) / SourceRoute(bos=0, port=3);
    #pkt = pkt / SourceRoute(bos=0, port=2) / SourceRoute(bos=0, port=2);
    #pkt = pkt / SourceRoute(bos=1, port=1)


if __name__ == '__main__':
    main()
