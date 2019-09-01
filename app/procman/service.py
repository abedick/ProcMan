import threading
import subprocess

from datetime import datetime

import src.util.color as color
import src.util.enum as enum

class manager(object):

    # All of these come directly from the config toml file

    name = ''
    path = ''
    entry_point = ''
    language = ''
    interpreted = False
    watch = False

    cmd = ''

    process = None

    mu = threading.Lock()
    state = None

    first_start_time = None
    last_start_Time = None

    number_failes = 0
    lsat_fail_time = None

    def __init__(self, raw_details):
        self.name = raw_details['name']
        self.path = raw_details['path']
        self.entry_point = raw_details['entry_point']
        self.language = raw_details['language']
        self.interpreted = raw_details['interpreted']
        self.watch = raw_details['watch']

        self.cmd = self._get_cmd()

        self.state = enum.ProcessState.UNINITIALIZED
    
    '''
        fork and exec the process
    '''
    def run(self):

        try:
            self.process = subprocess.Popen(["/usr/bin/python", self.cmd])

            self.mu.acquire()
            self.state = enum.ProcessState.RUNNING
            self.last_start_Time = datetime.now().strftime("%s")

            if self.first_start_time == None:
                self.first_start_time = datetime.now().strftime("%s")

            self.mu.release()

        except:

            color.magenta("could not start service")

        self.listener()

    '''
        listen to the process
    '''
    def listener(self):
        color.magenta("listening to child process")
        self.process.wait()
        color.magenta("child process terminated")

        color.magenta(str(self.state))

        # if process isn't restarting or shutting down (i.e. failed)
        if (self.state !=  enum.ProcessState.RESTARTING) and (self.state != enum.ProcessState.SHUTDOWN):
            color.magenta("restarting process from failure")

            self.mu.acquire()
            self.number_failes += 1
            self.last_fail_time = datetime.now().strftime("%s")
            self.mu.release()

            self.run()

    def stop(self):
        self.mu.acquire()
        self.state = enum.ProcessState.SHUTDOWN
        self.mu.release()
        self.process.kill()

    '''
        parse the complete path to the entry point
    '''
    def _get_cmd(self):
        cmd = self.path
        if cmd.endswith('/'):
            if self.entry_point.startswith('/'):
                cmd += self.entry_point[1:]
            else:
                cmd += self.entry_point
        else:
            if not self.entry_point.startswith('/'):
                cmd += self.entry_point[1:]
            else:
                cmd += self.entry_point
        return cmd