# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# *******************************************  InputState *****************************************************
#
"""

Overview
--------

An InputState receives the input to a Mechanism provided by the Projections to that Mechanism from others in a Process
or System.  If the InputState belongs to an `ORIGIN` Mechanism (see
`role of Mechanisms in Processes and Systems <Mechanism_Role_In_Processes_And_Systems>`), then it receives the input
specified when that Process or System is `run <Run>`.  The Projections received by an InputState are
listed in its `path_afferents <InputState.path_afferents>` attribute. Its
`function <InputState.function>` combines the values of these inputs, and the result is assigned to an item
corresponding to the InputState in the owner Mechanism's :keyword:`variable <Mechanism.Mechanism_Base.variable>` and
`input_values <Mechanism.Mechanism_Base.input_values>` attributes  (see `Mechanism InputStates <Mechanism_InputStates>`
for additional details about the role of InputStates in Mechanisms).


.. _InputState_Creation:

Creating an InputState
----------------------

An InputState can be created by calling its constructor, but in general this is not necessary as a Mechanism can
usually automatically create the InputState(s) it needs when it is created.  For example, if the Mechanism is
being created within the `pathway <Process_Base.pathway` of a `Process`, its InputState will be created and  assigned
as the `receiver <MappingProjection.receiver>` of a `MappingProjection` from the  preceding `Mechanism` in the
`pathway <Process_Base.pathway>`.

An InputState must be owned by a `Mechanism`.  When InputState is specified in the constructor for a `Mechanism`
(see `below <InputState_Specification>`), it is automatically assigned to that Mechanism as its owner. If the
InputState is created directly, its `owner <InputState.owner>` can specified in the **owner** argument of its
constructor; otherwise, its initialization will be `deferred <State_Deferred_Initialization>` until it is assigned to
an owner using the owner's `add_states` method.

.. _InputState_Primary:

Primary InputState
~~~~~~~~~~~~~~~~~~~

Every Mechanism has at least one InputState, referred to as its *primary InputState*.  If InputStates are not
`explicitly specified <InputState_Specification>` for a Mechanism, a primary InputState is automatically created
and assigned to its `input_state <Mechanism_Base.input_state>` attribute (note the singular),
and also to the first entry of the Mechanism's `input_states <Mechanism_Base.inpput_states>` attribute
(note the plural).  The `value <InputState.value>` of the primary InputState is assigned as the first (and often
only) item of the Mechanism's `input_values <Mechanism_Base.input_values>` attribute, which is the first item of the
Mechanism's `variable <Mechanism_Base.variable>` attribute.

.. _InputState_Specification

InputState Specification
~~~~~~~~~~~~~~~~~~~~~~~~

If one or more custom InputStates need to be specified for a `Mechanism` when it is created, this can be done in the
**input_states** argument of the Mechanism's constructor, or in an *INPUT_STATES* entry of a parameter dictionary
assigned to the constructor's **params** argument.  The latter takes precedence over the former (that is, if
InputStates are specified in the parameter dictionary, any specified in the **input_states** argument are ignored).

.. note::
    Assigning InputStates to a Mechanism in its constructor **replaces** any that are automatically generated for that
    Mechanism (i.e., those that it creates for itself by default).  If any of those need to be retained, they must be
    explicitly specified in the list assigned to the **input_states** argument or the *INPUT_STATES* entry of
    the parameter dictionary in the **params** argument).  The number of InputStates specified must also be equal
    to the number of items in the Mechanism's <variable <Mechanism_Base.variable>` attribute.

InputStates can also be **added** to a Mechanism, using the Mechanism's `add_states` method.  However, this has
consequences for the Mechanism's `variable <Mechanism.variable>` and possbily their relationship to the Mechanism's
`function <Mechanism_Base.function>` (these are discussed `below <InputStates_Mechanism_Variable_and_Function>`).
If the name of an InputState added to a Mechanism is the same as one that already exists, its name will be suffixed
with a numerical index (incremented for each OutputState with that name), and the OutputState will be added to the list
(that is, it will *not* replace ones that were already created).

Specifying an InputState can be done in any of the ways listed below.  To create multiple InputStates,
their specifications can be included in a list, or in a dictionary in which the key for each entry is a
string specifying the name for the InputState to be created, and the value its specification.  Any of the following
can be used to specify an InputState:

    * An existing **InputState object** or the name of one.  Its `value <InputState.value>` must be compatible with
      the item of the owner Mechanism's `variable <Mechanism_Base.variable>` to which it will be assigned.
    ..
    * The **InputState class**, keyword *INPUT_STATE*, or a string.  This creates a default InputState using the
      first item of the owner Mechanism's `variable <Mechanism_Base.variable>` as the InputState's
      `variable <InputState.variable>`. If the class name or *INPUT_STATE* keyword is used, a default name is
      assigned to the State;  if a string is specified, it is used as the name of the InputState (see :ref:`naming
      conventions <LINK>`).
    ..
    * A **value**.  This creates a default InputState using the specified value as InputState's
      `variable <InputState.variable>`. This must be compatible with the item of the owner Mechanism's
      `variable <Mechanism_Base.variable>`.
    ..
    * A **Projection subclass**. This creates a default InputState using the first item of the owner Mechanism's
      `variable <Mechanism_Base.variable>` as the InputState's `variable <InputState.variable>`, and a `Projection`
      of the specified type to the InputState using its `variable <InputState.variable>` as the template for the
      Projection's `value <Projection.value>`.
    ..

    COMMENT:
       CONFIRM THAT THIS IS TRUE:
    * A **Projection object**.  This creates a default InputState using the first item of the owner Mechanism's
      `variable <Mechanism_Base.variable>` as the InputState's `variable <InputState.variable>`, and assigns the
      State as the `Projection's <Projection>` `receiver <Projection.receiver>`. The Projection's `value
      <Projection.value>` must be compatible with the InputState's `variable <InputState.variable>`.
    COMMENT
    ..

    * A **State specification dictionary**.  This creates the specified InputState using the first item of the owner's
      `variable <Mechanism_Base.variable>` as the InputState's `variable <InputState.variable>`.  In addition to the
      standard entries of a `State specification dictionary <State_Specification>`, the dictionary can have a
      *PROJECTIONS* entry, the value of which can be a `Projection`, a
      `Projection specification dictionary <Projection_In_Context_Specification>`, or a list containing items that
      are either of those.  This can be used to specify one or more afferent `PathwayProjections <PathwayProjection>`
      to the InpuState, and/or `ModulatoryProjections <ModulatoryProjection>` for it to receive.

    ..
    * A **2-item tuple**.  The first item must be a value, and the second a `ModulatoryProjection` specification.
      This creates a default InputState using the first item as the InputState's `variable <InputState.variable>`,
      and assigns the InputState as a `receiver <ModulatoryProjection.receiver>` of the type of ModulatoryProjection
      specified in the second item.

    .. note::
       In all cases, the resulting `value <InputState.value>` of the InputState must be compatible with (that is, have
       the same number and type of elements as) as the corresponding item of its owner Mechanism's
       `variable <Mechanism_Base.variable>` attribute (see `below <InputStates_Mechanism_Variable_and_Function>`).

COMMENT:
   CHECK THIS:
             reference_value IS THE ITEM OF variable CORRESPONDING TO THE InputState
COMMENT

The values of a Mechanism's InputStates are assigned as items in its `input_values <Mechanism.input_values>`
attribute, in the order in which they are assigned in the constructor and/or added using the Mechanism's `add_states`
method, and in which they are listed in the Mechanism's `input_states <Mechanism.input_states>` attribute.  Note
that a Mechanism's `input_value <Mechanism_Base.input_value>` attribute has the same information as the
Mechanism's `variable <Mechanism.variable>`, but in a different format:  the former is a list and the latter a
2d np.array.


.. _InputStates_Mechanism_Variable_and_Function:

InputStates and a Mechanism's `variable <Mechanism_Base.variable>` and `function <Mechanism_Base.function>` Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Mechanism must have one InputState for each item of its `variable <Mechanism_Base.variable>` (see
`Mechanism <Mechanism_Variable>`).  The value specified in the **variable** or **size** arguments of the
Mechanism's constructor determines the number of items in its `variable <Mechanism_Base>`, which ordinarily matches
the size (along axis 0) of the input expected by its `function <Mechanism_Base.function>`.  Therefore,
if any InputStates are specified in the constructor, the number of them must match the number of items in
`variable <Mechanism_Base.variable>`.  InputStates can be added to a Mechanism's using `add_states` method;  this
extends its `variable <Mechanism_Base.variable>` by a number of items equal to the number of InputStates
added, and each new item is assigned a value compatible with the `value <InputState.value>` of the corresponding
InputState added.

.. note::
    Adding InputStates to a Mechanism using its `add_states` method may introduce an incompatibility with the
    Mechanism's `function <Mechanism_Base.function>`, which takes the Mechanism's `variable <Mechanism_Base.variable>`
    as its input; such an incompatibility will generate an error.  It is the user's responsibility to ensure that the
    explicit assignment of InputStates to a Mechanism is coordinated with the assignment of its
    `function <Mechanism_Base.function>`, so that the total number of InputStates (listed in the Mechanism's
    `input_states <Mechanism_Base.input_states>` attribute matches the number of items expected for the input to the
    function specified in the Mechanism's `function <Mechanism.function>` attribute  (i.e., its size along axis 0).


COMMENT:
However, if any InputStates are specified in its **input_states** argument or the *INPUT_STATES* entry of parameter
dictionary assigned to its **params** argument, then the number of InputStates specified determines the number of
items in the owner Mechanism's `variable <Mechanism_Base.variable>`, superseding any specification(s) in the
**variable** and/or **size** arguments of the constructor.  Each item of the `variable <Mechanism_Base.variable>` is
assigned a value compatible with the `value <InputState.value>` of the corresponding InputState). Similarly, if any
InputStates are added to a Mechanism using its `add_states` method, then its `variable <Mechanism_Base.variable>`
attribute is extended by a number of items equal to the number of InputStates added; and, again, each item is
assigned a value compatible with the `value <InputState.value>` of the corresponding InputState.

with one exception: If the Mechanism's `variable <Mechanism_Base.variable>` has more than one item, it may still be
assigned a single InputState;  in that case, the `value <InputState.value>` of that InputState must have the same
number of items as the Mechanisms's `variable <Mechanism_Base.variable>`.
COMMENT


.. _InputState_Projections:

Projections
~~~~~~~~~~~

When an InputState is created, it can be assigned one or more `Projections <Projection>`, using either the
**projections** argument of its constructor, or in an entry of a dictionary assigned to the **params** argument with
the key *PROJECTIONS*.  An InputState can be assigned either `MappingProjection(s) <MappingProjection>` or
`GatingProjection(s) <GatingProjection>`.  MappingProjections are assigned to its
`pathway_afferents <InputState.pathway_afferents>` attribute and GatingProjections to its
`mod_afferents <InputState.mod_afferents>` attribute.  See `State Projections <State_Projections>` for additional
details concerning the specification of Projections when creating a State.


.. _InputState_Structure:

Structure
---------

Every InputState is owned by a `Mechanism <Mechanism>`. It can receive one or more
`MappingProjections <MappingProjection>` from other Mechanisms, as well as from the Process or System to which its
owner belongs (if it is the `ORIGIN` Mechanism for that Process or System).  The MappingProjections received by an
InputState are listed in its `path_afferents <InputState.path_afferents>` attribute.  An InputState can also receive
one or more `GatingProjections <GatingProjection>` and that regulate its value (see the descriptions of Modulation
under `ModulatorySignals <ModulatorySignal_Modulation>` and `GatingSignals <GatingSignal_Modulation>` for additional
details). The GatingProjections received by an InputState are listed in its `mod_afferents <InputState.mod_afferents>`
attribute.

Like all PsyNeuLink components, an InputState also has the three following core attributes:

* `variable <InputState.variable>`:  this serves as a template for the `value <Projection.value>` of each Projection
  that the InputState receives: each must match both the number and type of elements of the InputState's
  `variable <InputState.variable>`.
..
* `function <InputState.function>`:  this aggregates the `value <Projection.value>` of all of the `Projections
  <Projection>` received by the InputState, and assigns the result to the InputState's `value <InputState.value>`
  attribute.  The default function is `LinearCombination` that performs an elementwise (Hadamard) sums the values.
  However, the parameters of the `function <InputState.function>` -- and thus the `value <InputState.value>` of the
  InputState -- can be modified by any `GatingProjections <GatingProjection>` received by the InputState (listed in its
  `mod_afferents <InputState.mod_afferents>` attribute.  A custom function can also be specified, so long as it
  generates a result that is compatible with the item of the Mechanism's `variable <Mechanism_Base.variable>` to
  which the InputState corresponds (see `above <InputStates_Mechanism_Variable_and_Function>`.
..
* `value <InputState.value>`:  this is the aggregated value of the `Projections <Projection>` received by the
  InputState and assigned to it by the InputState's `function <InputState.function>`, possibly modified by the
  influence of any `GatingProjections <GatingProjection>` received by the InputState. It must be compatible with the
  item of the owner Mechanism's `variable <Mechanism.Mechanism_Base.variable>` to which the InputState has been
  assigned.

Execution
---------

An InputState cannot be executed directly.  It is executed when the Mechanism to which it belongs is executed.
When this occurs, the InputState executes any Projections it receives, calls its `function <InputState.function>` to
aggregate their values, and then assigns the result to the InputState's `value <InputState.value>` attribute.  This,
in turn, is assigned to the item of the Mechanism's `variable <Mechanism.Mechanism_Base.variable>` and
`input_values <Mechanism.Mechanism_Base.input_values>` attributes corresponding to that InputState
(see `Mechanism variable and input_values attributes <Mechanism_Variable>` for additional details).

.. _InputState_Class_Reference:

Class Reference
---------------

"""
import warnings

