import re

class LAG(object):
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
        self.number = None
        self.name = ""
        print "Hello this is LAG of vendor %s with OS %s"%(self.vendor,self.firmware)

    def get_member_ports(self):
        member_ports = []
        for port in self.firewall.physical_ports:
            if port.parent_lag and port.parent_lag['num'] == self.number:
                member_ports.append(port)
        return member_ports 
#####################################################################################################
def parse_lag(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa_9dot0(firewall,chunk,start_num):
    # Initialize port
    lag = LAG(firewall,chunk,start_num)
    # Handle the starting line of the section seperately
    start_re = 'interface Port-channel([0-9]+)'
    start_line = lag.text[0]
    match = re.search(start_re,start_line)
    # Determine whether this is a management or ethernet interface
    lag.number = int(match.group(1))
    lag.line_counter += 1
    # Dict containing regex for all possible settings within a port subsection
    re_dict = {
    'vlans':'vlan id ([0-9]+[ ]*)',
    'ip':'(no )*ip address[ ]*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)*[ ]*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)*[ ]*(standby)*[ ]*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)*',
    'trunk':'encapsulation dot1q ([0-9]]+[ ]*)',
    'name': '(no )*nameif[ ]*([A-z0-9-_]+)*',
    'security':'(no )*security-level( [0-9]+)*',
    'description':'description ([A-z0-9-_ ]+)'}
    
    for line in lag.text[1:]:
        for item,regex in re_dict.iteritems():
            match = re.search(regex,line)
            if match:
                firewall.lines_parsed[lag.start+lag.line_counter] = line
                lag.line_counter += 1
                if item == 'vlans':
                    all_vlans = re.findall('[0-9]+',line)
                    for vlan in all_vlans:
                        lag.vlans.append(vlan)
                elif item == 'ip':
                    if not match.group(1):
                        if not match.group(4):
                            lag.l3addr = {'ip':match.group(2), 'mask': match.group(3)}
                        else:
                            lag.l3addr = {'ip':match.group(2), 'mask':match.group(3),
                                           'standby-ip':match.group(5)}
                elif item == 'port_type':
                    lag.port_type = 'trunk'
                elif item == 'name':
                    if not match.group(1):
                        lag.name = match.group(2)
                elif item == 'lag':
                    lag.parent_lag.update({'num':int(match.group(1)),'mode':match.group(2)})
                elif item == 'security':
                    if match.group(1):
                        lag.security = None
                    else:
                        lag.security = int(match.group(2))
                break
                
        if not match:
            firewall.lines_missed[lag.start+lag.line_counter] = line
            lag.line_counter += 1

    return lag
