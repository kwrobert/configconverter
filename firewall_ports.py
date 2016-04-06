import re

# A factory function to spit out an instance of the correct Port subclass
def getPort(firewall, chunk, start_num):
    if firewall.vendor == 'cisco' and firewall.firmware == 'ciscoasa':
        return CiscoASAPort(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified for \
        this port is not supported")


class Port(object):
    """The abstract base class for all port objects"""

    def __init__(self,firewall,chunk,start_num):
        self.firewall = firewall
        self.firmware = firewall.firmware
        self.vendor = firewall.vendor
        self.text = chunk
        self.start = start_num
        self.end = start_num + len(chunk)
        self.line_counter = 0
        print "Hello this is base port init"    
    def parse():
        raise NotImplementedError("You are calling the base classes implementation of this method. \
        Create a subclass and override it")

    def template():
        raise NotImplementedError("You are calling the base classes implementation of this method. \
        Create a subclass and override it")

class CiscoASAPort(Port):
    """An object to represent a physical port on a firewall"""
    
    def __init__(self, firewall, chunk, start_num):
        Port.__init__(self,firewall,chunk,start_num)
        self.vlans = []
        self.port_type = None
        # If any subinterfaces are found, we store them in a dictionary. The key is the number of
        # the subinterface (number after the dot i.e interface GigabitEthernet0/1.399). The value
        # is another dictionary which stores all the info about the subinterface
        self.subinterfaces = {}
        self.lag = {}
        self.speed = None
        self.number = [None,None,None]
        self.name = ""
        print "Hello I am a port of type: ",type(self)
    #-----------------------------------------------------------------------------#
    def parse(self):
        # Handle the starting line of the section seperately
        start_re = 'interface (Management|GigabitEthernet)([0-9]+)/([0-9]+)'
        start_line = self.text[0]
        match = re.search(start_re,start_line)
        self.number[0],self.number[2] = match.group(2),match.group(3)
        self.line_counter += 1
        # Dict containing regex for all possible settings within a port subsection
        re_dict = {'sub_interface':'interface GigabitEthernet([0-9]+)/([0-9]+).([0-9]+)',
                   'vlans':'vlan id ([0-9]+[ ]*)',
                   'ip':'(no )*ip address[ ]*([0-9]+.[0-9]+.[0-9]+.[0-9]+)*[ ]*([0-9]+.[0-9]+.[0-9]+.[0-9])*',
                   'trunk':'encapsulation dot1q ([0-9]]+[ ]*)',
                   'name': '(no )*nameif( [A-z0-9-_]+)*',
                   'lag': 'channel-group ([0-9]+) mode (active|passive)',
                   'security':'(no )*security-level( [0-9]+)*',
                   'description':'description ([A-z0-9-_ ]+)'}
        # Check for subinterfaces 
        subinterfaces = False
        for line in self.text[1:]:
            match = re.search(re_dict['sub_interface'],line)
            if match:
                subinterfaces = True
                self.port_type = "trunk"
                break
        # Parse depending on whether or not there are subinterfaces
        print len(self.text)
        if subinterfaces:
            # Here we need to properly parse subinterfaces
            print "Found some subinterfaces!"
            while self.line_counter < len(self.text):
                print self.line_counter
                line = self.text[self.line_counter]
                match = re.search(re_dict['sub_interface'],line)
                if match:
                    # Grab subinterface number from regex match
                    num = match.group(3)
                    # Initialize empty dict within subinterfaces dict to store info about
                    # subinterface
                    self.subinterfaces[num] = {}
                    # Make sure the firewall knows we parsed this line
                    self.firewall.lines_parsed[self.start+self.line_counter] = line
                    self.line_counter += 1
                    print self.line_counter
                    # While we haven't run into another subinterface collect info about this
                    # subinterface
                    while (self.line_counter < len(self.text)) and (not
                            re.search(re_dict['sub_interface'],self.text[self.line_counter])):
                        line = self.text[self.line_counter]
                        for item,regex in re_dict.iteritems():
                            match = re.search(regex,line)
                            if match:
                                self.firewall.lines_parsed[self.start+self.line_counter] = line
                                self.line_counter += 1
                                if item == 'vlans':
                                    all_vlans = re.findall('[0-9]+',line)
                                    vlans = []
                                    for vlan in all_vlans:
                                        vlans.append(vlan)
                                    self.subinterfaces[num]['vlans'] = vlans
                                elif item == 'ip':
                                    if not match.group(1):
                                        entries = {'ip':match.group(2), 'mask': match.group(3)}
                                        self.subinterfaces[num].update(entries)
                                elif item == 'name':
                                    if not match.group(1):
                                        self.subinterfaces[num].update({'name':match.group(2)})
                                # TODO: Can subinterfaces be members of a port channel? Ask
                                # Matt/Brian cuz this may not be necessary
                                elif item == 'lag':
                                    self.subinterfaces[num].lag.update({'num':int(match.group(1)),'mode':match.group(2)})
                                elif item == 'security':
                                    if match.group(1):
                                        self.subinterfaces[num].security = None
                                    else:
                                        self.subinterfaces[num].security = int(match.group(2))

                                break
                                
                        if not match:
                            self.firewall.lines_missed[self.start+self.line_counter] = line
                            self.line_counter += 1            
                        print self.line_counter  
        else:
            # Its a regular interface
            for line in self.text[1:]:
                for item,regex in re_dict.iteritems():
                    match = re.search(regex,line)
                    if match:
                        self.firewall.lines_parsed[self.start+self.line_counter] = line
                        self.line_counter += 1
                        if item == 'vlans':
                            all_vlans = re.findall('[0-9]+',line)
                            for vlan in all_vlans:
                                self.vlans.append(vlan)
                        elif item == 'ip':
                            if not match.group(1):
                                self.l3addr = {'ip':match.group(2), 'mask': match.group(3)}
                        elif item == 'port_type':
                            self.port_type = 'trunk'
                        elif item == 'name':
                            if not match.group(1):
                                self.name = match.group(2)
                        elif item == 'lag':
                            self.lag.update({'num':int(match.group(1)),'mode':match.group(2)})
                        elif item == 'security':
                            if match.group(1):
                                self.security = None
                            else:
                                self.security = int(match.group(2))
                        break
                        
                if not match:
                    self.firewall.lines_missed[self.start+self.line_counter] = line
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
