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
class Port(object):
    """An object to represent a physical port on a firewall"""
    
    def __init__(self, firewall, chunk, start_num):
        self.firewall = firewall
        self.text = chunk
        self.start = start_num
        self.end = start_num + len(chunk)
        self.line_counter = start_num
        self.vlans = []
        self.port_type = None
        self.speed = None
        self.number = [None,None,None] 
    
    def parse(self):
        if self.firewall.vendor == 'cisco' and self.firewall.firmware == 'ciscoasa':
            self._cisco_asa_parser()
        else:
            raise NotImplementedError("Sorry, we currently cannot parse cisco asa ports")
    
    def _cisco_asa_parser(self):
        # Handle the starting line of the section seperately
        start_re = 'interface GigabitEthernet([0-9]+)/([0-9]+)'
        start_line = self.text[0]
        match = re.search(start_re,start_line)
        self.number[0],self.number[2] = match.group(1),match.group(2)
        self.line_counter += 1
        # Dict containing regex for all possible settings within a port subsection
        re_dict = {'vlans':'vlan id ([0-9]+[ ]*)',
                   'ip':'ip address ([0-9]+.[0-9]+.[0-9]+.[0-9]+) ([0-9]+.[0-9]+.[0-9]+.[0-9])'}
        # Loop through the subsection
        for line in self.text[1:]:
            for item,regex in re_dict.iteritems():
                match = re.search(regex,line)
                if match:
                    self.firewall.lines_parsed[self.line_counter] = line
                    self.line_counter += 1
                    if item == 'vlans':
                        all_vlans = re.findall('[0-9]+',line)
                        for vlan in all_vlans:
                            self.vlans.append(vlan)
                    elif item == 'ip':
                        self.l3addr = {'ip':match.group(1), 'mask': match.group(2)}
                    break
                    
            if not match:
                self.firewall.lines_missed[self.line_counter] = line
                self.line_counter += 1

    def get_type():
        return self.port_type

    def set_type(type_string):
        if type_string != 'access' or type_string != 'trunk':
            raise ValueError("A port can only be an access port or a trunk port")
        elif type(type_string) != str:
            raise ValueError("Argument must be a string")
        else:
            self.port_type = type_string


class Firewall(object):
    
    def __init__(self, vendor, OS, conf_file):
        # Dictionaries for storing the objects contained within a firewall
        self.physical_ports = []
        self.address_objects = {}
        self.service_objects = {}
        self.routes = {}
        self.service_groups = {}
        self.address_groups = {}
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
        print "Hello, I am a %s firewall running OS version %s"%(self.vendor, self.firmware)
    #-----------------------------------------------------------------------------#
    def parse(self):
        """Externally exposed function that chooses the correct parser based on vendor and OS"""
        if self.vendor == 'cisco' and self.firmware == 'ciscoasa': 
            self._cisco_asa_parser()
        elif self.vendor == 'fortinet' and self.firmware == 'testfortiOS':
            self._fortinetParser()
        else:
            raise NotImplementedError("Sorry, your combination of vendor and firmware is not \
            supported")
    #-----------------------------------------------------------------------------#
    def _cisco_asa_parser(self):
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
                        self._cisco_asa_port_parser(line)
                    elif obj == 'address-object':
                        self._cisco_asa_addressobj_parser()
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
    #-----------------------------------------------------------------------------#
    def _cisco_asa_port_parser(self,start_line):
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
        port = Port(self,chunk,start_num)
        port.parse()
        if port.line_counter != self.line_counter:
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

    def _cisco_asa_addressobj_parser(self):
        start_line = self.line_counter
