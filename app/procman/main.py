import concurrent.futures as futures
import grpc
import signal
import subprocess
import sys
import threading
import time

from datetime import datetime

import src.util.enum as enum
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc
import src.intrigue.intrigue_pb2 as intrigue_pb2
import app.procman.service as service
import app.procman.rpc.remote as remote_server

class registration(object):

    id = None
    address = None
    fingerprint = None

    def __init__(self, id, addr, fp):
        self.id = id
        self.address = addr
        self.fingerprint = fp

class remote(object):

    # The address to the core control server used to establish all control links with
    core_address = ''

    # The registration from core with instructions for starting the procm grpc server
    reg = None
    reg_mu = threading.Lock()

    # The grpc server object
    server = None

    # The time the procman service is started
    start_time = None

    # The status of the service attached to the remote
    status = enum.RemoteState.UNINITIALIZED

    # The object that manages the child-process
    # The data needed to start the service will come from the registration
    manager = service.manager()

    # helps cleanup threads on shutdown if in connecting state
    # TODO: There is definitely a smoother way of handling this;
    #       The issue -- if the core has been shutdown and the grpc remote server is
    #       the caller of _connect, the thread is not set to deamon mode and will not
    #       exit with the main thread.
    continue_connecting = True

    # Service details about/ how to launch child service
    service_details = None

    # child process; i.e. the point of a process manager
    service = None

    def __init__(self, core_address):
        self.core_address = core_address
        self.start_time = datetime.now().strftime("%s")

    '''
        Begin the attempt to contact core
    '''
    def connect(self):
        print("attempting to make initial connection to core")
        connect_thread = threading.Thread(target=self._connect, daemon=True)
        connect_thread.start()

    '''
        (1)
        Intended to be run in it's own thread. Attempts to make connection to core
        and retrieve a registration that can then be used to start the grpc server
        for procm
    '''
    def _connect(self):
        
        if not self.continue_connecting:
            return

        channel = grpc.insecure_channel(self.core_address)
        stub = intrigue_pb2_grpc.ControlStub(channel)

        request = intrigue_pb2.ServiceUpdate()
        request.Request = "remote.register"
        request.Message = ""
        request.Env = ""
        request.Address = ""

        try:
            response = stub.NewRegistration(request)
            serviceInfo = response.ServiceInfo

            self.reg_mu.acquire()
            self.reg = registration(serviceInfo.ID, serviceInfo.Address, serviceInfo.Fingerprint)
            self.reg_mu.release()

            print("connected to core; registration =", end=' ')
            print(serviceInfo)

            try:
                self._start_server()
            except:
                print("error starting server...telling core")
                self._shutdown()

        except:
            print("could not contact core; trying again in 5 seconds")
            time.sleep(5)
            self._connect()
        
    '''
        (2)
        start the remote server with the address acquired from the registration
    '''
    def _start_server(self):
        print("starting remote server @ " + self.reg.address)
        
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        intrigue_pb2_grpc.add_RemoteServicer_to_server(remote_server.Remote(self), self.server)
        self.server.add_insecure_port(self.reg.address)
        self.server.start()
        print("server started")

    '''
        start the child service using the details passed in
    '''
    def launch(self, service_details):
        self.service_details = service_details

        path = service_details['path']
        entry = service_details['entry_point']
        interpreter = "/usr/bin/python"

        cmd = [interpreter, path+entry]


        self.service = subprocess.Popen(cmd)




    '''
        blocking until sigint
    '''
    def wait(self):
        print("waiting for signal to end remote")
        signal.sigwait([signal.SIGINT])
        self._shutdown()        

    '''
        sends a shutdown notice to core
    '''
    def _shutdown(self):
        print("shutdown")

        channel = grpc.insecure_channel(self.core_address)
        stub = intrigue_pb2_grpc.ControlStub(channel)

        request = intrigue_pb2.ServiceUpdate()
        request.Request = "shutdown.notif"

        try:
            # reg might not exist if the server has already been shutdown...
            request.Message = self.reg.id

            response = stub.UpdateRegistration(request)
            print(response)
        except:
            print("could not notify core of shutdown...")

        self.continue_connecting = False
    
    '''
        disconnection, wipe the registration and go back to connecting
    '''
    def core_shutdown(self):
        print("recieved core shutdown in remote object")

        self.reg_mu.acquire()
        self.reg = None
        self.reg_mu.release()

        # shutdown the current remote server if still running
        try:
            # True for graceful shutdown
            self.server.stop(True)
        except:
            pass

        # return to the connecting state, attempting to get a registration
        self._connect()

    '''
    '''
    def _register(self):
        print("registering a new service")
