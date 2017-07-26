# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# **********************************************  Projection ***********************************************************

"""
..
    Sections of this document:
      * :ref:`Projection_Overview`
      * :ref:`Projection_Creation`
      * :ref:`Projection_Structure`
         * :ref:`Projection_Sender`
         * :ref:`Projection_Receiver`
      * :ref:`Projection_Execution`
      * :ref:`Projection_Class_Reference`

.. _Projection_Overview:

Overview
--------

Projections allow information to be passed between `Mechanisms <Mechanism>`.  A Projection takes its input from the
`OutputState` of one Mechanism (its `sender <Projection.sender>`), and does whatever conversion is
needed to transmit that information to the `InputState` of another Mechanism (its
`receiver <Projection.receiver>`).  There are four types of Projections that serve different purposes:

* `MappingProjection`
    This takes the output of a `ProcessingMechanism <ProcessingMechanism>`, convert this by convolving it with
    the Projection's `matrix <MappingProjection.MappingProjection.matrix>` parameter, and transmit the result as
    input to another ProcessingMechanism.  Typically, MappingProjections are used to connect Mechanisms in the
    `pathway` of a `Process`.
..
* `ControlProjection`
    takes an `allocation <ControlProjection.ControlProjection.allocation>` specification, usually the ouptput
    of a `ControlMechanism <ControlMechanism>`, and transmit this to the `ParameterState` of a `ProcessingMechanism`
    that uses this to modulate a parameter of the Mechanism or its function. ControlProjections are typically used
    in the context of a `System`.
..
* `LearningProjection`
    takes the value of a `LearningSignal` from a `LearningMechanism`, and transmit this to the
    `ParameterState` of a `MappingProjection` which uses this to modify its
    `matrix <MappingProjection.MappingProjection.matrix>` parameter. LearningProjections are used when
    learning has been specified for a `Process <Process_Learning>` or `System <System_Execution_Learning>`.
..
* `GatingProjection`
    takes the `value <GatingSignal.value>` of a `GatingSignal` belonging to
    a GatingMechanism and conveys it to the `InputState` or `OutputState` of a
    `ProcessingMechanism` for use by the state's `function` in modulating its
    `value`.

COMMENT:
* Gating: takes an input signal and uses it to modulate the InputState and/or OutputState of the receiver
COMMENT

.. _Projection_Creation:

Creating a Projection
---------------------

A Projection can be created on its own, by calling the constructor for the desired type of Projection.  More
commonly, however, Projections are either specified `in context <Projection_In_Context_Specification>`, or
are `created automatically <Projection_Automatic_Creation>`, as described below.


.. _Projection_In_Context_Specification:

In Context Specification
~~~~~~~~~~~~~~~~~~~~~~~~

Projections can be specified in a number of places where they are required or permitted, for example in the
specification of a `pathway` for a `Process`, where the value of a parameter is specified
(e.g., to assign a ControlProjection) or where a MappingProjection is specified  (to assign it a LearningProjection).
Any of the following can be used to specify a Projection in context:

  * *Constructor*.  Used the same way in context as it is ordinarily.
  ..
  * *Projection reference*.  This must be a reference to a Projection that has already been created.
  ..
  * *Projection keyword*.  This creates a default instance of the specified type, and can be any of the following:

      * MAPPING_PROJECTION -- a `MappingProjection` with the `DefaultMechanism` as its :keyword:`sender`.
      |
      * CONTROL_PROJECTION -- a `ControlProjection` with the `DefaultControlMechanism` as its :keyword:`sender`.
      |
      * GATING_PROJECTION -- a `GatingProjection` with the `DefaultGatingMechanism` as its :keyword:`sender`.
      |
      * LEARNING_PROJECTION -- a `LearningProjection`.  At present, this can only be used together with the
        specification of a MappingProjection (see `tuple <Mapping_Matrix_Specification>` format).  If the
        :keyword:`receiver` of the MappingProjection projects to a `LearningMechanism <LearningMechanism>`,
        the latter will be used as the :keyword:`sender` for the LearningProjection.  Otherwise,
        a LearningMechanism will be created for it
        (see `Automatic Instantiation <LearningProjection_Automatic_Creation>` of a LearningProjection for details).
  ..
  * *Projection type*.  This creates a default instance of the specified Projection subclass.
  ..
  * *Specification dictionary*.  This can contain an entry specifying the type of Projection, and/or entries
    specifying the value of parameters used to instantiate it. These should take the following form:

      * PROJECTION_TYPE: *<name of a Projection type>* --
        if this entry is absent, a default Projection will be created that is appropriate for the context
        (for example, a `MappingProjection` for an `InputState`, and a `ControlProjection` for a `ParameterState`).
      |
      * PROJECTION_PARAMS: *Dict[Projection argument, argument value]* --
        the key for each entry of the dictionary must be the name of a Projection parameter, and its value the value
        of the parameter.  It can contain any of the standard parameters for instantiating a Projection (in particular
        its `sender <Projection_Sender>` and `receiver <Projection_Receiver>` or ones specific to a particular type of
        Projection (see documentation for subclass).

      COMMENT:  ??IMPLEMENTED FOR PROJECTION PARAMS??
        Note that parameter
        values in the specification dictionary will be used to instantiate the Projection.  These can be overridden
        during execution by specifying `runtime parameters <Mechanism_Runtime_parameters>` for the Projection,
        either when calling the `execute <Mechanism.Mechanism_Base.execute>` or `run <Mechanism.Mechanism_Base.run>`
        method for a Mechanism directly, or where it is specified in the `pathway` of a Process.
      COMMENT

.. _Projection_Automatic_Creation:

Automatic creation
~~~~~~~~~~~~~~~~~~

Under some circumstances PsyNeuLink will automatically create a Projection. For example, a `Process`
automatically generates a `MappingProjection` between adjacent Mechanisms in its `pathway` if none is specified;
and `LearningProjections <LearningProjection>` are automatically generated when `learning` is specified for a
`Process <Process_Learning>` or `System <System_Execution_Learning>`.  Creating a `state <State>` will also
automatically generate a Projection and a Mechanism as the Projection's `sender <Projection.sender>` if none is
specified in the constructor for the state (the type of Projection and Mechanism depend on the type of state -- see
`state subclasses <States>` for details).

.. _Projection_Structure:

Structure
---------

In addition to its `function <Projection.function>`, a Projection has two primary attributes:

.. _Projection_Sender:

Sender
~~~~~~

This must be an `OutputState`.  The Projection is assigned to the OutputState's `efferents <State_Base.efferents>`
list, and OutputState's `value <OutputState.OutputState.value>` is used as the :keyword:`variable` for Projection's
`function <Projection.function>`.  A sender can be specified as:

  * an **OutputState**, in any of the ways used to `specify an OutputState <OutputState_Specification>`.
  ..
  * a **Mechanism**, in which case the Mechanism's :ref:`primary OutputState  <OutputState_Primary>` is assigned as the
    `sender <Projection.sender>`.

If the `sender <Projection.sender>` is not specified and it can't be determined from the context, or an OutputState
specification is not associated with a Mechanism that can be determined from context, then a default Mechanism of a
type appropriate for the Projection is used, and its `primary OutputState <OutputState_Primary>` is assigned as the
`sender <Projection.sender>`. The type of default Mechanism
COMMENT:
    used by a Projection is specified in its :keyword:`paramClassDefaults[PROJECTION_SENDER]` class attribute, and
COMMENT
is assigned as follows:

  * `MappingProjection`: the
    :py:const:`DefaultProcessingMechanism <Components.__init__.DefaultProcessingMechanism LINK>`
    is used, and its `primary OutputState <OutputState_Primary>` is assigned as the `sender <Projection.sender>`.
  ..
  * `ControlProjection`: if the Projection's `receiver <Projection.receiver>` belongs to a system, then the system's
    `controller` is used as the Mechanism for the `sender <Projection.sender>`, an OutputState is added to the
    ControlMechanism, and assigned as the Projection's `sender <Projection.sender>`.  If the receiver does not
    belong to a system, the ControlProjection will be ignored.
  ..
  COMMENT:
  * `GatingProjection`:  DOCUMENT
  COMMENT
  ..
  * `LearningProjection`: if it is to a MappingProjection that projects to the `TERMINAL` Mechanism of a Process,
    then a `ComparatorMechanism` is created, and its `primary OutputState <OutputState_Primary>` is assigned as the
    `sender <Projection.sender>`.  Otherwise, a `WeightedErrorMechanism` is created and its
    `primary OutputState <OutputState_Primary>` is assigned as the `sender <Projection.sender>`.



.. _Projection_Receiver:

Receiver
~~~~~~~~

This must be an :doc:`InputState` or a :doc:`ParameterState`.  The Projection is assigned to the receiver's
`path_afferents <State_Base.path_afferents>` list, and the output of the Projection's
`function <Projection.function>` is transmitted to its receiver.  A `receiver <Projection.receiver>`
can be specified as:

  * an existing **InputState**;
  ..
  * an existing **Mechanism** or **Projection**; which of these is permissible, and how a state is assigned to it, is
    determined by the type of Projection — see subclasses for details).
  ..
  * a **specification dictionary** (see subclasses for details).
  ..
  .. note::
     a receiver **must** be specified for a Projection;  PsyNeuLink cannot create a default.  This reflects the
     principle of :ref:`Lazy Evaluation <LINK>` which, here, means that objects can create other objects from which
     they *expect* input, but cannot *impose* the creation of "downstream" objects.

COMMENT:
    If the ``receiver`` of a Projection is specified as a Projection or Mechanism, the type of state created and added
    to the Mechanism depends on the type of Projection:
        MappingProjection:
            receiver = <Mechanism>.input_state
        ControlProjection:
            sender = <Mechanism>.outputState
            receiver = <Mechanism>.parameterState if there is a corresponding parameter; otherwise, an error occurs
        LearningProjection:
            sender = <Mechanism>.outputState
            receiver = <MappingProjection>.parameterState IF AND ONLY IF there is a single one
                        that is a ParameterState;  otherwise, an exception is raised
COMMENT

.. _Projection_Execution:

Execution
---------

A Projection cannot be executed directly.  It is executed when the `state <States>` to which it projects — its
`receiver <Projection.receiver>` — is updated;  that occurs when the state's owner Mechanism is executed.  When a
Projection executes, it gets the value of its `sender <Projection.sender>`, assigns this as the :keyword:`variable`
of its `function <Projection.function>`, calls the function, and provides the result as to its
`receiver <Projection.receiver>`.  The `function <Projection.function>` of a Projection converts the value received
from its `sender <Projection.sender>` to a form suitable as input for its `receiver <Projection.receiver>`.

.. _Projection_Class_Reference:

"""
import inspect
import typecheck as tc
import warnings