import numpy as np
import typecheck as tc

from PsyNeuLink.Components.Functions.Function import Linear, LinearCombination
from PsyNeuLink.Components.States.State import StateError, State_Base, _instantiate_state_list, state_type_keywords
from PsyNeuLink.Globals.Keywords import EXPONENT, FUNCTION, INPUT_STATE, INPUT_STATE_PARAMS, MAPPING_PROJECTION, PROJECTION_TYPE, SUM, VARIABLE, WEIGHT
from PsyNeuLink.Globals.Preferences.ComponentPreferenceSet import is_pref_set
from PsyNeuLink.Globals.Preferences.PreferenceSet import PreferenceLevel
from PsyNeuLink.Globals.Utilities import append_type_to_name, iscompatible

state_type_keywords = state_type_keywords.update({INPUT_STATE})

# InputStatePreferenceSet = ComponentPreferenceSet(log_pref=logPrefTypeDefault,
#                                                          reportOutput_pref=reportOutputPrefTypeDefault,
#                                                          verbose_pref=verbosePrefTypeDefault,
#                                                          param_validation_pref=paramValidationTypeDefault,
#                                                          level=PreferenceLevel.TYPE,
#                                                          name='InputStateClassPreferenceSet')

# class InputStateLog(IntEnum):
#     NONE            = 0
#     TIME_STAMP      = 1 << 0
#     ALL = TIME_STAMP
#     DEFAULTS = NONE


