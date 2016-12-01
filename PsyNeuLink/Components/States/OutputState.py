# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# ******************************************  OutputState *****************************************************

"""

Overview
--------

The outputState(s) of a mechanism represent the output of the mechanism's ``function``, that can serve as the input to
other mechanisms, and/or as the output of a process and/or system (if the mechanism to which the outputState belongs
is the :keyword:`TERMINAL` mechanism [LINK] of that process or system).  A list of the outgoing projections from an
outputState is kept in its ``sendsToProjections`` attribute.

.. _OutputStates_Creation:

Creating an OutputState
-----------------------

An outputState can be created by calling its constructor, but in general this is not necessary as a mechanism can
usually automatically create the outputState(s) it needs when it is created.  For example, if the mechanism is
being created within the :ref:`pathway of a process <Process_Pathway>`, its outputState will be created and assigned
as the ``sender`` of a MappingProjection to the next mechanism in the pathway, or to the process's ``output`` if it is
the :keyword:`TERMINAL` mechanism of the process. If one or more custom outputStates need to be specified when a
mechanism is created, or added to an existing mechanism, this can be in an entry of the mechanism's parameter
dictionary, using the key :keyword:`OUTPUT_STATES` [LINK] and a value that specifies one or more outputStates.
For a single outputState, the value can be any of the specifications in the the list below.  To create multiple
outputStates, the value of the :keyword:`OUTPUT_STATES` entry can be either a list, each item of which can be any of
the specifications below;  or, it can be an OrderedDict, in which the key for each entry is a string  specifying the
name for the outputState to be created, and its value is one of the specifications below:

    * An existing **outputState** object or the name of one.  Its ``value`` must be compatible with the item of the
      owner mechanism's ``outputValue`` that will be assigned to it (see [LINK]).
    ..
    * The :class:`OutputState` **class** or a string.  This creates a default outputState using the owner
      mechanism's ``value`` as the template for the outputState's ``variable``. [LINK]  If :keyword:`OutputState`
      is used, a default name is assigned to the state;  if a string is, it is assigned as the name
      of the outputState (see [LINK] for naming conventions).
    ..
    * A **value**.  This creates a default outputState using the specified value as the outputState's ``variable``.
      This must be compatible with the items of the owner mechanism's ``outputValue`` that will be assigned to the
      outputState (see [LINK]).
    ..
    * A **specification dictionary**.  This creates the specified outputState using the items of the owner mechanism's
    ``outputValue`` that will be assigned to it as the template for the outputState's ``variable`` [LINK].

COMMENT:
   XXXXXXX CHECK ALL THIS:
             LIST OR ORDERED DICT SUPERCEDES AUTOMATIC ASSIGNMENT
             DICTIONARY KEY IS USED AS NAME
             NUMBER OF STATES MUST EQUAL LENGTH OF MECHANISM'S ATTRIBUTE (VARIABLE OR OUTPUTVALUE)
             SINGLE STATE FOR MULTI-ITEM MECHANISM ATTRIBUTE ASSIGNS (OR AT LEASET CHECKS FOR)
                MULTI-ITEM ATTRIBUTE OF STATE
             MATCH OF FORMATS OF CORRESPONDING ITEMS ARE VALIDATED
             ERROR IS GENERATED FOR NUMBER MISMATCH
             reference_value IS THE ITEM OF outputValue CORRESPONDING TO THE outputState
COMMENT
Assigning outputStates using the :keyword:`OUTPUT_STATES` entry of a mechanism's parameter dictionary supercedes the
automatic generation of outputStates for that mechanism.  If the mechanism requires multiple outputStates (i.e.,
it's ``outputValue`` attribute has more than on item), it assigns each item to its own outputState (see [LINK]).
Therefore, the number of outputStates specified must equal the number of items in the mechanisms's ``outputValue``.
An exception is if ``outputValue`` has more than one item, the mechanism may still be assigned a single
outputState;  in that case, the ``variable`` of that outputState must have the same number of items as
the  mechanisms's ``outputValue``.  For cases in which there are multiple outputStates, the order in which they are
specified in the list or OrderedDict must parallel the order in which the corresponding items appear in the
``outputValue`` attribute; furthemore, as noted above, the ``variable`` for each outputState must match
(in number and types of elements) the item  from the mechanism's ``outputValue`` that it will be assigned.

Finally, an outputState must be owned by a mechanism. Therefore, if the inputState is created directly,
the mechanism to which it belongs must be specified in the ``owner`` argument of its constructor; if the inputState
is specified in the :keyword:`INPUT_STATES` entry of the parameter dictionary for a mechanism, then the owner is
inferred from the context.

Structure
---------

Every outputState is owned by a :doc:`mechanism <Mechanism>`. It can send one or more MappingProjections to other
mechanisms;  it can also  be treated as the output of a process or system to which its owner belongs (if it is the
:keyword:`TERMINAL` [LINK] mechanism for that process or system).  A list of projections sent by an outputState is
maintained in its ``sendsToProjections`` attribute.  Like all PsyNeuLink components, it has the three following
fundamental attributes:

* ``variable``:  this must match (both in number and types of elements) the value of the item it is assigned from its
  mechanism's ``outputValue`` attribute (see LINK]).

* ``function``:  this is implemented for structural consistency, but is not currently used by PsyNeuLink.

* ``value``:  this is assigned the value of the outputState`s ``variable``, and used as the input for any projections
  that it sends.


Execution
---------

States cannot be executed directly.  They are executed when the mechanism to which they belong is executed. When this
occurs, the values of each ouputState of a mechanism are updated with the results of a call to the mechanism's
``function``: their values assigned the value of the corresponding item in the mechanism's ``outputValue`` attribute.


.. _OutputState_Class_Reference:

Class Reference
---------------


"""

