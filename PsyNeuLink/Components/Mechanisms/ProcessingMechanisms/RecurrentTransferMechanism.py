# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# NOTES:
#  * COULD NOT IMPLEMENT integrator_function in paramClassDefaults (see notes below)
#  * NOW THAT NOISE AND TIME_CONSTANT ARE PROPRETIES THAT DIRECTLY REFERERNCE integrator_function,
#      SHOULD THEY NOW BE VALIDATED ONLY THERE (AND NOT IN TransferMechanism)??
#  * ARE THOSE THE ONLY TWO integrator PARAMS THAT SHOULD BE PROPERTIES??

# ****************************************  RecurrentTransferMechanism *************************************************

"""
.. _Recurrent_Transfer_Overview:

Overview
--------

A RecurrentTransferMechanism is a subclass of `TransferMechanism` that implements a single-layered recurrent
network, in which each element is connected to every other element (instantiated in a recurrent
`AutoAssociativeProjection` referenced by the Mechanism's `matrix <RecurrentTransferMechanism.matrix>` parameter).
It also allows its previous input to be decayed, and reports the energy and, if appropriate, the entropy of its output.

.. _Recurrent_Transfer_Creation:

Creating a RecurrentTransferMechanism
-------------------------------------

A RecurrentTransferMechanism can be created directly by calling its constructor, or using the `mechanism` command and
specifying RECURRENT_TRANSFER_MECHANISM as its **mech_spec** argument.  The recurrent projection is automatically
created using the **matrix** (or **auto** and **hetero**) argument of the Mechanism's constructor. If used, the
**matrix** argument must specify either a square matrix or a `AutoAssociativeProjection` that uses one (the default is
`FULL_CONNECTIVITY_MATRIX`). Alternatively, **auto** and **hetero** can be specified: these set the diagonal and
off-diagonal terms, respectively. In all other respects, a RecurrentTransferMechanism is specified in the same way as a
standard `TransferMechanism`.

COMMENT:
8/7/17 CW: In past versions, the first sentence of the paragraph above was: "A RecurrentTransferMechanism can be
created directly by calling its constructor, or using the `mechanism() <Mechanism.mechanism>` function and specifying
RECURRENT_TRANSFER_MECHANISM as its **mech_spec** argument".
However, the latter method is no longer correct: it instead creates a DDM: the problem is line 590 in Mechanism.py,
as MechanismRegistry is empty!
COMMENT

.. _Recurrent_Transfer_Structure:

Structure
---------

The distinguishing feature of a RecurrentTransferMechanism is its `matrix <RecurrentTransferMechanism.matrix>`,
`auto <RecurrentTransferMechanism.auto>`, and `hetero <RecurrentTransferMechanism.hetero>` parameters, which
specify a self-projecting `AutoAssociativeProjection`;  that is, one that projects from the Mechanism's
`primary OutputState <OutputState_Primary>` back to its `primary InputState <InputState_Primary>`.
In all other respects the Mechanism is identical to a standard `TransferMechanism`.

In addition, a RecurrentTransferMechanism also has a `decay` <RecurrentTransferMechanism.decay>' parameter, that
multiplies its `previous_input <RecurrentTransferMechanism.previous_input>` value by the specified factor each time it is
executed.  It also has two additional OutputStates:  an ENERGY OutputState and, if its
`function <RecurrentTransferMechanism.function>` is bounded between 0 and 1 (e.g., a `Logistic` function), an ENTROPY
OutputState, that each report the respective values of the vector in it its
`primary (RESULTS) OutputState <OutputState_Primary>`.

.. _Recurrent_Transfer_Execution:

Execution
---------

When a RecurrentTransferMechanism executes, it includes in its input the value of its
`primary OutputState <OutputState_Primary>` (after multiplication by the `matrix` of the recurrent projection) from its
last execution.

COMMENT:
Previous version of sentence above: "When a RecurrentTransferMechanism executes, it includes in its input the value of
its `primary OutputState <OutputState_Primary>` from its last execution."
8/9/17 CW: Changed the sentence above. Rationale: If we're referring to the fact that the recurrent projection
takes the previous output before adding it to the next input, we should specifically mention the matrix transformation
that occurs along the way.
COMMENT

Like a `TransferMechanism`, the function used to update each element can be assigned using its
`function <RecurrentTransferMechanism.function>` parameter.  When a RecurrentTransferMechanism is executed,
if its `decay <RecurrentTransferMechanism.decay>` parameter is specified (and is not 1.0), it
decays the value of its `previous_input <RecurrentTransferMechanism.previous_input>` parameter by the
specified factor.  It then transforms its input (including from the recurrent projection) using the specified
function and parameters (see `Transfer_Execution`), and returns the results in its OutputStates.

.. _Recurrent_Transfer_Class_Reference:

Class Reference
---------------


"""

