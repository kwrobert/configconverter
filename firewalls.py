#####################################################################################################
# Name: firewalls.py
# Author: Kyle Robertson
# Company: Worldcom Exchange Inc. 
# Description: This file contains the generic base class and vendor specific subclasses for all 
# supported firewalls.
#####################################################################################################

#####################################################################################################
#                                           BASIC DESIGN
# There exists a generic firewall class that requires as instantiation parameters the config file,
# the firewall vendor, and the firewall firmware version. It has parser methods for each vendor that 
# are not exposed to the user. The .parse() function examines the vendor and OS version of the 
# firewall, then executes the appropriate parser. Each firewall parser only understands how to loop 
# through the  entire config file, and identify the sections of the config file that correspond to 
# the subobjects that make up a firewall. The firewall parser extracts these "chunks" then hands them 
# off to the appropriate subobject. The subobject is responsible for extracting all the necessary 
# information from the "chunk"
#####################################################################################################

import re
import os
import firewall_ports as fwp
import firewall_lags as fwl
import firewall_addressobj as fwa
import firewall_serviceobj as fws
#####################################################################################################
class Firewall(object):
    
    def __init__(self, vendor, OS, conf_file):
        # Dictionaries for tracking what lines we successfully handled and what lines we didn't 
        # understand
        self.lines_parsed = {}
        self.lines_missed = {}
        self.line_counter = 0
        self.firmware = OS
        self.vendor = vendor
        self.file_path = conf_file
        # Dictionaries for storing the objects contained within a firewall
        self.physical_ports = []
        self.address_objects = []
        self.service_objects = []
        self.lags = []
        self.vlan_interfaces = []
        self.routes = {}
        self.service_groups = {}
        self.address_groups = {}
        print "Hello, I am a firewall of vendor %s with firmware %s"%(self.vendor,self.firmware)
        # The first thing we need to do is get all the lines of the file, strip any newlines,
        # and remove any blank line. We write all nonblank lines to another file for the sake of
        # comparison. line_counter, lines_parsed, and lines_missed all refer to the nonblank file!
        with open(conf_file,'r') as file_handle:
            self.lines = [line.rstrip() for line in file_handle]
            self.lines = [line for line in self.lines if line]
            nbfile = os.path.join(os.path.dirname(conf_file),"nonblank-"+os.path.basename(conf_file))
            with open(nbfile,'w+') as nbconf:
                for line in self.lines:
                    nbconf.write(line+"\n")
#####################################################################################################
def parse_config(vendor,firmware,config_path):
    """Call the correct parser function based on vendor and OS"""

    if vendor == 'cisco' and firmware == 'ciscoasa':
        return _parse_ciscoasa(vendor,firmware,config_path)
    else:
        raise NotImplementedError("Sorry, parsing the vendor and firmware combination you specified \
        is not supported")
#-----------------------------------------------------------------------------------------------------#
def write_config(vendor,firmware,dest_path,firewall):
    """Call the correct parser function based on vendor and OS"""

    if vendor == 'cisco' and firmware == 'ciscoasa':
        return _write_ciscoasa(dest_path,firewall)
    elif vendor == 'fortinet' and firmware == 'testfortiOS':
        return _write_fortinet(dest_path,firewall)
    else:
        raise NotImplementedError("Sorry, writing the vendor and firmware combination you specified \
        is not supported")

#####################################################################################################
#                               CISCO ASA FUNCTIONS
#####################################################################################################
 
