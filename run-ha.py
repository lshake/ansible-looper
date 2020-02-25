#!/usr/bin/env python

import ansible_runner
import os
import re
import time
import random
from termcolor import colored

test_directory = "/Users/lshakesp/projects/ansible/ansible-runner/ha_tests"
ansible_tests_list = []
ansible_run_list = []
tests_list = []
iterations = 20
maxfailures = 3
debug = False


def get_tests(test_directory):
    directories = os.listdir(test_directory)
    tests = []
    for i in directories:
        if re.match('^[0-9][0-9].*', i):
            tests.append(i)
    random.shuffle(tests)
    print(tests)
    return(tests)


def launch_ansible_test(test_to_launch, test_directory, test_type):
    (t, r) = ansible_runner.interface.run_async(
        private_data_dir=test_directory + '/' + test_to_launch,
        playbook=test_type + '.yml')
    return({
        'thread': t,
        'runner': r,
        'test': test_to_launch,
        'test_directory': test_directory
    })


def launch_ansible_tests(list_of_tests, test_type):
    running_tests = []
    for test in list_of_tests:
        launched_test = launch_ansible_test(test, test_directory, test_type)
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


def convert_test_list_to_dict(list_of_tests, test_type):
    d = []
    for i in list_of_tests:
        d.append({
            'test_name': i,
            'test_type': test_type
        })
    return d


def launch_test_sequence(run_list):
    for test in run_list:
        launched_test = launch_ansible_test(
            test['test_name'], test_directory, test['test_type'])
        test['thread'] = launched_test['thread']
        test['runner'] = launched_test['runner']
        print(colored("Launching : {} - {}".format(
            test['test_name'], test['runner'].status), 'yellow')
        )
        while True:
            if test['runner'].status == 'successful':
                print(colored("Complete : {} - {} ".format(
                    test['test_name'], test['runner'].status), 'green')
                )
                break
            elif test['runner'].status == 'running' or test['runner'].status == 'starting':
                if debug:
                    print(colored("Running : {} - {}".format(
                        test['test_name'], test['runner'].status), 'cyan')
                    )
            else:
                print(colored("Error: {} - {}: HA Test failed terminating run".format(
                    test['test_name'], test['runner'].status), 'red')
                )
                exit(1)
            time.sleep(2)


if __name__ == '__main__':
    ansible_tests_list = get_tests(test_directory)
    ansible_run_list = convert_test_list_to_dict(ansible_tests_list, 'test')
    launch_test_sequence(ansible_run_list)