from PsyNeuLink.Components.Component import Component, InitStatus
from PsyNeuLink.Components.Mechanisms.Mechanism import Mechanism
from PsyNeuLink.Components.ShellClasses import Process, Projection, State
from PsyNeuLink.Globals.Keywords import CONTROL, CONTROL_PROJECTION, GATING, GATING_PROJECTION, INPUT_STATE, LEARNING, LEARNING_PROJECTION, MAPPING_PROJECTION, MATRIX_KEYWORD_SET, MECHANISM, OUTPUT_STATE, PARAMETER_STATE_PARAMS, PROJECTION, PROJECTION_SENDER, PROJECTION_TYPE, kwAddInputState, kwAddOutputState, kwProjectionComponentCategory
from PsyNeuLink.Globals.Preferences.PreferenceSet import PreferenceLevel
from PsyNeuLink.Globals.Registry import register_category
from PsyNeuLink.Globals.Utilities import ContentAddressableList, iscompatible, type_match

ProjectionRegistry = {}

kpProjectionTimeScaleLogEntry = "Projection TimeScale"

projection_keywords = set()

PROJECTION_SPEC_KEYWORDS = {MAPPING_PROJECTION,
                            LEARNING, LEARNING_PROJECTION,
                            CONTROL, CONTROL_PROJECTION,
                            GATING, GATING_PROJECTION}


class ProjectionError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)

