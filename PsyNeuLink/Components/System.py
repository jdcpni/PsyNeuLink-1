
# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# *****************************************    SYSTEM MODULE    ********************************************************

"""
..
    Sections:
      * `System_Overview`
      * `System_Creation`
      * `System_Structure`
         * `System_Graph`
         * `System_Mechanisms`
      * `System_Execution`
         * `System_Execution_Order`
         * `System_Execution_Phase`
         * `System_Execution_Input_And_Initialization`
         * `System_Execution_Learning`
         * `System_Execution_Control`
      * `System_Class_Reference`


.. _System_Overview:

Overview
--------

A System is a `Composition` that is a collection of `Processes <Process>` all of which are executed together.
Executing a System executes all of the `Mechanisms <Mechanism>` in its Processes in a structured order.
`Projections <Projection>` between Mechanisms in different Processes within the System are permitted,
as are recurrent Projections, but Projections from Mechanisms in other Systems are ignored (PsyNeuLink does not
support ESP).  A System can include two types of Mechanisms:

* `ProcessingMechanism`
    These receive input from one or more `Projections <Projection>`, transform their input in some way,
    and assign the result as their output.

* `AdaptiveMechanism`
    These are used to adjust the operation of other components.  There are two types:
    `LearningMechanisms <LearningMechanism>` that adjust Projections, and `ControlMechanisms <ControlMechanism>`
    that adjust the parameters of other Mechanisms and/or their functions.

.. _System_Creation:

Creating a System
-----------------

Systems are created by calling :py:func:`system`.  If no arguments are provided, a System with a single `Process`
containing a single `default_mechanism <Mechanism_Base.default_mechanism>` will be created.  More generally, a System
is created from one or more `Processes <Process>` that are specified in the **processes** argument of its constructor.
Whenever a System is created, a `ControlMechanism <ControlMechanism>` is created for it and assigned as its
`controller`.  The controller can be specified by assigning an existing ControlMechanism to the **controller**
argument of the System's constructor, or specifying a class of ControlMechanism;  if none is specified,
a `DefaultControlMechanism` is created.

.. note::
   At present, only `Processes <Process>` can be assigned to a System; `Mechanisms <Mechanism>` cannot be assigned
   directly to a System.  They must be assigned to the `pathway <Process_Pathway>` of a Process, and then that Process
   must be
   included
   in the **processes** argument of the constructor for the System.


.. _System_Structure:

Structure
---------

.. _System_Graph:

Graph
~~~~~

When a System is created, a graph is constructed that describes the `Projections <Projection>` (edges) among its
`Mechanisms <Mechanism>` (nodes). The graph is assigned to the System's `graph` attribute.  A System's graph can be
displayed using its `show_graph` method.  The graph is stored as a dictionary of dependencies, that can be passed to
graph theoretical tools for analysis.  A System can have recurrent Processing pathways, such as feedback loops, in
which case the System will have a cyclic graph.  PsyNeuLink also uses the graph of a System to determine the order
in which its Mechanisms are executed.  In order to do so in an orderly manner, however, the graph must be acyclic.
So, for execution, PsyNeuLink constructs an `executionGraph` from the System's `graph`. If the  System is acyclic,
these are the same. If the System is cyclic, then the `executionGraph` is a subset of the `graph` in which the
dependencies (edges) associated with Projections that close a loop have been removed. Note that this only impacts
the order of execution; the Projections themselves remain in effect, and will be fully functional during the
execution of the affected Mechanisms (see `System_Execution` below for a more detailed description).

.. _System_Mechanisms:

Mechanisms
~~~~~~~~~~

The `Mechanisms <Mechanism>` in a System are assigned designations based on the position they occupy in the `graph`
and/or the role they play in a System:

    `ORIGIN`: receives input to the System, and does not receive a `Projection` from any other
    `ProcessingMechanisms <ProcessingMechanism>`;

    `TERMINAL`: provides output from the System, and does not send Projections to any other ProcessingMechanisms;

    `SINGLETON`: both an `ORIGIN` and a `TERMINAL` Mechanism;

    `INITIALIZE_CYCLE`: sends a Projection that closes a recurrent loop;
    can be assigned an initial value;

    `CYCLE`: receives a Projection that closes a recurrent loop;

    `CONTROL`: monitors the value of another Mechanism for use in controlling parameter values;

    `LEARNING`: monitors the value of another Mechanism for use in learning;

    `TARGET`: ObjectiveMechanism that monitors a `TERMINAL` Mechanism of a Process

    `INTERNAL`: ProcessingMechanism that does not fall into any of the categories above.

    .. note:: Any `ORIGIN` and `TERMINAL` Mechanisms of a System must be, respectively,
       the `ORIGIN` or `TERMINAL` of any Process(es) to which they belong.  However, it is not
       necessarily the case that the `ORIGIN` and/or `TERMINAL` Mechanism of a Process is also the
       `ORIGIN` and/or `TERMINAL` of a System to which the Process belongs (see the Chain example below).

    .. note: designations are stored in the Mechanism.systems attribute (see _instantiate_graph below, and Mechanism)


COMMENT:
    .. _System_Control:
    Control
    ~~~~~~~

    .. _System_Learning:
    Learning
    ~~~~~~~~

    Based on Process

COMMENT

.. _System_Full_Fig:

**Components of a System**

.. figure:: _static/System_full_fig.svg
   :alt: Overview of major PsyNeuLink components
   :scale: 75 %

   Two `Processes <Process>` are shown, both belonging to the same System.  Each Process has a
   series of :doc:`ProcessingMechanisms <ProcessingMechanism>` linked by :doc:`MappingProjections <MappingProjection>`,
   that converge on a common final ProcessingMechanism.  Each ProcessingMechanism is labeled with its designation in
   the System.  The `TERMINAL` Mechanism for both Processes projects to an `ObjectiveMechanism` that is used to
   drive `learning <LearningProjection>` in Process B. It also projects to a separate ObjectiveMechanism that is used
   for control of ProcessingMechanisms in both Processes A and B.  Note that the Mechanisms and
   Projections responsible for learning and control belong to the System and can monitor and/or control Mechanisms
   belonging to more than one Process (as shown for control in this figure).

.. _System_Execution:

Execution
---------

A System can be executed by calling either its `execute <System_Base.execute>` or `run <System_Base.execute>` methods.
`execute <System_Base.execute>` executes the System once; that is, it executes a single `TRIAL`.
`run <System_Base.run>` allows a series of `TRIAL` \s to be executed, one for each input in the **inputs** argument
of the call to `run <System_Base.run>`.  For each `TRIAL`, it makes a series of calls to the `run <Scheduler.run>`
method of the relevant `Scheduler` (see `System_Execution_Processing` and `System_Execution_Learning` below), and
executes the Components returned by that Scheduler (constituting a `TIME_STEP` of execution) until every Component in
the System has been executed at least once, or another `termination condition <Scheduler_Termination_Conditions>` is
met.  The execution of each `TRIAL` occurs in four phases: `initialization <System_Execution_Input_And_Initialization>`,
`processing <System_Execution_Processing>`, `learning <System_Execution_Learning>`, and
`control <System_Execution_Control>`, each of which is described below.


.. _System_Execution_Input_And_Initialization:

Input and Initialization
~~~~~~~~~~~~~~~~~~~~~~~~
The input to a System is specified in the **input** argument of either its `execute <System_Base.execute>` or
`run <System_Base.run>` method. In both cases, the input for a single `TRIAL` must be a list or ndarray of values,
each of which is an appropriate input for the corresponding `ORIGIN` Mechanism (listed in
`origin_mechanisms <System_Base.origin_mechanisms>`). If the `execute <System_Base.execute>` method is used, input for
only a single `TRIAL` is provided, and only a single `TRIAL` is executed.  The `run <System_Base.run>` method can be
used for a sequence of `TRIAL` \s, by providing it with a list or ndarray of inputs, one for each `TRIAL`.  In both
cases, two other types of input can be provided:  a list or ndarray of initialization values, and a list or ndarray
of target values. Initialization values are assigned, at the start of a `TRIAL`, as input to Mechanisms that close
recurrent loops (designated as `INITIALIZE_CYCLE`, and listed in `recurrent_init_mechanisms`), and target values are
assigned as the TARGET input of the System's `TARGET` Mechanisms (see learning below;  also, see `Run` for additional
details of formatting input specifications).


.. _System_Execution_Processing:

Processing
~~~~~~~~~~

Once the relevant inputs have been assigned, the `ProcessingMechanisms <ProcessingMechanism>` of the System are
executed in the order they are listed in the `Processes <Process>` used to construct the System.  When a Mechanism is
executed, it receives input from any other Mechanisms that project to it within the System,  but not from Mechanisms
outside the System (PsyNeuLink does not support ESP).  The order of execution is determined by the System's
`executionGraph` attribute, which is a subset of the System's `graph` that has been "pruned" to be acyclic (i.e.,
devoid of recurrent loops).  While the `executionGraph` is acyclic, all recurrent Projections in the System remain
intact during execution and can be `initialized <System_Execution_Input_And_Initialization>` at the start of execution.
The order in which Components are executed can also be customized, using the System's Scheduler in combination with
`Condition` specifications for individual Components, to execute different Components at different time scales, or to
introduce dependencies among them (e.g., require that a recurrent mechanism settle before another one execute --
see `example <Condition_Recurrent_Example>`).


.. _System_Execution_Learning:

Learning
~~~~~~~~
The System will execute learning if it is specified for any `Process <Process_Learning>` in the System.  The System's
`learning` attribute indicates whether learning is enabled for the System. `Learning <Process_Learning>` is executed
for any components (individual Projections or Processes) for which it is specified after the  `processing
<System_Execution_Processing>` of each `TRIAL` has completed, but before the `controller is executed
<System_Execution_Control>`.  The learning components of a System can be displayed using the System's `show_graph`
method with its **show_learning** argument assigned `True`. The stimuli used for learning (both inputs and targets) can
be specified in either of two formats, Sequence or Mechanism, that are described in the :doc:`Run` module; see
`Run_Inputs` and `Run_Targets`).  Both formats require that an input be provided for each `ORIGIN` Mechanism of the
System (listed in its `origin_mechanisms <System_Base.origin_mechanisms>` attribute).  If the targets are specified
in `Sequence <Run_Targets_Sequence_Format>` or `Mechanism <Run_Targets_Mechanism_Format>` format, one target must be
provided for each `TARGET` Mechanism (listed in its `target_mechanisms <System_Base.target_mechanisms>` attribute).
Targets can also be specified in a `function format <Run_Targets_Function_Format>`, which generates a target for each
execution of the Mechanism.

.. note::
   A `target_mechanism <Process.Process_Base.target_mechanism>` of a Process is not necessarily one of the
   `target_mechanisms <System_Base.target_mechanisms>` of the System to which it belongs
   (see `LearningMechanism_Targets`).  Also, the changes to a System induced by learning are not applied until the
   Mechanisms that receive those projections are next executed; see :ref:`Lazy Evaluation <LINK>` for an explanation
   of "lazy" updating).


.. _System_Execution_Control:

Control
~~~~~~~
Every System is associated with a single `controller`.  The controller uses an `ObjectiveMechanism` to monitor the
OutputState(s) of one or more Mechanisms in the System (listed in its `monitored_output_states` attribute), and uses
that information to set the value of parameters for those or other Mechanisms in the System, or their functions (see
`ControlMechanism_Monitored_OutputStates` for a description of how to specify which OutputStates are monitored, and
`ControlProjection_Creation` for specifying parameters to be controlled).  The control components of a System can be
displayed using the System's `show_graph` method with its **show_control** argument assigned `True`.  The `controller`
is executed after `processing <System_Execution_Processing>` and `learning <System_Execution_Learning>` have completed
for a `TRIAL`, and sets the values of any parameters that it controls, which then take effect in the next `TRIAL`.

COMMENT:
   Examples
   --------
   XXX ADD EXAMPLES HERE FROM 'System Graph and Input Test Script'
   .. note::  All of the example Systems below use the following set of Mechanisms.  However, in practice, they must be
      created separately for each System;  using the same Mechanisms and Processes in multiple Systems can produce
      confusing results.

   Module Contents
   system() factory method:  instantiate system
   System_Base: class definition
COMMENT

.. _System_Class_Reference:

Class Reference
---------------

"""

import inspect
import logging
import math
import numbers
import re
import warnings
from collections import OrderedDict

import numpy as np
import typecheck as tc
from toposort import toposort, toposort_flatten

from PsyNeuLink.Components.Component import Component, ExecutionStatus, function_type
from PsyNeuLink.Components.Mechanisms.AdaptiveMechanisms.ControlMechanisms.ControlMechanism import ControlMechanism_Base
from PsyNeuLink.Components.Mechanisms.AdaptiveMechanisms.LearningMechanisms.LearningMechanism \
    import LearningMechanism
from PsyNeuLink.Components.Mechanisms.Mechanism import MechanismList, MonitoredOutputStatesOption
from PsyNeuLink.Components.Process import ProcessList, ProcessTuple
from PsyNeuLink.Components.ShellClasses import Mechanism, Process, System
from PsyNeuLink.Globals.Keywords import COMPONENT_INIT, CONROLLER_PHASE_SPEC, CONTROL, CONTROLLER, CYCLE, EVC_SIMULATION, EXECUTING, FUNCTION, IDENTITY_MATRIX, INITIALIZE_CYCLE, INITIALIZING, INITIAL_VALUES, INTERNAL, LEARNING, MATRIX, ORIGIN, SAMPLE, SINGLETON, SYSTEM, SYSTEM_INIT, TARGET, TERMINAL, TIME_SCALE, kwSeparator, kwSystemComponentCategory
from PsyNeuLink.Globals.Preferences.ComponentPreferenceSet import is_pref_set
from PsyNeuLink.Globals.Preferences.PreferenceSet import PreferenceLevel
from PsyNeuLink.Globals.Registry import register_category
from PsyNeuLink.Globals.Utilities import ContentAddressableList, append_type_to_name, convert_to_np_array, iscompatible, parameter_spec
from PsyNeuLink.Scheduling.Scheduler import Scheduler
from PsyNeuLink.Scheduling.TimeScale import TimeScale, CentralClock
from PsyNeuLink.Composition import Systemm

logger = logging.getLogger(__name__)

# ProcessRegistry ------------------------------------------------------------------------------------------------------

defaultInstanceCount = 0 # Number of default instances (used to index name)

# inspect() keywords
SCHEDULER = 'scheduler'
PROCESSES = 'processes'
MECHANISMS = 'mechanisms'
ORIGIN_MECHANISMS = 'origin_mechanisms'
INPUT_ARRAY = 'input_array'
RECURRENT_MECHANISMS = 'recurrent_mechanisms'
RECURRENT_INIT_ARRAY = 'recurrent_init_array'
TERMINAL_MECHANISMS = 'terminal_mechanisms'
OUTPUT_STATE_NAMES = 'output_state_names'
OUTPUT_VALUE_ARRAY = 'output_value_array'
NUM_PHASES_PER_TRIAL = 'num_phases'
TARGET_MECHANISMS = 'target_mechanisms'
LEARNING_PROJECTION_RECEIVERS = 'learning_projection_receivers'
LEARNING_MECHANISMS = 'learning_mechanisms'
CONTROL_MECHANISMS = 'control_mechanisms'
CONTROL_PROJECTION_RECEIVERS = 'control_projection_receivers'

