'''
To restart:
    docker kill --signal=INT CONTAINER_ID
'''
import signal

import os
from subprocess import Popen, PIPE, CalledProcessError

# ---------------------------------------------------------
# SIGNAL HANDLING
# ---------------------------------------------------------

run = True
current_subprocs = set()

def dispatch_signal(signum, frame):
    print(f'Dispatching signal {signum}')

    for proc in current_subprocs:
        if proc.poll() is None:
            # process.terminate() / proc.send_signal(signum) doesn't work when using shell=True
            # https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612
            os.killpg(os.getpgid(proc.pid), signum)

def restart(signum, frame):
    dispatch_signal(signal.SIGTERM, frame)

def stop(signum, frame):
    global run
    run = False

    dispatch_signal(signum, frame)

print('Listen...')
signal.signal(signal.SIGINT, restart)
signal.signal(signal.SIGTERM, stop)


# ---------------------------------------------------------
# RUN APP IN FORK
# ---------------------------------------------------------

src = os.environ.get('WWWDIR', '')
cmd = f'python {src}/app.py'

while run:
    print('Start child...')

    with Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, bufsize=1, universal_newlines=True, preexec_fn=os.setsid) as p:
        current_subprocs.add(p)

        for line in p.stdout:
            print(line, end='') # process line here

        for line in p.stderr:
            print('Err:', line, end='') # process line here

    print('Exit child...')
    current_subprocs.remove(p)

    if p.returncode > 1:
        raise CalledProcessError(p.returncode, p.args)