# Projection factory method:
# def projection(name=NotImplemented, params=NotImplemented, context=None):
#         """Instantiates default or specified subclass of Projection
#
#         If called w/o arguments or 1st argument=NotImplemented, instantiates default subclass (ParameterState)
#         If called with a name string:
#             - if registered in ProjectionRegistry class dictionary as name of a subclass, instantiates that class
#             - otherwise, uses it as the name for an instantiation of the default subclass, and instantiates that
#         If a params dictionary is included, it is passed to the subclass
#
#         :param name:
#         :param param_defaults:
#         :return:
#         """
#
#         # Call to instantiate a particular subclass, so look up in MechanismRegistry
#         if name in ProjectionRegistry:
#             return ProjectionRegistry[name].mechanismSubclass(params)
#         # Name is not in MechanismRegistry or is not provided, so instantiate default subclass
#         else:
#             # from Components.Defaults import DefaultProjection
#             return DefaultProjection(name, params)
#

class Projection_Base(Projection):
    """
    Projection_Base(  \
    receiver,         \
    sender=None,      \
    params=None,      \
    name=None,        \
    prefs=None)

    Base class for all Projections.

    .. note::
       Projection is an abstract class and should NEVER be instantiated by a direct call to its constructor.
       It should be created by calling the constructor for a subclass` or by using any of the other methods for
       `specifying a Projection <Projection_In_Context_Specification>`.


    COMMENT:
        Description
        -----------
            Projection category of Component class (default type:  MappingProjection)

        Gotchas
        -------
            When referring to the Mechanism that is a Projection's sender or receiver Mechanism, must add ".owner"

        Class attributes
        ----------------
            + componentCategory (str): kwProjectionFunctionCategory
            + className (str): kwProjectionFunctionCategory
            + suffix (str): " <className>"
            + registry (dict): ProjectionRegistry
            + classPreference (PreferenceSet): ProjectionPreferenceSet, instantiated in __init__()
            + classPreferenceLevel (PreferenceLevel): PreferenceLevel.CATEGORY
            + variableClassDefault (value): [0]
            + requiredParamClassDefaultTypes = {PROJECTION_SENDER: [str, Mechanism, State]}) # Default sender type
            + paramClassDefaults (dict)
            + FUNCTION (Function class or object, or method)

        Class methods
        -------------
            None

        ProjectionRegistry
        ------------------
            All Projections are registered in ProjectionRegistry, which maintains a dict for each subclass,
              a count for all instances of that type, and a dictionary of those instances
    COMMENT

    Attributes
    ----------

    variable : value
        input to Projection, received from OutputState.value of sender.

    sender : State
        State from which Projection receives its input.

    receiver : State
        State (of a Mechanism or Projection)
        State to which Projection sends its output.

    value : value
        Output of Projection, transmitted to InputState.variable of receiver.

    COMMENT:
        projectionSender : Mechanism, State, or Object
            This is assigned by __init__.py with the default sender state for each subclass.
            It is used if sender arg is not specified in the constructor or when the Projection is assigned.
            If it is different than the default;  where it is used, it overrides the ``sender`` argument even if that is
            provided.

        projectionSender : 1d array
            Used to instantiate projectionSender
    COMMENT

    name : str : default <Projection subclass>-<index>
        the name of the Projection.
        Specified in the **name** argument of the constructor for the Projection;  if not is specified,
        a default is assigned by ProjectionRegistry based on the Projection's subclass
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

    prefs : PreferenceSet or specification dict : Projection.classPreferences
        the `PreferenceSet` for the Projection.
        Specified in the **prefs** argument of the constructor for the Projection;  if it is not specified, a default is
        assigned using `classPreferences` defined in __init__.py
        (see :doc:`PreferenceSet <LINK>` for details).

    """

    color = 0

    componentCategory = kwProjectionComponentCategory
    className = componentCategory
    suffix = " " + className

    registry = ProjectionRegistry

    classPreferenceLevel = PreferenceLevel.CATEGORY

    variableClassDefault = [0]

    requiredParamClassDefaultTypes = Component.requiredParamClassDefaultTypes.copy()
    requiredParamClassDefaultTypes.update({PROJECTION_SENDER: [str, Mechanism, State]}) # Default sender type

    def __init__(self,
                 receiver,
                 sender=None,
                 params=None,
                 name=None,
                 prefs=None,
                 context=None):
        """Assign sender, receiver, and execute method and register Mechanism with ProjectionRegistry

        This is an abstract class, and can only be called from a subclass;
           it must be called by the subclass with a context value

# DOCUMENT:  MOVE TO ABOVE, UNDER INSTANTIATION
        Initialization arguments:
            - sender (Mechanism, State or dict):
                specifies source of input to Projection (default: senderDefault)
            - receiver (Mechanism, State or dict)
                 destination of Projection (default: none)
            - params (dict) - dictionary of Projection params:
                + FUNCTION:<method>
        - name (str): if it is not specified, a default based on the class is assigned in register_category,
                            of the form: className+n where n is the n'th instantiation of the class
            - prefs (PreferenceSet or specification dict):
                 if it is omitted, a PreferenceSet will be constructed using the classPreferences for the subclass
                 dict entries must have a preference keyPath as key, and a PreferenceEntry or setting as their value
                 (see Description under PreferenceSet for details)
            - context (str): must be a reference to a subclass, or an exception will be raised

        NOTES:
        * Receiver is required, since can't instantiate a Projection without a receiving State
        * If sender and/or receiver is a Mechanism, the appropriate State is inferred as follows:
            MappingProjection:
                sender = <Mechanism>.outputState
                receiver = <Mechanism>.input_state
            ControlProjection:
                sender = <Mechanism>.outputState
                receiver = <Mechanism>.paramsCurrent[<param>] IF AND ONLY IF there is a single one
                            that is a ParameterState;  otherwise, an exception is raised
        * _instantiate_sender, _instantiate_receiver must be called before _instantiate_function:
            - _validate_params must be called before _instantiate_sender, as it validates PROJECTION_SENDER
            - instantatiate_sender may alter self.variable, so it must be called before _validate_function
            - instantatiate_receiver must be called before _validate_function,
                 as the latter evaluates receiver.value to determine whether to use self.function or FUNCTION
        * If variable is incompatible with sender's output, it is set to match that and revalidated (_instantiate_sender)
        * if FUNCTION is provided but its output is incompatible with receiver value, self.function is tried
        * registers Projection with ProjectionRegistry

        :param sender: (State or dict)
        :param receiver: (State or dict)
        :param param_defaults: (dict)
        :param name: (str)
        :param context: (str)
        :return: None
        """
        from PsyNeuLink.Composition import Composition
        from PsyNeuLink.Components.States.ParameterState import ParameterState
        from PsyNeuLink.Components.States.State import State_Base

        if not isinstance(context, Projection_Base):
            raise ProjectionError("Direct call to abstract class Projection() is not allowed; "
                                 "use projection() or one of the following subclasses: {0}".
                                 format(", ".join("{!s}".format(key) for (key) in ProjectionRegistry.keys())))

        # Register with ProjectionRegistry or create one
        register_category(entry=self,
                          base_class=Projection_Base,
                          name=name,
                          registry=ProjectionRegistry,
                          context=context)

        # # MODIFIED 9/11/16 NEW:
        # Create projection's _stateRegistry and ParameterState entry
        self._stateRegistry = {}

        register_category(entry=ParameterState,
                          base_class=State_Base,
                          registry=self._stateRegistry,
                          context=context)

        self.default_composition = Composition()

        try:
            if self.init_status is InitStatus.DEFERRED_INITIALIZATION:
                self.init_args = locals().copy()
                self.init_args['context'] = self
                self.init_args['name'] = name

                # remove local imports
                del self.init_args['ParameterState']
                del self.init_args['State_Base']

                return
        except AttributeError:
            # if this Projection does not have an init_status attribute, we can guarantee that it's not in
            # deferred init state. It's tricky to ensure this attribute always exists due to the nature
            # of deferred init
            pass

