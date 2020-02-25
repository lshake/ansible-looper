#!/usr/bin/env python

import ansible_runner
import os
import re
import time
from termcolor import colored

test_directory = "./functional_tests"
ansible_tests_list = []
ansible_run_list = []
tests_list = []
iterations = 20
maxfailures = 3
keepartifacts = 5
debug = False


def get_tests(test_directory):
    directories = os.listdir(test_directory)
    tests = []
    for i in directories:
        if re.match('^[0-9][0-9].*', i):
            tests.append(i)
    return(sorted(tests))


def launch_ansible_test(test_to_launch, test_directory, test_type, invocation, failure_count):
    (t, r) = ansible_runner.interface.run_async(
        private_data_dir=test_directory + '/' + test_to_launch,
        playbook=test_type + '.yml',
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
    ansible_tests_list = get_tests(test_directory)
    ansible_run_list = launch_ansible_tests(ansible_tests_list, 'setup')
    check_ansible_loop(ansible_run_list, 1)
    ansible_run_list = launch_ansible_tests(ansible_tests_list, 'test')
    check_ansible_loop(ansible_run_list, iterations)
