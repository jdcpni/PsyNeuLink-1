from PsyNeuLink.Functions.Mechanisms.ProcessingMechanisms.DDM import *
from PsyNeuLink.Functions.Mechanisms.ProcessingMechanisms.Transfer import *
from PsyNeuLink.Functions.Process import process
from PsyNeuLink.Globals.Keywords import *
from PsyNeuLink.Globals.Run import run



myInputLayer = Transfer(name='Input Layer',
                        function=Linear(),
                        default_input_value = [0,0])

myHiddenLayer = Transfer(name='Hidden Layer 1',
                         function=Logistic(gain=1.0, bias=0),
                         default_input_value = np.zeros((5,)))

myDDM = DDM(name='My_DDM',
            function=BogaczEtAl(drift_rate=0.5,
                                threshold=1,
                                starting_point=0.0))

myProcess = process(name='Neural Network DDM Process',
                    default_input_value=[0, 0],
                    pathway=[myInputLayer,
                                   RANDOM_CONNECTIVITY_MATRIX,
                                   # FULL_CONNECTIVITY_MATRIX,
                                   myHiddenLayer,
                                   FULL_CONNECTIVITY_MATRIX,
                                   myDDM])

myProcess.reportOutputPref = True
myInputLayer.reportOutputPref = True
myHiddenLayer.reportOutputPref = True
myDDM.reportOutputPref = PreferenceEntry(True, PreferenceLevel.INSTANCE)

# myProcess.execute(input=[-1, 2])
# myProcess.run(inputs=[-1, 2])
run(myProcess, [[-1,2],[2,3],[5,5]])