# FIX: 6/23/16 NEEDS ATTENTION *******************************************************A
#      NOTE: SENDER IS NOT YET KNOWN FOR DEFAULT control_signal
#      WHY IS self.sender IMPLEMENTED WHEN sender IS NOT??

        self.sender = sender
        self.receiver = receiver

# MODIFIED 6/12/16:  VARIABLE & SENDER ASSIGNMENT MESS:
        # ADD _validate_variable, THAT CHECKS FOR SENDER?
        # WHERE DOES DEFAULT SENDER GET INSTANTIATED??
        # VARIABLE ASSIGNMENT SHOULD OCCUR AFTER THAT

# MODIFIED 6/12/16:  ADDED ASSIGNMENT HERE -- BUT SHOULD GET RID OF IT??
        # AS ASSIGNMENT SHOULD BE DONE IN _validate_variable, OR WHEREVER SENDER IS DETERMINED??
# FIX:  NEED TO KNOW HERE IF SENDER IS SPECIFIED AS A MECHANISM OR STATE
        try:
            variable = sender.value
        except:
            try:
                if self.receiver.prefs.verbosePref:
                    warnings.warn("Unable to get value of sender ({0}) for {1};  will assign default ({2})".
                                  format(sender, self.name, self.variableClassDefault))
                variable = None
            except AttributeError:
                raise ProjectionError("{} has no receiver assigned".format(self.name))

        # MODIFIED 6/27/17 NEW: commented this out because this is throwing an error as follows: -Changyan
        # AttributeError: 'MappingProjection' object has no attribute '_prefs'
        # MODIFIED 4/21/17 NEW: [MOVED FROM MappingProjection._instantiate_receiver]
        # Assume that if receiver was specified as a Mechanism, it should be assigned to its (primary) InputState
        if isinstance(self.receiver, Mechanism):
            # if (len(self.receiver.input_states) > 1 and
            #         (self.prefs.verbosePref or self.receiver.prefs.verbosePref)):
            #     print("{0} has more than one inputState; {1} was assigned to the first one".
            #           format(self.receiver.owner.name, self.name))
            self.receiver = self.receiver.input_state
        # MODIFIED 4/21/17 END


