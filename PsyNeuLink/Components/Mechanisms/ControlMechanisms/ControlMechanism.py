# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# **************************************  ControlMechanism ************************************************

"""
Overview
--------

ControlMechanisms monitor the outputState(s) of one or more ProcessingMechanisms in a :doc:`System` to assess the
outcome of processing by those mechanisms, and use this to regulate the value of
:doc:`ControlProjections <ControlProjection>` to other ProcessingMechanisms in the system for which the
ControlMechanism is a ``controller``.

.. _ControlMechanism_Creation:

Creating A ControlMechanism
---------------------------

ControlMechanisms can be created by using the standard Python method of calling the constructor for the desired type.
A ControlMechanism is also created automatically whenever a system is created (see :ref:`System_Creation`),
and assigned as the controller for that system (see :ref:`_System_Execution_Control`). The outputStates to be monitored
by a ControlMechanism are specified in its ``monitoredOutputStates`` argument, which can be specified in a number of
ways (see below).  When the ControlMechanism is created, it automatically creates its own inputState for each of the
outputStates it monitors, and assigns a :doc:`MappingProjection` from that outputState to the newly created inputState.
How a ControlMechanism creates its ControlProjections depends on the subclass.

.. _ControlMechanism_Monitored_OutputStates:

Monitored OutputStates
~~~~~~~~~~~~~~~~~~~~~~

The outputState(s) monitored by a ControlMechanism can be specified in any of the places listed below.  The
list also describes the order of precedence when more than one specification pertains to the same
outputState(s). In all cases, specifications can be a references to an outputState object, or a string that is the
name of one (see :ref:ControlMechanism_Examples' below).

The specification of whether an outputState is monitored by a ControlMechanism can be done in the following ways:

* An **outputState** can be *excluded* from being monitored by assigning :keyword:`None` as the value of the
  :keyword:`MONITOR_FOR_CONTROL` entry of a parameter specification dictionary in the outputState's ``params``
  argument.  This specification takes precedence over any others;  that is, specifying :keyword:`None` will suppress
  monitoring of that outputState, irrespective of any other specifications that might otherwise apply to that
  outputState;  thus, it can be used to exclude the outputState for cases in which it would otherwise be monitored
  based on one of the other specification methods below.
..
* The outputState of a particular **mechanism** can be designated to be monitored, by specifying it in the
  :keyword:`MONITOR_FOR_CONTROL` entry of a parameter specification dictionary in the mechanism's ``params``
  argument.  The value of the entry must be either a list containing the outputState(s) and/or their name(s),
  a :ref:`monitoredOutputState tuple <ControlMechanism_OutputState_Tuple>`, a :class:`MonitoredOutputStatesOption`
  value, or :keyword:`None`. The values of :class:`MonitoredOutputStatesOption` are treated as follows:
    * :keyword:`PRIMARY_OUTPUT_STATES`: only the primary (first) outputState of the mechanism will be monitored;
    * :keyword:`ALL_OUTPUT_STATES`:  all of the mechanism's outputStates will be monitored.
  This specification takes precedence of any of the other types listed below:  if it is :keyword:`None`, then none of
  that mechanism's outputStates will be monitored;   if it specifies outputStates to be monitored, those will be
  monitored even if the mechanism is not a :keyword:`TERMINAL` mechanism (see below).
..
* OutputStates to be monitored can be specified in the **ControlMechanism** responsible for the monitoring, or in the
  **system** for which that ControlMechanism is the :ref:`controller <System_Execution_Control>`).  Specification
  can be in the controlMechanism or system's ``monitor_for_control`` argument, or in the
  :keyword:`MONITOR_FOR_CONTROL` entry of a parameter specification dictionary in its ``params`` argument.  In
  either case, the value must be a list, each item of which must be one of the following:

  * An existing **outputState** or the name of one.
  ..

  * A **mechanism** or the name of one. Only the mechanism's primary (first) outputState will be monitored,
    unless a :class:`MonitoredOutputStatesOption` value is also in the list (see below), or the specification is
    overridden in a params dictionary specification for the mechanism (see above).
  ..
  * A :ref:`monitoredOutputState tuple <ControlMechanism_OutputState_Tuple>`.
  ..
  * A value of :class:`MonitoredOutputStatesOption`.  This applies to any mechanisms that appear in the list
    (except those that override it with their own ``monitor_for_control`` specification). If the value of
    :class:`MonitoredOutputStatesOption` appears alone in the list, it is treated as follows:

    * :keyword:`PRIMARY_OUTPUT_STATES`: only the primary (first) outputState of the :keyword:`TERMINAL` mechanism(s)
      in the system for which the ControlMechanism is the ``controller``.

    * :keyword:`ALL_OUTPUT_STATES`:  all of the outputStates of the :keyword:`TERMINAL` mechanism(s)
      in the system for which the ControlMechanism is the ``controller``.
  ..
  * :keyword:`None`.

  Specifications in a ControlMechanism take precedence over any in the system; both are superceded by specifications
  in the constructor or params dictionary for an outputState or mechanism.

.. _ControlMechanism_OutputState_Tuple:

**MonitoredOutputState Tuple**

A tuple can be used wherever an outputState can be specified, to configure how its value is combined with others by the
ControlMechanism's primary ``function`` and/or any others it may use to compute the outcome of processing. Each tuple
must have the three following items in the order listed:
  * an outputState or mechanism, the name of one, or a specification dictionary for one;
  ..
  * an exponent (int) - exponentiates the value of the outputState;
  ..
  * a weight (int) - multiplies the value of the outState.

.. _ControlMechanism_Execution:

Execution
---------

The ControlMechanism of a system is always the last to be executed (see System :ref:`System_Execution_Control`).  A
ControlMechanism's ``function`` takes as its input the values of the outputStates specified in its
:keyword:`MONITOR_FOR_CONTROL` parameter, and uses those to determine the value of its :doc:`ControlProjection`
projections. In the next round of execution, each ControlProjection's value is used by the :doc:`ParameterState` to which it
projects, to update the corresponding parameter of the recieving mechanism's function.

.. note::
   A :doc:`ParameterState` that receives a :doc:`ControlProjection` does not update its value until its owner
   mechanism executes (see :ref:`Lazy_Evaluation` for an explanation of "lazy" updating).  This means that even if a
   ControlMechanism has executed, a parameter that it controls will not assume its new value until the corresponding
   receiver mechanism has executed.

.. _ControlMechanism_Class_Reference:

Class Reference
---------------

"""

