# Python Experiment Manager
A simple interface for running multiple instances of a python program (eg grid-search).

## Installation
```sh
$ pip install -r requirements.txt
$ python setup.py build
$ python setup.py install
```

## Usage
  Specify the python and main executables in a config file (see example.cfg).
```python
from em.process_manager import ProcessManager

# Instantiate ProcessManager with executables and result directory
pm = ProcessManager(cfg.get('DEFAULT', 'python'),
                    cfg.get('DEFAULT', 'main'),
                    result_dir=cfg.get('DEFAULT', 'resultdir'),
                    sleep_time=0.1,
                    )
# Start the execution thread. It keeps checking for new params to run.
pm.start()

# Add configs to run
numbers = [10, 20, 30, 40, 50]
gpu = 1
for number in numbers[:-1]:
    pm.enqueue({'number':number, 'gpu': gpu})
pm.enqueue({'number':numbers[-1], 'gpu': gpu})

# Stops the thread, completes the leftover jobs and closes the logfiles.
pm.stop()
```
