import grpc
import json
import os
import shlex, subprocess
import sys
import toml

from datetime import datetime
from threading import Thread

import src.util.pprint as pprint
import src.intrigue.intrigue_pb2_grpc as intrigue_pb2_grpc
import src.intrigue.intrigue_pb2 as intrigue_pb2

'''
    starts a project using the path (specified by config) + the project name 
    (specified by user) if it can be found.

    if project_name == '' then list all projects found in path_to_projects
    if no projects in path_to_projects, ask the user if they would liek to create 
        one
'''
def start_project(path_to_projects, project_name=''):

    print("looking for projects in dir: " + path_to_projects)
    
    if project_name == '':

        names = _get_project_names(path_to_projects)
        if len(names) == 0:
            print("no projects found; would you like to create one?[Y/n]: ", end=' ')

            should_continue = input()
            if should_continue == 'y' or should_continue == 'Y':
                create_project(path_to_projects)

        else:
            print("found projects")
            print(pprint.seperator)

            for i in range(len(names)):
                print(str(i+1) + ". " + names[i])

            print(pprint.seperator)
            print("Choose a project (number or name): ", end=' ')

            selection = input()

            name = ''
            try:
                selection = int(selection)
                name = names[selection-1]
            except:
                try:
                    index = names.index(selection)
                    name = names[index]
                except:
                    print("...could not load project")
                    return
            
            _launch_project(path_to_projects, name)
            # print(name)
            # if not isInt:

    else:

        if os.path.exists(path_to_projects + project_name):
            print("found project")

            # Parse the config
            # try:
            # print(path_to_projects + project_name + "/config.toml")


            c = toml.load(path_to_projects + project_name + "/config.toml", _dict=dict)
            print(c)

            env = os.environ
            env['PROCM_OVERRIDE'] = "True"

            subprocess.Popen(["./procm.py", "-o", "--core"], env=env)
            Thread(target=launch_remotes, args=[c['services']]).start()

                
            # except:
            #     print("could not parse config!")

        else:
            print("could not find a project with the specified name")


def launch_remotes(services):
    print("launching remotes")
    print(services)

    service_processes = []

    for s in services:
        cmd = ["./procm.py", "-o", "--remote"]

        env = os.environ
        env['AUTO'] = "True"
        env['SRVINFO'] = json.dumps(s)

        subprocess.Popen(cmd, env=env)

'''
    create a new procm project using the cli
'''
def create_project(path_to_projects):
    print(pprint.seperator)
    print("creating new procm project")
    print(pprint.seperator)

    print("name:", end=' ')
    name = input()

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

    print("created at: " + project['created_at'])
    print("core address (default): " + project['core_address'])
    print("...created")
    print(pprint.seperator)
    print("...would you like to start the project now?[Y/n]", end=' ')
    start = input()

    return project['name'] if start == 'y' or start == 'Y' else None


def stop_project():
    print("stopping project")

    channel = grpc.insecure_channel("localhost:59500")
    stub = intrigue_pb2_grpc.ControlStub(channel)
    request = intrigue_pb2.EmptyRequest()
    stub.KillService(request)


'''
    returns the list of all directory names in path_to_projects
'''
def _get_project_names(path_to_projects):
    print(path_to_projects)
    names = os.listdir(path_to_projects)
    print(names)
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



''' 
    cli - report - list status of running procman
'''
def report():
    # print("getting the status of procman...")

    channel = grpc.insecure_channel("localhost:59500")
    stub = intrigue_pb2_grpc.ControlStub(channel)

    request = intrigue_pb2.Action()
    request.Request = "summary.all"

    response = stub.Summary(request)
    # print(response)

    pprint.report(response)


def _dump_config(path, name):
    print("todo")
    pass

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

    