import threading
import time
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

    # The total number of failures of the process
    number_fails = 0
    lsat_fail_time = None

    # The number of failures in a 30 second period (if >3, process will not be
    # automatically restarted)
    fail_timeout_cnt = 0

    log_fd = None

    def __init__(self, raw_details, log_fd):
        self.name = raw_details['name']
        self.path = raw_details['path']
        self.entry_point = raw_details['entry_point']
        self.language = raw_details['language']
        self.interpreted = raw_details['interpreted']
        self.watch = raw_details['watch']

        self.cmd = self._get_cmd()

        self.state = enum.ProcessState.UNINITIALIZED

        self.log_fd = log_fd
    
    '''
        fork and exec the process
    '''
    def run(self):

        try:
            self.process = subprocess.Popen(["/usr/bin/python", self.cmd])

            threading.Thread(target=self._manage_state, daemon=True)

            self.mu.acquire()
            self.state = enum.ProcessState.RUNNING
            self.last_start_Time = datetime.now().strftime("%s")

            if self.first_start_time == None:
                self.first_start_time = datetime.now().strftime("%s")

        except:
            self._log("could not start service")
        finally:
            if self.mu.locked():
                self.mu.release()

        self.listener()

    '''
        listen to the process
    '''
    def listener(self):
        self._log("listening to child process")
        self.process.wait()
        self._log("child process terminated")

        self._log(str(self.state))

        # if process isn't restarting or shutting down (i.e. failed)
        if (self.state !=  enum.ProcessState.RESTARTING) and (self.state != enum.ProcessState.SHUTDOWN):
            self._log("restarting process from failure")

            self.mu.acquire()
            self.number_fails += 1
            self.fail_timeout_cnt += 1
            self.last_fail_time = datetime.now().strftime("%s")
            self.mu.release()

            # Restart only if not failed too many times (kept track of by 
            # self.manage_state)
            if self.fail_timeout_cnt < 3:
                self.run()
            else:
                self._log("giving up on " + self.name)
                self.mu.acquire()
                self.state = enum.ProcessState.FAILED
                self.mu.release()

    '''

    '''
    def _manage_state(self):
        time.sleep(30)
        if self.state == enum.ProcessState.RUNNING:
            self.mu.acquire()
            self.state = enum.ProcessState.STABLE
            self.mu.release()

    def stop(self):
        self.mu.acquire()
        self.state = enum.ProcessState.SHUTDOWN
        self.mu.release()
        try:
            self.process.kill()
        except:
            self._log("no process to kill")

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


    def _log(self, msg):
        if self.log_fd == None:
            print(msg)
        else:
            self.log_fd.write(msg + "\n")
            self.log_fd.flush()