# FIX: SHOULDN'T default_variable HERE BE sender.value ??  AT LEAST FOR MappingProjection?, WHAT ABOUT ControlProjection??
# FIX:  ?LEAVE IT TO _validate_variable, SINCE SENDER MAY NOT YET HAVE BEEN INSTANTIATED
# MODIFIED 6/12/16:  ADDED ASSIGNMENT ABOVE
#                   (TO HANDLE INSTANTIATION OF DEFAULT ControlProjection SENDER -- BUT WHY ISN'T VALUE ESTABLISHED YET?
        # Validate variable, function and params, and assign params to paramsInstanceDefaults
        # Note: pass name of mechanism (to override assignment of componentName in super.__init__)
        super(Projection_Base, self).__init__(default_variable=variable,
                                              param_defaults=params,
                                              name=self.name,
                                              prefs=prefs,
                                              context=context.__class__.__name__)

        self.default_composition.add_projection(None, self, None)

    def _validate_params(self, request_set, target_set=None, context=None):
        """Validate PROJECTION_SENDER and/or sender arg (current self.sender), and assign one of them as self.sender

        Check:
        - that PROJECTION_SENDER is a Mechanism or State
        - if it is different from paramClassDefaults[PROJECTION_SENDER], use it
        - if it is the same or is invalid, check if sender arg was provided to __init__ and is valid
        - if sender arg is valid use it (if PROJECTION_SENDER can't be used);
        - otherwise use paramClassDefaults[PROJECTION_SENDER]
        - when done, sender is assigned to self.sender

        Note: check here only for sender's type, NOT content (e.g., length, etc.); that is done in _instantiate_sender

        :param request_set:
        :param target_set:
        :param context:
        :return:
        """

        super(Projection, self)._validate_params(request_set, target_set, context)

        # try:
        #     sender_param = target_set[PROJECTION_SENDER]
        # except KeyError:
        #     # This should never happen, since PROJECTION_SENDER is a required param
        #     raise ProjectionError("Program error: required param \'{0}\' missing in {1}".
        #                           format(PROJECTION_SENDER, self.name))

        if PROJECTION_SENDER in target_set:
            sender_param = target_set[PROJECTION_SENDER]
            # PROJECTION_SENDER is either an instance or class of Mechanism or State:
            if (isinstance(sender_param, (Mechanism, State)) or
                    (inspect.isclass(sender_param) and issubclass(sender_param, (Mechanism, State)))):
                # it is NOT the same as the default, use it
                if sender_param is not self.paramClassDefaults[PROJECTION_SENDER]:
                    self.sender = sender_param
                # it IS the same as the default, but sender arg was not provided, so use it (= default):
                elif self.sender is None:
                    self.sender = sender_param
                    if self.prefs.verbosePref:
                        warnings.warn("Neither {0} nor sender arg was provided for {1} projection to {2}; "
                                      "default ({3}) will be used".format(PROJECTION_SENDER,
                                                                          self.name,
                                                                          self.receiver.owner.name,
                                                                          sender_param.__class__.__name__))
                # it IS the same as the default, so check if sender arg (self.sender) is valid
                elif not (isinstance(self.sender, (Mechanism, State, Process)) or
                              # # MODIFIED 12/1/16 OLD:
                              # (inspect.isclass(self.sender) and
                              #      (issubclass(self.sender, Mechanism) or issubclass(self.sender, State)))):
                              # MODIFIED 12/1/16 NEW:
                              (inspect.isclass(self.sender) and issubclass(self.sender, (Mechanism, State)))):
                              # MODIFIED 12/1/16 END
                    # sender arg (self.sender) is not valid, so use PROJECTION_SENDER (= default)
                    self.sender = sender_param
                    if self.prefs.verbosePref:
                        warnings.warn("{0} was not provided for {1} projection to {2}, "
                                      "and sender arg ({3}) is not valid; default ({4}) will be used".
                                      format(PROJECTION_SENDER,
                                             self.name,
                                             self.receiver.owner.name,
                                             self.sender,
                                             sender_param.__class__.__name__))

        # FIX: IF PROJECTION, PUT HACK HERE TO ACCEPT AND FORGO ANY FURTHER PROCESSING??
                # IS the same as the default, and sender arg was provided, so use sender arg
                else:
                    pass
            # PROJECTION_SENDER is not valid, and:
            else:
                # sender arg was not provided, use paramClassDefault
                if self.sender is None:
                    self.sender = self.paramClassDefaults[PROJECTION_SENDER]
                    if self.prefs.verbosePref:
                        warnings.warn("{0} ({1}) is invalid and sender arg ({2}) was not provided;"
                                      " default {3} will be used".
                                      format(PROJECTION_SENDER, sender_param, self.sender,
                                             self.paramClassDefaults[PROJECTION_SENDER]))
                # sender arg is also invalid, so use paramClassDefault
                elif not isinstance(self.sender, (Mechanism, State)):
                    self.sender = self.paramClassDefaults[PROJECTION_SENDER]
                    if self.prefs.verbosePref:
                        warnings.warn("Both {0} ({1}) and sender arg ({2}) are both invalid; default {3} will be used".
                                      format(PROJECTION_SENDER, sender_param, self.sender,
                                             self.paramClassDefaults[PROJECTION_SENDER]))
                else:
                    self.sender = self.paramClassDefaults[PROJECTION_SENDER]
                    if self.prefs.verbosePref:
                        warnings.warn("{0} ({1}) is invalid; sender arg ({2}) will be used".
                                      format(PROJECTION_SENDER, sender_param, self.sender))
                if not isinstance(self.paramClassDefaults[PROJECTION_SENDER], (Mechanism, State)):
                    raise ProjectionError("Program error: {0} ({1}) and sender arg ({2}) for {3} are both "
                                          "absent or invalid and default (paramClassDefault[{4}]) is also invalid".
                                          format(PROJECTION_SENDER,
                                                 # sender_param.__name__,
                                                 # self.sender.__name__,
                                                 # self.paramClassDefaults[PROJECTION_SENDER].__name__))
                                                 sender_param,
                                                 self.sender,
                                                 self.name,
                                                 self.paramClassDefaults[PROJECTION_SENDER]))

    def _instantiate_attributes_before_function(self, context=None):
        self._instantiate_sender(context=context)
        self._instantiate_parameter_states(context=context)

    def _instantiate_parameter_states(self, context=None):

        from PsyNeuLink.Components.States.ParameterState import _instantiate_parameter_states
        _instantiate_parameter_states(owner=self, context=context)


    def _instantiate_sender(self, context=None):
        """Assign self.sender to OutputState of sender and insure compatibility with self.variable

        Assume self.sender has been assigned in _validate_params, from either sender arg or PROJECTION_SENDER
        Validate, set self.variable, and assign projection to sender's efferents attribute

        If self.sender is a Mechanism, re-assign it to <Mechanism>.outputState
        If self.sender is a State class reference, validate that it is a OutputState
        Assign projection to sender's efferents attribute
        If self.value / self.variable is None, set to sender.value
        """

        from PsyNeuLink.Components.States.OutputState import OutputState
        from PsyNeuLink.Components.States.ParameterState import ParameterState

        # # IMPLEMENTATION NOTE:  The following supported instantiation of a default sender type by a projection, for
        # #                       projections that did not yet have their sender specified;  however, this should now
        # #                       be covered by deferred_init(): sender is assigned in that call or by the time is made.
        # # If sender is a class, instantiate it:
        # # - assume it is a Mechanism or State (should have been validated in _validate_params)
        # # - implement default sender of the corresponding type
        # if inspect.isclass(self.sender):
        #     if issubclass(self.sender, OutputState):
        #         # MODIFIED 9/12/16 NEW:
        #         # self.paramsCurrent['function_params']['matrix']
        #         # FIX: ASSIGN REFERENCE VALUE HERE IF IT IS A MAPPING_PROJECTION??
        #         # MODIFIED 9/12/16 END
        #         self.sender = self.paramsCurrent[PROJECTION_SENDER](self.paramsCurrent[PROJECTION_SENDER_VALUE])
        #     else:
        #         raise ProjectionError("Sender ({0}) for {1} must be a OutputState".
        #                               format(self.sender.__name__, self.name))

        # If sender is specified as a Mechanism (rather than a State),
        #     get relevant OutputState and assign it to self.sender
        # IMPLEMENTATION NOTE: Assume that sender should be the primary OutputState; if that is not the case,
        #                      sender should either be explicitly assigned, or handled in an override of the
        #                      method by the relevant subclass prior to calling super
        if isinstance(self.sender, Mechanism):
            self.sender = self.sender.output_state

        # At this point, self.sender should be a OutputState
        if not isinstance(self.sender, OutputState):
            raise ProjectionError("Sender specified for {} ({}) must be a Mechanism or an OutputState".
                                  format(self.name, self.sender))

        # Assign projection to sender's efferents list attribute
        if not self in self.sender.efferents:
            self.sender.efferents.append(self)

        # Validate projection's variable (self.variable) against sender.outputState.value
        if iscompatible(self.variable, self.sender.value):
            # Is compatible, so assign sender.outputState.value to self.variable
            self.variable = self.sender.value

        else:
            # Not compatible, so:
            # - issue warning
            if self.prefs.verbosePref:
                warnings.warn("The variable ({0}) of {1} projection to {2} is not compatible with output ({3})"
                              " of function {4} for sender ({5}); it has been reassigned".
                      format(self.variable,
                             self.name,
                             self.receiver.owner.name,
                             self.sender.value,
                             self.sender.function.__class__.__name__,
                             self.sender.owner.name))
            # - reassign self.variable to sender.value
            self._instantiate_defaults(variable=self.sender.value, context=context)

    def _instantiate_attributes_after_function(self, context=None):
        self._instantiate_receiver(context=context)

    def _instantiate_receiver(self, context=None):
        """Call receiver's owner to add projection to its afferents list

        Notes:
        * Assume that subclasses implement this method in which they:
          - test whether self.receiver is a Mechanism and, if so, replace with State appropriate for projection
          - calls this method (as super) to assign projection to the Mechanism
        * Constraint that self.value is compatible with receiver.input_state.value
            is evaluated and enforced in _instantiate_function, since that may need to be modified (see below)
        * Verification that projection has not already been assigned to receiver is handled by _add_projection_to;
            if it has, a warning is issued and the assignment request is ignored

        :param context: (str)
        :return:
        """
        # IMPLEMENTATION NOTE: since projection is added using Mechanism.add_projection(projection, state) method,
        #                      could add state specification as arg here, and pass through to add_projection()
        #                      to request a particular state
        # IMPLEMENTATION NOTE: should check that projection isn't already received by receivers

        if isinstance(self.receiver, State):
            _add_projection_to(receiver=self.receiver.owner,
                               state=self.receiver,
                               projection_spec=self,
                               context=context)

        # This should be handled by implementation of _instantiate_receiver by projection's subclass
        elif isinstance(self.receiver, Mechanism):
            raise ProjectionError("PROGRAM ERROR: receiver for {0} was specified as a Mechanism ({1});"
                                  "this should have been handled by _instantiate_receiver for {2}".
                                  format(self.name, self.receiver.name, self.__class__.__name__))

        else:
            raise ProjectionError("Unrecognized receiver specification ({0}) for {1}".format(self.receiver, self.name))

    def _update_parameter_states(self, runtime_params=None, time_scale=None, context=None):
        for state_name, state in self._parameter_states.items():

            state.update(params=runtime_params, time_scale=time_scale, context=context)

            # Assign ParameterState's value to parameter value in runtime_params
            if runtime_params and state_name in runtime_params[PARAMETER_STATE_PARAMS]:
                param = param_template = runtime_params
            # Otherwise use paramsCurrent
            else:
                param = param_template = self.paramsCurrent

            # Determine whether template (param to type-match) is at top level or in a function_params dictionary
            try:
                param_template[state_name]
            except KeyError:
                param_template = self.function_params

            # Get its type
            param_type = type(param_template[state_name])
            # If param is a tuple, get type of parameter itself (= 1st item;  2nd is projection or Modulation)
            if param_type is tuple:
                param_type = type(param_template[state_name][0])

            # Assign version of ParameterState.value matched to type of template
            #    to runtime param or paramsCurrent (per above)
            param[state_name] = type_match(state.value, param_type)

    def add_to(self, receiver, state, context=None):
        _add_projection_to(receiver=receiver, state=state, projection_spec=self, context=context)


