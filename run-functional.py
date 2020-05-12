#!/usr/bin/env python

import argparse
import ast
import configparser
import ansible_runner
import os
import re
import time
from termcolor import colored
import yaml

test_directory = "./functional_tests"
ansible_tests_list = []
ansible_run_list = []
tests_list = []
iterations = 20
maxfailures = 3
keepartifacts = 5
debug = False
config = None

def parse_command_line():
    parser = argparse.ArgumentParser(
        description='Run ansible playbooks concurrently and with loops')
    parser.add_argument('-c', '--config', dest='config_file',
                        required=False, action='store', help='Config file in ini format')

    return parser.parse_args()

def parse_config_file(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def get_tests(test_directory):
    directories = os.listdir(test_directory)
    tests = []
    for i in directories:
        if re.match('^[0-9][0-9].*', i):
            tests.append(i)
    return(sorted(tests))


def launch_ansible_test(test_to_launch, test_directory, test_type, invocation, failure_count):

    inventory = config.get('General', 'inventory', fallback=None) if config else None

    extra_vars_file = config.get('General', 'extra_vars', fallback=None) if config else None
    extravars = None

    private_data_dir = test_directory + '/' + test_to_launch
    output_dir = config.get('General', 'output_dir', fallback=None) if config else None
    if output_dir:
        private_data_dir = output_dir + '/' + test_to_launch
        os.makedirs(private_data_dir, mode=0o700, exist_ok=True)
    else:
        pass

    if config and config.has_section('Ansible Runner Settings'):
        settings = dict(config.items('Ansible Runner Settings'))
    else:
        settings = None

     # ansible_runner.interface.run _SHOULD_ take a dict here. But it doesn't )-:
     # So instead we'll write a yaml file into the output dir, this seem to work...
    if settings and output_dir:

        # first convert from strings
        for v in settings:
            try:
                settings[v] = ast.literal_eval(settings[v])
            except ValueError:
                pass

        os.makedirs(private_data_dir + '/env', mode=0o700, exist_ok=True)
        if os.path.exists(private_data_dir + '/env/settings'):
            os.remove(private_data_dir + '/env/settings')
        with open(private_data_dir + '/env/settings', 'w') as f:
            yaml.safe_dump(settings, f)

    if extra_vars_file:
        with open(extra_vars_file, 'r') as f:
            extravars = yaml.safe_load(f)

    (t, r) = ansible_runner.interface.run_async(
        private_data_dir=private_data_dir,
        playbook=test_directory + '/' + test_to_launch + '/' + test_type + '.yml',
        inventory=inventory,
        extravars=extravars,
        rotate_artifacts=keepartifacts,
        ident=test_type + '_' + str(invocation) + '_' + str(failure_count))
    return({
        'thread': t,
        'runner': r,
        'test': test_to_launch,
        'test_directory': test_directory
    })


def launch_ansible_tests(list_of_tests, test_type):
    running_tests = []
    for test in list_of_tests:
        launched_test = launch_ansible_test(test, test_directory, test_type, 1, 0)
        running_tests.append({
            'thread': launched_test['thread'],
            'runner': launched_test['runner'],
            'test_name': launched_test['test'],
            'test_directory': launched_test['test_directory'],
            'test_type': test_type,
            'iteration': 1,
            'failures': 0
        })
        print(colored("Launching : {} - {} :{}: iteration {}".format(
            test, launched_test['runner'].status,
            test_type, 1), 'yellow')
        )
    return(running_tests)


def check_ansible_loop(run_list, iteration):
    while run_list:
        for test in run_list:
            if test['runner'].status == 'successful':
                if test['iteration'] >= iteration:
                    run_list.remove(test)
                    print(colored("Complete : {} - {} :{}: iteration {}".format(
                        test['test_name'], test['runner'].status,
                        test['test_type'], test['iteration']), 'green')
                    )
                else:
                    test['iteration'] += 1
                    launched_test = launch_ansible_test(
                        test['test_name'], test_directory, test['test_type'], test['iteration'], test['failures'])
                    test['thread'] = launched_test['thread']
                    test['runner'] = launched_test['runner']
                    print(colored("Launching : {} - {} :{}: iteration {}".format(
                        test['test_name'], test['runner'].status,
                        test['test_type'], test['iteration']), 'yellow')
                    )
            elif test['runner'].status == 'running' or test['runner'].status == 'starting':
                if debug:
                    print(colored("Running : {} - {} :{}: iteration {}".format(
                        test['test_name'], test['runner'].status,
                        test['test_type'], test['iteration']), 'cyan')
                    )
            else:
                if test['failures'] >= maxfailures:
                    run_list.remove(test)
                    print(colored("Error : {} - {}: {}: iteration {} Max failures exceeded, removeing test".format(
                        test['test_name'], test['runner'].status,
                        test['test_type'], test['iteration']), 'red')
                    )
                else:
                    test['failures'] += 1
                    launched_test = launch_ansible_test(
                        test['test_name'], test_directory, test['test_type'], test['iteration'], test['failures'])
                    test['thread'] = launched_test['thread']
                    test['runner'] = launched_test['runner']
                    print(colored("Re-launching : {} - {} :{}: iteration {}".format(
                        test['test_name'], test['runner'].status,
                        test['test_type'], test['iteration']), 'magenta')
                    )
        time.sleep(2)


if __name__ == '__main__':
    args = parse_command_line()
    if args.config_file:
        config = parse_config_file(args.config_file)
        test_directory = config.get('General', 'test_directory', fallback='./functional_tests')
        iterations = config.getint('General', 'iterations', fallback=20)
        keepartifacts = iterations
        maxfailures = config.getint('General', 'max_failures', fallback=3)

    ansible_tests_list = get_tests(test_directory)
    ansible_run_list = launch_ansible_tests(ansible_tests_list, 'setup')
    check_ansible_loop(ansible_run_list, 1)
    ansible_run_list = launch_ansible_tests(ansible_tests_list, 'test')
    check_ansible_loop(ansible_run_list, iterations)
