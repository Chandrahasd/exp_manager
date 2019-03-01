import sys
import os
import time
import queue
import subprocess
import gpustat
import threading

from gpu_utils import GPUUtils, get_cpu_usage, get_cpu_memory

class ProcessManager:
    """A Class for running multiple instances of same process with different arguments.
    It takes the python executable, the main executable and the arguments and runs them
    based on gpu-availability.
    """
    def __init__(self, python_exe, main_exe, result_dir=None):
        """Creates an instance of ProcessManager.
        Arguments:
        python_exe: the python executable
        main_exe: the main executable
        """
        self.python_exe = python_exe
        self.main_exe = main_exe
        self.pqueue = queue.Queue()
        self.running = queue.Queue()
        self.completed = queue.Queue()
        self.logfiles = {}
        self.thread = threading.Thread(target=self.run)
        self.terminate = False
        self.sleep_time = 6
        self.gpu_utils = GPUUtils(tuple(range(8)))
        self.gpu_memory = 1000
        self.gpu_empty = False
        self.cpu_usage_thr = 95.0
        self.cpu_memory_thr = 50 #GB
        self.ignore_list = []
        self.pid_process_map = {}
        self.tail_lines = 10
        if result_dir is not None:
            self.result_dir = result_dir
        else:
            self.result_dir = os.path.join(os.path.split(self.main_exe)[0], 'results')
            if not os.path.exists(self.result_dir):
                os.mkdir(self.result_dir)

    def _get_file_from_args(self, args):
        """Creates a log-file name from arguments
        """
        name = []
        for key, val in sorted(args.items(), key=lambda x:x[0]):
            # ignore directory parameters
            if '/' in key \
                    or (isinstance(val, str) and '/' in val) \
                    or key in self.ignore_list:
                continue
            name.append(f"{key}={val}")
        name = "%s.out" % ("_".join(name))
        return name

    def _get_log_file(self, args):
        return os.path.join(self.result_dir, self._get_file_from_args(args))

    def _get_process_log(self, pid):
        logfile = self.logfiles.get(pid)
        if logfile is None:
            return ""
        cmd = ['tail', '-n', f'{self.tail_lines}', logfile]
        tail_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        tail_process.wait()
        lines = []
        for line in tail_process.stdout:
            lines.append(line.decode('ascii', 'ignore'))
        return lines

    def _spawn(self, args):
        """spawns the main python script with given args as subprocess
        """
        if args.get('gpu') is None:
            args['gpu'] = self.gpu_utils.waitForGPU(self.gpu_memory, self.gpu_empty)
            self.ignore_list.append('gpu')
        cmd = [self.python_exe, self.main_exe]
        outfile = self._get_log_file(args)
        for key, val in args.items():
            cmd.append(f"--{key}")
            if val:
                cmd.append(f"{val}")
        logfile = open(outfile, 'w')
        print(f"OUTFILE : {outfile}")
        process = subprocess.Popen(cmd, stdout=logfile)
        self.logfiles[process.pid] = logfile
        self.pid_process_map[process.pid] = process
        return process

    def start(self):
        """starts executing the subprocesses in background
        """
        self.thread.start()

    def stop(self, force=False):
        """stops the background thread which runs the subprocesses.
        If force is True, then it won't run the jobs left in the queue.
        """
        self.terminate = True
        self.thread.join()
        if force:
            return
        while not self.pqueue.empty():
            args = self.pqueue.get()
            process = self._spawn(args)
            self.running.put(process)
        self.waitAll()

    def waitAll(self):
        for process in self.running.queue:
            print(f"waiting for process {process.args}")
            process.wait()
        for pid, logfile in self.logfiles.items():
            try:
                logfile.close()
                print(f"closed file {logfile}")
            except Exception as e:
                print(e)
                continue

    def enqueue(self, args):
        """adds the given args to be run as new subprocess
        """
        self.pqueue.put(args)

    def run(self):
        """runs the queued args as background processes.
        This method runs in background and can pickup jobs queued later.
        """
        while True:
            # break the loop if the terminate flag is on
            if self.terminate:
                break

            # wait for processes if the queue is empty
            if self.pqueue.empty():
                time.sleep(self.sleep_time)
                continue

            # wait if the cpu or memory usage is above threshold
            if get_cpu_memory() < self.cpu_memory_thr or get_cpu_usage() > self.cpu_usage_thr:
                time.sleep(self.sleep_time)
                continue

            # create the subprocess
            args = self.pqueue.get()
            process = self._spawn(args)
            self.running.put(process)
            time.sleep(self.sleep_time)

    def status(self):
        """gets the current count of queued, running and completed jobs
        """
        running_updated = queue.Queue()
        logs = {}
        run_status = {}
        for process in self.running.queue:
            logs[process.pid] = self._get_process_log(process.pid)
            if process.poll() is None:
                running_updated.put(process)
                run_status[process.pid] = 'running'
            else:
                self.completed.put(process)
                run_status[process.pid] = 'completed'
                try:
                    self.logfiles[process.pid].close()
                except:
                    continue
        self.running = running_updated
        yet_to_run = self.pqueue.qsize()
        total = self.pqueue.qsize() + self.running.qsize() + self.completed.qsize()
        return {'num_queued': self.pqueue.qsize(),
                'num_running': self.running.qsize(),
                'num_completed': self.completed.qsize(),
                'total': total,
                'queued': [x.pid for x in self.pqueue.queue],
                'running': [x.pid for x in self.running.queue],
                'completed': [x.pid for x in self.completed.queue],
                'status': run_status,
                'logs': logs,
                }
