import numpy as np
import random
import subprocess
import sys
import PsyNeuLink.Globals.Preferences.ComponentPreferenceSet


# Insures that runs are deterministic for use in Jenkins testing
random.seed(0)
np.random.seed(0)

scripts =  [
            'EVC System Laming Validation Test Script.py',
            'Multilayer Learning Test Script.py',
            'Reinforcement Learning Test Script.py',
            'DDM Test Script.py',
            'Stroop Model Test Script.py',
            'Stroop Model Learning Test Script.py',
            'Mixed NN & DDM script.py',
            'System Graph and Input Test Script.py',
            'Documentation Examples Script.py'
            ]

# foo_bar = __import__(script)
for script in scripts:
    file = open(script)
    print("\nRUNNING {}\n".format(script))

    # EXECUTES ALL SCRIPTS IN META SCRIPT'S NAMESPACE (INSURES ALL USE SAME random.seed):
    exec(file.read())

    # # EXECUTES EACH SCRIPT AS ITS OWN PROCESS (I.E., IN ITS OWN NAMESPACE):
    # for line in subprocess.check_output([sys.executable, script]).splitlines():
    #     print(str(line, 'utf-8'))

    file.close()
    print ("\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