def _parse_ciscoasa(vendor,firmware,config_path):
    # Initialize firewall 
    firewall = Firewall(vendor,firmware,config_path)
    # The dictionary of config items the parser understands, and their regex's 
    re_dict = {'port':'interface (GigabitEthernet|Management)[0-9]+/[0-9]+',
               'lag':'interface Port-channel([0-9]+)',
               'address-object':'^object network','comment':'^[#,!,:]',
               'service-object':'^object service'}
    # Compare the line to all the available regex's. Execute the appropiate parser for the sub
    # object 
    while firewall.line_counter < len(firewall.lines):
        print firewall.line_counter
        line = firewall.lines[firewall.line_counter]
        #print "LINE: ",line
        for obj,regex in re_dict.iteritems():
            match = re.search(regex,line)
            #print "OBJECT: ",obj
            #print "REGEX: ",regex
            #print "MATCH: ",match
            if match:
                print "Found a %s on line %d"%(obj,firewall.line_counter)
                firewall.lines_parsed[firewall.line_counter] = line
                if obj == 'port':
                    #_parse_ciscoasa_port(firewall,line)
                    _parse_asa_object(firewall,line,fwp.parse_port,firewall.physical_ports)
                elif obj == 'lag':
                    #_parse_ciscoasa_lag(firewall,line)
                    _parse_asa_object(firewall,line,fwl.parse_lag,firewall.lags)
                elif obj == 'address-object':
                    #_parse_ciscoasa_addressobj(firewall,line)
                    _parse_asa_object(firewall,line,fwa.parse_addrobj,firewall.address_objects)
                elif obj == 'service-object':
                    #_parse_ciscoasa_serviceobj(firewall,line)
                    _parse_asa_object(firewall,line,fws.parse_servobj,firewall.service_objects)
                elif obj == 'comment':
                    firewall.lines_parsed[firewall.line_counter] = line
                    firewall.line_counter += 1
                break    
        if not match:
            firewall.lines_missed[firewall.line_counter] = line
            firewall.line_counter +=1
    return firewall
#-----------------------------------------------------------------------------------------------------#
def _parse_asa_object(firewall,start_line,parse_func,container):
    # Build out the chunk (includes the line the chunk starts on) and pass it into the parser
    # for the subobject. Pass in the starting line number of the chunk so the subobject can add
    # lines parsed and lines missed to the corresponding dictionaries correctly
    chunk = [start_line]
    firewall.lines_parsed[firewall.line_counter] = start_line
    start_num = firewall.line_counter
    firewall.line_counter += 1
    while firewall.line_counter < len(firewall.lines) and firewall.lines[firewall.line_counter][0] == " ":
        chunk.append(firewall.lines[firewall.line_counter])
        firewall.line_counter += 1
    obj = parse_func(firewall,chunk,start_num)
    container.append(obj)
#---------------------------------------------------------------------------------------------------#
def _write_ciscoasa(dest_path,firewall):
    print "Writing cisco asa config!"
    print firewall
    print dest_path
#####################################################################################################
#                                   FORTINET FUNCTIONS
#####################################################################################################

def _write_fortinet(dest_path,firewall):
    print "Writing fortinet config from firewall"
    print firewall
    print dest_path
    with open(dest_path,'w+') as dest_file:
        _write_fortinet_ports(dest_file,firewall)
        _write_fortinet_lags(dest_file,firewall)
        _write_fortinet_vlanifaces(dest_file,firewall)
        dest_file.write("end\n")
        _write_fortinet_addrobjs(dest_file,firewall)
        _write_fortinet_serviceobjs(dest_file,firewall)
#---------------------------------------------------------------------------------------------------#
def _write_fortinet_ports(out_file,firewall):
    # Some firewall zero index their ports but fortinets don't, so fix that
    zero_indexed = False
    for port in firewall.physical_ports:
        if port.number[2] == 0:
            zero_indexed = True
    
    if zero_indexed:
        for port in firewall.physical_ports:
            port.number[2] += 1

    out_file.write("config system interface\n")
    for port in firewall.physical_ports:
        if port.kind == 'management':
            out_file.write('\tedit "mgmt%d"\n'%port.number[2])
        else:
            out_file.write('\tedit "port%d"\n'%port.number[2])

        if port.name:
            out_file.write('\t\tset alias "%s"\n'%port.name)
        
        out_file.write('\t\tset type physical\n')
        if port.l3addr:
            out_file.write('\t\tset ip %s %s\n'%(port.l3addr['ip'],port.l3addr['mask']))