class InputStateError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class InputState(State_Base):
    """
    InputState(                                \
    owner,                                     \
    reference_value=None,                      \
    function=LinearCombination(operation=SUM), \
    value=None,                                \
    projections=None,                          \
    params=None,                               \
    name=None,                                 \
    prefs=None)

    Subclass of `State` that calculates and represents the input to a `Mechanism` from one or more
    `PathwayProjection <PathwayProjection>`.

    COMMENT:

        Description
        -----------
            The InputState class is a Component type in the State category of Function,
            Its FUNCTION executes the Projections that it receives and updates the InputState's value

        Class attributes
        ----------------
            + componentType (str) = INPUT_STATE
            + paramClassDefaults (dict)
                + FUNCTION (LinearCombination, Operation.SUM)
                + FUNCTION_PARAMS (dict)
                # + kwStateProjectionAggregationFunction (LinearCombination, Operation.SUM)
                # + kwStateProjectionAggregationMode (LinearCombination, Operation.SUM)

        Class methods
        -------------
            _instantiate_function: insures that function is ARITHMETIC)
            update_state: gets InputStateParams and passes to super (default: LinearCombination with Operation.SUM)

        StateRegistry
        -------------
            All INPUT_STATE are registered in StateRegistry, which maintains an entry for the subclass,
              a count for all instances of it, and a dictionary of those instances

    COMMENT


    Arguments
    ---------

    owner : Mechanism
        the Mechanism to which the InputState belongs;  it must be specified or determinable from the context in which
        the InputState is created.

    reference_value : number, list or np.ndarray
        the value of the item of the owner Mechanism's `variable <Mechanism.Mechanism_Base.variable>` attribute to which
        the InputState is assigned; used as the template for the InputState's `value <InputState.value>` attribute.

    variable : number, list or np.ndarray
        specifies the template for the InputState's `variable <InputState.variable>` attribute.

    function : Function or method : default LinearCombination(operation=SUM)
        specifies the function used to aggregate the `values <Projection.value>` of the `Projections <Projection>`
        received by the InputState, under the possible influence of `GatingProjections <GatingProjection>` received
        by the InputState.  It must produce a result that has the same format (number and type of elements) as the
        item of its owner Mechanism's `variable <Mechanism.variable>` to which the InputState has been assigned.

    projections : list of Projection specifications
        species the `MappingProjection(s) <MappingProjection>` and/or `GatingProjection(s) <GatingProjection>` to be
        received by the InputState, and that will be listed in its `path_afferents <InputState.path_afferents>` and
        `mod_afferents <InputState.mod_afferents>` attributes, respectively (see `InputState_Projections` for additional
        details).

    params : Optional[Dict[param keyword, param value]]
        a `parameter dictionary <ParameterState_Specification>` that can be used to specify the parameters for
        the InputState or its function, and/or a custom function and its parameters. Values specified for parameters in
        the dictionary override any assigned to those parameters in arguments of the constructor.

    name : str : default InputState-<index>
        a string used for the name of the InputState.
        If not is specified, a default is assigned by StateRegistry of the Mechanism to which the InputState belongs
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

    prefs : Optional[PreferenceSet or specification dict : State.classPreferences]
        the `PreferenceSet` for the InputState.
        If it is not specified, a default is assigned using `classPreferences` defined in ``__init__.py``
        (see :doc:`PreferenceSet <LINK>` for details).


    Attributes
    ----------

    owner : Mechanism
        the Mechanism to which the InputState belongs.

    pathway_afferents : List[MappingProjection]
        a list of the `MappingProjections <MappingProjection>` received by the InputState
        (i.e., for which it is a `receiver <Projection.Projection.receiver>`).

    mod_afferents : List[GatingProjection]
        a list of the `GatingProjections <GatingProjection>` received by the InputState.

    variable : value, list or np.ndarray
        the template for the `value <Projection.Projection.value>` of each Projection that the InputState receives,
        each of which must match the format (number and types of elements) of the InputState's
        `variable <InputState.variable>`.

    size : int, list or np.ndarray of ints
        specifies variable as array(s) of zeros if **variable** is not passed as an argument;
        if **variable** is specified, it takes precedence over the specification of **size**.

    function : CombinationFunction : default LinearCombination(operation=SUM))
        performs an element-wise (Hadamard) aggregation of the `value <Projection.Projection.value>` of each Projection
        received by the InputState, under the possible influence of any `GatingProjections <GatingProjection>` received
        by the InputState.

    value : value or ndarray
        the aggregated value of the Projections received by the InputState; output of `function <InputState.function>`.
        If it is an ndarray, the full array is assigned as the value of an item of the owner Mechanism's
        `variable <Mechamism_Base.variable>`.

    name : str : default <State subclass>-<index>
        the name of the InputState.
        Specified in the **name** argument of the constructor for the OutputState.  If not is specified, a default is
        assigned by the StateRegistry of the Mechanism to which the OutputState belongs
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

        .. note::
            Unlike other PsyNeuLink components, State names are "scoped" within a Mechanism, meaning that States with
            the same name are permitted in different Mechanisms.  However, they are *not* permitted in the same
            Mechanism: States within a Mechanism with the same base name are appended an index in the order of their
            creation.

    prefs : PreferenceSet or specification dict : State.classPreferences
        the `PreferenceSet` for the InputState.
        Specified in the **prefs** argument of the constructor for the Projection;  if it is not specified, a default is
        assigned using `classPreferences` defined in ``__init__.py``
        (see :doc:`PreferenceSet <LINK>` for details).

    """

    #region CLASS ATTRIBUTES

    componentType = INPUT_STATE
    paramsType = INPUT_STATE_PARAMS

    classPreferenceLevel = PreferenceLevel.TYPE
    # Any preferences specified below will override those specified in TypeDefaultPreferences
    # Note: only need to specify setting;  level will be assigned to TYPE automatically
    # classPreferences = {
    #     kwPreferenceSetName: 'InputStateCustomClassPreferences',
    #     kp<pref>: <setting>...}

    # Note: the following enforce encoding as 1D np.ndarrays (one variable/value array per state)
    variableEncodingDim = 1
    valueEncodingDim = 1

    paramClassDefaults = State_Base.paramClassDefaults.copy()
    paramClassDefaults.update({PROJECTION_TYPE: MAPPING_PROJECTION})

    #endregion

    @tc.typecheck
    def __init__(self,
                 owner=None,
                 reference_value=None,
                 variable=None,
                 size=None,
                 function=LinearCombination(operation=SUM),
                 weight=None,
                 exponent=None,
                 projections=None,
                 params=None,
                 name=None,
                 prefs:is_pref_set=None,
                 context=None):

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(function=function,
                                                  weight=weight,
                                                  exponent=exponent,
                                                  params=params)

        # If owner or reference_value has not been assigned, defer init to State._instantiate_projection()
        if owner is None or reference_value is None:
            # Store args for deferred initialization
            self.init_args = locals().copy()
            self.init_args['context'] = self
            self.init_args['name'] = name
            self.init_args['projections'] = projections

            # Flag for deferred initialization
            self.init_status = InitStatus.DEFERRED_INITIALIZATION
            return

        self.reference_value = reference_value

        # Validate sender (as variable) and params, and assign to variable and paramsInstanceDefaults
        # Note: pass name of owner (to override assignment of componentName in super.__init__)
        super(InputState, self).__init__(owner,
                                         variable=variable,
                                         size=size,
                                         projections=projections,
                                         params=params,
                                         name=name,
                                         prefs=prefs,
                                         context=self)

    def _validate_params(self, request_set, target_set=None, context=None):
        """Validate weights and exponents

        This needs to be done here, since paramClassDefault declarations assign None as default
            (so that they can be ignored if not specified here or in the function)
        """

        super()._validate_params(request_set=request_set, target_set=target_set, context=context)

        if WEIGHT in target_set and target_set[WEIGHT] is not None:
            if not isinstance(target_set[WEIGHT], (int, float)):
                raise InputStateError("{} parameter of {} for {} ({}) must be an int or float".
                                      format(WEIGHT, self.name, self.owner.name, target_set[WEIGHT]))

        if EXPONENT in target_set and target_set[EXPONENT] is not None:
            if not isinstance(target_set[EXPONENT], (int, float)):
                raise InputStateError("{} parameter of {} for {} ({}) must be an int or float".
                                      format(EXPONENT, self.name, self.owner.name, target_set[EXPONENT]))


    def _instantiate_function(self, context=None):
        """Insure that function is LinearCombination and that output is compatible with owner.variable

        Insures that function:
            - is LinearCombination (to aggregate Projection inputs)
            - generates an output (assigned to self.value) that is compatible with the component of
                owner.function's variable that corresponds to this InputState,
                since the latter will be called with the value of this InputState;

        Notes:
        * Relevant item of owner.function's variable should have been provided
            as reference_value arg in the call to InputState__init__()
        * Insures that self.value has been assigned (by call to super()._validate_function)
        * This method is called only if the parameterValidationPref is True

        :param context:
        :return:
        """

        super(InputState, self)._instantiate_function(context=context)

        # Insure that function is Function.LinearCombination
        if not isinstance(self.function.__self__, (LinearCombination, Linear)):
            raise StateError("{0} of {1} for {2} is {3}; it must be of LinearCombination or Linear type".
                                      format(FUNCTION,
                                             self.name,
                                             self.owner.name,
                                             self.function.__self__.componentName, ))

        # Insure that self.value is compatible with (relevant item of) self.owner.variable
        if not iscompatible(self.value, self.reference_value):
            raise InputStateError("Value ({}) of {} {} for {} is not compatible with "
                                           "the variable ({}) of its function".
                                           format(self.value,
                                                  self.componentName,
                                                  self.name,
                                                  self.owner.name,
                                                  self.reference_value))
                                                  # self.owner.variable))

    def _instantiate_projections(self, projections, context=None):
        """Instantiate Projections specified in PROJECTIONS entry of params arg of State's constructor

        Call _instantiate_projections_to_state to assign:
            PathwayProjections to .pathway_afferents
            ModulatoryProjections to .mod_afferents
        """
        self._instantiate_projections_to_state(projections=projections, context=context)

    def _execute(self, function_params, context):
        """Call self.function with self.variable

        If there were no Transmissive Projections, ignore and return None
        """

        # If there were any Transmissive Projections:
        if self._path_proj_values:
            # Combine Projection values
            combined_values = self.function(variable=self._path_proj_values,
                                            params=function_params,
                                            context=context)
            return combined_values

        # There were no Projections
        else:
            # mark combined_values as none, so that (after being assigned to self.value)
            #    it is ignored in execute method (i.e., not combined with base_value)
            return None

    @property
    def pathway_projections(self):
        return self.path_afferents

    @pathway_projections.setter
    def pathway_projections(self, assignment):
        self.path_afferents = assignment


