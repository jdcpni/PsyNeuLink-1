# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
#
# *********************************************  WeightedError *******************************************************
#

import numpy as np
# from numpy import sqrt, random, abs, tanh, exp
from numpy import sqrt, abs, tanh, exp
from PsyNeuLink.Functions.Mechanisms.MonitoringMechanisms.MonitoringMechanism import *
# from PsyNeuLink.Functions.States.InputState import InputState
from PsyNeuLink.Functions.Utility import LinearMatrix

# WeightedError output (used to create and name outputStates):
kwWeightedErrors = 'WeightedErrors'

# WeightedError output indices (used to index output values):
class WeightedErrorOutput(AutoNumber):
    ERROR_SIGNAL = ()

class WeightedErrorError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class WeightedError(MonitoringMechanism_Base):
    """Implement WeightedError subclass

    Description:
        WeightedError is a Subtype of the MonitoringMechanism Type of the Mechanism Category of the Function class
        It's executeMethod computes the contribution of each sender element (rows of the kwMatrix param)
            to the error values of the receivers (elements of the error_signal array, columns of the kwMatrix param),
             weighted by the association of each sender with each receiver (specified in kwMatrix)
        The executeMethod returns an array with the weighted errors for each sender element

    Instantiation:
        - A WeightedError can be instantiated in several ways:
            - directly, by calling WeightedError()
            - by assigning a LearningSignal Projection to a ProcessingMechanism that has at least one other
                ProcessingMechanism to which it projects

    Initialization arguments:
        In addition to standard arguments params (see Mechanism), WeightedError also implements the following params:
        - error_signal (1D np.array)
        - params (dict):
            + kwMatrix (2D np.array):
                weight matrix used to calculate error_array
                width (number of columns) must match error_signal
        Notes:
        *  params can be set in the standard way for any Function subclass:
            - params provided in param_defaults at initialization will be assigned as paramInstanceDefaults
                 and used for paramsCurrent unless and until the latter are changed in a function call
            - paramInstanceDefaults can be later modified using assign_defaults
            - params provided in a function call (to execute or adjust) will be assigned to paramsCurrent

    MechanismRegistry:
        All instances of WeightedError are registered in MechanismRegistry, which maintains an entry for the subclass,
          a count for all instances of it, and a dictionary of those instances

    Naming:
        Instances of WeightedError can be named explicitly (using the name='<name>' argument).
        If this argument is omitted, it will be assigned "WeightedError" with a hyphenated, indexed suffix ('WeightedError-n')

    Execution:
        - Computes comparison of two inputStates of equal length and generates array of same length,
            as well as summary statistics (sum, sum of squares, and variance of comparison array values) 
        - self.execute returns self.value
        Notes:
        * WeightedError handles "runtime" parameters (specified in call to execute method) differently than std Functions:
            any specified params are kept separate from paramsCurrent (Which are not overridden)
            if the EXECUTE_METHOD_RUN_TIME_PARMS option is set, they are added to the current value of the
                corresponding ParameterState;  that is, they are combined additively with controlSignal output

    Class attributes:
        + functionType (str): WeightedError
        + classPreference (PreferenceSet): WeightedError_PreferenceSet, instantiated in __init__()
        + classPreferenceLevel (PreferenceLevel): PreferenceLevel.SUBTYPE
        + variableClassDefault (1D np.array):
        + paramClassDefaults (dict): {kwMatrix: kwIdentityMatrix}
        + paramNames (dict): names as above

    Class methods:
        None

    Instance attributes: none
        + variable (1D np.array): error_signal used by execute method
        + value (value): output of execute method
        + name (str): if it is not specified as an arg, a default based on the class is assigned in register_category
        + prefs (PreferenceSet): if not specified as arg, default set is created by copying WeightedError_PreferenceSet

    Instance methods:
        - validate_params(self, request_set, target_set, context):
            validates that width of kwMatrix param equals length of error_signal
        - execute(error_signal, params, time_scale, context)
            calculates and returns weighted error array (in self.value and values of self.outputStates)
    """

    functionType = "WeightedError"

    classPreferenceLevel = PreferenceLevel.SUBTYPE
    # These will override those specified in TypeDefaultPreferences
    classPreferences = {
        kwPreferenceSetName: 'WeightedErrorCustomClassPreferences',
        kpReportOutputPref: PreferenceEntry(True, PreferenceLevel.INSTANCE)}

    variableClassDefault = [0]  # error_signal

    # WeightedError parameter assignments):
    paramClassDefaults = Mechanism_Base.paramClassDefaults.copy()
    paramClassDefaults.update({
        # kwMatrix:kwIdentityMatrix,
        # kwMatrix:NotImplemented,
        kwMatrix: np.identity(2),
        kwOutputStates:[kwWeightedErrors],
    })

    paramNames = paramClassDefaults.keys()

    def __init__(self,
                 error_signal=NotImplemented,
                 params=NotImplemented,
                 name=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """Assign type-level preferences and call super.__init__
        """

        # Assign functionType to self.name as default;
        #  will be overridden with instance-indexed name in call to super
        if name is NotImplemented:
            self.name = self.functionType
        else:
            self.name = name
        self.functionName = self.functionType

        # if error_signal is NotImplemented:
        #     error_signal = self.variableClassDefault

#         if isinstance(params[kwExecuteMethodParams][kwIdentityMatrix], str):
#             matrix = get_param_value_for_keyword(LinearMatrix, kwIdentityMatrix)
#             if matrix:
#                 self.paramClassDefaults[kwExecuteMethodParams][kwIdentityMatrix] = matrix
# # FIX: MODIFY get_param_value_for_keyword TO TAKE PARAMS DICT

        super().__init__(variable=error_signal,
                         params=params,
                         name=name,
                         prefs=prefs,
                         context=self)
        TEST = True

    def validate_params(self, request_set, target_set=NotImplemented, context=NotImplemented):
        """Insure that width (number of columns) of kwMatrix equals length of error_signal
        """

        super().validate_params(request_set=request_set, target_set=target_set, context=context)
        # MODIFIED 8/19/16:
        # cols = target_set[kwMatrix].shape[1]
        cols = target_set[kwMatrix].shape[1]
        error_signal_len = len(self.variable[0])
        if  cols != error_signal_len:
            raise WeightedErrorError("Number of columns ({}) of weight matrix for {}"
                                     " must equal length of error_signal ({})".
                                     format(cols,self.name,error_signal_len))

    def execute(self,
                variable=NotImplemented,
                params=NotImplemented,
                time_scale = TimeScale.TRIAL,
                context=NotImplemented):

        """Computes the dot product of kwMatrix and error_signal and returns error_array
        """

        if context is NotImplemented:
            context = kwExecuting + self.name

        self.check_args(variable=variable, params=params, context=context)

        # Calculate new error signal
        error_array = np.dot(self.paramsCurrent[kwMatrix], self.variable[0])

        # Compute summed error for use by callers to decide whether to update
        self.summedErrorSignal = np.sum(error_array)

        # Map indices of output to outputState(s)
        self.outputStateValueMapping = {}
        self.outputStateValueMapping[kwWeightedErrors] = WeightedErrorOutput.ERROR_SIGNAL.value

        # Assign output values
        # Get length of output from kwOutputStates
        # Note: use paramsCurrent here (instead of outputStates), as during initialization the execute method
        #       is run (to evaluate output) before outputStates have been instantiated
        output = [None] * len(self.paramsCurrent[kwOutputStates])
        output[WeightedErrorOutput.ERROR_SIGNAL.value] = error_array

        if (self.prefs.reportOutputPref and kwExecuting in context):
            print ("\n{} error signal: {}". format(self.name, self.variable))
            print ("\nOutput:\n- weighted error array: {}".format(error_array))

        return output