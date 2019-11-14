import copy
import datetime
import logging
import os
import pdb
import random
import sys
import time
import unittest
from collections import OrderedDict

import pal_rpc
import pd_base_tests
import pltfm_pm_rpc
import ptf.dataplane as dataplane
from conn_mgr_pd_rpc.ttypes import *
from devport_mgr_pd_rpc.ttypes import *
from mc_pd_rpc.ttypes import *
from pal_rpc.ttypes import *
from pltfm_pm_rpc.ttypes import *
from ptf import config
from ptf.testutils import *
from ptf.thriftutils import *
from ptf_port import *
from res_pd_rpc.ttypes import *
from intloss.p4_pd_rpc.ttypes import *

this_dir = os.path.dirname(os.path.abspath(__file__))

# Front Panel Ports
fp_ports = ["1/0", "3/0"]

class AddEntry(pd_base_tests.ThriftInterfaceDataPlane):
    def __init__(self):
        pd_base_tests.ThriftInterfaceDataPlane.__init__(self, ["intloss"])
        self.devPorts = []
        self.dev_id = 0
    
    def runTest(self):
        sess_hdl = self.conn_mgr.client_init()
        dev_tgt = DevTarget_t(self.dev_id, hex_to_i16(0xFFFF))

        # get the device ports from front panel ports
        for fpPort in fp_ports:
            port, chnl = fpPort.split("/")
            devPort = \
                self.pal.pal_port_front_panel_port_to_dev_port_get(0,
                                                                int(port),
                                                                int(chnl))
            self.devPorts.append(devPort)
        # add and enable the platform ports
        print "\nenable ports", self.devPorts
        for i in self.devPorts:
            self.pal.pal_port_add(0, i,
                                    pal_port_speed_t.BF_SPEED_40G,
                                    pal_fec_type_t.BF_FEC_TYP_NONE)
            self.pal.pal_port_enable(0, i)  

        #hop tables
        self.actnspec = intloss_set_egr_action_spec_t(self.devPorts[0])
        self.matchspec = intloss_forward_match_spec_t(ig_intr_md_ingress_port=self.devPorts[1])
        print "Populating table entries 1 "
        result = self.client.forward_table_add_with_set_egr(sess_hdl,
                                                        dev_tgt,
                                                        self.matchspec,
                                                        self.actnspec)

        self.actnspec = intloss_set_egr_action_spec_t(self.devPorts[1])
        self.matchspec = intloss_forward_match_spec_t(ig_intr_md_ingress_port=self.devPorts[0])
        print "Populating table entries 2 "
        result = self.client.forward_table_add_with_set_egr(sess_hdl,
                                                        dev_tgt,
                                                        self.matchspec,
                                                        self.actnspec)

        self.conn_mgr.complete_operations(sess_hdl)
        self.client.packet_count_read_set_default_action_get_count(sess_hdl, dev_tgt)
        self.client.loss_calculate_set_default_action_cal_loss(sess_hdl, dev_tgt)
        self.client.loss_sign_get_set_default_action_get_sign(sess_hdl, dev_tgt)
        self.client.loss_add_sw3_set_default_action_add_loss_sw3(sess_hdl, dev_tgt)
        self.client.loss_add_sw2_set_default_action_add_loss_sw2(sess_hdl, dev_tgt)
        self.client.loss_add_sw1_set_default_action_add_loss_sw1(sess_hdl, dev_tgt)
        self.client.register_write_reg_count(sess_hdl, dev_tgt, 1, 0)
        self.conn_mgr.complete_operations(sess_hdl)