def _is_projection_spec(spec, include_matrix_keywords=True):
    """Evaluate whether spec is a valid Projection specification

    Return `True` if spec is any of the following:
    + Projection class (or keyword string constant for one):
    + Projection object:
    + 2-item tuple of which the second is a projection_spec (checked recursively with thi method):
    + specification dict containing:
        + PROJECTION_TYPE:<Projection class> - must be a subclass of Projection
    + Matrix keyword (if include_matrix_keywords is set to `True`)

    Otherwise, return :keyword:`False`
    """

    if inspect.isclass(spec) and issubclass(spec, Projection):
        return True
    if isinstance(spec, Projection):
        return True
    if isinstance(spec, dict) and PROJECTION_TYPE in spec:
        return True
    if isinstance(spec, str) and spec in PROJECTION_SPEC_KEYWORDS:
        return True
    if include_matrix_keywords:
        if isinstance(spec, str) and spec in MATRIX_KEYWORD_SET:
            return True
        from PsyNeuLink.Components.Functions.Function import get_matrix
        if get_matrix(spec) is not None:
            return True
    if isinstance(spec, tuple) and len(spec) == 2:
        # Call recursively on first item, which should be a standard projection spec
        if _is_projection_spec(spec[0]):
            # IMPLEMENTATION NOTE: keywords must be used to refer to subclass, to avoid import loop
            if _is_projection_subclass(spec[1], MAPPING_PROJECTION):
                return True
            if _is_projection_subclass(spec[1], LEARNING_PROJECTION):
                return True
            if _is_projection_subclass(spec[1], CONTROL_PROJECTION):
                return True
            if _is_projection_subclass(spec[1], GATING_PROJECTION):
                return True
    return False

def _is_projection_subclass(spec, keyword):
    """Evaluate whether spec is a valid specification of type

    keyword must specify a class registered in ProjectionRegistry

    Return true if spec ==
    + keyword
    + subclass of Projection associated with keyword (from ProjectionRegistry)
    + instance of the subclass
    + specification dict for instance of the subclass:
        keyword is a keyword for an entry in the spec dict
        keyword[spec] is a legal specification for the subclass

    Otherwise, return :keyword:`False`
    """
    if spec is keyword:
        return True
    # Get projection subclass specified by keyword
    try:
        type = ProjectionRegistry[keyword]
    except KeyError:
        pass
    else:
        # Check if spec is either the name of the subclass or an instance of it
        if inspect.isclass(spec) and issubclass(spec, type):
            return True
        if isinstance(spec, type):
            return True
    # spec is a specification dict for an instance of the projection subclass
    if isinstance(spec, dict) and keyword in spec:
        # Recursive call to determine that the entry of specification dict is a legal spec for the projection subclass
        if _is_projection_subclass(spec[keyword], keyword):
            return True
    return False