SystemRegistry = {}

kwSystemInputState = 'SystemInputState'


class SystemWarning(Warning):
     def __init__(self, error_value):
         self.error_value = error_value

class SystemError(Exception):
     def __init__(self, error_value):
         self.error_value = error_value

     def __str__(self):
         return repr(self.error_value)


# FIX:  IMPLEMENT DEFAULT PROCESS
# FIX:  NEED TO CREATE THE PROJECTIONS FROM THE PROCESS TO THE FIRST MECHANISM IN PROCESS FIRST SINCE,
# FIX:  ONCE IT IS IN THE GRAPH, IT IS NOT LONGER EASY TO DETERMINE WHICH IS WHICH IS WHICH (SINCE SETS ARE NOT ORDERED)

from PsyNeuLink.Components import SystemDefaultControlMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.ObjectiveMechanisms.ObjectiveMechanism import ObjectiveMechanism
from PsyNeuLink.Components.Process import process

# System factory method:
@tc.typecheck
def system(default_variable=None,
           size=None,
           processes:list=[],
           scheduler=None,
           initial_values:dict={},
           controller=SystemDefaultControlMechanism,
           enable_controller:bool=False,
           monitor_for_control:list=[MonitoredOutputStatesOption.PRIMARY_OUTPUT_STATES],
           control_signals:tc.optional(list)=None,
           # learning:tc.optional(_is_learning_spec)=None,
           learning_rate:tc.optional(parameter_spec)=None,
           targets:tc.optional(tc.any(list, np.ndarray))=None,
           params:tc.optional(dict)=None,
           name:tc.optional(str)=None,
           prefs:is_pref_set=None,
           context=None):
    """
    system(                                   \
    default_variable=None,                 \
    processes=None,                           \
    initial_values=None,                      \
    controller=SystemDefaultControlMechanism, \
    enable_controller=:keyword:False,         \
    monitor_for_control=None,                 \
    control_signals=None,                     \
    learning_rate=None,                       \
    targets=None,                             \
    params=None,                              \
    name=None,                                \
    prefs=None)

    COMMENT:
       VERSION WITH learning
        system(                                   \
        default_variable=None,                 \
        processes=None,                           \
        initial_values=None,                      \
        controller=SystemDefaultControlMechanism, \
        enable_controller=:keyword:`False`,       \
        monitor_for_control=None,                 \
        control_signals=None,                     \
        learning=None,                            \
        targets=None                              \
        params=None,                              \
        name=None,                                \
        prefs=None)
    COMMENT

    Factory method for System: returns instance of System.

    If called with no arguments, returns an instance of System with a single default Process and Mechanism;
    if called with a name string, that is used as the name of the instance of System returned;
    if a params dictionary is included, it is passed to the instantiated System.

    See :class:`System_Base` for class description

    Arguments
    ---------

    default_variable : list or ndarray of values : default default input for `ORIGIN` Mechanism of each Process
        the input to the System if none is provided in a call to the `execute <System_Base.execute>` or
        `run <System_Base.run>` methods. Should contain one item corresponding to the input of each `ORIGIN` Mechanism
        in the System.
        COMMENT:
            REPLACE DefaultProcess BELOW USING Inline markup
        COMMENT

    processes : list of Process specifications : default list('DefaultProcess')
        a list of the Processes to include in the System.
        Each Process specification can be an instance, the class name (creates a default Process), or a specification
        dictionary (see `Process` for details).

    initial_values : dict of Mechanism:value entries
        a dictionary of values used to initialize Mechanisms that close recurrent loops (designated as
        `INITIALIZE_CYCLE`). The key for each entry is a Mechanism object, and the value is a number,
        list or 1d np.array that must be compatible with the format of the first item of the Mechanism's
        `value <Mechanism.value>` (i.e., Mechanism.value[0]).

    controller : ControlMechanism : default SystemDefaultControlMechanism
        specifies the `ControlMechanism` used to monitor the `value <OutputState.value>` of the OutputState(s) for
        Mechanisms specified in `monitor_for_control`, and that specifies the `value <ControlSignal.value>` of the
        `ControlSignals <ControlSignal>` that control the parameters of Mechanisms (or their functions) in the System.

    enable_controller :  bool : default :keyword:`False`
        specifies whether the `controller` is executed during System execution.

    monitor_for_control : list of OutputState objects or specifications : default None
        specifies the OutputStates of the `TERMINAL` Mechanisms in the System to be monitored by its `controller`
        (see `ControlMechanism_Monitored_OutputStates` for specifying the `monitor_for_control` argument).

    COMMENT:
        learning : Optional[LearningProjection spec]
            implements `learning <LearningProjection_CreationLearningSignal>` for all Processes in the System.
    COMMENT

    learning_rate : float : None
        set the learning_rate for all `LearningMechanisms <LearningMechanism>` in the System
        (see `learning_rate` attribute for additional information).

    targets : Optional[List[List]], 2d np.ndarray] : default ndarrays of zeroes
        the values assigned to the TARGET input of each `TARGET` Mechanism in the System (listed in its
        `target_mechanisms` attribute).  There must be the same number of items as there are `target_mechanisms`,
        and each item must have the same format (length and number of elements) as the TARGET input
        for each of the corresponding `TARGET` Mechanisms.

    params : dict : default None
        a `parameter dictionary <ParameterState_Specification>` that can include any of the parameters above;
        the parameter's name should be used as the key for its entry. Values specified for parameters in the dictionary
        override any assigned to those parameters in arguments of the constructor.

    name : str : default System-<index>
        a string used for the name of the System
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names)

    prefs : PreferenceSet or specification dict : System.classPreferences
        the `PreferenceSet` for System (see :doc:`ComponentPreferenceSet <LINK>` for specification of PreferenceSet)

    COMMENT:
    context : str : default None
        string used for contextualization of instantiation, hierarchical calls, executions, etc.
    COMMENT

    Returns
    -------
    instance of System : System

    """


    # Called with descriptor keyword
    if not processes:
        processes = [process()]


    s = Systemm()
    for p in processes:
        s.add_pathway(p)

    return s


