import grpc
import inquirer
import json
import os
import shlex, subprocess
import shutil
import sys
import threading
import toml

from datetime import datetime
from threading import Thread

import src.util.pprint as pprint
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc
import src.intrigue.intrigue_pb2 as intrigue_pb2


'''
    refactor below
'''

def start(path_to_projects, project_name):

    print("  _                                                      ")
    print(" |_) ._ _   _ \\   _   _  _ |\/|  _. ._ \\   _.  _   _  ._ ")
    print(" |   | (_) (_  \\ (/_ _> _> |  | (_| | | \\ (_| (_| (/_ |  ")
    print("                                               _|        ")
    print(pprint.seperator)


    # Is there a project running?
    alive = _alive()
    if alive == None:
        _starter(path_to_projects, project_name)
    else:
        _manager()


def _manager():

    while True:
        choices = [
            inquirer.List('choice',
                        message="Choose an option",
                        choices = ["stop project", "restart project", "summary", "exit w/ shutdown", "exit"],
                        ),
        ]

        result = inquirer.prompt(choices)

        # Start the process
        if result['choice'] == "stop project":
            stop_project()
            break

        elif result['choice'] == "restart project":
            print("TODO")
            
        elif result['choice'] == "summary":
            report()
            print("...press enter to continue")
            input()

        elif result['choice'] == "exit w/ shutdown":
            stop_project()
            break
        else:
            break

def _starter(path_to_projects, project_name):
    choices = _get_project_names(path_to_projects)
    choices.append("Create a new Project")
    choices.append("Exit")

    choices = [
        inquirer.List('choice',
                      message="Load a project",
                      choices = choices,
                      ),
    ]

    project_choice = inquirer.prompt(choices)

    if project_choice['choice'] == "Create a new Project":
        _create_new(path_to_projects)
    elif project_choice['choice'] == "Exit":
        return
    else:
        _load_project(path_to_projects, project_choice['choice'])
        _manager()