# IMPLEMENTATION NOTE: MOVE THIS TO ModulatorySignals WHEN THAT IS IMPLEMENTED
@tc.typecheck
def _validate_receiver(sender_mech:Mechanism,
                       projection:Projection,
                       expected_owner_type:type,
                       spec_type=None,
                       context=None):
    """Check that projection is to expected_receiver_type and in the same system as the sender_mech (if specified)

    expected_owner_type must be a Mechanism or a Projection
    spec_type should be LEARNING_SIGNAL, CONTROL_SIGNAL or GATING_SIGNAL

    """
    spec_type = " in the {} arg ".format(spec_type) or ""

    if projection.init_status is InitStatus.DEFERRED_INITIALIZATION:
        # receiver = projection.init_args['receiver'].owner
        state = projection.init_args['receiver']
        receiver = state.owner
    else:
        # receiver = projection.receiver.owner
        state = projection.receiver
        receiver = state.owner

    if isinstance(receiver, Mechanism):
        receiver_mech = receiver
    elif isinstance(receiver, Projection):
        receiver_mech = receiver.receiver.owner
    else:
        raise ProjectionError("receiver of projection ({}) must be a {} or {}".
                              format(projection.name, MECHANISM, PROJECTION))

    if not isinstance(receiver, expected_owner_type):
        raise ProjectionError("A {} specified {}for {} ({}) projects to a component other than the {} of a {}".
                                    format(projection.__class__.__name__,
                                           spec_type,
                                           sender_mech.name,
                                           receiver,
                                           state.__class__.__name__,
                                           expected_owner_type.__name__))

    # Check if receiver_mech is in the same system as sender_mech;
    #    if either has not been assigned a system, return

    # Check whether mech is in the same system as sender_mech
    receiver_systems = set()
    # receiver_mech is a ControlMechanism (which has a system but no systems attribute)
    if hasattr(receiver_mech, 'system') and receiver_mech.system:
        receiver_systems.update({receiver_mech.system})
    # receiver_mech is a ProcessingMechanism (which has a systems but system attribute is usually None)
    elif hasattr(receiver_mech, 'systems') and receiver_mech.systems:
        receiver_systems.update(set(receiver_mech.systems))
    else:
        return

    sender_systems = set()
    # sender_mech is a ControlMechanism (which has a system but no systems attribute)
    if hasattr(sender_mech, 'system') and sender_mech.system:
        sender_systems.update({sender_mech.system})
    # sender_mech is a ProcessingMechanism (which has a systems but system attribute is usually None)
    elif hasattr(sender_mech, 'systems')and sender_mech.systems:
        sender_systems.update(set(sender_mech.systems))
    else:
        return

    #  Check that projection is to a (projection to a) mechanisms in the same system as sender_mech
    if not receiver_systems & sender_systems:
        raise ProjectionError("A {} specified {}for {} projects to a component that is not in the same system".
                                    format(projection.__class__.__name__,
                                           spec_type,
                                           sender_mech.name))

# IMPLEMENTATION NOTE:  THIS SHOULD BE MOVED TO COMPOSITION ONCE THAT IS IMPLEMENTED
def _add_projection_to(receiver, state, projection_spec, context=None):
    """Assign an "incoming" Projection to a receiver InputState or ParameterState of a Component object

    Verify that projection has not already been assigned to receiver;
        if it has, issue a warning and ignore the assignment request.

    Requirements:
       * receiver must be an appropriate Component object (currently, a Mechanism or a Projection);
       * state must be a specification of an InputState or ParameterState;
       * specification of InputState can be any of the following:
                - INPUT_STATE - assigns projection_spec to (primary) InputState;
                - InputState object;
                - index for Mechanism.input_states;
                - name of an existing InputState (i.e., key for Mechanism.input_states);
                - the keyword kwAddInputState or the name for an InputState to be added;
       * specification of ParameterState must be a ParameterState object
       * projection_spec can be any valid specification of a projection_spec
           (see `State._instantiate_projections_to_state`).

    Args:
        receiver (Mechanism or Projection)
        state (State subclass)
        projection_spec: (Projection, dict, or str)
        context

    """
    # IMPLEMENTATION NOTE:  ADD FULL SET OF ParameterState SPECIFICATIONS
    #                       CURRENTLY, ASSUMES projection_spec IS AN ALREADY INSTANTIATED PROJECTION

    from PsyNeuLink.Components.States.State import _instantiate_state
    from PsyNeuLink.Components.States.State import State_Base
    from PsyNeuLink.Components.States.InputState import InputState
    from PsyNeuLink.Components.States.ParameterState import ParameterState

    if not isinstance(state, (int, str, InputState, ParameterState)):
        raise ProjectionError("State specification(s) for {0} (as receivers of {1}) contain(s) one or more items"
                             " that is not a name, reference to an InputState or ParameterState object, "
                             " or an index (for input_states)".
                             format(receiver.name, projection_spec.name))

    # state is State object, so use that
    if isinstance(state, State_Base):
        state._instantiate_projections_to_state(projections=projection_spec, context=context)
        return

    # Generic INPUT_STATE is specified, so use (primary) InputState
    elif state is INPUT_STATE:
        receiver.input_state._instantiate_projections_to_state(projections=projection_spec, context=context)
        return

    # input_state is index into input_states OrderedDict, so get corresponding key and assign to input_state
    elif isinstance(state, int):
        try:
            key = receiver.input_states[state]
        except IndexError:
            raise ProjectionError("Attempt to assign projection_spec ({0}) to InputState {1} of {2} "
                                 "but it has only {3} input_states".
                                 format(projection_spec.name, state, receiver.name, len(receiver.input_states)))
        else:
            input_state = key

    # input_state is string (possibly key retrieved above)
    #    so try as key in input_states OrderedDict (i.e., as name of an InputState)
    if isinstance(state, str):
        try:
            receiver.input_state[state]._instantiate_projections_to_state(projections=projection_spec, context=context)
        except KeyError:
            pass
        else:
            if receiver.prefs.verbosePref:
                warnings.warn("Projection_spec {0} added to {1} of {2}".
                              format(projection_spec.name, state, receiver.name))
            # return

    # input_state is either the name for a new InputState or kwAddNewInputState
    if not state is kwAddInputState:
        if receiver.prefs.verbosePref:
            reassign = input("\nAdd new InputState named {0} to {1} (as receiver for {2})? (y/n):".
                             format(input_state, receiver.name, projection_spec.name))
            while reassign != 'y' and reassign != 'n':
                reassign = input("\nAdd {0} to {1}? (y/n):".format(input_state, receiver.name))
            if reassign == 'n':
                raise ProjectionError("Unable to assign projection {0} to receiver {1}".
                                      format(projection_spec.name, receiver.name))

    # validate that projection has not already been assigned to receiver
    if receiver.verbosePref or projection_spec.sender.owner.verbosePref:
        if projection_spec in receiver.all_afferents:
            warnings.warn("Request to assign {} as projection to {} was ignored; it was already assigned".
                          format(projection_spec.name, receiver.owner.name))

    input_state = _instantiate_state(owner=receiver,
                                    state_type=InputState,
                                    state_name=input_state,
                                    state_spec=projection_spec.value,
                                    constraint_value=projection_spec.value,
                                    constraint_value_name='Projection_spec value for new InputState',
                                    context=context)

    #  Update inputState and input_states
    if receiver.input_states:
        receiver.input_states[input_state.name] = input_state

    # No InputState(s) yet, so create them
    else:
        receiver.input_states = ContentAddressableList(component_type=State_Base,
                                                       list=[input_state],
                                                       name=receiver.name+'.input_states')

    input_state._instantiate_projections_to_state(projections=projection_spec, context=context)