import numbers

import numpy as np
import typecheck as tc

from PsyNeuLink.Components.Functions.Function import Linear, Stability, get_matrix
from PsyNeuLink.Components.Mechanisms.Mechanism import Mechanism_Base
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Projections.PathwayProjections.AutoAssociativeProjection import AutoAssociativeProjection, get_auto_matrix, get_hetero_matrix
from PsyNeuLink.Components.States.OutputState import PRIMARY_OUTPUT_STATE, StandardOutputStates
from PsyNeuLink.Components.States.ParameterState import ParameterState
from PsyNeuLink.Components.States.State import _instantiate_state
from PsyNeuLink.Globals.Keywords import AUTO, ENERGY, ENTROPY, FULL_CONNECTIVITY_MATRIX, HETERO, INITIALIZING, MATRIX, MEAN, MEDIAN, NAME, PARAMS_CURRENT, RECURRENT_TRANSFER_MECHANISM, RESULT, SET_ATTRIBUTE, STANDARD_DEVIATION, VARIANCE
from PsyNeuLink.Globals.Preferences.ComponentPreferenceSet import is_pref_set
from PsyNeuLink.Globals.Utilities import is_numeric_or_none
from PsyNeuLink.Scheduling.TimeScale import CentralClock, TimeScale


class RecurrentTransferError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)

DECAY = 'decay'

# This is a convenience class that provides list of standard_output_state names in IDE
class RECURRENT_OUTPUT():

    """
        .. _RecurrentTransferMechanism_Standard_OutputStates:

        `Standard OutputStates <OutputState_Standard>` for
        `RecurrentTransferMechanism`

        .. TRANSFER_RESULT:

        *RESULT* : 1d np.array
            the result of the `function <RecurrentTransferMechanism.function>`
            of the Mechanism

        .. TRANSFER_MEAN:

        *MEAN* : float
            the mean of the result

        *VARIANCE* : float
            the variance of the result

        .. ENERGY:

        *ENERGY* : float
            the energy of the result, which is calculated using the `Stability
            Function <Function.Stability.function>` with the ``ENERGY`` metric

        .. ENTROPY:

        *ENTROPY* : float
            The entropy of the result, which is calculated using the `Stability
            Function <Function.Stability.function>` with the ENTROPY metric
            (Note: this is only present if the Mechanism's `function` is bounded
            between 0 and 1 (e.g. the `Logistic` Function)).
        """
    RESULT=RESULT
    MEAN=MEAN
    MEDIAN=MEDIAN
    STANDARD_DEVIATION=STANDARD_DEVIATION
    VARIANCE=VARIANCE
    ENERGY=ENERGY
    ENTROPY=ENTROPY
    # THIS WOULD HAVE BEEN NICE, BUT IDE DOESN'T EXECUTE IT, SO NAMES DON'T SHOW UP
    # for item in [item[NAME] for item in DDM_standard_output_states]:
    #     setattr(DDM_OUTPUT.__class__, item, item)