class System_Base(System):
    """

    System_Base(                                  \
        default_variable=None,                 \
        processes=None,                           \
        initial_values=None,                      \
        controller=SystemDefaultControlMechanism, \
        enable_controller=:keyword:`False`,       \
        monitor_for_control=None,                 \
        control_signals=None,                     \
        learning_rate=None,                       \
        targets=None,                             \
        params=None,                              \
        name=None,                                \
        prefs=None)

    COMMENT:
        VERSION WITH learning
        System_Base(                              \
        default_variable=None,                 \
        processes=None,                           \
        initial_values=None,                      \
        controller=SystemDefaultControlMechanism, \
        enable_controller=:keyword:`False`,       \
        monitor_for_control=`None`,               \
        learning=None,                            \
        targets=None,                             \
        params=None,                              \
        name=None,                                \
        prefs=None)
    COMMENT

    Base class for System.

    .. note::
       System is an abstract class and should NEVER be instantiated by a direct call to its constructor.
       It should be instantiated using the :func:`system` factory method (see it for description of parameters).

    COMMENT:
        Description
        -----------
            System is a Category of the Component class.
            It implements a System that is used to execute a collection of processes.

       Class attributes
       ----------------
        + componentCategory (str): kwProcessFunctionCategory
        + className (str): kwProcessFunctionCategory
        + suffix (str): " <kwMechanismFunctionCategory>"
        + registry (dict): ProcessRegistry
        + classPreference (PreferenceSet): ProcessPreferenceSet, instantiated in __init__()
        + classPreferenceLevel (PreferenceLevel): PreferenceLevel.CATEGORY
        + variableClassDefault = inputValueSystemDefault                     # Used as default input value to Process)
        + paramClassDefaults = {PROCESSES: [Mechanism_Base.default_mechanism],
                                CONTROLLER: SystemDefaultControlMechanism,
                                TIME_SCALE: TimeScale.TRIAL}
       Class methods
       -------------
        - _validate_variable(variable, context):  insures that variable is 3D np.array (one 2D for each Process)
        - _instantiate_attributes_before_function(context):  calls self._instantiate_graph
        - _instantiate_function(context): validates only if self.prefs.paramValidationPref is set
        - _instantiate_graph(input, context):  instantiates Processes in self.process and constructs executionList
        - identify_origin_and_terminal_mechanisms():  assign self.origin_mechanisms and self.terminalMechanisms
        - _assign_output_states():  assign OutputStates of System (currently = terminalMechanisms)
        - execute(input, time_scale, context):  executes Mechanisms in order specified by executionList
        - variableInstanceDefaults(value):  setter for variableInstanceDefaults;  does some kind of error checking??

       SystemRegistry
       --------------
        Register in SystemRegistry, which maintains a dict for the subclass, a count for all instances of it,
         and a dictionary of those instances

        TBI: MAKE THESE convenience lists, akin to self.terminalMechanisms
        + input (list): contains Process.input for each Process in self.processes
        + output (list): containts Process.ouput for each Process in self.processes
        [TBI: + input (list): each item is the Process.input object for the corresponding Process in self.processes]
        [TBI: + outputs (list): each item is the Process.output object for the corresponding Process in self.processes]
    COMMENT

    Attributes
    ----------

    componentType : SYSTEM

    processes : list of Process objects
        list of Processes in the System specified by the **processes** argument of the construtor.

        .. can be appended with prediction Processes by EVCMechanism
           used with self.input to constsruct self.process_tuples

        .. _processList : ProcessList
            Provides access to (process, input) tuples.
            Derived from self.input and self.processes.
            Used to construct :py:data:`executionGraph <System_Base.executionGraph>` and execute the System

    controller : ControlMechanism : default SystemDefaultControlMechanism
        the `ControlMechanism` used to monitor the `value <OutputState.value>` of the OutputState(s) for Mechanisms
        specified in `monitor_for_control`, and that specifies the `value <ControlSignal.value>` of the
        `ControlSignals <ControlSignal>` that control the parameters of Mechanisms (or their functions) in the System.

    enable_controller :  bool : default :keyword:`False`
        determines whether the `controller` is executed during System execution.

    learning : bool : default False
        indicates whether learning is being used;  is set to `True` if learning is specified for any Processes
        in the System or for the System itself.

    learning_rate : float : default None
        determines the learning_rate for all `LearningMechanisms <LearningMechanism>` in the System.  This overrides any
        values set for the function of individual LearningMechanisms or `LearningSignals <LearningSignal>`, and persists
        for all subsequent executions of the System.  If it is set to `None`, then the learning_rate is determined by
        last value assigned to each LearningMechanism (either directly, or following the execution of any Process or
        System to which the LearningMechanism belongs and for which a learning_rate was set).

    targets : 2d nparray : default zeroes
        used as template for the values of the System's `target_input_states`, and to represent the targets specified in
        the **targets** argument of System's `execute <System.execute>` and `run <System.run>` methods.

    graph : OrderedDict
        contains a graph of all of the Components in the System.
        Each entry specifies a set of <Receiver>: {sender, sender...} dependencies.
        The key of each entry is a receiver Component, and
        the value is a set of Mechanisms that send Projections to that receiver.
        If a key (receiver) has no dependents, its value is an empty set.

    executionGraph : OrderedDict
        contains an acyclic subset of the System's `graph`, hierarchically organized by a toposort.
        Used to specify the order in which Components are executed.

    execution_sets : list of sets
        contains a list of Component sets.
        Each set contains Components to be executed at the same time.
        The sets are ordered in the sequence with which they should be executed.

    executionList : list of Mechanisms and/or Projections
        contains a list of Components in the order in which they are executed.
        The list is a random sample of the permissible orders constrained by the `executionGraph`.

    mechanisms : list of Mechanism objects
        contains a list of all Mechanisms in the System.

        .. property that points to _allMechanisms.mechanisms (see below)

    mechanismsDict : Dict[Mechanism:Process]
        contains a dictionary of all Mechanisms in the System, listing the Processes to which they belong.
        The key of each entry is a `Mechanism` object, and the value of each entry is a list of `Processes <Process>`.

        .. Note: the following attributes use lists of tuples (Mechanism, runtime_param, phaseSpec) and MechanismList
              xxx_mechs are lists of tuples defined in the Process pathways;
                  tuples are used because runtime_params and phaseSpec are attributes that need
                  to be able to be specified differently for the same Mechanism in different contexts
                  and thus are not easily managed as Mechanism attributes
              xxxMechanismLists point to MechanismList objects that provide access to information
                  about the Mechanism <type> listed in mechs (i.e., the Mechanisms, names, etc.)

        .. _all_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all Mechanisms in the System (serve as keys in self.graph).

        .. _allMechanisms : MechanismList
            Contains all Mechanisms in the System (based on _all_mechs).

        .. _origin_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all ORIGIN Mechanisms in the System.

        .. _terminal_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all TERMINAL Mechanisms in the System.

        .. _learning_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all LearningMechanisms in the System.

        .. _target_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all TARGET `ObjectiveMechanisms <ObjectiveMechanism>`  in the System that are a `TERMINAL`
            for at least one Process to which it belongs and that Process has learning enabled --  the criteria for
            being a target used in learning.

        .. _learning_mechs : list of (Mechanism, runtime_param, phaseSpec) tuples
            Tuples for all LearningMechanisms in the System (used for learning).

        .. _control_object_item : list of a single (Mechanism, runtime_param, phaseSpec) tuple
            Tuple for the controller in the System.

    origin_mechanisms : MechanismList
        contains all `ORIGIN` Mechanisms in the System (i.e., that don't receive Projections from any other
        Mechanisms.

        .. based on _origin_mechs
           System.input contains the input to each `ORIGIN` Mechanism

    terminalMechanisms : MechanismList
        contains all `TERMINAL` Mechanisms in the System (i.e., that don't project to any other ProcessingMechanisms).

        .. based on _terminal_mechs
           System.ouput contains the output of each TERMINAL Mechanism

    recurrent_init_mechanisms : MechanismList
        contains Mechanisms with recurrent Projections that are candidates for
        `initialization <System_Execution_Input_And_Initialization>`.

    learning_mechanisms : MechanismList
        contains all `LearningMechanism <LearningMechanism>` in the System.

    target_mechanisms : MechanismList
        contains all `TARGET` Mechanisms in the System (used for learning).
        COMMENT:
            based on _target_mechs)
        COMMENT

    target_input_states : List[SystemInputState]
        one item for each `TARGET` Mechanism in the System (listed in `target_mechanisms`).  Used to represent the
        :keyword:`targets` specified in the System's `execute <System.execute>` and `run <System.run>` methods, and
        provide their values to the the TARGET InputState of each `TARGET` Mechanism during execution.

    control_mechanisms : MechanismList
        contains `controller` of the System
        COMMENT:
            ??and any other `ControlMechanisms <ControlMechanism>` in the System
            (based on _control_mechs).
        COMMENT

    value : 3D ndarray
        contains an array of 2D arrays, each of which is the `output_values` of a `TERMINAL` Mechanism in the System.

        .. _phaseSpecMax : int
            Maximum phase specified for any Mechanism in System.  Determines the phase of the last (set of)
            ProcessingMechanism(s) to be executed in the System.

        .. numPhases : int
            number of phases for System (read-only).

            .. implemented as an @property attribute; = _phaseSpecMax + 1

    initial_values : list or ndarray of values :  default array of zero arrays
        values used to initialize Mechanisms that close recurrent loops (designated as `INITIALIZE_CYCLE`).
        Must be the same length as the list of `INITIALIZE_CYCLE` Mechanisms in the System contained in
        `recurrent_init_mechanisms`.

    timeScale : TimeScale  : default TimeScale.TRIAL
        determines the default `TimeScale` value used by Mechanisms in the System.

    results : List[OutputState.value]
        list of return values (OutputState.value) from the sequence of executions.

    name : str : default System-<index>
        the name of the System;
        Specified in the **name** argument of the constructor for the System;
        if not is specified, a default is assigned by SystemRegistry
        (see :doc:`Registry <LINK>` for conventions used in naming, including for default and duplicate names).

    prefs : PreferenceSet or specification dict : System.classPreferences
        the `PreferenceSet` for System.
        Specified in the **prefs** argument of the constructor for the System;  if it is not specified, a default is
        assigned using `classPreferences` defined in __init__.py
        (see :ref:`PreferenceSet <LINK>` for details).

    """

    componentCategory = kwSystemComponentCategory
    className = componentCategory
    suffix = " " + className
    componentType = "System"

    registry = SystemRegistry

    classPreferenceLevel = PreferenceLevel.CATEGORY
    # These will override those specified in CategoryDefaultPreferences
    # classPreferences = {
    #     kwPreferenceSetName: 'SystemCustomClassPreferences',
    #     kpReportOutputPref: PreferenceEntry(False, PreferenceLevel.INSTANCE)}

    # Use inputValueSystemDefault as default input to process
    # variableClassDefault = inputValueSystemDefault
    variableClassDefault = None

    paramClassDefaults = Component.paramClassDefaults.copy()
    paramClassDefaults.update({TIME_SCALE: TimeScale.TRIAL,
                               'outputStates': {},
                               '_phaseSpecMax': 0,
                               'stimulusInputStates': [],
                               'inputs': [],
                               'current_input': None,
                               'target_input_states': [],
                               'targets': None,
                               'current_targets': None,
                               'learning': False
                               })

    # FIX 5/23/17: ADD control_signals ARGUMENT HERE (AND DOCUMENT IT ABOVE)
    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 size=None,
                 processes=None,
                 initial_values=None,
                 controller=SystemDefaultControlMechanism,
                 enable_controller=False,
                 monitor_for_control=None,
                 control_signals=None,
                 # learning=None,
                 learning_rate=None,
                 targets=None,
                 params=None,
                 name=None,
                 scheduler=None,
                 prefs:is_pref_set=None,
                 context=None):

        processes = processes or []
        monitor_for_control = monitor_for_control or [MonitoredOutputStatesOption.PRIMARY_OUTPUT_STATES]

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(processes=processes,
                                                  initial_values=initial_values,
                                                  controller=controller,
                                                  enable_controller=enable_controller,
                                                  monitor_for_control=monitor_for_control,
                                                  control_signals=control_signals,
                                                  learning_rate=learning_rate,
                                                  targets=targets,
                                                  params=params)

        self.function = self.execute
        self.scheduler_processing = scheduler
        self.scheduler_learning = None
        self.termination_processing = None
        self.termination_learning = None

        register_category(entry=self,
                          base_class=System_Base,
                          name=name,
                          registry=SystemRegistry,
                          context=context)

        if not context:
            # context = INITIALIZING + self.name
            context = INITIALIZING + self.name + kwSeparator + SYSTEM_INIT

        super().__init__(default_variable=default_variable,
                         size=size,
                         param_defaults=params,
                         name=self.name,
                         prefs=prefs,
                         context=context)

        self._execution_id = None

        # Get/assign controller

        # Existing controller has been assigned
        if isinstance(self.controller, ControlMechanism_Base):
            if self.controller.system is None:
                self.controller.system = self
            elif not self.controller.system is self:
                raise SystemError("The controller assigned to {} ({}) already belongs to another system ({})".
                                  format(self.name, self.controller.name, self.controller.system.name))

        # Instantiate controller from class specification
        else:
            self.controller = self.controller(system=self,
                                              monitor_for_control=monitor_for_control,
                                              control_signals=control_signals)

        # Check whether controller has input, and if not then disable
        # # MODIFIED 5/10/17 OLD:
        # try:
        #     has_input_states = bool(self.controller.input_states)
        # except:
        #     has_input_states = False
        # MODIFIED 5/10/17 NEW:
        has_input_states = isinstance(self.controller.input_states, ContentAddressableList)
        # MODIFIED 5/10/17 END

        if not has_input_states:
            # If controller was enabled (and verbose is set), warn that it has been disabled
            if self.enable_controller and self.prefs.verbosePref:
                print("{} for {} has no input_states, so controller will be disabled".
                      format(self.controller.name, self.name))
            self.enable_controller = False


        # Compare _phaseSpecMax with controller's phaseSpec, and assign default if it is not specified
        try:
            # Get phaseSpec from controller
            self._phaseSpecMax = max(self._phaseSpecMax, self.controller.phaseSpec)
        except (AttributeError, TypeError):
            # Controller phaseSpec not specified
            try:
                # Assign System specification of Controller phaseSpec if provided
                self.controller.phaseSpec = self.paramsCurrent[CONROLLER_PHASE_SPEC]
                self._phaseSpecMax = max(self._phaseSpecMax, self.controller.phaseSpec)
            except:
                # No System specification, so use System max as default
                self.controller.phaseSpec = self._phaseSpecMax

        # IMPLEMENT CORRECT REPORTING HERE
        # if self.prefs.reportOutputPref:
        #     print("\n{0} initialized with:\n- pathway: [{1}]".
        #           # format(self.name, self.pathwayMechanismNames.__str__().strip("[]")))
        #           format(self.name, self.names.__str__().strip("[]")))

    def _validate_variable(self, variable, context=None):
        """Convert variableClassDefault and self.variable to 2D np.array: one 1D value for each input state
        """
        super(System_Base, self)._validate_variable(variable, context)

        # # MODIFIED 6/26/16 OLD:
        # # Force System variable specification to be a 2D array (to accommodate multiple input states of 1st mech(s)):
        # self.variableClassDefault = convert_to_np_array(self.variableClassDefault, 2)
        # self.variable = convert_to_np_array(self.variable, 2)
        # FIX:  THIS CURRENTLY FAILS:
        # # MODIFIED 6/26/16 NEW:
        # # Force System variable specification to be a 3D array (to accommodate input states for each Process):
        # self.variableClassDefault = convert_to_np_array(self.variableClassDefault, 3)
        # self.variable = convert_to_np_array(self.variable, 3)
        # MODIFIED 10/2/16 NEWER:
        # Force System variable specification to be a 2D array (to accommodate multiple input states of 1st mech(s)):
        if variable is None:
            return
        self.variableClassDefault = convert_to_np_array(self.variableClassDefault, 2)
        self.variable = convert_to_np_array(self.variable, 2)

    def _validate_params(self, request_set, target_set=None, context=None):
        """Validate controller, processes and initial_values
        """
        super()._validate_params(request_set=request_set, target_set=target_set, context=context)

        controller = target_set[CONTROLLER]
        if (not isinstance(controller, ControlMechanism_Base) and
                not (inspect.isclass(controller) and issubclass(controller, ControlMechanism_Base))):
            raise SystemError("{} (controller arg for \'{}\') is not a ControllerMechanism or subclass of one".
                              format(controller, self.name))

        for process in target_set[PROCESSES]:
            if not isinstance(process, Process):
                raise SystemError("{} (in processes arg for \'{}\') is not a Process object".format(process, self.name))

        if INITIAL_VALUES in target_set and target_set[INITIAL_VALUES] is not None:
            for mech, value in target_set[INITIAL_VALUES].items():
                if not isinstance(mech, Mechanism):
                    raise SystemError("{} (key for entry in initial_values arg for \'{}\') "
                                      "is not a Mechanism object".format(mech, self.name))

    def _instantiate_attributes_before_function(self, context=None):
        """Instantiate processes and graph

        These calls must be made before _instantiate_function as the latter may be called during init for validation
        """
        self._instantiate_processes(input=self.variable, context=context)
        self._instantiate_graph(context=context)
        self._instantiate_learning_graph(context=context)

    def _instantiate_function(self, context=None):
        """Suppress validation of function

        This is necessary to:
        - insure there is no FUNCTION specified (not allowed for a System object)
        - suppress validation (and attendant execution) of System execute method (unless VALIDATE_PROCESS is set)
            since generally there is no need, as all of the mechanisms in PROCESSES have already been validated
        """

        if self.paramsCurrent[FUNCTION] != self.execute:
            print("System object ({0}) should not have a specification ({1}) for a {2} param;  it will be ignored").\
                format(self.name, self.paramsCurrent[FUNCTION], FUNCTION)
            self.paramsCurrent[FUNCTION] = self.execute

        # If validation pref is set, instantiate and execute the System
        if self.prefs.paramValidationPref:
            super(System_Base, self)._instantiate_function(context=context)
        # Otherwise, just set System output info to the corresponding info for the last mechanism(s) in self.processes
        else:
            self.value = self.processes[-1].output_state.value

    def _instantiate_processes(self, input=None, context=None):