# def _instantiate_input_states(owner, input_states=None, context=None):
def _instantiate_input_states(owner, input_states=None, context=None):
    """Call State._instantiate_state_list() to instantiate ContentAddressableList of InputState(s)

    Create ContentAddressableList of InputState(s) specified in paramsCurrent[INPUT_STATES]

    If input_states is not specified:
        - use owner.input_states as list of InputState specifications
        - if owner.input_states is empty, user owner.variable to create a default InputState

    When completed:
        - self.input_states contains a ContentAddressableList of one or more input_states
        - self.input_state contains the `primary InputState <InputState_Primary>`:  first or only one in input_states
        - paramsCurrent[INPUT_STATES] contains the same ContentAddressableList (of one or more input_states)
        - each InputState corresponds to an item in the variable of the owner's function
        - the value of all of the input_states is stored in a list in input_value
        - if there is only one InputState, it is assigned the full value

    Note: State._instantiate_state_list()
              parses self.variable (2D np.array, passed in constraint_value)
              into individual 1D arrays, one for each input state

    (See State._instantiate_state_list() for additional details)
    """

    # This allows method to be called by Mechanism.add_input_states() with set of user-specified input_states,
    #    while calls from init_methods continue to use owner.input_states (i.e., InputState specifications
    #    assigned in the **input_states** argument of the Mechanism's constructor)
    input_states = input_states or owner.input_states

    state_list = _instantiate_state_list(owner=owner,
                                         state_list=input_states,
                                         state_type=InputState,
                                         state_param_identifier=INPUT_STATE,
                                         constraint_value=owner.variable,
                                         constraint_value_name=VARIABLE,
                                         context=context)

    # Call from Mechanism.add_states, so add to rather than assign input_states (i.e., don't replace)
    if context and 'COMMAND_LINE' in context:
        owner.input_states.extend(state_list)
    else:
        owner._input_states = state_list

    # Check that number of input_states and their variables are consistent with owner.variable,
    #    and adjust the latter if not
    for i, input_state in enumerate(owner.input_states):
        try:
            variable_item_is_OK = iscompatible(owner.variable[i], input_state.value)
            if not variable_item_is_OK:
                break
        except IndexError:
            variable_item_is_OK = False
            break

    if not variable_item_is_OK:
        # NOTE: This block of code appears unused, and the 'for' loop appears to cause an error anyways. (7/11/17 CW)
        old_variable = owner.variable
        new_variable = []
        for state in owner.input_states:
            new_variable.append(state.value)
        owner.variable = np.array(new_variable)
        if owner.verbosePref:
            warnings.warn("Variable for {} ({}) has been adjusted "
                          "to match number and format of its input_states: ({})".
                          format(old_variable, append_type_to_name(owner),owner.variable))
