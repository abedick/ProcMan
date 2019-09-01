import src.intrigue.intrigue_pb2 as intrigue_pb2
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc

class Remote(intrigue_pb2_grpc.RemoteServicer):

    # for communicating back information regarding rpc requests from core
    remote = None

    def __init__(self, remote):
        self.remote = remote

    def NotifyAction(self, request, context):
        print("NotifyAction")
        print(request)
        if request.Request == "notif.shutdown":
            print("recieved shutdown notification from core")

            override = False
            if request.Message == "forceful":
                override = True

            self.remote.core_shutdown(override)
            return intrigue_pb2.Receipt()

    def Summary(self, request, context):
        print("remote.summary.request")

        manager = intrigue_pb2.ProcessManager()

        try:
            manager.ID = self.remote.reg.id
            manager.Address = self.remote.reg.address
            manager.Errors.extend(["test.errs"])    
        except:
            manager.Errors.extend(["could not report data; reg == None"])


        # dummy service
        service = intrigue_pb2.Service()
        service.Name = self.remote.manager.name
        service.Language = self.remote.manager.language
        service.Fails = 0
        service.Restarts = 0
        # service.Pid = self.remote.manager.process.Pid()
        service.Pid = 111
        service.Status = "s.status"
        service.Path = self.remote.manager.path
        
        manager.Services.extend([service])

        manager.StartTime = self.remote.start_time
        manager.Status = self.remote.status.name
        manager.LogPath = "not.configured"

        receipt = intrigue_pb2.SummaryReceipt()
        receipt.Remotes.extend([manager])

        return receipt

    def UpdateRegistration(self, request, context):
        print("UpdateRegistration")
        print(request)


    def Alive(self, request, context):
        print("Alive")