# FIX: ALLOW Projections (??ProjectionTiming TUPLES) TO BE INTERPOSED BETWEEN MECHANISMS IN PATHWAY
# FIX: AUGMENT LinearMatrix TO USE FULL_CONNECTIVITY_MATRIX IF len(sender) != len(receiver)
        """Instantiate processes of system

        Use self.processes (populated by self.paramsCurrent[PROCESSES] in Function._assign_args_to_param_dicts
        If self.processes is empty, instantiate default process by calling process()
        Iterate through self.processes, instantiating each (including the input to each input projection)
        If input is specified, check that it's length equals the number of processes
        If input is not specified, compose from the input for each Process (value specified or, if None, default)
        Note: specification of input for system takes precedence over specification for processes

        # ??STILL THE CASE, OR MOVED TO _instantiate_graph:
        Iterate through Process._mechs for each Process;  for each sequential pair:
            - create set entry:  <receiving Mechanism>: {<sending Mechanism>}
            - add each pair as an entry in self.executionGraph
        """

        # # MODIFIED 2/8/17 OLD:  [SEE BELOW]
        # self.variable = []
        # MODIFIED 2/8/17 END
        self.mechanismsDict = {}
        self._all_mechs = []
        self._allMechanisms = MechanismList(self, self._all_mechs)

        # Get list of processes specified in arg to init, possibly appended by EVCMechanism (with prediction processes)
        processes_spec = self.processes

        # Assign default Process if PROCESS is empty, or invalid
        if not processes_spec:
            from PsyNeuLink.Components.Process import Process_Base
            processes_spec.append(ProcessTuple(Process_Base(), None))

        # If input to system is specified, number of items must equal number of processes with origin mechanisms
        if input is not None and len(input) != len(self.origin_mechanisms):
            raise SystemError("Number of items in input ({}) must equal number of processes ({}) in {} ".
                              format(len(input), len(self.origin_mechanisms),self.name))

        #region VALIDATE EACH ENTRY, STANDARDIZE FORMAT AND INSTANTIATE PROCESS

        # Convert all entries to (process, input) tuples, with None as filler for absent input
        input_index = input_index_curr = 0
        for i in range(len(processes_spec)):

            # MODIFIED 2/8/17 NEW:
            # Get list of origin mechanisms for processes that have already been converted
            #   (for use below in assigning input)
            orig_mechs_already_processed = list(p[0].origin_mechanisms[0] for
                                                p in processes_spec if isinstance(p,ProcessTuple))
            # MODIFIED 2/8/17 END

            # Entry is not a tuple
            #    presumably it is a process spec, so enter it as first item of ProcessTuple
            if not isinstance(processes_spec[i], tuple):
                processes_spec[i] = ProcessTuple(processes_spec[i], None)

            # Entry is a tuple but not a ProcessTuple, so convert it
            if isinstance(processes_spec[i], tuple) and not isinstance(processes_spec[i], ProcessTuple):
                processes_spec[i] = ProcessTuple(processes_spec[i][0], processes_spec[i][1])

            # Input was NOT provided on command line, so get it from the process
            if input is None:
                process = processes_spec[i].process
                process_input = []
                for process_input_state in process.process_input_states:
                    process_input.extend(process_input_state.value)
                processes_spec[i] = ProcessTuple(process, process_input)
            # Input was provided on command line, so assign that to input item of tuple
            else:
                # Assign None as input to processes implemented by controller (controller provides their input)
                #    (e.g., prediction processes implemented by EVCMechanism)
                if processes_spec[i].process._isControllerProcess:
                    processes_spec[i] = ProcessTuple(processes_spec[i].process, None)
                else:
                    # MODIFIED 2/8/17 NEW:
                    # Replace input item in tuple with one from command line
                    # Note:  check if origin mechanism for current process is same as any previous one;
                    #        if it is, use that one (and don't increment index for input
                    #        otherwise, assign input and increment input_index
                    try:
                        input_index_curr = orig_mechs_already_processed.index(processes_spec[i][0].origin_mechanisms[0])
                    except ValueError:
                        input_index += 1
                    processes_spec[i] = ProcessTuple(processes_spec[i].process, input[input_index_curr])
                    input_index_curr = input_index
                    # MODIFIED 2/8/17 END

            # Validate input
            if (processes_spec[i].input is not None and
                    not isinstance(processes_spec[i].input,(numbers.Number, list, np.ndarray))):
                raise SystemError("Second item of entry {0} ({1}) must be an input value".
                                  format(i, processes_spec[i].input))

            process = processes_spec[i].process
            process_input = processes_spec[i].input

            # # MODIFIED 2/8/17 OLD: [MOVED ASSIGNMENT OF self.variable TO _instantiate_graph()
            # #                       SINCE THAT IS WHERE SYSTEM'S ORIGIN MECHANISMS ARE IDENTIFIED]
            # self.variable.append(process_input)
            # # MODIFIED 2/8/17 END

            # IMPLEMENT: THIS IS WHERE LEARNING SPECIFIED FOR A SYSTEM SHOULD BE IMPLEMENTED FOR EACH PROCESS IN THE
            #            SYSTEM;  NOTE:  IF THE PROCESS IS ALREADY INSTANTIATED WITHOUT LEARNING
            #            (FIRST CONDITIONAL BELOW), MAY NEED TO BE RE-INSTANTIATED WITH LEARNING
            #            (QUESTION:  WHERE TO GET SPECS FOR PROCESS FOR RE-INSTANTIATION??)

            # If process item is a Process object, assign process_input as default
            if isinstance(process, Process):
                if process_input is not None:
                    process._instantiate_defaults(variable=process_input, context=context)
                # If learning_rate is specified for system but not for process, then apply to process
                # # MODIFIED 3/21/17 OLD:
                # if self.learning_rate and not process.learning_rate:
                    # # FIX:  assign_params WANTS TO CREATE A ParamaterState ON process FOR learning_rate
                    # process.assign_params(request_set={LEARNING_RATE:self.learning_rate})
                # # MODIFIED 3/21/17 NEW:[learning_rate SHOULD BE NOT BE RE-ASSIGNED FOR PROCESS, BUT RATHER ON EXECUTE]
                # if self.learning_rate is not None and process.learning_rate is None:
                #     process.learning_rate = self.learning_rate
                # # MODIFIED 3/21/17 END

            # Otherwise, instantiate Process
            else:
                if inspect.isclass(process) and issubclass(process, Process):
                    # FIX: MAKE SURE THIS IS CORRECT
                    # Provide self as context, so that Process knows it is part of a System (and which one)
                    # Note: this is used by Process._instantiate_pathway() when instantiating first Mechanism
                    #           in Pathway, to override instantiation of projections from Process.input_state
                    process = Process(default_variable=process_input,
                                      learning_rate=self.learning_rate,
                                      context=self)
                elif isinstance(process, dict):
                    # IMPLEMENT:  HANDLE Process specification dict here;
                    #             include process_input as ??param, and context=self
                    raise SystemError("Attempt to instantiate process {0} in PROCESSES of {1} "
                                      "using a Process specification dict: not currently supported".
                                      format(process.name, self.name))
                else:
                    raise SystemError("Entry {0} of PROCESSES ({1}) must be a Process object, class, or a "
                                      "specification dict for a Process".format(i, process))

            # # process should now be a Process object;  assign to processList
            # self.processList.append(process)

            # Assign the Process a reference to this System
            process.systems.append(self)
            if process.learning:
                self.learning = True

            # Get max of Process phaseSpecs
            self._phaseSpecMax = int(max(math.floor(process._phaseSpecMax), self._phaseSpecMax))

            # Iterate through mechanism tuples in Process' mechs
            #     to construct self._all_mechs and mechanismsDict
            # FIX: ??REPLACE WITH:  for sender_object_item in Process._mechs
            for sender_object_item in process._mechs:

                sender_mech = sender_object_item

                # THIS IS NOW DONE IN _instantiate_graph
                # # Add system to the Mechanism's list of systems of which it is member
                # if not self in sender_object_item[MECHANISM].systems:
                #     sender_mech.systems[self] = INTERNAL

                # Assign sender mechanism entry in self.mechanismsDict, with object_item as key and its Process as value
                #     (this is used by Process._instantiate_pathway() to determine if Process is part of System)
                # If the sender is already in the System's mechanisms dict
                if sender_object_item in self.mechanismsDict:
                    # existing_object_item = self._allMechanisms._get_tuple_for_mech(sender_mech)
                    # Add to entry's list
                    self.mechanismsDict[sender_mech].append(process)
                else:
                    # Add new entry
                    self.mechanismsDict[sender_mech] = [process]
                if not sender_object_item in self._all_mechs:
                    self._all_mechs.append(sender_object_item)

            process._allMechanisms = MechanismList(process, components_list=process._mechs)

        # # MODIFIED 2/8/17 OLD: [SEE ABOVE]
        # self.variable = convert_to_np_array(self.variable, 2)
        # # MODIFIED 2/8/17 END
        #
        # # Instantiate processList using process_tuples, and point self.processes to it
        # # Note: this also points self.params[PROCESSES] to self.processes
        self.process_tuples = processes_spec
        self._processList = ProcessList(self, self.process_tuples)
        self.processes = self._processList.processes

    def _instantiate_graph(self, context=None):
        """Construct graph (full) and executionGraph (acyclic) of system

        Instantate a graph of all of the mechanisms in the system and their dependencies,
            designate a type for each mechanism in the graph,
            instantiate the executionGraph, a subset of the graph with any cycles removed,
                and topologically sorted into a sequentially ordered list of sets
                containing mechanisms to be executed at the same time

        graph contains a dictionary of dependency sets for all mechanisms in the system:
            reciever_object_item : {sender_object_item, sender_object_item...}
        executionGraph contains an acyclic subset of graph used to determine sequence of mechanism execution;

        They are constructed as follows:
            sequence through self.processes;  for each process:
                begin with process.firstMechanism (assign as ORIGIN if it doesn't receive any projections)
                traverse all projections
                for each mechanism encountered (receiver), assign to its dependency set the previous (sender) mechanism
                for each assignment, use toposort to test whether the dependency introduced a cycle; if so:
                    eliminate the dependent from the executionGraph, and designate it as CYCLE (unless it is an ORIGIN)
                    designate the sender as INITIALIZE_CYCLE (it can receive and initial_value specification)
                if a mechanism doe not project to any other ProcessingMechanisms (ignore learning and control mechs):
                    assign as TERMINAL unless it is already an ORIGIN, in which case assign as SINGLETON

        Construct execution_sets and exeuction_list

        Assign MechanismLists:
            allMechanisms
            origin_mechanisms
            terminalMechanisms
            recurrent_init_mechanisms (INITIALIZE_CYCLE)
            learning_mechansims
            control_mechanisms

        Validate initial_values

        """

        def is_monitoring_mech(mech):
            if ((isinstance(mech, ObjectiveMechanism) and mech._role) or
                    isinstance(mech, (LearningMechanism, ControlMechanism_Base))):
                return True
            else:
                return False

        # Use to recursively traverse processes
        def build_dependency_sets_by_traversing_projections(sender_mech):

            # If sender is an ObjectiveMechanism being used for learning or control,
            #     or a LearningMechanism or a ControlMechanism,
            # Assign as LEARNING and move on
            if is_monitoring_mech(sender_mech):
                sender_mech.systems[self] = LEARNING
                return

            # Delete any projections to mechanism from processes or mechanisms in processes not in current system
            for input_state in sender_mech.input_states:
                for projection in input_state.all_afferents:
                    sender = projection.sender.owner
                    system_processes = self.processes
                    if isinstance(sender, Process):
                        if not sender in system_processes:
                            del projection
                    elif not all(sender_process in system_processes for sender_process in sender.processes):
                        del projection

            # If sender_mech has no projections left, raise exception
            if not any(any(projection for projection in input_state.all_afferents)
                       for input_state in sender_mech.input_states):
                raise SystemError("{} only receives projections from other processes or mechanisms not"
                                  " in the current system ({})".format(sender_mech.name, self.name))

            # Assign as TERMINAL (or SINGLETON) if it:
            #    - is not an Objective Mechanism used for Learning or Control and
            #    - it is not a ControlMechanism and
            #    - it has no outgoing projections or
            #          only ones to ObjectiveMechanism(s) used for Learning or Control
            # Note:  SINGLETON is assigned if mechanism is already a TERMINAL;  indicates that it is both
            #        an ORIGIN AND A TERMINAL and thus must be the only mechanism in its process
            if (
                # It is not a ControlMechanism
                not (isinstance(sender_mech, ControlMechanism_Base) or
                    # It is not an ObjectiveMechanism used for Learning or Control
                    (isinstance(sender_mech, ObjectiveMechanism) and sender_mech._role in (LEARNING,CONTROL))) and
                        # All of its projections
                        all(
                            all(
                                # are to ControlMechanism(s)...
                                isinstance(projection.receiver.owner, (ControlMechanism_Base, LearningMechanism)) or
                                 # ObjectiveMechanism(s) used for Learning or Control
                                 (isinstance(projection.receiver.owner, ObjectiveMechanism) and
                                             projection.receiver.owner._role in (LEARNING, CONTROL)) or
                                # itself!
                                 projection.receiver.owner is sender_mech
                            for projection in output_state.efferents)
                        for output_state in sender_mech.output_states)):
                try:
                    if sender_mech.systems[self] is ORIGIN:
                        sender_mech.systems[self] = SINGLETON
                    else:
                        sender_mech.systems[self] = TERMINAL
                except KeyError:
                    sender_mech.systems[self] = TERMINAL
                return

            for output_state in sender_mech.output_states:

                for projection in output_state.efferents:
                    receiver = projection.receiver.owner
                    # receiver_tuple = self._allMechanisms._get_tuple_for_mech(receiver)

                    # If receiver is not in system's list of mechanisms, must belong to a process that has
                    #    not been included in the system, so ignore it
                    if not receiver or is_monitoring_mech(receiver):
                        continue

                    try:
                        self.graph[receiver].add(sender_mech)
                    except KeyError:
                        self.graph[receiver] = {sender_mech}

                    # Use toposort to test whether the added dependency produced a cycle (feedback loop)
                    # Do not include dependency (or receiver on sender) in executionGraph for this projection
                    #  and end this branch of the traversal if the receiver has already been encountered,
                    #  but do mark for initialization
                    # Notes:
                    # * This is because it is a feedback connection, which introduces a cycle into the graph
                    #     that precludes use of toposort to determine order of execution;
                    #     however, the feedback projection will still be used during execution
                    #     so the sending mechanism should be designated as INITIALIZE_CYCLE
                    # * Check for receiver mechanism and not its tuple,
                    #     since the same mechanism can appear in more than one tuple (e.g., with different phases)
                    #     and would introduce a cycle irrespective of the tuple in which it appears in the graph
                    # FIX: MODIFY THIS TO (GO BACK TO) USING if receiver_tuple in self.executionGraph
                    # FIX  BUT CHECK THAT THEY ARE IN DIFFERENT PHASES
                    if receiver in self.executionGraph:
                        # Try assigning receiver as dependent of current mechanism and test toposort
                        try:
                            # If receiver_tuple already has dependencies in its set, add sender_mech to set
                            if self.executionGraph[receiver]:
                                self.executionGraph[receiver].\
                                    add(sender_mech)
                            # If receiver set is empty, assign sender_mech to set
                            else:
                                self.executionGraph[receiver] = \
                                    {sender_mech}
                            # Use toposort to test whether the added dependency produced a cycle (feedback loop)
                            list(toposort(self.executionGraph))
                        # If making receiver dependent on sender produced a cycle (feedback loop), remove from graph
                        except ValueError:
                            self.executionGraph[receiver].\
                                remove(sender_mech)
                            # Assign sender_mech INITIALIZE_CYCLE as system status if not ORIGIN or not yet assigned
                            if not sender_mech.systems or not (sender_mech.systems[self] in {ORIGIN, SINGLETON}):
                                sender_mech.systems[self] = INITIALIZE_CYCLE
                            if not (receiver.systems[self] in {ORIGIN, SINGLETON}):
                                receiver.systems[self] = CYCLE
                            continue

                    else:
                        # Assign receiver as dependent on sender mechanism
                        try:
                            # FIX: THIS WILL ADD SENDER_MECH IF RECEIVER IS IN GRAPH BUT = set()
                            # FIX: DOES THAT SCREW UP ORIGINS?
                            self.executionGraph[receiver].\
                                add(sender_mech)
                        except KeyError:
                            self.executionGraph[receiver] = \
                                {sender_mech}

                    if not sender_mech.systems:
                        sender_mech.systems[self] = INTERNAL

                    # Traverse list of mechanisms in process recursively
                    build_dependency_sets_by_traversing_projections(receiver)

        self.graph = OrderedDict()
        self.executionGraph = OrderedDict()


        # Sort for consistency of output
        sorted_processes = sorted(self.processes, key=lambda process : process.name)

        for process in sorted_processes:
            first_mech = process.firstMechanism

            # Treat as ORIGIN if ALL projections to the first mechanism in the process are from:
            #    - the process itself (ProcessInputState)
            #    - another mechanism in the in process (i.e., feedback projections from *within* the process)
            #    - mechanisms from other process for which it is an origin
            # Notes:
            # * This precludes a mechanism that is an ORIGIN of a process from being an ORIGIN for the system
            #       if it receives any projections from any other mechanisms in the system (including other processes)
            #       other than ones in processes for which it is also their ORIGIN
            # * This does allow a mechanism to be the ORIGIN (but *only* the ORIGIN) for > 1 process in the system
            if all(
                    all(
                            # All projections must be from a process (i.e., ProcessInputState) to which it belongs
                            # # MODIFIED 2/8/17 OLD:
                            # #          [THIS CHECKED FOR PROCESS IN SYSTEM'S LIST OF PROCESSES
                            # #           IT CRASHED IF first_mech WAS ASSIGNED TO ANY PROCESS THAT WAS NOT ALSO
                            # #           ASSIGNED TO THE SYSTEM TO WHICH THE first_mech BELONGS
                            #  projection.sender.owner in sorted_processes or
                            # MODIFIED 2/8/17 NEW:
                            #          [THIS CHECKS THAT PROJECTION IS FROM A PROCESS IN first_mech's LIST OF PROCESSES]
                            #           PROBABLY ISN"T NECESSARY, AS IT SHOULD BE COVERED BY INITIAL ASSIGNMENT OF PROJ]
                            projection.sender.owner in first_mech.processes or
                            # MODIFIED 2/8/17 END
                            # or from mechanisms within its own process (e.g., [a, b, a])
                            projection.sender.owner in list(process.mechanisms) or
                            # or from mechanisms in other processes for which it is also an ORIGIN ([a,b,a], [a,c,a])
                            all(ORIGIN in first_mech.processes[proc]
                                for proc in projection.sender.owner.processes
                                if isinstance(projection.sender.owner,Mechanism))
                        # For all the projections to each InputState
                        for projection in input_state.path_afferents)
                    # For all input_states for the first_mech
                    for input_state in first_mech.input_states):
                # Assign its set value as empty, marking it as a "leaf" in the graph
                object_item = first_mech
                self.graph[object_item] = set()
                self.executionGraph[object_item] = set()
                first_mech.systems[self] = ORIGIN

            build_dependency_sets_by_traversing_projections(first_mech)

        # # MODIFIED 4/1/17 NEW:
        # # HACK TO LABEL TERMINAL MECHS -- SHOULD HAVE BEEN HANDLED ABOVE
        # # LABELS ANY MECH AS A TARGET THAT PROJECTS TO AN ObjectiveMechanism WITH LEARNING AS ITS role
        # for mech in self.mechanisms:
        #     for output_state in mech.outputStates.values():
        #         for projection in output_state.efferents:
        #             receiver = projection.receiver.owner
        #             if isinstance(receiver, ObjectiveMechanism) and receiver.role == LEARNING:
        #                 mech.systems[self] = TERMINAL
        #                 break
        #         if mech.systems[self] == TERMINAL:
        #             break
        # # MODIFIED 4/1/17 END

        # Print graph
        if self.verbosePref:
            warnings.warn("In the system graph for \'{}\':".format(self.name))
            for receiver_object_item, dep_set in self.executionGraph.items():
                mech = receiver_object_item
                if not dep_set:
                    print("\t\'{}\' is an {} mechanism".
                          format(mech.name, mech.systems[self]))
                else:
                    status = mech.systems[self]
                    if status is TERMINAL:
                        status = 'a ' + status
                    elif status in {INTERNAL, INITIALIZE_CYCLE}:
                        status = 'an ' + status
                    print("\t\'{}\' is {} mechanism that receives projections from:".format(mech.name, status))
                    for sender_object_item in dep_set:
                        print("\t\t\'{}\'".format(sender_object_item.name))

        # For each mechanism (represented by its tuple) in the graph, add entry to relevant list(s)
        # Note: ignore mechanisms belonging to controllerProcesses (e.g., instantiated by EVCMechanism)
        #       as they are for internal use only;
        #       this also ignored learning-related mechanisms (they are handled below)
        self._origin_mechs = []
        self._terminal_mechs = []
        self.recurrent_init_mechs = []
        self._control_object_item = []

        for object_item in self.executionGraph:

            mech = object_item

            if mech.systems[self] in {ORIGIN, SINGLETON}:
                for process, status in mech.processes.items():
                    if process._isControllerProcess:
                        continue
                    self._origin_mechs.append(object_item)
                    break

            if object_item.systems[self] in {TERMINAL, SINGLETON}:
                for process, status in mech.processes.items():
                    if process._isControllerProcess:
                        continue
                    self._terminal_mechs.append(object_item)
                    break

            if object_item.systems[self] in {INITIALIZE_CYCLE}:
                for process, status in mech.processes.items():
                    if process._isControllerProcess:
                        continue
                    self.recurrent_init_mechs.append(object_item)
                    break

            if isinstance(object_item, ControlMechanism_Base):
                if not object_item in self._control_object_item:
                    self._control_object_item.append(object_item)

        self.origin_mechanisms = MechanismList(self, self._origin_mechs)
        self.terminalMechanisms = MechanismList(self, self._terminal_mechs)
        self.recurrent_init_mechanisms = MechanismList(self, self.recurrent_init_mechs)
        self.control_Mechanism = MechanismList(self, self._control_object_item) # Used for inspection and in case there
                                                                              # are multiple controllers in the future

        try:
            self.execution_sets = list(toposort(self.executionGraph))
        except ValueError as e:
            if 'Cyclic dependencies exist' in e.args[0]:
                # if self.verbosePref:
                # print('{} has feedback connections; be sure that the following items are properly initialized:'.
                #       format(self.name))
                raise SystemError("PROGRAM ERROR: cycle (feedback loop) in {} not detected by _instantiate_graph ".
                                  format(self.name))

        # Create instance of sequential (execution) list:
        # MODIFIED 10/31/16 OLD:
        # self.executionList = toposort_flatten(self.executionGraph, sort=False)
        # MODIFIED 10/31/16 NEW:
        temp = toposort_flatten(self.executionGraph, sort=False)
        self.executionList = self._toposort_with_ordered_mechs(self.executionGraph)
        # MODIFIED 10/31/16 END

        # MODIFIED 6/27/17 NEW: (CW)
        # changed "orig_mech_input.extend(input_state.value)" to "orig_mech_input.append(input_state.value)"
        # this is accompanied by a change to the code around line 1510 where a for loop was added.
        # MODIFIED 2/8/17 NEW:
        # Construct self.variable from inputs to ORIGIN mechanisms
        self.variable = []
        for mech in self.origin_mechanisms:
            orig_mech_input = []
            for input_state in mech.input_states:
                orig_mech_input.append(input_state.value)
            self.variable.append(orig_mech_input)
        self.variable = convert_to_np_array(self.variable, 2)  # should add Utility to allow conversion to 3D array
        # MODIFIED 2/8/17 END
        # An example: when input state values are vectors, then self.variable is a 3D array because an origin
        # mechanism could have multiple input states if there is a recurrent input state. However, if input state values
        # are all non-vector objects, such as strings, then self.variable would be a 2D array. so we should
        # convert that to a 3D array
        # MODIFIED 6/27/17 END

        # Instantiate StimulusInputStates
        self._instantiate_stimulus_inputs()

        # Validate initial values
        # FIX: CHECK WHETHER ALL MECHANISMS DESIGNATED AS INITIALIZE HAVE AN INITIAL_VALUES ENTRY
        # FIX: ONLY CHECKS FIRST ITEM OF self._default_value (ASSUMES THAT IS ALL THAT WILL GET ASSIGNED)
        # FIX: ONLY CHECK ONES THAT RECEIVE PROJECTIONS
        if self.initial_values is not None:
            for mech, value in self.initial_values.items():
                if not mech in self.executionGraph:
                    raise SystemError("{} (entry in initial_values arg) is not a Mechanism in \'{}\'".
                                      format(mech.name, self.name))
                mech._update_value
                if not iscompatible(value, mech.default_value[0]):
                    raise SystemError("{} (in initial_values arg for \'{}\') is not a valid value for {}".
                                      format(value, self.name, append_type_to_name(self)))

    def _instantiate_stimulus_inputs(self, context=None):

