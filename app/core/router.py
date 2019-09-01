import grpc
import threading
import uuid

from datetime import datetime

import src.util.enum as enum
import src.util.color as color
import src.intrigue.intrigue_pb2 as intrigue_pb2
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc

class remote_server(object):

    address = ''
    id = '' 
    state = enum.RemoteState.RUNNING
    mode = ''
    last_ping = ''
    fingerprint = ''

    def __init__(self, reg):
        self.address = reg['addr']
        self.id = reg['id']
        self.last_ping = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.mode = reg['mode']
        self.fingerprint = reg['fingerprint']

    '''
        updates the state of the remote_server; up to the caller to pass in an 
        actual state as defined by RemoteStateEnum
    '''
    def update_state(self, new_state):
        self.state = new_state


# Router controls the handling of attached remote servers including assigning addresses
# and managing the actual instance of each along with reporting all associated errors
class router(object):

    # map[ID]RemoteServer holds the internal lookup of each of the attached remote servers
    remotes = {}

    verbose = True

    mu = threading.Lock()

    # id handling
    id_counter = 0
    id_mu = threading.Lock()

    # address handling
    hostname = "localhost"
    next_port = 59500
    addr_mu = threading.Lock()


    def __init__(self):
        pass

    def add_service(self, mode, addr, env):

        reg = {}
        reg['id'] = self._assign_id()
        reg['addr'] = self._assign_address()
        reg['mode'] = "unmanaged"
        reg['fingerprint'] = str(uuid.uuid1())

        service = remote_server(reg)

        self.mu.acquire()
        self.remotes[service.id] = service
        self.mu.release()

        return reg

    def shutdown_service(self, id):

        service = self._lookup_service_by_id(id)
        if service == None:
            return "error.not_found"
        
        service.update_state(enum.RemoteState.KILLED)
        return "success"

    '''
        iterates through all stored services and forwards them to _send_shutdown
    '''
    def shutdown_all(self, override):
        for service in self.remotes:
            self._send_shutdown(self.remotes[service].id, self.remotes[service].address, override)

    '''
        sends a grpc message to the address with the shutdown notification procedure
    '''
    def _send_shutdown(self, id, address, override):
        channel = grpc.insecure_channel(address)
        stub = intrigue_pb2_grpc.RemoteStub(channel)

        request = intrigue_pb2.Action()
        request.Request = "notif.shutdown"
        if override:
            request.Message = "forceful"
        request.RemoteID = id

        try:
            stub.NotifyAction(request)
        except:
            color.cyan("error sending update request")

    '''
        returns the remote_server object with the associated id; else None
    '''
    def _lookup_service_by_id(self, id):
        return self.remotes[id]

    '''
        get all the stored remotes
    '''
    def lookup_all_remotes(self):
        return self.remotes

    '''
        assign_id returns the next ID and then increments the counter
    '''
    def _assign_id(self):
        self.id_mu.acquire()
        self.id_counter += 1
        self.id_mu.release()
        return "r" + str(self.id_counter)

    '''
        assign_address using the hostname and incremented port
    '''
    def _assign_address(self):
        self.addr_mu.acquire()
        self.next_port += 2
        self.addr_mu.release()
        return self.hostname + ':' + str(self.next_port)
