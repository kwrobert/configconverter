import re

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
        self.port_type = None
        self.vlans = []
        self.kind = ""
        self.parent_lag = {}
        self.number = [None,None,None]
        self.name = ""
        print "Hello this is port of vendor %s with OS %s"%(self.vendor,self.firmware)
#####################################################################################################
def parse_port(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'ciscoasa':
        return _parse_ciscoasa(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa(firewall,chunk,start_num):
    # Initialize port
    port = Port(firewall,chunk,start_num)
    # Handle the starting line of the section seperately
    start_re = 'interface (Management|GigabitEthernet)([0-9]+)/([0-9]+)'
    start_line = port.text[0]
    match = re.search(start_re,start_line)
    # Determine whether this is a management or ethernet interface
    if match.group(1) == 'Management':
        port.kind = "management"
    else:
        port.kind = "ethernet"
    port.number[0],port.number[2] = match.group(2),match.group(3)
    port.line_counter += 1
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
    for line in port.text[1:]:
        match = re.search(re_dict['sub_interface'],line)
        if match:
            subinterfaces = True
            port.port_type = "trunk"
            break
    # Parse depending on whether or not there are subinterfaces
    print len(port.text)
    if subinterfaces:
        # Here we need to properly parse subinterfaces
        print "Found some subinterfaces!"
        while port.line_counter < len(port.text):
            print port.line_counter
            line = port.text[port.line_counter]
            match = re.search(re_dict['sub_interface'],line)
            if match:
                # Grab subinterface number from regex match
                num = match.group(3)
                # Initialize empty dict within subinterfaces dict to store info about
                # subinterface
                firewall.vlan_interfaces[num] = {}
                # Make sure the firewall knows we parsed this line
                firewall.lines_parsed[port.start+port.line_counter] = line
                port.line_counter += 1
                print port.line_counter
                # While we haven't run into another subinterface collect info about this
                # subinterface
                while (port.line_counter < len(port.text)) and (not
                        re.search(re_dict['sub_interface'],port.text[port.line_counter])):
                    line = port.text[port.line_counter]
                    for item,regex in re_dict.iteritems():
                        match = re.search(regex,line)
                        if match:
                            firewall.lines_parsed[port.start+port.line_counter] = line
                            port.line_counter += 1
                            if item == 'vlans':
                                all_vlans = re.findall('[0-9]+',line)
                                vlans = []
                                for vlan in all_vlans:
                                    vlans.append(vlan)
                                firewall.vlan_interfaces[num]['vlans'] = vlans
                            elif item == 'ip':
                                if not match.group(1):
                                    entries = {'ip':match.group(2), 'mask': match.group(3)}
                                    firewall.vlan_interfaces[num].update(entries)
                            elif item == 'name':
                                if not match.group(1):
                                    firewall.vlan_interfaces[num].update({'name':match.group(2)})
                            # TODO: Can subinterfaces be members of a port channel? Ask
                            # Matt/Brian cuz this may not be necessary
                            elif item == 'lag':
                                firewall.vlan_interfaces[num].parent_lag.update({'num':int(match.group(1)),'mode':match.group(2)})
                            elif item == 'security':
                                if match.group(1):
                                    firewall.vlan_interfaces[num].security = None
                                else:
                                    firewall.vlan_interfaces[num].security = int(match.group(2))

                            break
                            
                    if not match:
                        firewall.lines_missed[port.start+port.line_counter] = line
                        port.line_counter += 1            
                    print port.line_counter  
    else:
        # Its a regular interface
        for line in port.text[1:]:
            for item,regex in re_dict.iteritems():
                match = re.search(regex,line)
                if match:
                    firewall.lines_parsed[port.start+port.line_counter] = line
                    port.line_counter += 1
                    if item == 'vlans':
                        all_vlans = re.findall('[0-9]+',line)
                        for vlan in all_vlans:
                            port.vlans.append(vlan)
                    elif item == 'ip':
                        if not match.group(1):
                            port.l3addr = {'ip':match.group(2), 'mask': match.group(3)}
                    elif item == 'port_type':
                        port.port_type = 'trunk'
                    elif item == 'name':
                        if not match.group(1):
                            port.name = match.group(2)
                    elif item == 'lag':
                        port.parent_lag.update({'num':int(match.group(1)),'mode':match.group(2)})
                    elif item == 'security':
                        if match.group(1):
                            port.security = None
                        else:
                            port.security = int(match.group(2))
                    break
                    
            if not match:
                firewall.lines_missed[port.start+port.line_counter] = line
                port.line_counter += 1

    return port