# FIX: ZERO VALUE OF ALL ProcessInputStates BEFORE EXECUTING
# FIX: RENAME SystemInputState -> SystemInputState

        # Create SystemInputState for each ORIGIN mechanism in origin_mechanisms and
        #    assign MappingProjection from the SystemInputState to the ORIGIN mechanism
        for i, origin_mech in zip(range(len(self.origin_mechanisms)), self.origin_mechanisms):

            # Skip if ORIGIN mechanism already has a projection from a SystemInputState in current system
            # (this avoids duplication from multiple passes through _instantiate_graph)
            if any(self is projection.sender.owner for projection in origin_mech.input_state.path_afferents):
                continue
            # MODIFIED 6/27/17 NEW:
            # added a for loop to iterate over origin_mech.input_states to allow for
            # multiple input states in an origin mechanism (useful only if the origin mechanism is a KWTA)
            # Check, for each ORIGIN mechanism, that the length of the corresponding item of self.variable matches the
            # length of the ORIGIN inputState's variable attribute
            for j in range(len(origin_mech.input_states)):
                if len(self.variable[i][j]) != len(origin_mech.input_states[j].variable):
                    raise SystemError("Length of input {} ({}) does not match the length of the input ({}) for the "
                                      "corresponding ORIGIN mechanism ()".
                                       format(i,
                                              len(self.variable[i][j]),
                                              len(origin_mech.input_states[j].variable),
                                              origin_mech.name))
            # MODIFIED 6/27/17 END

            stimulus_input_state = SystemInputState(owner=self,
                                                        variable=origin_mech.input_state.variable,
                                                        prefs=self.prefs,
                                                        name="System Input {}".format(i))
            self.stimulusInputStates.append(stimulus_input_state)
            self.inputs.append(stimulus_input_state.value)

            # Add MappingProjection from stimulus_input_state to ORIGIN mechainsm's inputState
            from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
            MappingProjection(sender=stimulus_input_state,
                    receiver=origin_mech,
                    name=self.name+' Input Projection to '+origin_mech.name)


    def _instantiate_learning_graph(self, context=None):
        """Build graph of LearningMechanisms and LearningProjections
        """

        self.learningGraph = OrderedDict()
        self.learningExecutionGraph = OrderedDict()

        def build_dependency_sets_by_traversing_projections(sender_mech, process):

            # MappingProjections are legal recipients of learning projections (hence the call)
            #  but do not send any projections, so no need to consider further
            from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
            if isinstance(sender_mech, MappingProjection):
                return

            # All other sender_mechs must be either a LearningMechanism or a ComparatorMechanism with role=LEARNING
            elif not (isinstance(sender_mech, LearningMechanism) or
                          (isinstance(sender_mech, ObjectiveMechanism) and sender_mech._role is LEARNING)):
                raise SystemError("PROGRAM ERROR: {} is not a legal object for learning graph;"
                                  "must be a LearningMechanism or an ObjectiveMechanism".
                                  format(sender_mech))

            # MANAGE TARGET ObjectiveMechanism FOR INTERNAL or TERMINAL CONVERGENCE of PATHWAYS

            # If sender_mech is an ObjectiveMechanism, and:
            #    - none of the mechanisms that project to it are are a TERMINAL mechanism for the current process, or
            #    - all of the mechanisms that project to it already have an ObjectiveMechanism, then:
            #        - do not include the ObjectiveMechanism in the graph;
            #        - be sure that its outputState projects to the ERROR_SIGNAL inputState of a LearningMechanism
            #            (labelled "learning_mech" here -- raise an exception if it does not;
            #        - determine whether learning_mech's ERROR_SIGNAL inputState receives any other projections
            #            from another ObjectiveMechanism or LearningMechanism (labelled "error_signal_projection" here)
            #            -- if it does, be sure that it is from the same system and if so return;
            #               (note:  this shouldn't be true, but the test is here for completeness and sanity-checking)
            #        - if learning_mech's ERROR_SIGNAL inputState does not receive any projections from
            #            another objectiveMechanism and/or LearningMechanism in the system, then:
            #            - find the sender to the ObjectiveMechanism (labelled "error_source" here)
            #            - find the 1st projection from error_source that projects to the ACTIVATION_INPUT inputState of
            #                a LearningMechanism (labelled "error_signal" here)
            #            - instantiate a MappingProjection from error_signal to learning_mech
            #                projected
            # IMPLEMENTATION NOTE: Composition should allow 1st condition if user indicates internal TARGET is desired;
            #                      for now, however, assuming this is not desired (i.e., only TERMINAL mechanisms
            #                      should project to ObjectiveMechanisms) and always replace internal
            #                      ObjectiveMechanism with projection from a LearningMechanism (if it is available)

            # FIX: RELABEL "sender_mech" as "obj_mech" here

            if isinstance(sender_mech, ObjectiveMechanism) and len(self.learningExecutionGraph):

                # TERMINAL CONVERGENCE
                # All of the mechanisms that project to sender_mech
                #    project to another ObjectiveMechanism already in the learning_graph
                if all(
                        any(
                                (isinstance(receiver_mech, ObjectiveMechanism) and
                                 # its already in a dependency set in the learningExecutionGraph
                                         receiver_mech in set.union(*list(self.learningExecutionGraph.values())) and
                                     not receiver_mech is sender_mech)
                                # receivers of senders to sender_mech
                                for receiver_mech in [proj.receiver.owner for proj in
                                                      mech.output_state.efferents])
                        # senders to sender_mech
                        for mech in [proj.sender.owner
                                     for proj in sender_mech.input_states[SAMPLE].path_afferents]):

                    # Get the ProcessingMechanism that projected to sender_mech
                    error_source_mech = sender_mech.input_states[SAMPLE].path_afferents[0].sender.owner

                    # Get the other ObjectiveMechanism to which the error_source projects (in addition to sender_mech)
                    other_obj_mech = next((projection.receiver.owner for projection in
                                           error_source_mech.output_state.efferents if
                                           isinstance(projection.receiver.owner, ObjectiveMechanism)), None)
                    sender_mech = other_obj_mech

                # INTERNAL CONVERGENCE
                # None of the mechanisms that project to it are a TERMINAL mechanism
                elif not all(all(projection.sender.owner.processes[proc] is TERMINAL
                                 for proc in projection.sender.owner.processes)
                             for projection in sender_mech.input_states[SAMPLE].path_afferents):

                    # Get the LearningMechanism to which the sender_mech projected
                    try:
                        learning_mech = sender_mech.output_state.efferents[0].receiver.owner
                        if not isinstance(learning_mech, LearningMechanism):
                            raise AttributeError
                    except AttributeError:
                        raise SystemError("{} does not project to a LearningMechanism in the same process {}".
                                          format(sender_mech.name, process.name))

                    from PsyNeuLink.Components.Mechanisms.AdaptiveMechanisms.LearningMechanisms.LearningAuxilliary \
                        import ACTIVATION_INPUT, ERROR_SIGNAL

                    # Get the ProcessingMechanism that projected to sender_mech
                    error_source_mech = sender_mech.input_states[SAMPLE].path_afferents[0].sender.owner

                    # Get the other LearningMechanism to which the error_source projects (in addition to sender_mech)
                    error_signal_mech = next((projection.receiver.owner for projection in
                                              error_source_mech.output_state.efferents if
                                              projection.receiver.name is ACTIVATION_INPUT), None)


                    # Check if learning_mech receives an error_signal_projection
                    #    from any other ObjectiveMechanism or LearningMechanism in the system;
                    # If it does, get the first one found
                    error_signal_projection = next ((projection for projection
                                                     in learning_mech.input_states[ERROR_SIGNAL].path_afferents
                                                     if (isinstance(projection.sender.owner,(ObjectiveMechanism,
                                                                                            LearningMechanism)) and
                                                     not projection.sender.owner is sender_mech and
                                                     self in projection.sender.owner.systems.values())), None)
                    # If learning_mech receives another error_signal projection,
                    #    reassign sender_mech to the sender of that projection
                    # FIX:  NEED TO ALSO REASSIGN learning_mech.function_object.error_matrix TO ONE FOR sender_mech
                    if error_signal_projection:
                        if self.verbosePref:
                            warnings.warn("Although {} a TERMINAL mechanism for the {} process, it is an "
                                          "internal mechanism for other proesses in the {} system; therefore "
                                          "its ObjectiveMechanism ({}) will be replaced with the {} LearningMechanism".
                                          format(error_source_mech.name,
                                                 process.name,
                                                 self.name,
                                                 sender_mech.name,
                                                 error_signal_mech))
                        sender_mech = error_signal_projection.sender.owner

                    # FIX:  FINISH DOCUMENTATION HERE ABOUT HOW THIS IS DIFFERENT THAN ABOVE
                    if error_signal_mech is None:
                        raise SystemError("Could not find projection to an {} inputState of a LearningMechanism for "
                                          "the ProcessingMechanism ({}) that projects to {} in the {} process"
                                          "".format(ACTIVATION_INPUT,
                                                    error_source_mech.name,
                                                    sender_mech.name,
                                                    process.name))
                    # learning_mech does not receive another error_signal projection,
                    #     so assign one to it from error_signal_mech
                    #     (the other LearningMechanism to which the error_source_mech projects)
                    # and reassign learning_mech.function_object.error_matrix
                    #     (to the one for the projection to which error_signal_mech projects)
                    else:
                        mp = MappingProjection(sender=error_signal_mech.output_states[ERROR_SIGNAL],
                                               receiver=learning_mech.input_states[ERROR_SIGNAL],
                                               matrix=IDENTITY_MATRIX)
                        if mp is None:
                            raise SystemError("Could not instantiate a MappingProjection "
                                              "from {} to {} for the {} process".
                                              format(error_signal_mech.name, learning_mech.name))

                        # Reassign error_matrix to one for the projection to which the error_signal_mech projects
                        learning_mech.function_object.error_matrix = \
                            error_signal_mech._output_states['matrix_LearningSignal'].efferents[0].receiver
                        # Delete error_matrix parameterState for error_matrix
                        #    (since its value, which was the IDENTITY_MATRIX, is now itself ParameterState,
                        #     and Components are not allowed  as the value of a ParameterState
                        #     -- see ParameterState._instantiate_parameter_state())
                        if 'error_matrix' in learning_mech._parameter_states:
                            del learning_mech._parameter_states['error_matrix']

                        sender_mech = error_signal_mech

            # Delete any projections to mechanism from processes or mechanisms in processes not in current system
            for input_state in sender_mech.input_states:
                for projection in input_state.all_afferents:
                    sender = projection.sender.owner
                    system_processes = self.processes
                    if isinstance(sender, Process):
                        if not sender in system_processes:
                            del projection
                    elif not all(sender_process in system_processes for sender_process in sender.processes):
                        del projection

            # If sender_mech has no projections left, raise exception
            if not any(any(projection for projection in input_state.path_afferents)
                       for input_state in sender_mech.input_states):
                raise SystemError("{} only receives projections from other processes or mechanisms not"
                                  " in the current system ({})".format(sender_mech.name, self.name))

            for output_state in sender_mech.output_states:

                for projection in output_state.efferents:
                    receiver = projection.receiver.owner
                    try:
                        self.learningGraph[receiver].add(sender_mech)
                    except KeyError:
                        self.learningGraph[receiver] = {sender_mech}

                    # Use toposort to test whether the added dependency produced a cycle (feedback loop)
                    # Do not include dependency (or receiver on sender) in learningExecutionGraph for this projection
                    #  and end this branch of the traversal if the receiver has already been encountered,
                    #  but do mark for initialization
                    # Notes:
                    # * This is because it is a feedback connection, which introduces a cycle into the learningGraph
                    #     that precludes use of toposort to determine order of execution;
                    #     however, the feedback projection will still be used during execution
                    #     so the sending mechanism should be designated as INITIALIZE_CYCLE
                    # * Check for receiver mechanism and not its tuple,
                    #     since the same mechanism can appear in more than one tuple (e.g., with different phases)
                    #     and would introduce a cycle irrespective of the tuple in which it appears in the learningGraph

                    if receiver in self.learningExecutionGraph:
                    # if receiver in self.learning_execution_graph_mechs:
                        # Try assigning receiver as dependent of current mechanism and test toposort
                        try:
                            # If receiver already has dependencies in its set, add sender_mech to set
                            if self.learningExecutionGraph[receiver]:
                                self.learningExecutionGraph[receiver].add(sender_mech)
                            # If receiver set is empty, assign sender_mech to set
                            else:
                                self.learningExecutionGraph[receiver] = {sender_mech}
                            # Use toposort to test whether the added dependency produced a cycle (feedback loop)
                            list(toposort(self.learningExecutionGraph))
                        # If making receiver dependent on sender produced a cycle, remove from learningGraph
                        except ValueError:
                            self.learningExecutionGraph[receiver].remove(sender_mech)
                            receiver.systems[self] = CYCLE
                            continue

                    else:
                        # Assign receiver as dependent on sender mechanism
                        try:
                            # FIX: THIS WILL ADD SENDER_MECH IF RECEIVER IS IN GRAPH BUT = set()
                            # FIX: DOES THAT SCREW UP ORIGINS?
                            self.learningExecutionGraph[receiver].add(sender_mech)
                        except KeyError:
                            self.learningExecutionGraph[receiver] = {sender_mech}

                    if not sender_mech.systems:
                        sender_mech.systems[self] = LEARNING

                    # Traverse list of mechanisms in process recursively
                    build_dependency_sets_by_traversing_projections(receiver, process)

        # Sort for consistency of output
        sorted_processes = sorted(self.processes, key=lambda process : process.name)

        # This assumes that the first mechanism in process.learning_mechanisms is the last in the learning sequence
        # (i.e., that the list is being traversed "backwards")
        for process in sorted_processes:
            if process.learning and process._learning_enabled:
                build_dependency_sets_by_traversing_projections(process.learning_mechanisms[0], process)

        # FIX: USE TOPOSORT TO FIND, OR AT LEAST CONFIRM, TARGET MECHANISMS, WHICH SHOULD EQUAL COMPARATOR MECHANISMS
        self.learningExecutionList = toposort_flatten(self.learningExecutionGraph, sort=False)
        # self.learningExecutionList = self._toposort_with_ordered_mechs(self.learningExecutionGraph)

        # Construct learning_mechanisms and target_mechanisms MechanismLists

        self._learning_mechs = []
        self._target_mechs = []

        from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
        for item in self.learningExecutionList:
            if isinstance(item, MappingProjection):
                continue

            # If a learning_rate has been specified for the system, assign that to all LearningMechanisms
            #    for which a mechanism-specific learning_rate has NOT been assigned
            if (isinstance(item, LearningMechanism) and
                        self.learning_rate is not None and
                        item.function_object.learning_rate is None):
                item.function_object.learning_rate = self.learning_rate

            if not item in self._learning_mechs:
                self._learning_mechs.append(item)
            if isinstance(item, ObjectiveMechanism) and not item in self._target_mechs:
                self._target_mechs.append(item)
        self.learning_mechanisms = MechanismList(self, self._learning_mechs)
        self.target_mechanisms = MechanismList(self, self._target_mechs)

        # Instantiate TargetInputStates
        self._instantiate_target_inputs(context=context)

    def _instantiate_target_inputs(self, context=None):

        if self.learning and self.targets is None:
            if not self.target_mechanisms:
                raise SystemError("PROGRAM ERROR: Learning has been specified for {} but it has no target_mechanisms".
                                  format(self.name))
            # # MODIFIED 6/25/17 OLD:
            # raise SystemError("Learning has been specified for {} so its \'targets\' argument must also be specified".
            #                   format(self.name))
            # MODIFIED 6/25/17 NEW:
            # target arg was not specified in System's constructor,
            #    so use the value of the TARGET InputState for the TARGET Mechanism(s) as the default
            self.targets = [target.input_states[TARGET].value for target in self.target_mechanisms]
            if self.verbosePref:
                warnings.warn("Learning has been specified for {} but its \'targets\' argument was not specified;"
                              "default will be used ({})".format(self.name, self.targets))
            # MODIFIED 6/25/17 END

        self.targets = np.atleast_2d(self.targets)

        # Create SystemInputState for each TARGET mechanism in target_mechanisms and
        #    assign MappingProjection from the SystemInputState
        #    to the TARGET mechanism's TARGET inputSate
        #    (i.e., from the SystemInputState to the ComparatorMechanism)
        for i, target_mech in zip(range(len(self.target_mechanisms)), self.target_mechanisms):

            # Create ProcessInputState for each target and assign to targetMechanism's target inputState
            target_mech_TARGET_input_state = target_mech.input_states[TARGET]

            # Check, for each TARGET mechanism, that the length of the corresponding item of targets matches the length
            #    of the TARGET (ComparatorMechanism) target inputState's variable attribute
            if len(self.targets[i]) != len(target_mech_TARGET_input_state.variable):
                raise SystemError("Length of target ({}: {}) does not match the length ({}) of the target "
                                  "expected for its TARGET mechanism {}".
                                   format(len(self.targets[i]),
                                          self.targets[i],
                                          len(target_mech_TARGET_input_state.variable),
                                          target_mech.name))

            system_target_input_state = SystemInputState(owner=self,
                                                        variable=target_mech_TARGET_input_state.variable,
                                                        prefs=self.prefs,
                                                        name="System Target {}".format(i))
            self.target_input_states.append(system_target_input_state)

            # Add MappingProjection from system_target_input_state to TARGET mechainsm's target inputState
            from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
            MappingProjection(sender=system_target_input_state,
                    receiver=target_mech_TARGET_input_state,
                    name=self.name+' Input Projection to '+target_mech_TARGET_input_state.name)

    def _assign_output_states(self):
        """Assign outputStates for System (the values of which will comprise System.value)

        Assign the outputs of terminal Mechanisms in the graph to the system's output_values

        Note:
        * Current implementation simply assigns terminal mechanisms as outputStates
        * This method is included so that sublcasses and/or future versions can override it to make custom assignments

        """
        for mech in self.terminalMechanisms.mechanisms:
            self.output_states[mech.name] = mech.output_states

    def initialize(self):
        """Assign :py:data:`initial_values <System_Base.initialize>` to mechanisms designated as \
        `INITIALIZE_CYCLE` and contained in recurrent_init_mechanisms.
        """
        # FIX:  INITIALIZE PROCESS INPUT??
        # FIX: CHECK THAT ALL MECHANISMS ARE INITIALIZED FOR WHICH mech.system[SELF]==INITIALIZE
        # FIX: ADD OPTION THAT IMPLEMENTS/ENFORCES INITIALIZATION
        # FIX: ADD SOFT_CLAMP AND HARD_CLAMP OPTIONS
        # FIX: ONLY ASSIGN ONES THAT RECEIVE PROJECTIONS
        for mech, value in self.initial_values.items():
            mech.initialize(value)

    def execute(self,
                input=None,
                target=None,
                execution_id=None,
                clock=CentralClock,
                time_scale=None,
                termination_processing=None,
                termination_learning=None,
                # time_scale=TimeScale.TRIAL
                context=None):
        """Execute mechanisms in system at specified :ref:`phases <System_Execution_Phase>` in order \
        specified by the :py:data:`executionGraph <System_Base.executionGraph>` attribute.

        Assign items of input to `ORIGIN` mechanisms

        Execute mechanisms in the order specified in executionList and with phases equal to
        ``CentralClock.time_step % numPhases``.

        Execute any learning components specified at the appropriate phase.

        Execute controller after all mechanisms have been executed (after each numPhases)

        .. Execution:
            - the input arg in system.execute() or run() is provided as input to ORIGIN mechanisms (and system.input);
                As with a process, ORIGIN mechanisms will receive their input only once (first execution)
                    unless clamp_input (or SOFT_CLAMP or HARD_CLAMP) are specified, in which case they will continue to
            - execute() calls mechanism.execute() for each mechanism in its execute_graph in sequence
            - outputs of TERMINAL mechanisms are assigned as system.ouputValue
            - system.controller is executed after execution of all mechanisms in the system
            - notes:
                * the same mechanism can be listed more than once in a system, inducing recurrent processing

        Arguments
        ---------
        input : list or ndarray
            a list or array of input value arrays, one for each `ORIGIN` mechanism in the system.

            .. [TBI: time_scale : TimeScale : default TimeScale.TRIAL
               specifies a default TimeScale for the system]

            .. context : str

        Returns
        -------
        output values of system : 3d ndarray
            Each item is a 2d array that contains arrays for each outputState.value of each TERMINAL mechanism

        """
        if self.scheduler_processing is None:
            self.scheduler_processing = Scheduler(system=self)

        if self.scheduler_learning is None:
            self.scheduler_learning = Scheduler(graph=self.learningExecutionGraph)

        if not context:
            context = EXECUTING + " " + SYSTEM + " " + self.name
            self.execution_status = ExecutionStatus.EXECUTING

        # Update execution_id for self and all mechanisms in graph (including learning) and controller
        from PsyNeuLink.Globals.Run import _get_unique_id
        self._execution_id = execution_id or _get_unique_id()
        # FIX: GO THROUGH LEARNING GRAPH HERE AND ASSIGN EXECUTION TOKENS FOR ALL MECHANISMS IN IT
        # self.learningExecutionList
        for mech in self.executionGraph:
            mech._execution_id = self._execution_id
        for learning_mech in self.learningExecutionList:
            learning_mech._execution_id = self._execution_id
        self.controller._execution_id = self._execution_id
        if self.enable_controller and self.controller.input_states:
            for state in self.controller.input_states:
                for projection in state.all_afferents:
                    projection.sender.owner._execution_id = self._execution_id

        self._report_system_output = self.prefs.reportOutputPref and context and EXECUTING in context
        if self._report_system_output:
            self._report_process_output = any(process.reportOutputPref for process in self.processes)

        self.timeScale = time_scale or TimeScale.TRIAL

        # FIX: MOVE TO RUN??
        #region ASSIGN INPUTS TO SystemInputStates
        #    that will be used as the input to the MappingProjection to each ORIGIN mechanism
        num_origin_mechs = len(list(self.origin_mechanisms))

        if input is None:
            if (self.prefs.verbosePref and
                    not (not context or COMPONENT_INIT in context)):
                print("- No input provided;  default will be used: {0}")
            input = np.zeros_like(self.variable)
            for i in range(num_origin_mechs):
                input[i] = self.origin_mechanisms[i].variableInstanceDefault

        else:
            num_inputs = np.size(input,0)

            # Check if input items are of different lengths (indicated by dtype == np.dtype('O'))
            if num_inputs != num_origin_mechs:
                num_inputs = np.size(input)
               # Check that number of inputs matches number of ORIGIN mechanisms
                if isinstance(input, np.ndarray) and input.dtype is np.dtype('O') and num_inputs == num_origin_mechs:
                    pass
                else:
                    raise SystemError("Number of items in input ({0}) to {1} does not match "
                                      "its number of origin Mechanisms ({2})".
                                      format(num_inputs, self.name,  num_origin_mechs ))

            # Get SystemInputState that projects to each ORIGIN mechanism and assign input to it
            for i, origin_mech in zip(range(num_origin_mechs), self.origin_mechanisms):
                # For each inputState of the ORIGIN mechanism
                for j in range(len(origin_mech.input_states)):
                   # Get the input from each projection to that inputState (from the corresponding SystemInputState)
                    system_input_state = next((projection.sender
                                               for projection in origin_mech.input_states[j].path_afferents
                                               if isinstance(projection.sender, SystemInputState)), None)
                    if system_input_state:
                        system_input_state.value = input[i][j]
                    else:
                        print("Failed to find expected SystemInputState for {} at input state number ({}), ({})".
                              format(origin_mech.name, j+1, origin_mech.input_states[j]))
                        # raise SystemError("Failed to find expected SystemInputState for {}".format(origin_mech.name))

        self.input = input
        if termination_processing is not None:
            self.termination_processing = termination_processing
        if termination_learning is not None:
            self.termination_learning = termination_learning
        #endregion

        if self._report_system_output:
            self._report_system_initiation(clock=clock)


        #region EXECUTE MECHANISMS

        # TEST PRINT:
        # for i in range(len(self.executionList)):
        #     print(self.executionList[i][0].name)
        # sorted_list = list(object_item[0].name for object_item in self.executionList)

        # Execute system without learning on projections (that will be taken care of in _execute_learning()
        self._execute_processing(clock=clock, context=context)
        #endregion

        # region EXECUTE LEARNING FOR EACH PROCESS

        # Don't execute learning for simulation runs
        if not EVC_SIMULATION in context and self.learning:
            self._execute_learning(clock=clock, context=context + ' ' + LEARNING)
        # endregion


        #region EXECUTE CONTROLLER