def _create_new(path_to_projects):
    print(pprint.seperator)
    print("creating a new project")
    print(pprint.seperator)

    questions = [
        inquirer.Text('name', message="give the project a name")
    ]

    new_project = inquirer.prompt(questions)
    name = new_project['name']

    dir_name = _create_project_dir(path_to_projects,name.replace(' ','_'), 0)
    if dir_name != name:
        print("directory name: " + dir_name)

    project = {}
    project['name'] = dir_name
    project['created_at'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    project['updated_at'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    project['core_address'] = 'localhost:59500'
    project['services'] = []

    _create_project_config_file(path_to_projects, project)

    while True:
        print(pprint.seperator)

        yesno = [
            inquirer.List('continue',
                        message="Add services now",
                        choices = ['yes', 'no'],
                        ),
        ]

        yesno = inquirer.prompt(yesno)

        if yesno['continue'] == "no":
            break

        service = _create_new_service()
        project['services'].append(service)

    _create_project_config_file(path_to_projects, project)

    _load_project(path_to_projects, project['name'])


def _load_project(path_to_projects, name):
    print(pprint.seperator)
    print("project: " + name)
    print(pprint.seperator)

    choices = [
        inquirer.List('choice',
                      message="Choose an option",
                      choices = ["start project", "edit config", "delete project", "go back"],
                      ),
    ]

    result = inquirer.prompt(choices)

    # Start the process
    if result['choice'] == "start project":



        # Load the config
        conf = _parse_config(path_to_projects, name)
        if conf == None:
            print("could not parse the config...")
            return

        # Set the env and launch the core
        env = os.environ
        env['PROCM_OVERRIDE'] = "True"
        env['LOGPATH'] = path_to_projects + name + "/logs/core.log"

        # Apparently there might be an error in subprocess.Popen that leads to a
        # data race, adding a lock around the calls to subprocess.Popen seems to
        # have fixed the issue
        # https://stackoverflow.com/questions/18439712/subprocesss-popen-closes-stdout-stderr-filedescriptors-used-in-another-thread-w
        l = threading.Lock()
        l.acquire()
        subprocess.Popen(["./procm.py", "-o", "--core"], env=env)
        l.release()

        # start each service
        services = conf['services']
        for s in services:

            cmd = ["./procm.py", "-o", "--remote"]

            env = os.environ
            env['AUTO'] = "True"
            env['SRVINFO'] = json.dumps(s)
            env['LOGPATH'] = path_to_projects + name + "/logs/remotes.log"

            l.acquire()
            subprocess.Popen(cmd, env=env)
            l.release()

    elif result['choice'] == "go back":
        print(pprint.seperator)
        start(path_to_projects, None)

    elif result['choice'] == "edit config":
        _edit_project(path_to_projects, name)

    elif result['choice'] == "delete project":
        print(pprint.seperator)

        try:
            shutil.rmtree(path_to_projects + name)
            print("sucessfully deleted project")
        except:
            print("could not delete project")    

        start(path_to_projects, None)

def _edit_project(path_to_projects, name):
    print(pprint.seperator)
    print("project: " + name)
    print(pprint.seperator)


    choices = [
        inquirer.List('choice',
                      message="Choose an option",
                      choices = ["view config", "add service", "modify service", "remove services", "go back"],
                      ),
    ]

    result = inquirer.prompt(choices)

    if result['choice'] == "go back":
        print(pprint.seperator)
        _load_project(path_to_projects, name)
    else:
        c = None
        try:
            c = _parse_config(path_to_projects, name)
        except:
            print(pprint.seperator)
            print("could not load project config!")
            return

        if result['choice'] == "add service":

            c['services'].append(_create_new_service())
            print(pprint.seperator)
            print("...added")

        elif result['choice'] == "remove service":
            print("TODO")
            return

        _dump_config(path_to_projects, c)
        _edit_project(path_to_projects, name)

def _create_new_service():
    questions = [
        inquirer.Text('name', message="name"),
        inquirer.Text('path', message="path"),
        inquirer.Text('entry_point', message="entry point"),
        inquirer.Text('language', message="language"),
        inquirer.Text('interpreter', message="interpreter"),
        inquirer.Text('watch', message="rebuild on save"),
        inquirer.Text('env', message="environment variables"),
        inquirer.Text('flags', message="flags"),
    ]

    print(pprint.seperator)
    new_service = inquirer.prompt(questions)

    service = {
        "name": new_service["name"],
        "path": new_service["path"],
        "entry_point": new_service["entry_point"],
        "language": new_service["language"],
        "interpreter": new_service["interpreter"],
        "watch": new_service["watch"],
        "env": new_service["env"],
        "flags": new_service["flags"],
    }

    return service

def stop_project():
    print("stopping project")

    channel = grpc.insecure_channel("localhost:59500")
    stub = intrigue_pb2_grpc.ControlStub(channel)
    request = intrigue_pb2.EmptyRequest()
    try:
        stub.KillService(request)
    except:
        print("something wrong in shutdown...")


'''
    returns the list of all directory names in path_to_projects
'''
def _get_project_names(path_to_projects):
    names = os.listdir(path_to_projects)
    return names

'''
    create the project directory using the name of the project as given by the user,
    if the name is already taken (i.e. a folder exists w/ name) then increment the
    attempt and try again in the format name_attempt
'''
def _create_project_dir(path, name, attempt):
    working_name = path + name + '_' + str(attempt)
    if attempt == 0:
        working_name = path + name

    # if project with name already exists, increment attempt and try again
    if os.path.exists(working_name):
        return _create_project_dir(path,name,attempt+1)

    os.mkdir(working_name)
    os.mkdir(working_name + "/logs")

    return name if attempt == 0 else name + '_' + str(attempt)

'''
    creates the project config file at path/config.dir_name
'''
def _create_project_config_file(path, config):
    f = open(path + config['name'] + "/config.toml", "w+")
    f.write(toml.dumps(config))
    f.close()


'''
    launch project forks and exec's the project specified by the name
'''
def _launch_project(path, name):
    print(pprint.seperator)

    # launch the core without waiting
    cmd = ["./procm.py", "-o", "--core"]
    p = subprocess.Popen(cmd, stderr=None, stdout=subprocess.DEVNULL, stdin=None)
    # p.wait()



def _alive():
    channel = grpc.insecure_channel("localhost:59500")
    stub = intrigue_pb2_grpc.ControlStub(channel)

    try:
        response = stub.Alive(intrigue_pb2.Ping())
        return response
    except:
        return None

def _summary():
    channel = grpc.insecure_channel("localhost:59500")
    stub = intrigue_pb2_grpc.ControlStub(channel)

    request = intrigue_pb2.Action()
    request.Request = "summary.all"

    try:
        response = stub.Summary(request)
        return response
    except:
        return None



''' 
    cli - report - list status of running procman
'''
def report():
    # print("getting the status of procman...")


    '''
        TODO: have each service in a selectable for more info on it 
    '''

    stub = intrigue_pb2_grpc.ControlStub(grpc.insecure_channel("localhost:59500"))
    remotes = stub.Summary(intrigue_pb2.Action(Request="summary.all"))

    print("--------------------------------------------------------------------------------------")
    print("    {0:4}\u2502{1:8}\u2502{2:8}\u2502{3:7}\u2502{4:12}\u2502{5:6}\u2502{6:6}\u2502{7:24}"
            .format("id", "name", "langauge", "watched","status", "pid", "errors", "path"))
    print("    {0:\u2550<4}\u256A{0:\u2550<8}\u256A{0:\u2550<8}\u256A{0:\u2550<7}\u256A{0:\u2550<12}\u256A{0:\u2550<6}\u256A{0:\u2550<6}\u256A{0:\u2550<24}"
            .format(""))

    rmts = []
    for rmt in remotes.Remotes:
        rmts.append(" {0:4}\u2502{1:8}\u2502{2:8}\u2502{3:7}\u2502{4:12}\u2502{5:6}\u2502{6:6}\u2502{7:24}"
                .format(rmt.ID, rmt.Services[0].Name, rmt.Services[0].Language,  "no", rmt.Services[0].Status, rmt.Services[0].Pid, "errors", "path"))
    # print("-----------------------------------------------------------------------------------")

    rmts.append(" restart all")
    rmts.append(" reload")
    rmts.append(" ...back")

    choices = [
        inquirer.List('choice',
                      message=None,
                      choices = rmts,
                      ),
    ]

    result = inquirer.prompt(choices)

    if result['choice'] == " reload":
        report()

    elif result['choice'] == " ...back":
        _manager()

def _dump_config(path, config):
    f = open(path + config['name'] + "/config.toml", "w+")
    f.write(toml.dumps(config))
    f.close()

def _parse_config(path, name):
    try:
        c = toml.load(path + name + "/config.toml", _dict=dict)
        return c
    except:
        return None

def edit_project(path, name):
    config = _parse_config(path,name)

    if config == None:
        print("error parsing config")
        return
