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

def getFirewall(vendor,firmware,config_path):
    # TODO: Use __subclasses__ to loop through subclasses for Firewall. Make can_handle method
    # within each subclass to check whether the given subclass can handle the vendor/OS combo. 
    # If we reach the end of the loop and haven't found a subclass that can handle the OS/vendor
    # combo, then raise a not implemented error 
    if vendor == 'cisco' and firmware == 'ciscoasa':
        return CiscoASAFirewall(vendor,firmware,config_path)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified for \
        this port is not supported")

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
        print "Hello, this is base firewall init"

    def parse():
        raise NotImplementedError("You are calling the base classes implementation of this method. \
        Create a subclass and override it")

    def template():
        raise NotImplementedError("You are calling the base classes implementation of this method. \
        Create a subclass and override it")
    
    
class CiscoASAFirewall(Firewall):
    def __init__(self,vendor,OS,conf_file):
        Firewall.__init__(self,vendor,OS,conf_file) 
        # Dictionaries for storing the objects contained within a firewall
        self.physical_ports = []
        self.address_objects = {}
        self.service_objects = {}
        self.routes = {}
        self.service_groups = {}
        self.address_groups = {}
        print "Hello, I am a firewall of type: ",type(self)
    #-----------------------------------------------------------------------------#
    def parse(self):
        # The dictionary of basic objects the parser understands, and their regex's 
        re_dict = {'port':'interface GigabitEthernet[0-9]+/[0-9]+','address-object':'^object network',
                   'comment':'^[#,!,:]'}
        # Compare the line to all the available regex's. Execute the appropiate parser for the sub
        # object 
        while self.line_counter < len(self.lines):
            print self.line_counter
            line = self.lines[self.line_counter]
            #print "LINE: ",line
            for obj,regex in re_dict.iteritems():
                match = re.search(regex,line)
                #print "OBJECT: ",obj
                #print "REGEX: ",regex
                #print "MATCH: ",match
                if match:
                    print "Found a %s on line %d"%(obj,self.line_counter)
                    self.lines_parsed[self.line_counter] = line
                    if obj == 'port':
                        self.port_parser(line)
                    elif obj == 'address-object':
                        self.addressobj_parser()
                    elif obj == 'comment':
                        self.lines_parsed[self.line_counter] = line
                        self.line_counter += 1
                    break    
            if not match:
                self.lines_missed[self.line_counter] = line
                self.line_counter +=1
        print "Here are the lines we parsed"
        print self.lines_parsed.keys()
        print "Here are the lines we missed"
        print self.lines_missed.keys()
        if set(self.lines_parsed.keys()).intersection(self.lines_missed.keys()):
            print "You messed up, here are the lines that are in both dicts"
            print set(self.lines_parsed.keys()).intersection(self.lines_missed.keys()) 
        for line_num in sorted(self.lines_missed.keys()):
            print "%d: %s"%(line_num,self.lines_missed[line_num])
    #-----------------------------------------------------------------------------#
    def port_parser(self,start_line):
        # Build out the chunk (includes the line the chunk starts on) and pass it into the parser
        # for the subobject. Pass in the starting line number of the chunk so the subobject can add
        # lines parsed and lines missed to the corresponding dictionaries correctly
        chunk = [start_line]
        self.lines_parsed[self.line_counter] = start_line
        start_num = self.line_counter
        self.line_counter += 1
        while self.lines[self.line_counter][0] == " ":
            chunk.append(self.lines[self.line_counter])
            self.line_counter += 1
        #print "###############################"
        #print chunk
        #print "###############################"
        port = fwp.getPort(self,chunk,start_num)
        port.parse()
        if port.line_counter+port.start != self.line_counter:
            print "Firewall: ",self.line_counter
            print "Port: ",port.line_counter 
            print "YOU FUCKED UP" 
            quit()
        self.physical_ports.append(port)
        #print self.physical_ports
        #for port in self.physical_ports:
        #    for key, value in vars(port).iteritems():
        #        print "KEY: ", key
        #        print "VALUE: ",value
        #    for value in dir(port):
        #        print "VALUE: ",value
        #    print port.vlans

    def addressobj_parser(self):
        start_line = self.line_counter
        self.line_counter += 1