# FIX: 1) RETRY APPENDING TO EXECUTE LIST AND COMPARING TO THIS VERSION
# FIX: 2) REASSIGN INPUT TO SYSTEM FROM ONE DESIGNATED FOR EVC SIMULUS (E.G., StimulusPrediction)

        # Only call controller if this is not a controller simulation run (to avoid infinite recursion)
        if not EVC_SIMULATION in context and self.enable_controller:
            try:
                if self.controller.phaseSpec == (clock.time_step % self.numPhases):
                    self.controller.execute(clock=clock,
                                            time_scale=TimeScale.TRIAL,
                                            runtime_params=None,
                                            context=context)
                    if self._report_system_output:
                        print("{0}: {1} executed".format(self.name, self.controller.name))

            except AttributeError as error_msg:
                if not 'INIT' in context:
                    raise SystemError("PROGRAM ERROR: Problem executing controller for {}: {}".
                                      format(self.name, error_msg))
        #endregion

        # Report completion of system execution and value of designated outputs
        if self._report_system_output:
            self._report_system_completion(clock=clock)

        return self.terminalMechanisms.outputStateValues

    def _execute_processing(self, clock=CentralClock, context=None):
    # def _execute_processing(self, clock=CentralClock, time_scale=TimeScale.Trial, context=None):
        # Execute each Mechanism in self.executionList, in the order listed during its phase


            # Only update Mechanism on time_step(s) determined by its phaseSpec (specified in Mechanism's Process entry)
