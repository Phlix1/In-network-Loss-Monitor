/*
Copyright 2013-present Barefoot Networks, Inc. 

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

// This is P4 sample source for basic_switching

#include <tofino/intrinsic_metadata.p4>
#include "tofino/stateful_alu_blackbox.p4"
#include <tofino/constants.p4>

header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr: 32;
    }
}

header_type ipv4_option_t {
    fields {
        copyFlag : 1;
        optClass : 2;
        option : 5;
        optionLength : 8;
    }
}

header_type mri_t {
    fields {
        count : 16;
        pathid : 32;
        pcount : 32;
    }
}

header_type switch_t {
    fields {
        hop : 8;
        loss : 32;
    }
}

parser start {
    return parse_ethernet;
}

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        0x800 : parse_ipv4;
        default: ingress;
    }
}

header ipv4_t ipv4;

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.ihl) {
        5 : ingress;
        default: parse_ipv4_option;
    }
}

header ipv4_option_t ipv4_option;

parser parse_ipv4_option {
    extract(ipv4_option);
    return select(latest.option) {
        31: parse_mri;
        default: ingress;
    }
}

header_type user_metadata_t {
    fields {
        remaining : 16;
        pcount : 32;
        loss : 32;
        loss_sign : 32;
    }
}

metadata user_metadata_t md;


header mri_t mri;

parser parse_mri {
    extract(mri);
    return select(latest.count) {
        3 : parse_swtrace3;
        default: ingress;
    }
}

header switch_t swtrace1;

parser parse_swtrace1 {
    extract(swtrace1);
    return ingress;
}

header switch_t swtrace2;

parser parse_swtrace2 {
    extract(swtrace2);
    return parse_swtrace1;
}


header switch_t swtrace3;

parser parse_swtrace3 {
    extract(swtrace3);
    return parse_swtrace2;
}


register reg_count {
    width : 32;
    instance_count: 10;
}

blackbox stateful_alu packet_count {
    reg: reg_count;
    update_lo_1_value : register_lo + 1;
    output_value : alu_lo;
    output_dst : md.pcount;
}

table packet_count_read {
    actions { get_count; }
    default_action: get_count;
}

action get_count(){
    packet_count.execute_stateful_alu(mri.pathid);  
}

table loss_calculate {
    actions { cal_loss; }
    default_action: cal_loss;
}

action cal_loss(){
    subtract(md.loss, mri.pcount, md.pcount);
}

table loss_sign_get {
    actions { get_sign; }
    default_action: get_sign;    
}

action get_sign(){
    bit_and(md.loss_sign, 0x8000,md.loss);
    modify_field(mri.pcount, md.pcount); 
}

table loss_add_sw3 {
    actions { add_loss_sw3; }
    default_action: add_loss_sw3;    
}

action add_loss_sw3(){
    subtract(swtrace3.hop, 64, ipv4.ttl);
    modify_field(swtrace3.loss, md.loss);  
}

table loss_add_sw2 {
    actions { add_loss_sw2; }
    default_action: add_loss_sw2;    
}

action add_loss_sw2(){
    subtract(swtrace2.hop, 64, ipv4.ttl);
    modify_field(swtrace2.loss, md.loss); 
}

table loss_add_sw1 {
    actions { add_loss_sw1; }
    default_action: add_loss_sw1;    
}

action add_loss_sw1(){
    subtract(swtrace1.hop, 64, ipv4.ttl);
    modify_field(swtrace1.loss, md.loss); 
}


action set_egr(egress_spec) {
    add_to_field(ipv4.ttl, -1);
    modify_field(ig_intr_md_for_tm.ucast_egress_port, egress_spec);
}

action nop() {
}

table forward {
    reads {
        ig_intr_md.ingress_port : exact;
    }
    actions {
        set_egr;
        nop;
    }
}

control ingress {
    apply(forward);
    if (valid(mri)){
        apply(packet_count_read); 
        apply(loss_calculate);
        apply(loss_sign_get);
        if (md.loss_sign==0x0000) {
            if (swtrace3.loss == 0) {
                apply(loss_add_sw3);
            }
            else if (swtrace2.loss == 0) {
                apply(loss_add_sw2);
            }
            else if (swtrace1.loss == 0) {
                apply(loss_add_sw1);
            }
        }
    }
    
}

control egress {
}

