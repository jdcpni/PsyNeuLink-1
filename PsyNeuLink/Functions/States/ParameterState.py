# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
#
# **************************************  ParameterState ******************************************************
#

from PsyNeuLink.Functions.States.State import *
from PsyNeuLink.Functions.Utility import *

# class ParameterStateLog(IntEnum):
#     NONE            = 0
#     TIME_STAMP      = 1 << 0
#     ALL = TIME_STAMP
#     DEFAULTS = NONE


class ParameterStateError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


# class ParameterState_Base(State_Base):
class ParameterState(State_Base):
    """Implement subclass type of State that represents parameter value for execute function of a Mechanism

    Definition for ParameterState functionType in State category of Function class

    Description:
        The ParameterState class is a functionType in the State category of Function,
        Its kwExecuteMethod executes the projections that it receives and updates the ParameterState's value

    Instantiation:
        - ParameterStates can be instantiated in one of two ways:
            - directly: requires explicit specification of its value and ownerMechanism;
                - specification of value can be any of the forms allowed for specifying a State
                    (default value will be inferred from anything other than a value or ParamValueProjection tuple)
                - ownerMechanism must be a reference to a Mechanism object, or DefaultProcessingMechanism_Base will be used
            - as part of the instantiation of a mechanism:
                - the mechanism for which it is being instantiated will automatically be used as the ownerMechanism
                - the value of the ownerMechanism's param for which the ParameterState is being instantiated
                    will be used as its variable (that must also be compatible with its self.value)
        - self.variable must be compatible with self.value (enforced in validate_variable)
            note: although it may receive multiple projections, the output of each must conform to self.variable,
                  as they will be combined to produce a single value that must be compatible with self.variable
        - self.executeMethod (= params[kwExecuteMethod]) must be Utility.LinearCombination (enforced in validate_params)

    Execution:
        - get ParameterStateParams
        - pass params to super, which aggregates inputs from projections
        - combine input from projections (processed in super) with baseValue using paramModulationOperation
        - combine result with value specified at runtime in kwParameterStateParams
        - assign result to self.value

    StateRegistry:
        All ParameterStates are registered in StateRegistry, which maintains an entry for the subclass,
          a count for all instances of it, and a dictionary of those instances

    Naming:
        ParameterStates can be named explicitly (using the name argument). If this argument is omitted,
         it will be assigned "ParameterState" with a hyphenated, indexed suffix ('ParameterState-n')

    Parameters:
        The default for kwExecuteMethod is LinearCombination using kwAritmentic.Operation.PRODUCT:
           self.value is multiplied by  the output of each of the  projections it receives (generally ControlSignals)
# IMPLEMENTATION NOTE:  *** CONFIRM THAT THIS IS TRUE:
        kwExecuteMethod can be set to another function, so long as it has type kwLinearCombinationFunction
        The parameters of kwExecuteMethod can be set:
            - by including them at initialization (param[kwExecuteMethod] = <function>(sender, params)
            - calling the adjust method, which changes their default values (param[kwExecuteMethod].adjust(params)
            - at run time, which changes their values for just for that call (self.execute(sender, params)
    Class attributes:
        + functionType (str) = kwMechanisParameterState
        + classPreferences
        + classPreferenceLevel (PreferenceLevel.Type)
        + paramClassDefaults (dict)
            + kwExecuteMethod (LinearCombination)
            + kwExecuteMethodParams  (Operation.PRODUCT)
            + kwProjectionType (kwControlSignal)
            + kwParamModulationOperation   (ModulationOperation.MULTIPLY)
        + paramNames (dict)
    Class methods:
        instantiate_execute_method: insures that execute method is ARITHMETIC) (default: Operation.PRODUCT)
        update_state: updates self.value from projections, baseValue and runtime in kwParameterStateParams

    Instance attributes:
        + paramInstanceDefaults (dict) - defaults for instance (created and validated in Functions init)
        + params (dict) - set currently in effect
        + paramNames (list) - list of keys for the params dictionary
        + ownerMechanism (Mechanism)
        + value (value)
        + params (dict)
        + baseValue (value)
        + projections (list)
        + modulationOperation (ModulationOperation)
        + name (str)
        + prefs (dict)

    Instance methods:
        none
    """

    #region CLASS ATTRIBUTES

    functionType = kwParameterState

    classPreferenceLevel = PreferenceLevel.TYPE
    # Any preferences specified below will override those specified in TypeDefaultPreferences
    # Note: only need to specify setting;  level will be assigned to TYPE automatically
    # classPreferences = {
    #     kwPreferenceSetName: 'ParameterStateCustomClassPreferences',
    #     kp<pref>: <setting>...}


    paramClassDefaults = State_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwExecuteMethod: LinearCombination,
                               kwExecuteMethodParams : {kwOperation: LinearCombination.Operation.PRODUCT},
                               kwParamModulationOperation: ModulationOperation.MULTIPLY,
                               kwProjectionType: kwControlSignal})
    #endregion

    def __init__(self,
                 owner_mechanism,
                 reference_value=NotImplemented,
                 value=NotImplemented,
                 params=NotImplemented,
                 name=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """
IMPLEMENTATION NOTE:  *** DOCUMENTATION NEEDED (SEE CONTROL SIGNAL??)

        :param owner_mechanism: (Mechanism)
        :param reference_value: (value)
        :param params: (dict)
        :param name: (str)
        :param prefs: (PreferenceSet)
        :param context: (str)
        :return:
        """

        # Assign functionType to self.name as default;
        #  will be overridden with instance-indexed name in call to super
        if name is NotImplemented:
            self.name = self.functionType
        else:
            self.name = name

        self.functionName = self.functionType

        self.reference_value = reference_value

        # Validate sender (as variable) and params, and assign to variable and paramsInstanceDefaults
        # Note: pass name of mechanism (to override assignment of functionName in super.__init__)
        super(ParameterState, self).__init__(owner_mechanism,
                                                  value=value,
                                                  params=params,
                                                  name=name,
                                                  prefs=prefs,
                                                  context=self)

        self.modulationOperation = self.paramsCurrent[kwParamModulationOperation]

    def instantiate_execute_method(self, context=NotImplemented):
        """Insure execute method is LinearCombination and that its output is compatible with param with which it is associated

        Notes:
        * Relevant param should have been provided as reference_value arg in the call to InputState__init__()
        * Insures that self.value has been assigned (by call to super().validate_execute_method)
        * This method is called only if the parameterValidationPref is True

        :param context:
        :return:
        """

        super().instantiate_execute_method(context=context)

        # Insure that execute method is LinearCombination
        if not isinstance(self.execute.__self__, LinearCombination):
            raise StateError("Function {0} for {1} of {2} must be of LinearCombination type".
                                 format(self.execute.__self__.functionName, kwExecuteMethod, self.name))

        # # Insure that output of execute method (self.value) is compatible with relevant parameter value
        if not iscompatible(self.value, self.reference_value):
            raise ParameterStateError("Value ({0}) of {1} for {2} mechanism is not compatible with "
                                           "the variable ({3}) of its execute method".
                                           format(self.value,
                                                  self.name,
                                                  self.ownerMechanism.name,
                                                  self.ownerMechanism.variable))


    def update(self, params=NotImplemented, time_scale=TimeScale.TRIAL, context=NotImplemented):
        """Parse params for parameterState params and XXX ***

# DOCUMENTATION:  MORE HERE:
        - get ParameterStateParams
        - pass params to super, which aggregates inputs from projections
        - combine input from projections (processed in super) with baseValue using paramModulationOperation
        - combine result with value specified at runtime in kwParameterStateParams
        - assign result to self.value


        :param params:
        :param time_scale:
        :param context:
        :return:
        """

        #region GET INPUT FROM PROJECTIONS

        # Get parameterState params
        try:
            # Get parameterState params
            parameter_state_params = params[kwParameterStateParams]

        except (KeyError, TypeError):
            parameter_state_params = NotImplemented

        super(ParameterState, self).update(params=parameter_state_params,
                                                      time_scale=time_scale,
                                                      context=context)
        #endregion

        #region COMBINE PROJECTIONS INPUT WITH BASE PARAM VALUE
        try:
            # Check whether modulationOperation has been specified at runtime
            self.modulationOperation = parameter_state_params[kwParamModulationOperation]
        except (KeyError, TypeError):
            # If not, ignore (leave self.modulationOperation assigned to previous value)
            pass

        # If self.value has not been set, assign to baseValue
        if self.value is None:
            if context is NotImplemented:
                context = kwAssign + ' Base Value'
            else:
                context = context + kwAssign + ' Base Value'
            self.value = self.baseValue

        # Otherwise, combine param's value with baseValue using modulatonOperation
        else:
            if context is NotImplemented:
                context = kwAssign + ' Modulated Value'
            else:
                context = context + kwAssign + ' Modulated Value'
            self.value = self.modulationOperation(self.baseValue, self.value)
        #endregion

        #region APPLY RUNTIME PARAM VALUES
        # If there are not any runtime params, or executeMethodRuntimeParamsPref is disabled, return
        if (parameter_state_params is NotImplemented or
                    self.prefs.executeMethodRuntimeParamsPref is ModulationOperation.DISABLED):
            return

        # Assign class-level pref as default operation
        default_operation = self.prefs.executeMethodRuntimeParamsPref

        try:
            value, operation = parameter_state_params[self.name]

        except KeyError:
            # No runtime param for this param state
            return

        except TypeError:
            # If single ("exposed") value, use default_operation (class-level executeMethodRuntimeParamsPref)
            self.value = default_operation(parameter_state_params[self.name], self.value)
        else:
            # If tuple, use param-specific ModulationOperation as operation
            self.value = operation(value, self.value)

            # Assign class-level pref as default operation
            default_operation = self.prefs.executeMethodRuntimeParamsPref
        #endregion