#---------------------------------------------------------------------------------------------------#
def _write_fortinet_lags(out_file,firewall):
    for lag in firewall.lags:
        if lag.name:
            out_file.write('\tedit "%s"\n'%lag.name)
        else:
            out_file.write('\tedit "TEMPNAME"\n')
        out_file.write("\t\tset type aggregate\n")
        mem_ports = '\t\tset member'
        for mem_port in lag.get_member_ports():
            mem_ports += ' "port%d"'%mem_port.number[2]
        out_file.write(mem_ports+'\n')
        if lag.l3addr:
            out_file.write('\t\tset ip %s %s\n'%(lag.l3addr['ip'],lag.l3addr['mask']))
#---------------------------------------------------------------------------------------------------#
def _write_fortinet_vlanifaces(out_file,firewall):
    for vlaniface in firewall.vlan_interfaces:
        if vlaniface.name:
            out_file.write('\tedit "%s"\n'%vlaniface.name)
        else:
            out_file.write('\tedit "TEMPNAME"\n')
        mem_ports = '\t\tset interface'
        for mem_port in vlaniface.get_member_ports():
            mem_ports += ' "port%d"'%mem_port.number[2]
        out_file.write(mem_ports+'\n')
        out_file.write("\t\tvlan id %d\n"%vlaniface.number)
        if vlaniface.l3addr:
            out_file.write('\t\tset ip %s %s\n'%(vlaniface.l3addr['ip'],vlaniface.l3addr['mask']))
#---------------------------------------------------------------------------------------------------#
def _write_fortinet_addrobjs(out_file,firewall):
    out_file.write("config firewall address\n")
    for addrobj in firewall.address_objects:
        out_file.write('\tedit "%s"\n'%addrobj.name)
        if addrobj.kind == 'subnet':
            out_file.write('\t\tset type subnet\n')
            out_file.write('\t\tset address %s %s\n'%(addrobj.network_address,addrobj.mask))
            out_file.write('\tnext\n')
        elif addrobj.kind == 'range':
            out_file.write('\t\tset type iprange\n')
            out_file.write('\t\tset end-ip %s\n'%addrobj.end_ip)
            out_file.write('\t\tset start-ip %s\n'%addrobj.start_ip)
            out_file.write('\tnext\n')
    out_file.write("end\n")
#-----------------------------------------------------------------------------------------------------#
def _write_fortinet_serviceobjs(out_file,firewall):
    out_file.write("config firewall service custom\n")
    for servobj in firewall.service_objects:
        print servobj
        print vars(servobj)
        out_file.write('\tedit "%s"\n'%servobj.name)
        if servobj.protocol == 'icmp':
            out_file.write('\t\tset protocol ICMP\n')
        elif servobj.protocol == 'tcp':
            out_file.write('\t\tset protocol TCP\n')
            if servobj.strt_destport and servobj.end_destport:
                out_file.write('\t\tset tcp-portrange %d-%d\n'%(servobj.strt_destport,servobj.end_destport))
            elif servobj.strt_destport:
                out_file.write('\t\tset tcp-portrange %d\n'%servobj.strt_destport)
            else:
                print "NO TCP DESTINATION PORTS!"
        elif servobj.protocol == 'udp':
            out_file.write('\t\tset protocol UDP\n')
            out_file.write('\t\tset tcp-portrange 0:0\n')
            if servobj.strt_destport and servobj.end_destport:
                out_file.write('\t\tset udp-portrange %d-%d\n'%(servobj.strt_destport,servobj.end_destport))
            elif servobj.strt_destport:
                out_file.write('\t\tset udp-portrange %d\n'%servobj.strt_destport)
            else:
                print "NO UDP DESTINATION PORTS!"
        out_file.write('\tnext\n')
    out_file.write("end\n")
