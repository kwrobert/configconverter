import re

asa_port_names = {
'aol'                            : 5120,
'bgp'                            : 179,
'biff'                           : 512, 
'bootpc'                         : 68,
'bootps'                         : 67,
'chargen'                        : 19,
'cifs'                           : 3020,
'citrix-ica'                     : 1494,
'cmd'                            : 514,
'ctiqbe'                         : 2748,
'daytime'                        : 13,
'discard'                        : 9,
'domain'                         : 53,
'echo'                           : 7,
'exec'                           : 512,
'finger'                         : 79,
'ftp'                            : 21,
'ftp-data'                       : 20,
'gopher'                         : 70,
'h323'                           : 1720,
'hostname'                       : 101,
'http'                           : 80,
'https'                          : 443,
'ident'                          : 113,
'imap4'                          : 143,
'irc'                            : 194,
'isakmp'                         : 500,
'kerberos'                       : 750,
'klogin'                         : 543,
'kshell'                         : 544,
'ldap'                           : 389,
'ldaps'                          : 636,
'login'                          : 513,
'lotusnotes'                     : 1352,
'lpd'                            : 515,
'netbios-ns'                     : 137,
'netbios-dgm'                    : 138,
'netbios-ssn'                    : 139,
'nfs'                            : 2049,
'nntp'                           : 119,
'ntp'                            : 123,
'pcanywhere-data'                : 5631,
'pcanywhere-status'              : 5632,
'pim-auto-rp'                    : 496,
'pop2'                           : 109,
'pop3'                           : 110,
'pptp'                           : 1723,
'radius'                         : 1645,
'radius-acct'                    : 1646,
'rip'                            : 520,
'rsh'                            : 514,
'rtsp'                           : 554,
'sip'                            : 5060,
'smtp'                           : 25,
'snmp'                           : 161,
'snmptrap'                       : 162,
'sqlnet'                         : 1521,
'ssh'                            : 22,
'sunrpc'                         : 111,
'syslog'                         : 514,
'tacacs'                         : 49,
'talk'                           : 517,
'telnet'                         : 23,
'tftp'                           : 69,
'time'                           : 37,
'uucp'                           : 540,
'who'                            : 513,
'whois'                          : 43,
'www'                            : 80,
'xdmcp'                          : 177
}


class ServiceObject(object):
    """The abstract base class for all port objects"""

    def __init__(self,firewall,chunk,start_num):
        self.firewall = firewall
        self.firmware = firewall.firmware
        self.vendor = firewall.vendor
        self.text = chunk
        self.start = start_num
        self.end = start_num + len(chunk)
        self.line_counter = 0
        self.name = ""
        self.protocol = ""
        self.strt_srcport = None 
        self.end_srcport = None 
        self.srcop = ""
        self.destop = ""
        self.strt_destport = None
        self.end_destport = None
        print "Hello this is a service object of vendor %s with OS %s"%(self.vendor,self.firmware)
#####################################################################################################
def parse_servobj(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa_9dot0(firewall,chunk,start_num):
    # Initialize port
    servobj = ServiceObject(firewall,chunk,start_num)
    servobj.name = servobj.text[servobj.line_counter].split()[-1]
    firewall.lines_parsed[firewall.line_counter+servobj.line_counter] = servobj.text[servobj.line_counter]
    servobj.line_counter += 1
    # The dictionary of config items the parser understands, and their regex's 
    re_dict = {'description':'description ([A-z0-9-_ ]+)',
               'service':'service (tcp|udp|icmp) source (eq|neq|lt|gt|range) ([A-z]+|([0-9]+)( [0-9]+)*)( destination)*( eq| neq| lt| gt| range)*( [A-z]+| ([0-9]+)( [0-9]+)*)*'}
    # Compare the line to all the available regex's. Execute the appropiate parser for the sub
    # object 
    while servobj.line_counter < len(servobj.text):
        line = servobj.text[servobj.line_counter]
        #print "LINE: ",line
        for obj,regex in re_dict.iteritems():
            match = re.search(regex,line)
            #print "OBJECT: ",obj
            #print "REGEX: ",regex
            #print "MATCH: ",match
            if match:
                firewall.lines_parsed[firewall.line_counter+servobj.line_counter] = line
                if obj == 'service':
                    servobj.protocol = match.group(1)
                    servobj.srcop = match.group(2)
                    # Catch situations where the port is referenced by name and look it up in the
                    # port dictionary for asa's. Also handle the shifting group reference when there
                    # is a range operator vs. when there isn't
                    print line
                    print match
                    print match.group(0)
                    print match.group(1)
                    print match.groups()
                    if servobj.srcop == 'range':
                        try:
                            servobj.strt_srcport = int(match.group(4))
                        except ValueError:
                            servobj.strt_srcport = asa_port_names[match.group(4)]
                        if match.group(5):
                            servobj.end_srcport = int(match.group(5))
                    else:
                        try:
                            servobj.strt_srcport = int(match.group(3))
                        except ValueError:
                            servobj.strt_srcport = asa_port_names[match.group(3)]
                    if match.group(7):                           
                        servobj.destop = match.group(7).lstrip() # TODO: these calls to lstrip() could
                                                                 # probably be avoided with a better
                                                                 # regex
                    if servobj.destop == 'range':
                        try:
                            servobj.strt_destport = int(match.group(9)) 
                        except ValueError:
                            servobj.strt_destport = asa_port_names[match.group(9)]
                        if match.group(10):
                            servobj.end_destport = int(match.group(10))                
                    elif match.group(8):
                        try:
                            servobj.strt_destport = int(match.group(8))
                        except ValueError:
                            servobj.strt_destport = asa_port_names[match.group(8).lstrip()]
                elif obj == 'description':
                    servobj.description = match.group(1)
                servobj.line_counter += 1
                break    
        if not match:
            firewall.lines_missed[firewall.line_counter+servobj.line_counter] = line
            servobj.line_counter +=1
    return servobj