# import Components
from PsyNeuLink.Components.States.State import *
from PsyNeuLink.Components.States.State import _instantiate_state_list
from PsyNeuLink.Components.Functions.Function import *

# class OutputStateLog(IntEnum):
#     NONE            = 0
#     TIME_STAMP      = 1 << 0
#     ALL = TIME_STAMP
#     DEFAULTS = NONE


class OutputStateError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class OutputState(State_Base):
    """
    OutputState(                               \
    owner,                                     \
    reference_value,                           \
    value=None,                                \
    function=LinearCombination(operation=SUM), \
    params=None,                               \
    name=None,                                 \
    prefs=None)

    Implements subclass of State that represents the output of a mechanism

    COMMENT:

        Description
        -----------
            The OutputState class is a type in the State category of Component,
            It is used primarily as the sender for MappingProjections
            Its FUNCTION updates its value:
                note:  currently, this is the identity function, that simply maps variable to self.value

        Class attributes:
            + componentType (str) = OUTPUT_STATES
            + paramClassDefaults (dict)
                + FUNCTION (LinearCombination)
                + FUNCTION_PARAMS   (Operation.PRODUCT)
            + paramNames (dict)

        Class methods:
            function (executes function specified in params[FUNCTION];  default: LinearCombination with Operation.SUM)

        StateRegistry
        -------------
            All OutputStates are registered in StateRegistry, which maintains an entry for the subclass,
              a count for all instances of it, and a dictionary of those instances

    COMMENT


    Arguments
    ---------

    owner : Mechanism
        the mechanism to which the outputState belongs; it must be specified or determinable from the context in which
        the outputState is created.

    reference_value : number, list or np.ndarray
        the component of the owner mechanism's ``outputValue`` attribute to which the outputState corresponds.

    value : number, list or np.ndarray
        used as the template for ``variable``.

    function : Function or method : default LinearCombination(operation=SUM)
        implemented for structural consistency;  not currently used by PsyNeuLink.

    params : Optional[Dict[param keyword, param value]]
        a dictionary that can be used to specify the parameters for the outputState, parameters for its function,
        and/or a custom function and its parameters (see :doc:`Component` for specification of a params dict).

    name : str : default OutputState-<index>
        a string used for the name of the outputState.
        If not is specified, a default is assigned by the StateRegistry of the mechanism to which the outputState
        belongs (see :doc:`Registry` for conventions used in naming, including for default and duplicate names).[LINK]

    prefs : Optional[PreferenceSet or specification dict : State.classPreferences]
        the PreferenceSet for the outputState.
        If it is not specified, a default is assigned using ``classPreferences`` defined in __init__.py
        (see Description under PreferenceSet for details) [LINK].


    Attributes
    ----------

    owner : Mechanism
        the mechanism to which the outputState belongs.

    sendsToProjections : Optional[List[Projection]]
        a list of the projections sent by the outputState (i.e., for which the outputState is a ``sender``).

    variable : number, list or np.ndarray
        assigned an item of the ``outputValue`` of its owner mechanism.

    function : CombinationFunction : default LinearCombination(operation=SUM))
        implemented for structural consistency;  not currently used by PsyNeuLink.

    value : number, list or np.ndarray
        assigned the value of the outputState`s ``variable``, and used as the input for any projections that it sends.

    name : str : default <State subclass>-<index>
        name of the outputState.
        Specified in the name argument of the call to create the outputState.  If not is specified, a default is
        assigned by the StateRegistry of the mechanism to which the outputState belongs
        (see :doc:`Registry` for conventions used in naming, including for default and duplicate names).[LINK]

        .. note::
            Unlike other PsyNeuLink components, states names are "scoped" within a mechanism, meaning that states with
            the same name are permitted in different mechanisms.  However, they are *not* permitted in the same
            mechanism: states within a mechanism with the same base name are appended an index in the order of their
            creation).

    prefs : PreferenceSet or specification dict : State.classPreferences
        the PreferenceSet for the outputState.
        Specified in the prefs argument of the call to create the projection;  if it is not specified, a default is
        assigned using ``classPreferences`` defined in __init__.py
        (see Description under PreferenceSet for details) [LINK].

    """

    #region CLASS ATTRIBUTES

    componentType = OUTPUT_STATES
    paramsType = OUTPUT_STATE_PARAMS

    classPreferenceLevel = PreferenceLevel.TYPE
    # Any preferences specified below will override those specified in TypeDefaultPreferences
    # Note: only need to specify setting;  level will be assigned to TYPE automatically
    # classPreferences = {
    #     kwPreferenceSetName: 'OutputStateCustomClassPreferences',
    #     kp<pref>: <setting>...}

    paramClassDefaults = State_Base.paramClassDefaults.copy()
    paramClassDefaults.update({PROJECTION_TYPE: MAPPING_PROJECTION})
    #endregion

    tc.typecheck
    def __init__(self,
                 owner,
                 reference_value,
                 value=None,
                 function=LinearCombination(operation=SUM),
                 params=None,
                 name=None,
                 prefs:is_pref_set=None,
                 context=None):

        # IMPLEMENTATION NOTE:
        # Potential problem:
        #    - a OutputState may correspond to a particular item of owner.value
        #        in which case there will be a mismatch here
        #    - if OutputState is being instantiated from Mechanism (in _instantiate_output_states)
        #        then the item of owner.value is known and has already been checked
        #        (in the call to _instantiate_state)
        #    - otherwise, should ignore

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(function=function, params=params)

        self.reference_value = reference_value

        # FIX: 5/26/16
        # IMPLEMENTATION NOTE:
        # Consider adding self to owner.outputStates here (and removing from ControlProjection._instantiate_sender)
        #  (test for it, and create if necessary, as per outputStates in ControlProjection._instantiate_sender),

        # Validate sender (as variable) and params, and assign to variable and paramsInstanceDefaults
        super().__init__(owner,
                         value=value,
                         params=params,
                         name=name,
                         prefs=prefs,
                         context=self)


    def _validate_variable(self, variable, context=None):
        """Insure variable is compatible with output component of owner.function relevant to this state

        Validate self.variable against component of owner's value (output of owner's function)
             that corresponds to this outputState (since that is what is used as the input to OutputState);
             this should have been provided as reference_value in the call to OutputState__init__()

        Note:
        * This method is called only if the parameterValidationPref is True

        :param variable: (anything but a dict) - variable to be validated:
        :param context: (str)
        :return none:
        """

        super(OutputState,self)._validate_variable(variable, context)

        self.variableClassDefault = self.reference_value

        # Insure that self.variable is compatible with (relevant item of) output value of owner's function
        if not iscompatible(self.variable, self.reference_value):
            raise OutputStateError("Value ({0}) of outputState for {1} is not compatible with "
                                           "the output ({2}) of its function".
                                           format(self.value,
                                                  self.owner.name,
                                                  self.reference_value))

