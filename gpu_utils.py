import sys
import os
import gpustat
import time
import psutil


class GPUUtils:
    def __init__(self, gpus = None, wait = 120, avoid_times = 10):
        if gpus is None:
            x = gpustat.new_query()
            self.gpus = [xx.index for xx in x.gpus]
        else:
            self.gpus = gpus
        self.wait = wait
        self.avoid_times = avoid_times
        self.prev_gpu = 0

    def getFreeGPU(self, memory, empty, avoid_times):
        x = gpustat.new_query()
        free_gpu = -1
        num_processes = 1000
        for gpu in x.gpus:
            cur_gpu_index = (self.prev_gpu+gpu.index)%len(x.gpus)
            cur_gpu = x.gpus[cur_gpu_index]
            if empty and len(cur_gpu.processes) > 0:
                continue
            if cur_gpu_index not in self.gpus:
                continue
            if cur_gpu.memory_free >= memory and len(cur_gpu.processes) < num_processes:
                if avoid_times > 0 and cur_gpu_index == self.prev_gpu:
                    continue
                free_gpu = cur_gpu_index
                num_processes = len(cur_gpu.processes)
        return free_gpu

    def waitForGPU(self, memory, empty=False):
        '''Waits till a gpu is free with memory size 'memory'
        '''
        sleep_time = self.wait
        avoid_times = self.avoid_times
        free_gpu = self.getFreeGPU(memory, empty, avoid_times)
        if free_gpu == self.prev_gpu:
            free_gpu = -1
        while free_gpu < 0:
            # print(f"No gpu free. sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            free_gpu = self.getFreeGPU(memory, empty, avoid_times)
            if avoid_times > 0 and (free_gpu == self.prev_gpu or free_gpu < 0):
                free_gpu = -1
                avoid_times -= 1
        self.prev_gpu = free_gpu
        return free_gpu

    def getAllFreeGPUs(self, memory, empty=False):
        x = gpustat.new_query()
        free_gpus = []
        for gpu in x.gpus:
            if empty and len(gpu.processes)>0:
                continue
            if gpu.memory_free > memory:
                free_gpus.append(gpu)
        return free_gpus

def get_cpu_memory(unit='gb'):
    meminfo = psutil.virtual_memory()
    if unit.lower() in ['gb']:
        return meminfo.available/(1024.0**3)
    elif unit.lower() in ['mb']:
        return meminfo.available/(1024.0**2)
    elif unit.lower() in ['kb']:
        return meminfo.available/(1024.0)
    else:
        return meminfo.available

def get_cpu_usage():
    return psutil.cpu_percent(interval=5)

def main():
    gutils = GPUUtils(tuple(range(8)), wait=1, avoid_times=1)
    for i in range(5):
        print(gutils.waitForGPU(1000, empty=False))
    print(get_cpu_usage())
    print(get_cpu_memory())


if __name__ == "__main__":
    main()

