import grpc
import os
import signal

import src.util.enum as enum
import src.intrigue.intrigue_pb2 as intrigue_pb2
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc

class Control(intrigue_pb2_grpc.ControlServicer):

    # The reference back to core
    core = None

    def __init__(self, core):
        self.core = core

    def StartService(self, request, context):
        print("StartService")

    def KillService(self, request, context):
        os.kill(os.getpid(), signal.SIGINT)
        print("KillService")

    def RestartService(self, request, context):
        print("RestartService")

    def Summary(self, request, context):

        if request.Request == "summary.all":
            print("getting summary for all connected remotes")

            rmts = self.core.router.lookup_all_remotes()
            rmts_info = []
            for i in rmts:

                # try to contact the service
                try:
                    channel = grpc.insecure_channel(rmts[i].address)
                    stub = intrigue_pb2_grpc.RemoteStub(channel)

                    request = intrigue_pb2.Action(Request='request.info.all')
                    response = stub.Summary(request)
                    rmts_info.extend(response.Remotes)

                except:
                    
                    # if fail to contact service and it's not marked as killed, 
                    # update the state to failed
                    if rmts[i].state != enum.RemoteState.KILLED:
                        rmts[i].update_state(enum.RemoteState.FAILED)

                    # If fail to contact service, use as much info from core as
                    # possible
                    rmt = intrigue_pb2.ProcessManager()
                    rmt.ID = rmts[i].id
                    rmt.Address = rmts[i].address

                    rmt.Status = rmts[i].state.name                    
                    rmts_info.extend([rmt])

            receipt = intrigue_pb2.SummaryReceipt()
            receipt.Remotes.extend(rmts_info)
            return receipt

    def StopServer(self, request, context):
        print("StopServer")

    def NewRegistration(self, request, context):
        print("registerRemote; ", request)

        msg = request.Message
        env = request.Env
        addr = request.Address

        registration = self.core.register_remote(msg, addr, env)
        print(registration)
        if registration == None:
            receipt = intrigue_pb2.Receipt()
            receipt.Message = "error"
            return receipt

        summary = intrigue_pb2.ServiceSummary()
        summary.Address = registration['addr']
        summary.ID = registration['id']
        summary.Fingerprint = registration['fingerprint']

        receipt = intrigue_pb2.Receipt()
        receipt.Message = "registered"
        receipt.ServiceInfo.CopyFrom(summary)
        return receipt

    def UpdateRegistration(self, request, context):
        print("UpdateRegistration")
        print(request)

        resp = intrigue_pb2.Receipt()

        if request.Request == "shutdown.notif":
            status = self.core.shutdown_remote(request.Message)
            resp.Message = status

            print("status of shutdown process = ", status)
        
        return resp

    def Alive(self, request, context):
        print("Alive")
