#!/usr/local/bin/python3

import argparse
import json
import os
import subprocess
import toml

from threading import Thread

import app.core.main as router
import app.cli.main as cli
import app.procman.main as procman

address = "localhost:59500"
path_to_projects = "./projects/"

'''
    tentative colors for debug
        core = cyan
        remotes = magenta
        cli = white
'''

def main(args):

    if args.override:

        if args.core:

            core = router.core(address)
            core.start_server()
            
            # parse the config
            if args.config != "":
                try:
                    c = toml.load(args.config, _dict=dict)
                    Thread(target=launch_remotes, args=[c['services']]).start()
                except:
                    # print("could not parse config!")
                    pass

            core.wait()

        elif args.remote:

            pm = procman.remote(address)
            pm.connect()
            
            auto = None
            try:
                auto = os.environ['AUTO']
            except:
                pass

            if auto == "True":
                # print("will launch child service")
                service_string = os.environ['SRVINFO']
                service = json.loads(service_string)
                pm.launch(service)

            pm.wait()

        else:
            print("error, must specify core or remote in override mode")


    elif args.stop:
        cli.stop_project()

    elif args.report:
        cli.report()

    else:
        cli.start(path_to_projects, None)

def launch_remotes(services):
    print("launching remotes")
    print(services)

    service_processes = []

    for s in services:
        cmd = ["./procm.py", "-o", "--remote"]

        env = os.environ
        env['AUTO'] = "True"
        env['SRVINFO'] = json.dumps(s)

        service_processes.append(subprocess.Popen(cmd, env=env))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    '''
        override options allow procm to be ran in override mode;
        - must specify core or remote
    '''
    parser.add_argument("-o", dest='override', action='store_true')
    parser.add_argument("--core", dest='core', action='store_true')
    parser.add_argument("--remote", dest='remote', action='store_true')
    parser.add_argument("--config", dest='config')
    parser.add_argument("--stop", dest='stop', action='store_true')

    '''
        managed operation flags (only to be used by the cli launcher)
    '''
    parser.add_argument("-m", dest='managed', action='store_true')
    parser.add_argument("--run", dest='run', action='store_true')
    parser.add_argument("--name", dest='name')

    parser.add_argument("--edit", dest='edit')

    parser.add_argument("--report", dest='report', action='store_true')

    main(parser.parse_args())