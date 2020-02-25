# ansible-runner-looper

Simple python wrapper around ansible-runner for performing tests in parallel and in sequence.

## Functional Testing

The run-functional.py script sources a directory of ansible-runner jobs and invokes them concurrently.  A finite state machine is used to check the state of each job, track failures and relaunch jobs until a set number of iterations have been completed.   Jobs can fail up to a set maximum of times, after which they are removed from the run list.

## HA Testing

The run-ha.py script sources a directory of ansible-runner jobs and invokes them in a random sequential order.  Any job failure terminates the run and exits.   