# IMPLEMENTATION NOTE: COPIED FROM DefaultProcessingMechanism;
#                      ADD IN GENERIC CONTROL STUFF FROM DefaultControlMechanism

from collections import OrderedDict

from PsyNeuLink.Components.Mechanisms.Mechanism import Mechanism_Base
from PsyNeuLink.Components.ShellClasses import *


ControlMechanismRegistry = {}


class ControlMechanismError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value


class ControlMechanism_Base(Mechanism_Base):
    """
    ControlMechanism_Base(     \
    default_input_value=None,  \
    monitor_for_control=None,  \
    function=Linear,           \
    params=None,               \
    name=None,                 \
    prefs=None)

    Abstract class for ControlMechanism.

    .. note::
       ControlMechanisms should NEVER be instantiated by a direct call to the base class.
       They should be instantiated using the constructor for a :doc:`subclass <ControlMechanism>`.

    COMMENT:
        Description:
            # DOCUMENTATION NEEDED:
              ._instantiate_control_projection INSTANTIATES OUTPUT STATE FOR EACH CONTROL SIGNAL ASSIGNED TO THE
             INSTANCE
            .EXECUTE MUST BE OVERRIDDEN BY SUBCLASS
            WHETHER AND HOW MONITORING INPUT STATES ARE INSTANTIATED IS UP TO THE SUBCLASS

            Protocol for assigning DefaultController:
               Initial assignment is to SystemDefaultController (instantiated and assigned in Components.__init__.py)
               When any other ControlMechanism is instantiated, if its params[MAKE_DEFAULT_CONTROLLER] == True
                   then its _take_over_as_default_controller method is called in _instantiate_attributes_after_function()
                   which moves all ControlProjections from DefaultController to itself, and deletes them there

            MONITOR_FOR_CONTROL param determines which states will be monitored.
                specifies the outputStates of the terminal mechanisms in the System to be monitored by ControlMechanism
                this specification overrides any in System.params[], but can be overridden by Mechanism.params[]
                ?? if MonitoredOutputStates appears alone, it will be used to determine how states are assigned from
                    system.executionGraph by default
                if MonitoredOutputStatesOption is used, it applies to any mechanisms specified in the list for which
                    no outputStates are listed; it is overridden for any mechanism for which outputStates are
                    explicitly listed
                TBI: if it appears in a tuple with a Mechanism, or in the Mechamism's params list, it applies to
                    just that mechanism

        Class attributes:
            + componentType (str): System Default Mechanism
            + paramClassDefaults (dict):
                + FUNCTION: Linear
                + FUNCTION_PARAMS:{SLOPE:1, INTERCEPT:0}
                + MONITOR_FOR_CONTROL: List[]
    COMMENT

    COMMENT:
        Arguments
        ---------

            NOT CURRENTLY IN USE:
            default_input_value : value, list or np.ndarray : ``defaultControlAllocation`` [LINK]
                the default allocation for the ControlMechanism;
                it length should equal the number of ``controlSignals``.

        monitor_for_control : List[OutputState specification] : default None
            specifies set of outputStates to monitor (see :ref:`ControlMechanism_Monitored_OutputStates` for
            specification options).

        function : TransferFunction : default Linear(slope=1, intercept=0)
            specifies function used to combine values of monitored output states.

        params : Optional[Dict[param keyword, param value]]
            a dictionary that can be used to specify the parameters for the mechanism, parameters for its function,
            and/or a custom function and its parameters (see :doc:`Mechanism` for specification of a params dict).

        name : str : default ControlMechanism-<index>
            a string used for the name of the mechanism.
            If not is specified, a default is assigned by MechanismRegistry
            (see :doc:`Registry` for conventions used in naming, including for default and duplicate names).[LINK]

        prefs : Optional[PreferenceSet or specification dict : Mechanism.classPreferences]
            the PreferenceSet for the mechanism.
            If it is not specified, a default is assigned using ``classPreferences`` defined in __init__.py
            (see Description under PreferenceSet for details) [LINK].
    COMMENT


    Attributes
    ----------

    controlProjections : List[ControlProjection]
        list of :doc:`ControlProjections <ControlProjection>` managed by the ControlMechanism.
        There is one for each ouputState in the ``outputStates`` dictionary.

    controlProjectionCosts : 2d np.array
        array of costs associated with each of the control signals in the ``controlProjections`` attribute.

    allocationPolicy : 2d np.array
        array of values currently assigned to each control signal in the ``controlProjections`` attribute.


    """

    componentType = "ControlMechanism"

    initMethod = INIT_FUNCTION_METHOD_ONLY


    classPreferenceLevel = PreferenceLevel.TYPE
    # Any preferences specified below will override those specified in TypeDefaultPreferences
    # Note: only need to specify setting;  level will be assigned to TYPE automatically
    # classPreferences = {
    #     kwPreferenceSetName: 'ControlMechanismClassPreferences',
    #     kp<pref>: <setting>...}

    # variableClassDefault = defaultControlAllocation
    # This must be a list, as there may be more than one (e.g., one per controlSignal)
    variableClassDefault = [defaultControlAllocation]

    from PsyNeuLink.Components.Functions.Function import Linear
    paramClassDefaults = Mechanism_Base.paramClassDefaults.copy()
    paramClassDefaults.update({CONTROL_PROJECTIONS: None})

    @tc.typecheck
    def __init__(self,
                 default_input_value=None,
                 monitor_for_control:tc.optional(list)=None,
                 function = Linear(slope=1, intercept=0),
                 params=None,
                 name=None,
                 prefs:is_pref_set=None,
                 context=None):

        self.system = None

        # MODIFIED 11/5/16 NEW:
        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(monitor_for_control=monitor_for_control,
                                                  function=function,
                                                  params=params)
         # MODIFIED 11/5/16 END

        super(ControlMechanism_Base, self).__init__(variable=default_input_value,
                                                    params=params,
                                                    name=name,
                                                    prefs=prefs,
                                                    context=self)

    def _validate_params(self, request_set, target_set=NotImplemented, context=None):
        """Validate SYSTEM, MONITOR_FOR_CONTROL and FUNCTION_PARAMS

        If SYSTEM is not specified:
        - OK if controller is DefaultControlMechanism
        - otherwise, raise an exception
        Check that all items in MONITOR_FOR_CONTROL are Mechanisms or OutputStates for Mechanisms in self.system
        Check that len(WEIGHTS) = len(MONITOR_FOR_CONTROL)
        """

        # DefaultController does not require a system specification
        #    (it simply passes the defaultControlAllocation for default ConrolSignal Projections)
        from PsyNeuLink.Components.Mechanisms.ControlMechanisms.DefaultControlMechanism import DefaultControlMechanism
        if isinstance(self,DefaultControlMechanism):
            pass

        # For all other ControlMechanisms, validate System specification
        else:
            try:
                if not isinstance(request_set[SYSTEM], System):
                    raise KeyError
            except KeyError:
                raise ControlMechanismError("A system must be specified in the SYSTEM param to instantiate {0}".
                                                  format(self.name))
            else:
                self.paramClassDefaults[SYSTEM] = request_set[SYSTEM]
        # MODIFIED 11/10/16 END

        super(ControlMechanism_Base, self)._validate_params(request_set=request_set,
                                                                 target_set=target_set,
                                                                 context=context)

    def _validate_monitored_state_spec(self, state_spec, context=None):
        """Validate specified outputstate is for a Mechanism in the System

        Called by both self._validate_params() and self.add_monitored_state() (in ControlMechanism)
        """
        super(ControlMechanism_Base, self)._validate_monitored_state(state_spec=state_spec, context=context)

        # Get outputState's owner
        from PsyNeuLink.Components.States.OutputState import OutputState
        if isinstance(state_spec, OutputState):
            state_spec = state_spec.owner

        # Confirm it is a mechanism in the system
        if not state_spec in self.system.mechanisms:
            raise ControlMechanismError("Request for controller in {0} to monitor the outputState(s) of "
                                              "a mechanism ({1}) that is not in {2}".
                                              format(self.system.name, state_spec.name, self.system.name))

        # Warn if it is not a terminalMechanism
        if not state_spec in self.system.terminalMechanisms.mechanisms:
            if self.prefs.verbosePref:
                print("Request for controller in {0} to monitor the outputState(s) of a mechanism ({1}) that is not"
                      " a terminal mechanism in {2}".format(self.system.name, state_spec.name, self.system.name))

    def _instantiate_attributes_before_function(self, context=None):
        """Instantiate self.system

        Assign self.system
        """
        self.system = self.paramsCurrent[SYSTEM]
        super()._instantiate_attributes_before_function(context=context)

    def _instantiate_monitored_output_states(self, context=None):
        raise ControlMechanismError("{0} (subclass of {1}) must implement _instantiate_monitored_output_states".
                                          format(self.__class__.__name__,
                                                 self.__class__.__bases__[0].__name__))

    def _instantiate_control_mechanism_input_state(self, input_state_name, input_state_value, context=None):
        """Instantiate inputState for ControlMechanism

        Extend self.variable by one item to accommodate new inputState
        Instantiate an inputState using input_state_name and input_state_value
        Update self.inputState and self.inputStates

        Args:
            input_state_name (str):
            input_state_value (2D np.array):
            context:

        Returns:
            input_state (InputState):

        """
        # Extend self.variable to accommodate new inputState
        if self.variable is None:
            self.variable = np.atleast_2d(input_state_value)
        else:
            self.variable = np.append(self.variable, np.atleast_2d(input_state_value), 0)
        variable_item_index = self.variable.size-1

        # Instantiate inputState
        from PsyNeuLink.Components.States.State import _instantiate_state
        from PsyNeuLink.Components.States.InputState import InputState
        input_state = _instantiate_state(owner=self,
                                                  state_type=InputState,
                                                  state_name=input_state_name,
                                                  state_spec=defaultControlAllocation,
                                                  state_params=None,
                                                  constraint_value=np.array(self.variable[variable_item_index]),
                                                  constraint_value_name='Default control allocation',
                                                  context=context)

        #  Update inputState and inputStates
        try:
            self.inputStates[input_state_name] = input_state
        except AttributeError:
            self.inputStates = OrderedDict({input_state_name:input_state})
            self.inputState = list(self.inputStates.values())[0]
        return input_state

    def _instantiate_attributes_after_function(self, context=None):
        """Take over as default controller (if specified) and implement any specified ControlProjections

        """

        try:
            # If specified as DefaultController, reassign ControlProjections from DefaultController
            if self.paramsCurrent[MAKE_DEFAULT_CONTROLLER]:
                self._take_over_as_default_controller(context=context)
        except KeyError:
            pass

        # If ControlProjections were specified, implement them
        try:
            if self.paramsCurrent[CONTROL_PROJECTIONS]:
                for key, projection in self.paramsCurrent[CONTROL_PROJECTIONS].items():
                    self._instantiate_control_projection(projection, context=self.name)
        except:
            pass

    def _take_over_as_default_controller(self, context=None):

        from PsyNeuLink.Components import DefaultController

        # Iterate through old controller's outputStates
        to_be_deleted_outputStates = []
        for outputState in DefaultController.outputStates:

            # Iterate through projections sent for outputState
            for projection in DefaultController.outputStates[outputState].sendsToProjections:

                # Move ControlProjection to self (by creating new outputState)
                # IMPLEMENTATION NOTE: Method 1 -- Move old ControlProjection to self
                #    Easier to implement
                #    - call _instantiate_control_projection directly here (which takes projection as arg)
                #        instead of instantiating a new ControlProjection (more efficient, keeps any settings);
                #    - however, this bypasses call to Projection._instantiate_sender()
                #        which calls Mechanism.sendsToProjections.append(),
                #        so need to do that in _instantiate_control_projection
                #    - this is OK, as it is case of a Mechanism managing its *own* projections list (vs. "outsider")
                self._instantiate_control_projection(projection, context=context)

                # # IMPLEMENTATION NOTE: Method 2 - Instantiate new ControlProjection
                # #    Cleaner, but less efficient and ?? may lose original params/settings for ControlProjection
                # # TBI: Implement and then use Mechanism.add_project_from_mechanism()
                # self._add_projection_from_mechanism(projection, new_output_state, context=context)

                # Remove corresponding projection from old controller
                DefaultController.outputStates[outputState].sendsToProjections.remove(projection)

            # Current controller's outputState has no projections left (after removal(s) above)
            if not DefaultController.outputStates[outputState].sendsToProjections:
                # If this is the old controller's primary outputState, set it to None
                if DefaultController.outputState is DefaultController.outputStates[outputState]:
                    DefaultController.outputState = None
                # Delete outputState from old controller's outputState dict
                to_be_deleted_outputStates.append(DefaultController.outputStates[outputState])
        for item in to_be_deleted_outputStates:
            del DefaultController.outputStates[item.name]

    def _instantiate_control_projection(self, projection, context=None):
        """Add outputState and assign as sender to requesting ControlProjection

        Updates allocationPolicy and controlSignalCosts attributes to accomodate instantiated projection

        Args:
            projection:
            context:

        Returns state: (OutputState)

        """

        from PsyNeuLink.Components.Projections.ControlProjection import ControlProjection
        if not isinstance(projection, ControlProjection):
            raise ControlMechanismError("PROGRAM ERROR: Attempt to assign {0}, "
                                              "that is not a ControlProjection, to outputState of {1}".
                                              format(projection, self.name))

        output_name = projection.receiver.name + '_ControlProjection' + '_Output'

        #  Update self.value by evaluating function
        self._update_value(context=context)
        # IMPLEMENTATION NOTE: THIS ASSUMED THAT self.value IS AN ARRAY OF OUTPUT STATE VALUES, BUT IT IS NOT
        #                      RATHER, IT IS THE OUTPUT OF THE EXECUTE METHOD (= EVC OF monitoredOutputStates)
        #                      SO SHOULD ALWAYS HAVE LEN = 1 (INDEX = 0)
        #                      self.allocationPolicy STORES THE outputState.value(s)
        output_item_index = len(self.value)-1
        output_value = self.value[output_item_index]

        # Instantiate outputState for self as sender of ControlProjection
        from PsyNeuLink.Components.States.State import _instantiate_state
        from PsyNeuLink.Components.States.OutputState import OutputState
        state = _instantiate_state(owner=self,
                                            state_type=OutputState,
                                            state_name=output_name,
                                            state_spec=defaultControlAllocation,
                                            state_params=None,
                                            constraint_value=output_value,
                                            constraint_value_name='Default control allocation',
                                            # constraint_index=output_item_index,
                                            context=context)

        projection.sender = state

        # Update allocationPolicy to accommodate instantiated projection and add output_value
        try:
            self.allocationPolicy = np.append(self.self.allocationPolicy, np.atleast_2d(output_value, 0))
        except AttributeError:
            self.allocationPolicy = np.atleast_2d(output_value)

        # Update self.outputState and self.outputStates
        try:
            self.outputStates[output_name] = state
        except AttributeError:
            self.outputStates = OrderedDict({output_name:state})
            self.outputState = self.outputStates[output_name]

        # Add projection to list of outgoing projections
        state.sendsToProjections.append(projection)

        # Add projection to list of ControlProjections
        try:
            self.controlProjections.append(projection)
        except AttributeError:
            self.controlProjections = []

        # Update controlSignalCosts to accommodate instantiated projection
        try:
            self.controlSignalCosts = np.append(self.controlSignalCosts, np.empty((1,1)),axis=0)
        except AttributeError:
            self.controlSignalCosts = np.empty((1,1))

        return state

    def __execute__(self, time_scale=TimeScale.TRIAL, runtime_params=NotImplemented, context=None):
        """Updates ControlProjections based on inputs

        Must be overriden by subclass
        """
        raise ControlMechanismError("{0} must implement execute() method".format(self.__class__.__name__))

    def show(self):

        print ("\n---------------------------------------------------------")

        print ("\n{0}".format(self.name))
        print("\n\tMonitoring the following mechanism outputStates:")
        for state_name, state in list(self.inputStates.items()):
            for projection in state.receivesFromProjections:
                monitored_state = projection.sender
                monitored_state_mech = projection.sender.owner
                monitored_state_index = self.monitoredOutputStates.index(monitored_state)
                exponent = \
                    np.ndarray.item(self.paramsCurrent[OUTCOME_AGGREGATION_FUNCTION].exponents[
                    monitored_state_index])
                weight = \
                    np.ndarray.item(self.paramsCurrent[OUTCOME_AGGREGATION_FUNCTION].weights[monitored_state_index])
                print ("\t\t{0}: {1} (exp: {2}; wt: {3})".
                       format(monitored_state_mech.name, monitored_state.name, exponent, weight))

        print ("\n\tControlling the following mechanism parameters:".format(self.name))
        # Sort for consistency of output:
        state_names_sorted = sorted(self.outputStates.keys())
        for state_name in state_names_sorted:
            for projection in self.outputStates[state_name].sendsToProjections:
                print ("\t\t{0}: {1}".format(projection.receiver.owner.name, projection.receiver.name))

        print ("\n---------------------------------------------------------")