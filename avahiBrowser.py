# Based on http://avahi.org/wiki/PythonBrowseExample

import dbus, gobject, avahi, redis, socket
from dbus import DBusException
from dbus.mainloop.glib import DBusGMainLoop
from symbol import except_clause

r = redis.StrictRedis(host='localhost', port=6379, db=0)

TYPE = '_casqsys._tcp'

def service_resolved(*args):
    # Server discovery check
    print 'adding %s with %s' % (args[2], args[7])
    ip = args[7]
    try:
        s = socket.create_connection((ip, 80), 5)
        # trying to connect to http server for 2 seconds
        s.shutdown(2)
        s.close()
        # everything fine, let's add ip to db
        r.sadd('ip', ip)
    except:
        # something went wrong ip not added
        print 'Unreachable ' + ip
          
def print_error(*args):
    print 'error_handler'
    print args[0]
    
def myhandler(interface, protocol, name, stype, domain, flags):
    # discovery call back
    #print "Found service '%s' type '%s' domain '%s' " % (name, stype, domain)
    if (0 == (flags & avahi.LOOKUP_RESULT_LOCAL)):
        server.ResolveService(interface, protocol, name, stype,
                              domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                              reply_handler=service_resolved, error_handler=print_error)

loop = DBusGMainLoop()

bus = dbus.SystemBus(mainloop=loop)

server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, '/'),
        'org.freedesktop.Avahi.Server')

def check_stream():
    # server check loop
    print "Checking present helmet"
    for ip in r.smembers('ip'):
        print "Checking : " + ip
        try:
            s = socket.create_connection((ip, 80), 5)
            s.shutdown(2)
            s.close()
        except:
            print 'Removing ' + ip
            r.srem('ip', ip)
    # return True to allow periodic calls
    return True


def check_hosts():
    print "Avahi Check"
    sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
            server.ServiceBrowserNew(avahi.IF_UNSPEC,
                avahi.PROTO_UNSPEC, TYPE, 'local', dbus.UInt32(0))),
            avahi.DBUS_INTERFACE_SERVICE_BROWSER)
    sbrowser.connect_to_signal("ItemNew", myhandler)
    # return True to allow periodic calls
    return True
    
check_hosts()

gobject.timeout_add(10000, check_stream)
# stream checks every 10 s

gobject.timeout_add(60000, check_hosts)
# new server seeks every minutes

gobject.MainLoop().run()
