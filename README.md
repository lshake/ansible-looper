# ansible-runner-looper

Simple python wrapper around ansible-runner for performing tests in parallel and in sequence.

## Functional Testing

The run-functional.py script sources a directory of ansible-runner jobs and invokes them concurrently.  A finite state machine is used to check the state of each job, track failures and relaunch jobs until a set number of iterations have been completed.   Jobs can fail up to a set maximum of times, after which they are removed from the run list.



## HA Testing

The run-ha.py script sources a directory of ansible-runner jobs and invokes them in a random sequential order.  Any job failure terminates the run and exits.   

## Configuration file
The scripts take as input a configuration file in [ini](https://en.wikipedia.org/wiki/INI_file) format.

The following sections are defined:

**General:**

| Key             | Description|
|-----            |----------  |
| test_directory  | Directory containing the tests
| inventory       | Path to Ansible inventory
| extra_vars      | Path to file YAML file containing extra Ansible variables
| iterations      | Number of iterations to run
| output_dir      | Directory to store all output of the test runs


**Ansible Runner Settings:**

This section contain key-value pairs corresponding to the Ansible Runner library [Settings](https://ansible-runner.readthedocs.io/en/latest/intro.html#env-settings-settings-for-runner-itself). 