# IMPLEMENTATION NOTE:  THIS SHOULD BE MOVED TO COMPOSITION ONCE THAT IS IMPLEMENTED
def _add_projection_from(sender, state, projection_spec, receiver, context=None):
    """Assign an "outgoing" Projection from an OutputState of a sender Mechanism

    projection_spec can be any valid specification of a projection_spec (see State._instantiate_projections_to_state)
    state must be a specification of an OutputState
    Specification of OutputState can be any of the following:
            - OUTPUT_STATE - assigns projection_spec to (primary) OutputState
            - OutputState object
            - index for Mechanism.outputStates OrderedDict
            - name of OutputState (i.e., key for Mechanism.OutputStates OrderedDict))
            - the keyword kwAddOutputState or the name for an OutputState to be added

    Args:
        sender (Mechanism):
        projection_spec: (Projection, dict, or str)
        state (OutputState, str, or value):
        context:
    """


    from PsyNeuLink.Components.States.State import _instantiate_state
    from PsyNeuLink.Components.States.State import State_Base
    from PsyNeuLink.Components.States.OutputState import OutputState

    # Validate that projection is not already assigned to sender; if so, warn and ignore

    if isinstance(projection_spec, Projection):
        projection = projection_spec
        if ((isinstance(sender, OutputState) and projection.sender is sender) or
                (isinstance(sender, Mechanism) and projection.sender is sender.output_state)):
            if sender.verbosePref:
                warnings.warn("Request to assign {} as sender of {}, but it has already been assigned".
                              format(sender.name, projection.name))
                return

    if not isinstance(state, (int, str, OutputState)):
        raise ProjectionError("State specification for {0} (as sender of {1}) must be the name, reference to "
                              "or index of an OutputState of {0} )".format(sender.name, projection_spec))

    # state is State object, so use that
    if isinstance(state, State_Base):
        state._instantiate_projection_from_state(projection_spec=projection_spec, receiver=receiver, context=context)
        return

    # Generic OUTPUT_STATE is specified, so use (primary) OutputState
    elif state is OUTPUT_STATE:
        sender.output_state._instantiate_projections_to_state(projections=projection_spec, context=context)
        return

    # input_state is index into OutputStates OrderedDict, so get corresponding key and assign to output_state
    elif isinstance(state, int):
        try:
            key = list(sender.output_states.keys)[state]
        except IndexError:
            raise ProjectionError("Attempt to assign projection_spec ({0}) to OutputState {1} of {2} "
                                 "but it has only {3} OutputStates".
                                 format(projection_spec.name, state, sender.name, len(sender.output_states)))
        else:
            output_state = key

    # output_state is string (possibly key retrieved above)
    #    so try as key in output_states ContentAddressableList (i.e., as name of an OutputState)
    if isinstance(state, str):
        try:
            sender.output_state[state]._instantiate_projections_to_state(projections=projection_spec, context=context)
        except KeyError:
            pass
        else:
            if sender.prefs.verbosePref:
                warnings.warn("Projection_spec {0} added to {1} of {2}".
                              format(projection_spec.name, state, sender.name))
            # return

    # output_state is either the name for a new OutputState or kwAddNewOutputState
    if not state is kwAddOutputState:
        if sender.prefs.verbosePref:
            reassign = input("\nAdd new OutputState named {0} to {1} (as sender for {2})? (y/n):".
                             format(output_state, sender.name, projection_spec.name))
            while reassign != 'y' and reassign != 'n':
                reassign = input("\nAdd {0} to {1}? (y/n):".format(output_state, sender.name))
            if reassign == 'n':
                raise ProjectionError("Unable to assign projection {0} to sender {1}".
                                      format(projection_spec.name, sender.name))

    output_state = _instantiate_state(owner=sender,
                                     state_type=OutputState,
                                     state_name=output_state,
                                     state_spec=projection_spec.value,
                                     constraint_value=projection_spec.value,
                                     constraint_value_name='Projection_spec value for new InputState',
                                     context=context)
    #  Update outputState and outputStates
    try:
        sender.output_states[output_state.name] = output_state
    # No OutputState(s) yet, so create them
    except AttributeError:
        from PsyNeuLink.Components.States.State import State_Base
        sender.output_states = ContentAddressableList(component_type=State_Base,
                                                      list=[output_state],
                                                      name=sender.name+'.output_states')

    output_state._instantiate_projections_to_state(projections=projection_spec, context=context)
