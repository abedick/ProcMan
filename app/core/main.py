import concurrent.futures as futures
import grpc
import os
import signal
import threading

import src.intrigue.intrigue_pb2 as intrigue_pb2
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc
import app.core.rpc.control as control
import app.core.router as rtr
import src.util.color as color

class core(object):

    # The address that the control server will be hosted at
    address = ''

    # The grpc server object
    server = None

    # The object that holds the information related to each connected remote 
    # process manager
    router = rtr.router()

    # read from an env var, if true, when sending shutdown message, remotes must
    # terminate their children and then themselves
    override = False

    log_fd = None

    '''
        initialize the core w/ the address passed in 
    '''
    def __init__(self, address):

        try:
            log_path = os.environ['LOGPATH']
            self.log_fd = open(log_path, "a+")
        except:
            print("could not create log for core")

        self._print(" ._                         ")
        self._print(" |_) ._ _   _ |\\/|  _. ._  ")
        self._print(" |   | (_) (_ |  | (_| | |  ")

        self.address = address

        try:
            override = os.environ['PROCM_OVERRIDE']
            if override == 'True':
                self.override = True
        except:
            pass

    '''
        start the grpc server using the address passed into the constructor
    '''
    def start_server(self):
        self._print("starting service @ " + self.address)
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        intrigue_pb2_grpc.add_ControlServicer_to_server(control.Control(self), self.server)
        self.server.add_insecure_port(self.address)
        self.server.start()
        self._print("core started")

    '''
        register the remote server (called from the control object)
    '''
    def register_remote(self, mode, addr, env):
        self._print("registering new remote")
        return self.router.add_service(mode, addr, env)

    '''
        mark the shutdown of a remote (as per the stored state)
    '''
    def shutdown_remote(self, id):
        return self.router.shutdown_service(id)

    '''
        block the main thread until shutdown; then run the shutdown procedures
    '''
    def wait(self):
        self._print("waiting for signal to end server")
        signal.sigwait([signal.SIGINT])

        self._shutdown()

    '''
        send the shutdown notice to the router
    '''
    def _shutdown(self):
        self._print("sending shutdown notif to all attached services")

        # Shutdown the server, handling no new requests and cancelling all in flight
        self.server.stop(None)

        # Send shutdown to remote grpc servers
        self.router.shutdown_all(self.override)

        try:
            self.log_fd.close()
        except:
            pass

    def _print(self, msg):
        if self.log_fd == None:
            print(msg)
        else:
            try:
                self.log_fd.write(msg + "\n")
                self.log_fd.flush()
            except:
                print("fucking hell")