# FIX: NEED TO IMPLEMENT FRACTIONAL UPDATES (IN Mechanism.update()) FOR phaseSpec VALUES THAT HAVE A DECIMAL COMPONENT
        if self.scheduler_processing is None:
            raise SystemError('System.py:_execute_processing - {0}\'s scheduler is None, must be initialized before execution'.format(self.name))
        logger.debug('{0}.scheduler processing termination conditions: {1}'.format(self, self.termination_processing))
        for next_execution_set in self.scheduler_processing.run(termination_conds=self.termination_processing):
            logger.debug('Running next_execution_set {0}'.format(next_execution_set))
            i = 0
            for mechanism in next_execution_set:
                logger.debug('\tRunning mechanism {0}'.format(mechanism))
                for p in self.processes:
                    try:
                        rt_params = p.runtime_params_dict[mechanism]
                    except:
                        rt_params = None

                processes = list(mechanism.processes.keys())
                process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                process_names = list(p.name for p in process_keys_sorted)

                mechanism.execute(clock=clock,
                                  time_scale=self.timeScale,
                                  # time_scale=time_scale,
                                  runtime_params=rt_params,
                                  context=context +
                                          "| mechanism: " + mechanism.name +
                                          " [in processes: " + str(process_names) + "]")


                if self._report_system_output and  self._report_process_output:

                    # REPORT COMPLETION OF PROCESS IF ORIGIN:
                    # Report initiation of process(es) for which mechanism is an ORIGIN
                    # Sort for consistency of reporting:
                    processes = list(mechanism.processes.keys())
                    process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                    for process in process_keys_sorted:
                        if mechanism.processes[process] in {ORIGIN, SINGLETON} and process.reportOutputPref:
                            process._report_process_initiation(input=mechanism.input_values[0])

                    # REPORT COMPLETION OF PROCESS IF TERMINAL:
                    # Report completion of process(es) for which mechanism is a TERMINAL
                    # Sort for consistency of reporting:
                    processes = list(mechanism.processes.keys())
                    process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                    for process in process_keys_sorted:
                        if process.learning and process._learning_enabled:
                            continue
                        if mechanism.processes[process] == TERMINAL and process.reportOutputPref:
                            process._report_process_completion()

            if i == 0:
                # Zero input to first mechanism after first run (in case it is repeated in the pathway)
                # IMPLEMENTATION NOTE:  in future version, add option to allow Process to continue to provide input
                # FIX: USE clamp_input OPTION HERE, AND ADD HARD_CLAMP AND SOFT_CLAMP
                self.variable = convert_to_np_array(self.input, 2) * 0
            i += 1

    def _execute_learning(self, clock=CentralClock, context=None):
        # Execute each LearningMechanism as well as LearningProjections in self.learningExecutionList

        # FIRST, if targets were specified as a function, call the function now
        #    (i.e., after execution of the pathways, but before learning)
        # Note:  this accomodates functions that predicate the target on the outcome of processing
        #        (e.g., for rewards in reinforcement learning)
        if isinstance(self.targets, function_type):
            self.current_targets = self.targets()

        if self.current_targets is None:
           raise SystemError("No targets were specified in the call to execute {} with learning".format(self.name))

        for i, target_mech in zip(range(len(self.target_mechanisms)), self.target_mechanisms):
        # Assign each item of targets to the value of the targetInputState for the TARGET mechanism
        #    and zero the value of all ProcessInputStates that project to the TARGET mechanism
            self.target_input_states[i].value = self.current_targets[i]

        # NEXT, execute all components involved in learning
        if self.scheduler_learning is None:
            raise SystemError('System.py:_execute_learning - {0}\'s scheduler is None, must be initialized before execution'.format(self.name))
        logger.debug('{0}.scheduler learning termination conditions: {1}'.format(self, self.termination_learning))
        for next_execution_set in self.scheduler_learning.run(termination_conds=self.termination_learning):
            logger.debug('Running next_execution_set {0}'.format(next_execution_set))
            for component in next_execution_set:
                logger.debug('\tRunning component {0}'.format(component))

                from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
                if isinstance(component, MappingProjection):
                    continue

                params = None

                component_type = component.componentType

                processes = list(component.processes.keys())

                # Sort for consistency of reporting:
                process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                process_names = list(p.name for p in process_keys_sorted)

                context_str = str("{} | {}: {} [in processes: {}]".
                                  format(context,
                                         component_type,
                                         component.name,
                                         re.sub(r'[\[,\],\n]','',str(process_names))))

                # Note:  DON'T include input arg, as that will be resolved by mechanism from its sender projections
                component.execute(
                    clock=clock,
                    time_scale=self.timeScale,
                    runtime_params=params,
                    # time_scale=time_scale,
                    context=context_str
                )
                # # TEST PRINT:
                # print ("EXECUTING LEARNING UPDATES: ", component.name)

        # THEN update all MappingProjections
        for next_execution_set in self.scheduler_learning.run(termination_conds=self.termination_learning):
            logger.debug('Running next_execution_set {0}'.format(next_execution_set))
            for component in next_execution_set:
                logger.debug('\tRunning component {0}'.format(component))

                if isinstance(component, (LearningMechanism, ObjectiveMechanism)):
                    continue
                if not isinstance(component, MappingProjection):
                    raise SystemError("PROGRAM ERROR:  Attempted learning on non-MappingProjection")

                component_type = "mappingProjection"
                processes = list(component.sender.owner.processes.keys())


                # Sort for consistency of reporting:
                process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                process_names = list(p.name for p in process_keys_sorted)

                context_str = str("{} | {}: {} [in processes: {}]".
                                  format(context,
                                         component_type,
                                         component.name,
                                         re.sub(r'[\[,\],\n]','',str(process_names))))

                component._parameter_states[MATRIX].update(time_scale=TimeScale.TRIAL, context=context_str)

                # TEST PRINT:
                # print ("EXECUTING WEIGHT UPDATES: ", component.name)

        # FINALLY report outputs
        if self._report_system_output and self._report_process_output:
            # Report learning for target_mechanisms (and the processes to which they belong)
            # Sort for consistency of reporting:
            print("\n\'{}' learning completed:".format(self.name))

            for target_mech in self.target_mechanisms:
                processes = list(target_mech.processes.keys())
                process_keys_sorted = sorted(processes, key=lambda i : processes[processes.index(i)].name)
                process_names = list(p.name for p in process_keys_sorted)
                # print("\n\'- Target: {}' error: {} (processes: {})".
                print("- error for target ({}): {}".
                      # format(append_type_to_name(target_mech),
                      format(target_mech.name,
                             re.sub(r'[\[,\],\n]','',str([float("{:0.3}".format(float(i)))
                                                         for i in target_mech.output_state.value])),
                             ))
                             # process_names))

    def run(self,
            inputs,
            num_trials=None,
            reset_clock=True,
            initialize=False,
            targets=None,
            learning=None,
            call_before_trial=None,
            call_after_trial=None,
            call_before_time_step=None,
            call_after_time_step=None,
            clock=CentralClock,
            time_scale=None,
            termination_processing=None,
            termination_learning=None,
            context=None):
        """Run a sequence of executions

        Call execute method for each execution in a sequence specified by inputs.  See :doc:`Run` for details of
        formatting input specifications.

        Arguments
        ---------

        inputs : List[input] or ndarray(input) : default default_variable for a single execution
            the input for each in a sequence of executions (see :doc:`Run` for detailed description of formatting
            requirements and options).

        reset_clock : bool : default `True`
            if True, resets the :py:class:`CentralClock <TimeScale.CentralClock>` to 0 before a sequence of executions.

        initialize : bool default :keyword:`False`
            if `True`, calls the :py:meth:`initialize <System_Base.initialize>` method of the system before a
            sequence of executions.

        targets : List[input] or np.ndarray(input) : default `None`
            the target values for the LearningMechanisms of the system for each execution.
            The length (of the outermost level if a nested list, or lowest axis if an ndarray) must be equal to that
            of ``inputs``.

        learning : bool :  default `None`
            enables or disables learning during execution.
            If it is not specified, the current state is left intact.
            If it is `True`, learning is forced on; if it is :keyword:`False`, learning is forced off.

        call_before_trial : Function : default= `None`
            called before each trial in the sequence is executed.

        call_after_trial : Function : default= `None`
            called after each trial in the sequence is executed.

        call_before_time_step : Function : default= `None`
            called before each time_step of each trial is executed.

        call_after_time_step : Function : default= `None`
            called after each time_step of each trial is executed.

        time_scale : TimeScale :  default TimeScale.TRIAL
            specifies whether Mechanisms are executed for a single time step or a trial.

        Returns
        -------

        <system>.results : List[Mechanism.OutputValue]
            list of the OutputValue for each `TERMINAL` Mechanism of the system returned for each execution.

        """
        if self.scheduler_processing is None:
            self.scheduler_processing = Scheduler(system=self)

        if self.scheduler_learning is None:
            self.scheduler_learning = Scheduler(graph=self.learningExecutionGraph)

        logger.debug(inputs)

        from PsyNeuLink.Globals.Run import run
        return run(self,
                   inputs=inputs,
                   num_trials=num_trials,
                   reset_clock=reset_clock,
                   initialize=initialize,
                   targets=targets,
                   learning=learning,
                   call_before_trial=call_before_trial,
                   call_after_trial=call_after_trial,
                   call_before_time_step=call_before_time_step,
                   call_after_time_step=call_after_time_step,
                   time_scale=time_scale,
                   termination_processing=termination_processing,
                   termination_learning=termination_learning,
                   clock=clock,
                   context=context)

    def _report_system_initiation(self, clock=CentralClock):
        """Prints iniiation message, time_step, and list of processes in system being executed
        """

        if 'system' in self.name or 'System' in self.name:
            system_string = ''
        else:
            system_string = ' system'

        if clock.time_step == 0:
            print("\n\'{}\'{} executing with: **** (time_step {}) ".
                  format(self.name, system_string, clock.time_step))
            processes = list(process.name for process in self.processes)
            print("- processes: {}".format(processes))
            if np.size(self.input, 0) == 1:
                input_string = ''
            else:
                input_string = 's'
            print("- input{}: {}".format(input_string, self.input.tolist()))

        else:
            print("\n\'{}\'{} executing ********** (time_step {}) ".
                  format(self.name, system_string, clock.time_step))

    def _report_system_completion(self, clock=CentralClock):
        """Prints completion message and output_values of system
        """

        if 'system' in self.name or 'System' in self.name:
            system_string = ''
        else:
            system_string = ' system'

        # Print output value of primary (first) outputState of each terminal Mechanism in System
        # IMPLEMENTATION NOTE:  add options for what to print (primary, all or monitored outputStates)
        print("\n\'{}\'{} completed ***********(time_step {})".format(self.name, system_string, clock.time_step))
        # for object_item in self._terminal_mechs:
        #     if object_item.mechanism.phaseSpec == (clock.time_step % self.numPhases):
        #         print("- output for {0}: {1}".
        #               format(object_item.mechanism.name,
        #                      re.sub('[\[,\],\n]','',str(["{:0.3}".
        #                                         format(float(i)) for i in object_item.mechanism.output_state.value]))))
        if self.learning:
            from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.ObjectiveMechanisms.ComparatorMechanism \
                import MSE
            for mech in self.target_mechanisms:
                if not MSE in mech.output_states:
                    continue
                print("\n- MSE: {:0.3}".
                      format(float(mech.output_states[MSE].value)))


    # TBI:
    # class InspectOptions(AutoNumber):
    #     """Option value keywords for `inspect` and `show` methods.
    #     """
    #     ALL = ()
    #     """Show all values.
    #     """
    #     EXECUTION_SETS = ()
    #     """Show `execution_sets` attribute."""
    #     ExecutionList = ()
    #     """Show `executionList` attribute."""
    #     ATTRIBUTES = ()
    #     """Show system's attributes."""
    #     ALL_OUTPUTS = ()
    #     """"""
    #     ALL_OUTPUT_LABELS = ()
    #     """"""
    #     PRIMARY_OUTPUTS = ()
    #     """"""
    #     PRIMARY_OUTPUT_LABELS = ()
    #     """"""
    #     MONITORED_OUTPUTS = ()
    #     """"""
    #     MONITORED_OUTPUT_LABELS = ()
    #     """"""
    #     FLAT_OUTPUT = ()
    #     """"""
    #     DICT_OUTPUT = ()
    #     """"""

    def show(self, options=None):
        """Print ``execution_sets``, ``executionList``, `ORIGIN`, `TERMINAL` Mechanisms,
        `TARGET` Mechanisms, ``outputs`` and their labels for the System.

        Arguments
        ---------

        options : InspectionOptions
            [TBI]
        """

        # # IMPLEMENTATION NOTE:  Stub for implementing options:
        # if options and self.InspectOptions.ALL_OUTPUT_LABELS in options:
        #     pass

        print ("\n---------------------------------------------------------")
        print ("\n{0}".format(self.name))


        print ("\n\tControl enabled: {0}".format(self.enable_controller))
        print ("\n\tProcesses:")

        for process in self.processes:
            print ("\t\t{} [learning enabled: {}]".format(process.name, process._learning_enabled))


        # Print execution_sets (output of toposort)
        print ("\n\tExecution sets: ".format(self.name))
        # Sort for consistency of output
        execution_sets_sorted = sorted(self.execution_sets)
        for i in range(len(execution_sets_sorted)):
        # for i in range(len(self.execution_sets)):
            print ("\t\tSet {0}:\n\t\t\t".format(i),end='')
            print("{ ",end='')
            sorted_mechs_names_in_set = sorted(list(object_item.name
                                                    for object_item in self.execution_sets[i]))
            for name in sorted_mechs_names_in_set:
                print("{0} ".format(name), end='')
            print("}")

        # Print executionList sorted by phase and including EVC mechanism

        # Sort executionList by phase
        sorted_execution_list = self.executionList.copy()


        # Sort by phaseSpec and, within each phase, by mechanism name
