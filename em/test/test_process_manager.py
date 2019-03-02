import unittest
import os
from copy import deepcopy
from configparser import ConfigParser
from em.process_manager import ProcessManager

cfg = ConfigParser()
cfg.read('./example.cfg')

class TestProcessManager(unittest.TestCase):
    def testFilename(self):
        args = {'int':1,
                'float':3.2,
                'str':'string',
                'path':'/home/user/',
                'udr':'a_b_c'}
        pm = ProcessManager('python', '/home/main', result_dir='/results', sleep_time=0.1)
        self.assertEqual(pm._get_file_from_args(args), "float=3.2_int=1_str=string_udr=a_b_c.out")

    def testProcessSpawn(self):
        pm = ProcessManager(cfg.get('DEFAULT', 'python'),
                            cfg.get('DEFAULT', 'main'),
                            result_dir=cfg.get('DEFAULT', 'resultdir'),
                            sleep_time=0.1,
                            )
        number = 10
        gpu = 1
        args = {'number': number, 'gpu': gpu}
        process = pm._spawn(args)
        process.wait()
        num_lines = 0
        with open(pm._get_log_file(args), 'r') as fin:
            for line in fin:
                num_lines += 1
        self.assertEqual(num_lines, number)

    def testMultiprocess(self):
        pm = ProcessManager(cfg.get('DEFAULT', 'python'),
                            cfg.get('DEFAULT', 'main'),
                            result_dir=cfg.get('DEFAULT', 'resultdir'),
                            sleep_time=0.1,
                            )
        pm.start()
        numbers = [10, 20, 30, 40, 50]
        gpu = 1
        for number in numbers[:-1]:
            pm.enqueue({'number':number, 'gpu': gpu})
        pm.enqueue({'number':numbers[-1], 'gpu': gpu})
        pm.stop()
        for number in numbers:
            self.assertTrue(os.path.exists(pm._get_log_file({'number':number, 'gpu': gpu})))

if __name__ == "__main__":
    unittest.main()