# IMPLEMENTATION NOTE:  IMPLEMENTS OFFSET PARAM BUT IT IS NOT CURRENTLY BEING USED
class RecurrentTransferMechanism(TransferMechanism):
    """
    RecurrentTransferMechanism(        \
    default_variable=None,             \
    size=None,                         \
    function=Linear,                   \
    matrix=FULL_CONNECTIVITY_MATRIX,   \
    auto=None,                         \
    hetero=None,                       \
    initial_value=None,                \
    decay=None,                        \
    noise=0.0,                         \
    time_constant=1.0,                 \
    range=(float:min, float:max),      \
    time_scale=TimeScale.TRIAL,        \
    params=None,                       \
    name=None,                         \
    prefs=None)

    Subclass of `TransferMechanism` that implements a single-layer auto-recurrent network.

    COMMENT:
        Description
        -----------
            RecurrentTransferMechanism is a Subtype of the TransferMechanism Subtype of the ProcessingMechanisms Type
            of the Mechanism Category of the Component class.
            It implements a TransferMechanism with a recurrent projection (default matrix: FULL_CONNECTIVITY_MATRIX).
            In all other respects, it is identical to a TransferMechanism.
    COMMENT

    Arguments
    ---------

    default_variable : number, list or np.ndarray : default Transfer_DEFAULT_BIAS
        specifies the input to the Mechanism to use if none is provided in a call to its
        `execute <Mechanism_Base.execute>` or `run <Mechanism_Base.run>` method;
        also serves as a template to specify the length of `variable <RecurrentTransferMechanism.variable>` for
        `function <RecurrentTransferMechanism.function>`, and the `primary outputState <OutputState_Primary>`
        of the Mechanism.

    size : int, list or np.ndarray of ints
        specifies variable as array(s) of zeros if **variable** is not passed as an argument;
        if **variable** is specified, it takes precedence over the specification of **size**.

    function : TransferFunction : default Linear
        specifies the function used to transform the input;  can be `Linear`, `Logistic`, `Exponential`,
        or a custom function.

    matrix : list, np.ndarray, np.matrix, matrix keyword, or AutoAssociativeProjection : default FULL_CONNECTIVITY_MATRIX
        specifies the matrix to use for creating a `recurrent AutoAssociativeProjection <Recurrent_Transfer_Structure>`,
        or a AutoAssociativeProjection to use. If **auto** or **hetero** arguments are specified, the **matrix** argument
        will be ignored in favor of those arguments.

    auto : number, 1D array, or None : default None
        specifies matrix as a diagonal matrix with diagonal entries equal to **auto**, if **auto** is not None;
        If **auto** and **hetero** are both specified, then matrix is the sum of the two matrices from **auto** and
        **hetero**. For example, setting **auto** to 1 and **hetero** to -1 would set matrix to have a diagonal of
        1 and all non-diagonal entries -1. if the **matrix** argument is specified, it will be overwritten by
        **auto** and/or **hetero**, if either is specified. **auto** can be specified as a 1D array with length equal
        to the size of the Mechanism, if a non-uniform diagonal is desired. Can be modified by control.

    hetero : number, 2D array, or None : default None
        specifies matrix as a hollow matrix with all non-diagonal entries equal to **hetero**, if **hetero** is not None;
        If **auto** and **hetero** are both specified, then matrix is the sum of the two matrices from **auto** and
        **hetero**. For example, setting **auto** to 1 and **hetero** to -1 would set matrix to have a diagonal of
        1 and all non-diagonal entries -1. if the **matrix** argument is specified, it will be overwritten by
        **auto** and/or **hetero**, if either is specified. **hetero** can be specified as a 2D array with dimensions
        equal to the matrix dimensions, if a non-uniform diagonal is desired. Can be modified by control.

    initial_value :  value, list or np.ndarray : default Transfer_DEFAULT_BIAS
        specifies the starting value for time-averaged input (only relevant if
        `time_constant <RecurrentTransferMechanism.time_constant>` is not 1.0).
        :py:data:`Transfer_DEFAULT_BIAS <LINK->SHOULD RESOLVE TO VALUE>`

    decay : number : default 1.0
        specifies the amount by which to decrement its `previous_input <RecurrentTransferMechanism.previous_input>`
        each time it is executed.

    noise : float or function : default 0.0
        a stochastically-sampled value added to the result of the `function <RecurrentTransferMechanism.function>`:
        if it is a float, it must be in the interval [0,1] and is used to scale the variance of a zero-mean Gaussian;
        if it is a function, it must return a scalar value.

    time_constant : float : default 1.0
        the time constant for exponential time averaging of input when the Mechanism is executed with `time_scale`
        set to `TimeScale.TIME_STEP`::

         result = (time_constant * current input) +
         (1-time_constant * result on previous time_step)

    range : Optional[Tuple[float, float]]
        specifies the allowable range for the result of `function <RecurrentTransferMechanism.function>`:
        the first item specifies the minimum allowable value of the result, and the second its maximum allowable value;
        any element of the result that exceeds the specified minimum or maximum value is set to the value of
        `range <RecurrentTransferMechanism.range>` that it exceeds.

    params : Optional[Dict[param keyword, param value]]
        a `parameter dictionary <ParameterState_Specification>` that can be used to specify the parameters for
        the Mechanism, its function, and/or a custom function and its parameters.  Values specified for parameters in
        the dictionary override any assigned to those parameters in arguments of the constructor.

    time_scale :  TimeScale : TimeScale.TRIAL
        specifies whether the Mechanism is executed using the `TIME_STEP` or `TRIAL` `TimeScale`.
        This must be set to `TimeScale.TIME_STEP` for the `time_constant <RecurrentTransferMechanism.time_constant>`
        parameter to have an effect.

    name : str : default RecurrentTransferMechanism-<index>
        a string used for the name of the Mechanism.
        If not is specified, a default is assigned by `MechanismRegistry`
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

    prefs : Optional[PreferenceSet or specification dict : Mechanism.classPreferences]
        the `PreferenceSet` for Mechanism.
        If it is not specified, a default is assigned using `classPreferences` defined in __init__.py
        (see :doc:`PreferenceSet <LINK>` for details).

    context : str : default componentType+INITIALIZING
        string used for contextualization of instantiation, hierarchical calls, executions, etc.

    Attributes
    ----------

    variable : value
        the input to Mechanism's `function <RecurrentTransferMechanism.variable>`.

    function : Function
        the Function used to transform the input.

    matrix : 2d np.array
        the `matrix <AutoAssociativeProjection.matrix>` parameter of the `recurrent_projection` for the Mechanism.

    recurrent_projection : AutoAssociativeProjection
        an `AutoAssociativeProjection` that projects from the Mechanism's `primary outputState <OutputState_Primary>`
        back to its `primary inputState <Mechanism_InputStates>`.

    decay : float : default 1.0
        determines the amount by which to multiply the `previous_input <RecurrentTransferMechanism.previous_input>`
        value each time it is executed.

    COMMENT:
       THE FOLLOWING IS THE CURRENT ASSIGNMENT
    COMMENT
    initial_value :  value, list or np.ndarray : Transfer_DEFAULT_BIAS
        determines the starting value for time-averaged input
        (only relevant if `time_constant <RecurrentTransferMechanism.time_constant>` parameter is not 1.0).
        :py:data:`Transfer_DEFAULT_BIAS <LINK->SHOULD RESOLVE TO VALUE>`

    noise : float or function : default 0.0
        a stochastically-sampled value added to the output of the `function <RecurrentTransferMechanism.function>`:
        if it is a float, it must be in the interval [0,1] and is used to scale the variance of a zero-mean Gaussian;
        if it is a function, it must return a scalar value.

    time_constant : float
        the time constant for exponential time averaging of input
        when the Mechanism is executed using the `TIME_STEP` `TimeScale`::

          result = (time_constant * current input) + (1-time_constant * result on previous time_step)

    range : Tuple[float, float]
        determines the allowable range of the result: the first value specifies the minimum allowable value
        and the second the maximum allowable value;  any element of the result that exceeds minimum or maximum
        is set to the value of `range <RecurrentTransferMechanism.range>` it exceeds.  If
        `function <RecurrentTransferMechanism.function>`
        is `Logistic`, `range <RecurrentTransferMechanism.range>` is set by default to (0,1).

    previous_input : 1d np.array of floats
        the value of the input on the previous execution, including the value of `recurrent_projection`.

    value : 2d np.array [array(float64)]
        result of executing `function <RecurrentTransferMechanism.function>`; same value as first item of
        `output_values <RecurrentTransferMechanism.output_values>`.

    COMMENT:
        CORRECTED:
        value : 1d np.array
            the output of ``function``;  also assigned to ``value`` of the TRANSFER_RESULT OutputState
            and the first item of ``output_values``.
    COMMENT

    outputStates : Dict[str, OutputState]
        an OrderedDict with the following `outputStates <OutputState>`:

        * `TRANSFER_RESULT`, the :keyword:`value` of which is the **result** of `function <RecurrentTransferMechanism.function>`;
        * `TRANSFER_MEAN`, the :keyword:`value` of which is the mean of the result;
        * `TRANSFER_VARIANCE`, the :keyword:`value` of which is the variance of the result;
        * `ENERGY`, the :keyword:`value` of which is the energy of the result,
          calculated using the `Stability` Function with the ENERGY metric;
        * `ENTROPY`, the :keyword:`value` of which is the entropy of the result,
          calculated using the `Stability` Function with the ENTROPY metric;
          note:  this is only present if the Mechanism's :keyword:`function` is bounded between 0 and 1
          (e.g., the `Logistic` function).

    output_values : List[array(float64), float, float]
        a list with the following items:

        * **result** of the ``function`` calculation (value of TRANSFER_RESULT outputState);
        * **mean** of the result (``value`` of TRANSFER_MEAN outputState)
        * **variance** of the result (``value`` of TRANSFER_VARIANCE outputState);
        * **energy** of the result (``value`` of ENERGY outputState);
        * **entropy** of the result (if the ENTROPY outputState is present).

    time_scale :  TimeScale
        specifies whether the Mechanism is executed using the `TIME_STEP` or `TRIAL` `TimeScale`.

    name : str : default RecurrentTransferMechanism-<index>
        the name of the Mechanism.
        Specified in the **name** argument of the constructor for the Projection;
        if not is specified, a default is assigned by `MechanismRegistry`
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

    prefs : PreferenceSet or specification dict : Mechanism.classPreferences
        the `PreferenceSet` for Mechanism.
        Specified in the **prefs** argument of the constructor for the Mechanism;
        if it is not specified, a default is assigned using `classPreferences` defined in ``__init__.py``
        (see :doc:`PreferenceSet <LINK>` for details).

    Returns
    -------
    instance of RecurrentTransferMechanism : RecurrentTransferMechanism

    """
    componentType = RECURRENT_TRANSFER_MECHANISM

    paramClassDefaults = TransferMechanism.paramClassDefaults.copy()

    standard_output_states = TransferMechanism.standard_output_states.copy()
    standard_output_states.extend([{NAME:ENERGY}, {NAME:ENTROPY}])

    class Params(TransferMechanism.Params):
        auto = 'auto'
        hetero = 'hetero'
        decay = 'decay'

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 size=None,
                 function=Linear,
                 matrix=FULL_CONNECTIVITY_MATRIX,
                 auto=None,
                 hetero=None,
                 initial_value=None,
                 decay: is_numeric_or_none=None,
                 noise: is_numeric_or_none=0.0,
                 time_constant: is_numeric_or_none=1.0,
                 range=None,
                 input_states: tc.optional(tc.any(list, dict)) = None,
                 output_states: tc.optional(tc.any(list, dict))=None,
                 time_scale=TimeScale.TRIAL,
                 params=None,
                 name=None,
                 prefs: is_pref_set=None,
                 context=componentType+INITIALIZING):
        """Instantiate RecurrentTransferMechanism
        """
        if output_states is None:
            output_states = [RESULT]

        if isinstance(hetero, (list, np.matrix)):
            hetero = np.array(hetero)

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(input_states=input_states,
                                                  initial_value=initial_value,
                                                  matrix=matrix,
                                                  decay=decay,
                                                  output_states=output_states,
                                                  params=params,
                                                  noise=noise,
                                                  auto=auto,
                                                  hetero=hetero)

        if not isinstance(self.standard_output_states, StandardOutputStates):
            self.standard_output_states = StandardOutputStates(self,
                                                               self.standard_output_states,
                                                               indices=PRIMARY_OUTPUT_STATE)

        super().__init__(default_variable=default_variable,
                         size=size,
                         input_states=input_states,
                         function=function,
                         initial_value=initial_value,
                         noise=noise,
                         time_constant=time_constant,
                         range=range,
                         output_states=output_states,
                         time_scale=time_scale,
                         params=params,
                         name=name,
                         prefs=prefs,
                         context=context)

    def _validate_params(self, request_set, target_set=None, context=None):
        """Validate shape and size of auto, hetero, matrix and decay.
        """

        super()._validate_params(request_set=request_set, target_set=target_set, context=context)

        if AUTO in target_set:
            auto_param = target_set[AUTO]
            if (auto_param is not None) and not isinstance(auto_param, (np.ndarray, list, numbers.Number)):
                raise RecurrentTransferError("auto parameter ({}) of {} is of incompatible type: it should be a "
                                             "number, None, or a 1D numeric array".format(auto_param, self))
            if isinstance(auto_param, (np.ndarray, list)) and len(auto_param) != 1 and len(auto_param) != self.size[0]:
                raise RecurrentTransferError("auto parameter ({0}) for {1} is of incompatible length with the size "
                                             "({2}) of its owner, {1}.".format(auto_param, self, self.size[0]))

        if HETERO in target_set:
            hetero_param = target_set[HETERO]
            if hetero_param is not None and not isinstance(hetero_param, (np.matrix, np.ndarray, list, numbers.Number)):
                raise RecurrentTransferError("hetero parameter ({}) of {} is of incompatible type: it should be a "
                                             "number, None, or a 2D numeric matrix or array".format(hetero_param, self))
            hetero_shape = np.array(hetero_param).shape
            if hetero_shape != (1,) and hetero_shape != (1, 1):
                if isinstance(hetero_param, (np.ndarray, list, np.matrix)) and hetero_shape[0] != self.size[0]:
                    raise RecurrentTransferError("hetero parameter ({0}) for {1} is of incompatible size with the size "
                                                 "({2}) of its owner, {1}.".format(hetero_param, self, self.size[0]))
                if isinstance(hetero_param, (np.ndarray, list, np.matrix)) and hetero_shape[0] != hetero_shape[1]:
                    raise RecurrentTransferError("hetero parameter ({}) for {} must be square.".format(hetero_param, self))

        # Validate MATRIX
        if MATRIX in target_set:

            matrix_param = target_set[MATRIX]
            size = self.size[0]

            if isinstance(matrix_param, AutoAssociativeProjection):
                matrix = matrix_param.matrix

            elif isinstance(matrix_param, str):
                matrix = get_matrix(matrix_param, size, size)

            elif isinstance(matrix_param, (np.matrix, list)):
                matrix = np.array(matrix_param)

            else:
                matrix = matrix_param
            if matrix is None:
                rows = cols = size # this is a hack just to skip the tests ahead: if the matrix really is None, that is
                # checked up ahead, in _instantiate_attributes_before_function()
            else:
                rows = np.array(matrix).shape[0]
                cols = np.array(matrix).shape[1]

            # Shape of matrix must be square
            if rows != cols:
                if isinstance(matrix_param, AutoAssociativeProjection):
                    # if __name__ == '__main__':
                    err_msg = ("{} param of {} must be square to be used as recurrent projection for {}".
                               format(MATRIX, matrix_param.name, self.name))
                else:
                    err_msg = "{0} param for {1} must be square; currently, the {0} param is: {2}".\
                        format(MATRIX, self.name, matrix)
                raise RecurrentTransferError(err_msg)

            # Size of matrix must equal length of variable:
            if rows != size:
                if (matrix_param, AutoAssociativeProjection):
                    # if __name__ == '__main__':
                    err_msg = ("Number of rows in {} param for {} ({}) must be same as the size of variable for "
                               "{} {} (whose size is {} and whose variable is {})".
                               format(MATRIX, self.name, rows, self.__class__.__name__, self.name, self.size, self.instance_defaults.variable))
                else:
                    err_msg = ("Size of {} param for {} ({}) must be the same as its variable ({})".
                               format(MATRIX, self.name, rows, size))
                raise RecurrentTransferError(err_msg)


        if DECAY in target_set and target_set[DECAY] is not None:

            decay = target_set[DECAY]
            if not (0.0 <= decay and decay <= 1.0):
                raise RecurrentTransferError("{} argument for {} ({}) must be from 0.0 to 1.0".
                                             format(DECAY, self.name, decay))

    def _instantiate_attributes_before_function(self, context=None):
        """ using the `matrix` argument the user passed in (which is now stored in function_params), instantiate
        ParameterStates for auto and hetero if they haven't already been instantiated. This is useful if auto and
        hetero were None in the initialization call.
        """
        super()._instantiate_attributes_before_function(context=context)

        param_keys = self._parameter_states.key_values
        specified_matrix = get_matrix(self.params[MATRIX], self.size[0], self.size[0])

        if specified_matrix is None and (AUTO not in param_keys or HETERO not in param_keys):
            raise RecurrentTransferError("Matrix parameter ({}) for {} failed to produce a suitable matrix: "
                                         "if the matrix parameter does not produce a suitable matrix, the "
                                         "'auto' and 'hetero' parameters must be specified; currently, either"
                                         "auto or hetero parameter is missing.".format(self.params[MATRIX], self))

        if AUTO not in param_keys:
            d = np.diagonal(specified_matrix).copy()
            state = _instantiate_state(owner=self,
                                       state_type=ParameterState,
                                       state_name=AUTO,
                                       state_spec=d,
                                       state_params=None,
                                       constraint_value=d,
                                       constraint_value_name=AUTO,
                                       context=context)
            if state is not None:
                self._parameter_states[AUTO] = state
            else:
                raise RecurrentTransferError("Failed to create ParameterState for `auto` attribute for {} \"{}\"".
                                           format(self.__class__.__name__, self.name))
        if HETERO not in param_keys:
            m = specified_matrix.copy()
            np.fill_diagonal(m, 0.0)
            state = _instantiate_state(owner=self,
                                       state_type=ParameterState,
                                       state_name=HETERO,
                                       state_spec=m,
                                       state_params=None,
                                       constraint_value=m,
                                       constraint_value_name=HETERO,
                                       context=context)
            if state is not None:
                self._parameter_states[HETERO] = state
            else:
                raise RecurrentTransferError("Failed to create ParameterState for `hetero` attribute for {} \"{}\"".
                                           format(self.__class__.__name__, self.name))

    def _instantiate_attributes_after_function(self, context=None):
        """Instantiate recurrent_projection, matrix, and the functions for the ENERGY and ENTROPY outputStates
        """

        super()._instantiate_attributes_after_function(context=context)

        auto = self.params[AUTO]
        hetero = self.params[HETERO]
        if auto is not None and hetero is not None:
            a = get_auto_matrix(auto, size=self.size[0])
            if a is None:
                raise RecurrentTransferError("The `auto` parameter of {} {} was invalid: it was equal to {}, and was of"
                                             " type {}. Instead, the `auto` parameter should be a number, 1D array, "
                                             "2d array, 2d list, or numpy matrix".
                                           format(self.__class__.__name__, self.name, auto, type(auto)))
            c = get_hetero_matrix(hetero, size=self.size[0])
            if c is None:
                raise RecurrentTransferError("The `hetero` parameter of {} {} was invalid: it was equal to {}, and was "
                                             "of type {}. Instead, the `hetero` parameter should be a number, 1D array "
                                             "of length one, 2d array, 2d list, or numpy matrix".
                                           format(self.__class__.__name__, self.name, hetero, type(hetero)))
            self.matrix = a + c
        elif auto is not None:
            self.matrix = get_auto_matrix(auto, size=self.size[0])
            if self.matrix is None:
                raise RecurrentTransferError("The `auto` parameter of {} {} was invalid: it was equal to {}, and was of "
                                           "type {}. Instead, the `auto` parameter should be a number, 1D array, "
                                           "2d array, 2d list, or numpy matrix".
                                           format(self.__class__.__name__, self.name, auto, type(auto)))

        elif hetero is not None:
            self.matrix = get_hetero_matrix(hetero, size=self.size[0])
            if self.matrix is None:
                raise RecurrentTransferError("The `hetero` parameter of {} {} was invalid: it was equal to {}, and was of "
                                           "type {}. Instead, the `hetero` parameter should be a number, 1D array of "
                                           "length one, 2d array, 2d list, or numpy matrix".
                                           format(self.__class__.__name__, self.name, hetero, type(hetero)))

        # (7/19/17 CW) this line of code is now questionable, given the changes to matrix and the recurrent projection
        if isinstance(self.matrix, AutoAssociativeProjection):
            self.recurrent_projection = self.matrix

        else:
            self.recurrent_projection = self._instantiate_recurrent_projection(self, matrix=self.matrix, context=context)

        # self._matrix = self.recurrent_projection.matrix

        if ENERGY in self.output_states.names:
            energy = Stability(self.instance_defaults.variable[0],
                               metric=ENERGY,
                               transfer_fct=self.function,
                               matrix=self.recurrent_projection._parameter_states[MATRIX])
            self.output_states[ENERGY]._calculate = energy.function

        if ENTROPY in self.output_states.names:
            if self.function_object.bounds == (0,1) or range == (0,1):
                entropy = Stability(self.instance_defaults.variable[0],
                                    metric=ENTROPY,
                                    transfer_fct=self.function,
                                    matrix=self.recurrent_projection._parameter_states[MATRIX])
                self.output_states[ENTROPY]._calculate = entropy.function
            else:
                del self.output_states[ENTROPY]

    def _execute(
        self,
        variable=None,
        runtime_params=None,
        clock=CentralClock,
        time_scale=TimeScale.TRIAL,
        context=None,
        composition=None,
        execution_id=None,
    ):
        """Implement decay
        """
        if context is None or (INITIALIZING not in context):
            if self.decay is not None and self.decay != 1.0:
                self.previous_input = self.previous_input * float(self.decay)

        return super()._execute(
            variable=variable,
            runtime_params=runtime_params,
            clock=CentralClock,
            time_scale=time_scale,
            context=context,
            composition=composition,
            execution_id=execution_id,
        )

    def _update_parameter_states(self, runtime_params=None, time_scale=None, context=None, composition=None, execution_id=None):
        for state in self._parameter_states:
            # (8/2/17 CW) because the auto and hetero params are solely used by the AutoAssociativeProjection
            # (the RecurrentTransferMechanism doesn't use them), the auto and hetero param states are updated in the
            # projection's _update_parameter_states, and accordingly are not updated here
            if state.name != AUTO or state.name != HETERO:
                state.update(params=runtime_params, time_scale=time_scale, context=context, composition=composition, execution_id=execution_id)

    # 8/2/17 CW: this property is not optimal for performance: if we want to optimize performance we should create a
    # single flag to check whether to get matrix from auto and hetero?
    @property
    def matrix(self):
        if hasattr(self, '_parameter_states') \
                and 'auto' in self._parameter_states and 'hetero' in self._parameter_states:
            if not hasattr(self, 'size'):
                raise Exception('Error in retrieving matrix parameter for {}: `size` is not instantiated.'.format(self))
            a = get_auto_matrix(self.auto, self.size[0])
            c = get_hetero_matrix(self.hetero, self.size[0])
            return a + c
        else:
            # if auto and hetero are not yet instantiated, then just use the standard method of attribute retrieval
            # (simplified version of Component's basic make_property getter)
            name = 'matrix'
            backing_field = '_matrix'
            try:
                return self._parameter_states[name].value
            except (AttributeError, TypeError):
                return getattr(self, backing_field)

    @matrix.setter
    def matrix(self, val):
        if hasattr(self, '_parameter_states')\
                and 'auto' in self._parameter_states and 'hetero' in self._parameter_states:
            if hasattr(self, 'size'):
                val = get_matrix(val, self.size[0], self.size[0])
            temp_matrix = val.copy()
            self.auto = np.diag(temp_matrix).copy()
            np.fill_diagonal(temp_matrix, 0)
            self.hetero = temp_matrix
        else:
            name = 'matrix'
            backing_field = '_matrix'
            if self.paramValidationPref and hasattr(self, PARAMS_CURRENT):
                val_type = val.__class__.__name__
                curr_context = SET_ATTRIBUTE + ': ' + val_type + str(val) + ' for ' + name + ' of ' + self.name
                # self.prev_context = "nonsense" + str(curr_context)
                self._assign_params(request_set={name: val}, context=curr_context)
            else:
                setattr(self, backing_field, val)

            # Update user_params dict with new value
            self.user_params.__additem__(name, val)

            # If the parameter is associated with a ParameterState, assign the value to the ParameterState's variable
            if hasattr(self, '_parameter_states') and name in self._parameter_states:
                param_state = self._parameter_states[name]

                # MODIFIED 7/24/17 CW: If the ParameterState's function has an initializer attribute (i.e. it's an
                # integrator function), then also reset the 'previous_value' and 'initializer' attributes by setting
                # 'reset_initializer'
                if hasattr(param_state.function_object, 'initializer'):
                    param_state.function_object.reset_initializer = val

    # IMPLEMENTATION NOTE:  THIS SHOULD BE MOVED TO COMPOSITION ONCE THAT IS IMPLEMENTED
    @tc.typecheck
    def _instantiate_recurrent_projection(self,
                                          mech: Mechanism_Base,
                                          # this typecheck was failing, I didn't want to fix (7/19/17 CW)
                                          # matrix:is_matrix=FULL_CONNECTIVITY_MATRIX,
                                          matrix=FULL_CONNECTIVITY_MATRIX,
                                          context=None):
        """Instantiate a AutoAssociativeProjection from mech to itself

        """

        if isinstance(matrix, str):
            size = len(mech.instance_defaults.variable[0])
            matrix = get_matrix(matrix, size, size)

        return AutoAssociativeProjection(owner=mech,
                                         matrix=matrix,
                                         name=mech.name + ' recurrent projection')