#        sorted_execution_list.sort(key=lambda object_item: object_item.phase)


        # Add controller to execution list for printing if enabled
        if self.enable_controller:
            sorted_execution_list.append(self.controller)


        mech_names_from_exec_list = list(object_item.name for object_item in self.executionList)
        mech_names_from_sorted_exec_list = list(object_item.name for object_item in sorted_execution_list)

        # print ("\n\tExecution list: ".format(self.name))
        # phase = 0
        # print("\t\tPhase {}:".format(phase))
        # for object_item in sorted_execution_list:
        #     if object_item.phase != phase:
        #         phase = object_item.phase
        #         print("\t\tPhase {}:".format(phase))
        #     print ("\t\t\t{}".format(object_item.mechanism.name))
        #
        # print ("\n\tOrigin mechanisms: ".format(self.name))
        # for object_item in self.origin_mechanisms.mechs_sorted:
        #     print("\t\t{0} (phase: {1})".format(object_item.mechanism.name, object_item.phase))
        #
        # print ("\n\tTerminal mechanisms: ".format(self.name))
        # for object_item in self.terminalMechanisms.mechs_sorted:
        #     print("\t\t{0} (phase: {1})".format(object_item.mechanism.name, object_item.phase))
        #     for output_state in object_item.mechanism.output_states:
        #         print("\t\t\t{0}".format(output_state.name))
        #
        # # if any(process.learning for process in self.processes):
        # if self.learning:
        #     print ("\n\tTarget mechanisms: ".format(self.name))
        #     for object_item in self.target_mechanisms.mechs:
        #         print("\t\t{0} (phase: {1})".format(object_item.mechanism.name, object_item.phase))
        #
        # print ("\n---------------------------------------------------------")


    def inspect(self):
        """Return dictionary with system attributes and values

        Diciontary contains entries for the following attributes and values:

            PROCESSES: list of `Processes <Process>` in system

            MECHANISMS: list of all `Mechanisms <Mechanism>` in the system

            ORIGIN_MECHANISMS: list of `ORIGIN` Mechanisms

            INPUT_ARRAY: ndarray of the inputs to the `ORIGIN` Mechanisms

            RECURRENT_MECHANISMS:  list of `INITALIZE_CYCLE` Mechanisms

            RECURRENT_INIT_ARRAY: ndarray of initial_values

            TERMINAL_MECHANISMS: list of `TERMINAL` Mechanisms

            OUTPUT_STATE_NAMES: list of `OutputState` names corresponding to 1D arrays in output_value_array

            OUTPUT_VALUE_ARRAY: 3D ndarray of 2D arrays of output.value arrays of OutputStates for all `TERMINAL`
            Mechanisms

            NUM_PHASES_PER_TRIAL: number of phases required to execute all Mechanisms in the system

            LEARNING_MECHANISMS: list of `LearningMechanisms <LearningMechanism>`

            TARGET: list of `TARGET` Mechanisms

            LEARNING_PROJECTION_RECEIVERS: list of `MappingProjections <MappingProjection>` that receive learning
            projections

            CONTROL_MECHANISMS: list of `ControlMechanisms <ControlMechanism>`

            CONTROL_PROJECTION_RECEIVERS: list of `ParameterStates <ParameterState>` that receive learning projections

        Returns
        -------
        Dictionary of System attributes and values : dict

        """

        input_array = []
        for mech in list(self.origin_mechanisms.mechanisms):
            input_array.append(mech.value)
        input_array = np.array(input_array)

        recurrent_init_array = []
        for mech in list(self.recurrent_init_mechanisms.mechanisms):
            recurrent_init_array.append(mech.value)
        recurrent_init_array = np.array(recurrent_init_array)

        output_state_names = []
        output_value_array = []
        for mech in list(self.terminalMechanisms.mechanisms):
            output_value_array.append(mech.output_values)
            for name in mech.output_states:
                output_state_names.append(name)
        output_value_array = np.array(output_value_array)

        from PsyNeuLink.Components.Projections.ModulatoryProjections.ControlProjection import ControlProjection
        from PsyNeuLink.Components.Projections.ModulatoryProjections.LearningProjection import LearningProjection
        learning_projections = []
        controlled_parameters = []
        for mech in list(self.mechanisms):
            for parameter_state in mech._parameter_states:
                try:
                    for projection in parameter_state.mod_afferents:
                        if isinstance(projection, ControlProjection):
                            controlled_parameters.append(parameter_state)
                except AttributeError:
                    pass
            for output_state in mech.output_states:
                try:
                    for projection in output_state.efferents:
                        for parameter_state in projection.paramaterStates:
                            for sender in parameter_state.mod_afferents:
                                if isinstance(sender, LearningProjection):
                                    learning_projections.append(projection)
                except AttributeError:
                    pass

        inspect_dict = {
            PROCESSES: self.processes,
            MECHANISMS: self.mechanisms,
            ORIGIN_MECHANISMS: self.origin_mechanisms.mechanisms,
            INPUT_ARRAY: input_array,
            RECURRENT_MECHANISMS: self.recurrent_init_mechanisms,
            RECURRENT_INIT_ARRAY: recurrent_init_array,
            TERMINAL_MECHANISMS: self.terminalMechanisms.mechanisms,
            OUTPUT_STATE_NAMES: output_state_names,
            OUTPUT_VALUE_ARRAY: output_value_array,
            NUM_PHASES_PER_TRIAL: self.numPhases,
            LEARNING_MECHANISMS: self.learning_mechanisms,
            TARGET_MECHANISMS: self.target_mechanisms,
            LEARNING_PROJECTION_RECEIVERS: learning_projections,
            CONTROL_MECHANISMS: self.control_mechanism,
            CONTROL_PROJECTION_RECEIVERS: controlled_parameters,
        }

        return inspect_dict

    def _toposort_with_ordered_mechs(self, data):
        """Returns a single list of dependencies, sorted by object_item[MECHANISM].name"""
        result = []
        for dependency_set in toposort(data):
            d_iter = iter(dependency_set)
            result.extend(sorted(dependency_set, key=lambda item : next(d_iter).name))
        return result

    def _cache_state(self):

        # http://stackoverflow.com/questions/11218477/how-can-i-use-pickle-to-save-a-dict
        # import pickle
        #
        # a = {'hello': 'world'}
        #
        # with open('filename.pickle', 'wb') as handle:
        #     pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)
        #
        # with open('filename.pickle', 'rb') as handle:
        #     b = pickle.load(handle)
        #
        # print a == b

        # >>> import dill
        # >>> pik = dill.dumps(d)

        # import pickle
        # with open('cached_PNL_sys.pickle', 'wb') as handle:
        #     pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # import dill
        # self.cached_system = dill.dumps(self, recurse=True)

        # def mechanisms_cache:
        #     self.input_value = []
        #     self.value= []
        #     self.output_value = []
        #
        # for mech in self.mechanisms:
        #     for
        pass

    def _restore_state(self):
        pass

    @property
    def mechanisms(self):
        """List of all mechanisms in the system

        Returns
        -------
        all mechanisms in the system : List[mechanism]

        """
        return self._allMechanisms.mechanisms

    # # MODIFIED 11/1/16 NEW:
    # @property
    # def processes(self):
    #     return sorted(self._processList.processes)

    # @property
    # def input_value(self):
    #     """Value of input to system
    #
    #     Returns
    #     -------
    #     value of input to system : ndarray
    #     """
    #     return self.variable

    @property
    def numPhases(self):
        """Number of phases required to execute all ProcessingMechanisms in the system

        Equals maximum phase value of ProcessingMechanisms in the system + 1

        Returns
        -------
        number of phases in system : int

        """
        return self._phaseSpecMax + 1

    # @property
    # def execution_graph_mechs(self):
    #     """Mechanisms whose mechs appear as keys in self.executionGraph
    #
    #     :rtype: list of Mechanism objects
    #     """
    #     return self.executionGraph

    def show_graph(self,
                   direction = 'BT',
                   show_learning = False,
                   show_control = False,
                   learning_color = 'green',
                   control_color='blue',
                   output_fmt='pdf',
                   ):
        """Generate a display of the graph structure of mechanisms and projections in the system.

        By default, only the `ProcessingMechanisms <ProcessingMechanism>` and `MappingProjections <MappingProjection>`
        in the `System's graph <System.graph>` are displayed.  However, the **show_learning** and
        **show_control** arguments can be used to also show the `learning <LearningMechanism>` and
        `control <ControlMechanism>` components of the system, respectively.  `Mechanisms <Mechanism>` are always
        displayed as (oval) nodes.  `Projections <Projection>` are displayed as labelled arrows, unless
        **show_learning** is assigned **True**, in which case MappingProjections that receive a `LearningProjection`
        are displayed as diamond-shaped nodes. The numbers in parentheses within a Mechanism node indicate its
        dimensionality.

        Arguments
        ---------

        direction : keyword : default 'BT'
            'BT': bottom to top; 'TB': top to bottom; 'LR': left to right; and 'RL`: right to left.

        show_learning : bool : default False
            determines whether or not to show the learning components of the system;
            they will all be displayed in the color specified for **learning_color**.
            Projections that receive a `LearningProjection` will be shown as a diamond-shaped node.

        show_control :  bool : default False
            determines whether or not to show the control components of the system;
            they will all be displayed in the color specified for **control_color**.

        learning_color : keyword : default `green`
            determines the color in which the learning components are displayed

        control_color : keyword : default `blue`
            determines the color in which the learning components are displayed (note: if the System's
            `controller <System.controller>`) is an `EVCMechanism`, then a link is shown in red from the
            `prediction Mechanisms <EVCMechanism_Prediction_Mechanisms>` it creates to the corresponding
            `ORIGIN` Mechanisms of the System, to indicate that although no projection are created for these,
            the prediction Mechanisms determine the input to the `ORIGIN` Mechanisms when the EVCMechanism
            `simulates execution <EVCMechanism_Execution>` of the System.

        output_fmt : keyword : default 'pdf'
            'pdf': generate and open a pdf with the visualization;
            'jupyter': return the object (ideal for working in jupyter/ipython notebooks).


        Returns
        -------

        display of system : `pdf` or Graphviz graph object
            'pdf' (placed in current directory) if :keyword:`output_fmt` arg is 'pdf';
            Graphviz graph object if :keyword:`output_fmt` arg is 'jupyter'.

        """

        from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.ObjectiveMechanisms.ObjectiveMechanism import ObjectiveMechanism
        from PsyNeuLink.Components.Mechanisms.AdaptiveMechanisms.LearningMechanisms.LearningMechanism import LearningMechanism
        from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection

        import graphviz as gv

        system_graph = self.graph
        learning_graph=self.learningGraph

        # build graph and configure visualisation settings
        G = gv.Digraph(engine = "dot",
                       node_attr  = {'fontsize':'12', 'fontname': 'arial', 'shape':'oval'},
                       edge_attr  = {'arrowhead':'halfopen', 'fontsize': '10', 'fontname': 'arial'},
                       graph_attr = {"rankdir" : direction} )


        # work with system graph
        rcvrs = list(system_graph.keys())
        # loop through receivers
        for rcvr in rcvrs:
            # rcvr_name = rcvr[0].name
            # rcvr_shape = rcvr[0].variable.shape[1]
            rcvr_name = rcvr.name
            rcvr_shape = rcvr.variable.shape[1]
            rcvr_label = rcvr_name


            # loop through senders
            sndrs = system_graph[rcvr]
            for sndr in sndrs:
                sndr_name = sndr.name
                sndr_shape = sndr.variable.shape[1]
                sndr_label = sndr_name

                # find edge name
                projs = sndr.output_state.efferents
                for proj in projs:
                    if proj.receiver.owner == rcvr:
                        edge_name = proj.name
                        # edge_shape = proj.matrix.shape
                        try:
                            has_learning = proj.has_learning_projection
                        except AttributeError:
                            has_learning = None
                edge_label = edge_name
                #### CHANGE MADE HERE ###
                # if rcvr is learning mechanism, draw arrow with learning color
                if isinstance(rcvr, LearningMechanism) or isinstance(rcvr, ObjectiveMechanism):
                    break
                else:
                    arrow_color="black"
                if show_learning and has_learning:
                    # expand
                    G.node(sndr_label, shape="oval")
                    G.node(edge_label, shape="diamond")
                    G.node(rcvr_label, shape="oval")
                    G.edge(sndr_label, edge_label, arrowhead='none')
                    G.edge(edge_label, rcvr_label)
                else:
                    # render normally
                    G.edge(sndr_label, rcvr_label, label = edge_label, color=arrow_color)

        # add learning graph if show_learning
        if show_learning:
            rcvrs = list(learning_graph.keys())
            for rcvr in rcvrs:
                # if rcvr is projection
                if isinstance(rcvr, MappingProjection):
                    # for each sndr of rcvr
                    sndrs = learning_graph[rcvr]
                    for sndr in sndrs:
                        edge_label = rcvr._parameter_states['matrix'].mod_afferents[0].name
                        G.edge(sndr.name, rcvr.name, color=learning_color, label = edge_label)
                else:
                    sndrs = list(learning_graph[rcvr])
                    for sndr in sndrs:
                        projs = sndr.input_state.path_afferents

                        for proj in projs:
                            edge_name=proj.name
                        G.node(rcvr.name, color=learning_color)
                        G.node(sndr.name, color=learning_color)
                        G.edge(sndr.name, rcvr.name, color=learning_color, label=edge_name)


        # add control graph if show_control
        if show_control:
            controller = self.controller

            connector = controller.input_state.path_afferents[0]
            objmech = connector.sender.owner

            # main edge
            G.node(controller.name, color=control_color)
            G.node(objmech.name, color=control_color)
            G.edge(objmech.name, controller.name, label=connector.name, color=control_color)

            # outgoing edges
            for output_state in controller.control_signals:
                for projection in output_state.efferents:
                    edge_name
                    rcvr_name = projection.receiver.owner.name
                    G.edge(controller.name, rcvr_name, label=projection.name, color=control_color)

            # incoming edges
            for istate in objmech.input_states:
                for proj in istate.path_afferents:
                    sndr_name = proj.sender.owner.name
                    G.edge(sndr_name, objmech.name, label=proj.name, color=control_color)

            # prediction mechanisms
            for object_item in self.executionList:
                mech = object_item[0]
                if mech._role is CONTROL:
                    G.node(mech.name, color=control_color)
                    recvr = mech.origin_mech
                    G.edge(mech.name, recvr.name, label=' prediction assignment', color='red')
                    pass

        # return
        if   output_fmt == 'pdf':
            G.view(self.name.replace(" ", "-"), cleanup=True)
        elif output_fmt == 'jupyter':
            return G


SYSTEM_TARGET_INPUT_STATE = 'SystemInputState'

from PsyNeuLink.Components.States.OutputState import OutputState
class SystemInputState(OutputState):
    """Encodes target for the system and transmits it to a `TARGET` mechanism in the system

    Each instance encodes a `target <System.target>` to the system (also a 1d array in 2d array of
    `targets <System.targets>`) and provides it to a `MappingProjection` that projects to a `TARGET`
    mechanism of the system.

    .. Declared as a subclass of OutputState so that it is recognized as a legitimate sender to a Projection
       in Projection._instantiate_sender()

       self.value is used to represent the item of the targets arg to system.execute or system.run

    """
    def __init__(self, owner=None, variable=None, name=None, prefs=None):
        """Pass variable to MappingProjection from Process to first Mechanism in Pathway

        :param variable:
        """
        if not name:
            self.name = owner.name + "_" + SYSTEM_TARGET_INPUT_STATE
        else:
            self.name = owner.name + "_" + name
        self.prefs = prefs
        self.efferents = []
        self.owner = owner
        self.value = variable