def _instantiate_output_states(owner, context=None):
    """Call State._instantiate_state_list() to instantiate orderedDict of outputState(s)

    Create OrderedDict of outputState(s) specified in paramsCurrent[INPUT_STATES]
    If INPUT_STATES is not specified, use self.variable to create a default output state
    When completed:
        - self.outputStates contains an OrderedDict of one or more outputStates
        - self.outputState contains first or only outputState in OrderedDict
        - paramsCurrent[OUTPUT_STATES] contains the same OrderedDict (of one or more outputStates)
        - each outputState corresponds to an item in the output of the owner's function
        - if there is only one outputState, it is assigned the full value

    (See State._instantiate_state_list() for additional details)

    IMPLEMENTATION NOTE:
        default(s) for self.paramsCurrent[OUTPUT_STATES] (self.value) is assigned here
        rather than in _validate_params, as it requires function to have been instantiated first

    :param context:
    :return:
    """
    owner.outputStates = _instantiate_state_list(owner=owner,
                                                state_list=owner.paramsCurrent[OUTPUT_STATES],
                                                state_type=OutputState,
                                                state_param_identifier=OUTPUT_STATES,
                                                constraint_value=owner.value,
                                                constraint_value_name="output",
                                                context=context)
    # Assign self.outputState to first outputState in dict
    owner.outputState = list(owner.outputStates.values())[0]