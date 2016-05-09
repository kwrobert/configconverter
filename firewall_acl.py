import firewall_serviceobj as fws

class ACL(object):

    def __init__(self, firewall, name,start_num):
        self.name = name
        self.firewall = firewall
        self.rules = []

class ExtendedACLRule(object):

    def __init__(self, acl, priority):

        self.parent_acl = acl
        self.priority = priority
        self.protocol = ""
        self.protocol_content = ""
        self.kind = ""
        self.action = "" 
        self.src_type = ""
        self.src_content = ""
        self.src_op = ""
        self.start_srcport = None
        self.end_srcport = None
        self.dest_type = ""
        self.dest_content = "" 
        self.dest_op = ""
        self.start_destport = None
        self.end_destport = None
        self.active = True

class StandardACLRule(object):

    def __init__(self,acl,priority):
        self.parent_acl = acl
        self.priority = priority
        self.ip = ""
        self.mask = ""
        self.active = True

def parse_ACL(firewall,text,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0(firewall,text,start_num)
    else:
        raise NotImplementedError("Sorry, parsing the vendor and firmware combination you specified \
        is not supported")

def _parse_ciscoasa_9dot0(firewall,textlist,start_num):
    
    # Get the name of the parent ACL for the rule line and make sure it doesn't already exist
    line = textlist[0]
    data = line.split()
    name = data[1]
    if firewall.has_acl_of_name(name):
        acl = firewall.get_acl_by_name(name)
    else:
        acl = ACL(firewall,name,start_num) 
    # If its not a remark, make a rule
    if data[2] != 'remark':
        priority = len(acl.rules)+1
        kind = data[2]
    else:
        return acl
   
    if kind == 'extended':
        rule = _parse_ciscoasa_9dot0_extended(data,acl,priority,kind)
    elif kind == 'standard':
        rule = _parse_ciscoasa_9dot0_standard(data,acl,priority,kind)
    acl.rules.append(rule)
    
    # NOTE: We don't increment the firewall counter here because acl rules only occupy a single
    # line so incrementing would cause the code to parse every other acl
    return acl

def _parse_ciscoasa_9dot0_extended(data,acl,priority,kind):
    # We need to fix how we handle "protocols" here, because you can have an "object" protocol
    # which is followed by a name which completely fucks up all the assumed index numbers
    rule = ExtendedACLRule(acl,priority)
    rule.kind = kind
    rule.action = data[3]
    rule.protocol = data[4]
    if rule.protocol == 'object' or rule.protocol == 'object-group':
        rule.protocol_content = data[5]
        start = 6
    else:
        start = 5
    print "FIX THE PROTOCOL PARSING PIECE SO ASA ACLS"
    #quit() 

    ## Determine the protocol, which will always be the first element to the right of the action
    #ind = data.index(rule.action)
    #rule.protocol = data[ind+1]

    # Determine the type and content of source and destination traffic. This section is highly
    # variable
    print data
    content = data[start:]
    print content
    # Determine whether or not src is "any" and handle the cascading consequences of that 
    port_ops = ('eq','neq','lt','gt','range')
    if content[0] == 'any':
        rule.src_type = 'any'
        rule.src_content = 'any'
        if content[1] in port_ops:
            print "There are port operators for source content"
            rule.src_op = content[1]
            srcopind = 1
            quit()
        else:
            rule.dest_type = content[1]
            desttypeind = 1
    else:
        rule.src_type = content[0]
        rule.src_content = content[1]
        if content[2] in port_ops:
            print "There are port operators for source content"
            rule.src_op = content[2]
            srcopind = 2
        else:
            desttypeind = 2
            rule.dest_type = content[desttypeind]

    if rule.src_op:
       if rule.src_op == 'eq':
           try:
               rule.start_srcport = int(content[srcopind+1])
           except ValueError:
               rule.start_srcport = fws.asa_port_names[content[srcopind+1]]
           desttypeind = srcopind+2
           rule.dest_type = content[desttypeind]
       elif rule.src_op == 'lt':
           try:
               rule.end_srcport = int(content[srcopind+1])
           except ValueError:
               rule.end_srcport = fws.asa_port_names[content[srcopind+1]]
           rule.start_srcport = 1
           desttypeind = srcopind+2
           rule.dest_type = content[desttypeind]
       elif rule.src_op == 'gt':
           try:
               rule.start_srcport = int(content[srcopind+1])
           except ValueError:
               rule.start_srcport = fws.asa_port_names[content[srcopind+1]]
           rule.end_srcport = 65535
           desttypeind = srcopind+2
           rule.dest_type = content[desttypeind]
       elif rule.src_op == 'range':
           try:
               rule.start_srcport = int(content[srcopind+1])
           except ValueError:
               rule.start_srcport = fws.asa_port_names[content[srcopind+1]]
           try:
               rule.end_srcport = int(content[srcopind+2])
           except ValueError:
               rule.end_srcport = fws.asa_port_names[content[srcopind+2]]
           desttypeind = srcopind+3
           rule.dest_type = content[desttypeind]
       elif rule.src_op == 'neq':
           print "what the fuck do I even do here?"
           quit()
       else: 
           print "WOAH THIS OPERATOR IS WEIRD"
           print rule.src_op
           quit()
    if rule.dest_type == 'any':
        rule.dest_content = 'any'
        try:
            if content[desttypeind+1] in port_ops:
                print "There are port operators for dest content"
                rule.dest_op = content[desttypeind+1]
                destopind=desttypeind+1
        except IndexError:
            pass
    else:
        rule.dest_content = content[desttypeind+1]
        # We need to at least check if there is a port operator, but if its not there then we get an
        # index error, hence the try,except clause
        try:
            if content[desttypeind+2] in port_ops:
                rule.dest_op = content[desttypeind+2]
                destopind = desttypeind+2
        except IndexError:
            pass

    if rule.dest_op:
       if rule.dest_op == 'eq':
           try:
               rule.start_destport = int(content[destopind+1])
           except ValueError:
               rule.start_destport = fws.asa_port_names[content[destopind+1]]
       elif rule.dest_op == 'lt':
           try:
               rule.end_destport = int(content[destopind+1])
           except ValueError:
               rule.end_destport = fws.asa_port_names[content[destopind+1]]
           rule.start_destport = 1
       elif rule.dest_op == 'gt':
           try:
               rule.start_destport = int(content[destopind+1])
           except ValueError:
               rule.start_destport = fws.asa_port_names[content[destopind+1]]
           rule.end_destport = 65535
       elif rule.dest_op == 'range':
           try:
               rule.start_destport = int(content[destopind+1])
           except ValueError:
               rule.start_destport = fws.asa_port_names[content[destopind+1]]
           try:
               rule.end_destport = int(content[destopind+2])
           except ValueError:
               rule.end_destport = fws.asa_port_names[content[destopind+2]]
       elif rule.dest_op == 'neq':
           print "what the fuck do I even do here?"
           quit()
       else: 
           print "WOAH THIS OPERATOR IS WEIRD"
           print rule.dest_op
           quit()
    
    # Determine if rule is active
    if content[-1] == 'inactive':
        rule.active = False
    
    print vars(rule)
    return rule

def _parse_ciscoasa_9dot0_standard(data,acl,priority,kind):
    print 'WOAH ITS A STANDARD RULE WRITE SOME CODE'
    print data
    
    rule = StandardACLRule(acl,priority)
    rule.kind = kind
    rule.action = data[3]
    
    if data[4] == 'any':
        rule.ip = data[4]
        rule.mask = '0.0.0.0'
    elif data[4] == 'host':
        rule.ip = data[5]
        rule.mask = '255.255.255.255'
    else:
        rule.ip = data[4]
        rule.mask = data[5]

    if data[-1] == 'inactive':
        rule.active = False
    print vars(rule)
    return rule
