import numpy as np
import pytest

from PsyNeuLink.Components.Mechanisms.Mechanism import MechanismError
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.IntegratorMechanism import IntegratorMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection

from PsyNeuLink.Components.Functions.Function import AccumulatorIntegrator, ConstantIntegrator, Linear, SimpleIntegrator
from PsyNeuLink.Components.Functions.Function import AdaptiveIntegrator, DriftDiffusionIntegrator, OrnsteinUhlenbeckIntegrator
from PsyNeuLink.Components.Functions.Function import FunctionError
from PsyNeuLink.Components.Process import process
from PsyNeuLink.Globals.Keywords import EXECUTING
from PsyNeuLink.Scheduling.TimeScale import TimeScale

# ======================================= FUNCTION TESTS ============================================

# VALID FUNCTIONS:

# ------------------------------------------------------------------------------------------------
# TEST 1
# integration_type = simple


def test_integrator_simple():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=SimpleIntegrator(
        ),
        time_scale=TimeScale.TIME_STEP
    )
#     # P = process(pathway=[I])

    #  returns previous_value + rate*variable + noise
    # so in this case, returns 10.0
    val = float(I.execute(10))

    # testing initializer
    I.function_object.reset_initializer = 5.0

    val2 = float(I.execute(0))

    assert [val, val2] == [10.0, 5.0]

# ------------------------------------------------------------------------------------------------
# TEST 2
# integration_type = adaptive


def test_integrator_adaptive():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=AdaptiveIntegrator(
            rate=0.5
        ),
        time_scale=TimeScale.TIME_STEP
    )
    # val = float(I.execute(10)[0])
    # P = process(pathway=[I])
    val = float(I.execute(10))
    # returns (rate)*variable + (1-rate*previous_value) + noise
    # rate = 1, noise = 0, so in this case, returns 10.0

    # testing initializer
    I.function_object.reset_initializer = 1.0
    val2 = float(I.execute(1))

    assert [val, val2] == [5.0, 1.0]
# ------------------------------------------------------------------------------------------------
# TEST 3
# integration_type = constant


def test_integrator_constant():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function= ConstantIntegrator(
            rate = 1.0
        ),
        time_scale=TimeScale.TIME_STEP
    )
    # val = float(I.execute(10)[0])
    # P = process(pathway=[I])
    val = float(I.execute())
    # returns previous_value + rate + noise
    # rate = 1.0, noise = 0, so in this case returns 1.0

    # testing initializer
    I.function_object.reset_initializer = 10.0
    val2 = float(I.execute())

    assert [val, val2] == [1.0, 11.0]
# ------------------------------------------------------------------------------------------------
# TEST 4
# integration_type = diffusion


def test_integrator_diffusion():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function= DriftDiffusionIntegrator(
        ),
        time_scale=TimeScale.TIME_STEP
    )
    # val = float(I.execute(10)[0])
    # P = process(pathway=[I])
    val = float(I.execute(10))

    # testing initializer
    I.function_object.reset_initializer = 1.0
    val2 = float(I.execute(0))

    assert [val, val2] == [10.0, 1.0]

# ------------------------------------------------------------------------------------------------

# INVALID FUNCTIONS:

# ------------------------------------------------------------------------------------------------
# TEST 1
# function = Linear


# def test_integrator_linear():

#     # SHOULD CAUSE AN ERROR??

#     with pytest.raises(FunctionError) as error_text:
#         I = IntegratorMechanism(
#             name='IntegratorMechanism',
#             function=Linear(),
#             time_scale=TimeScale.TIME_STEP
#         )
#         # val = float(I.execute(10)[0])
# #         P = process(pathway=[I])
#         val = float(I.execute(10))
#     assert val == 10


# ======================================= INPUT TESTS ============================================

# VALID INPUT:

# ------------------------------------------------------------------------------------------------
# TEST 1
# input = float

def test_integrator_input_float():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=SimpleIntegrator(
        )
    )
    # P = process(pathway=[I])
    val = float(I.execute(10.0))
    assert val == 10.0

# ------------------------------------------------------------------------------------------------
# TEST 2
# input = list of length 1


def test_integrator_input_list():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=SimpleIntegrator(
        )
    )
    # P = process(pathway=[I])
    val = float(I.execute([10.0]))
    assert val == 10.0

# ------------------------------------------------------------------------------------------------
# TEST 3
# input = list of length 5


def test_integrator_input_list_len_5():

    I = IntegratorMechanism(
        name='IntegratorMechanism',
        default_variable=[0, 0, 0, 0, 0],
        function=SimpleIntegrator(
        )
    )
    # P = process(pathway=[I])
    val = I.execute([10.0, 5.0, 2.0, 1.0, 0.0])[0]
    expected_output = [10.0, 5.0, 2.0, 1.0, 0.0]

    for i in range(len(expected_output)):
        v = val[i]
        e = expected_output[i]
        np.testing.assert_allclose(v, e, atol=1e-08, err_msg='Failed on expected_output[{0}]'.format(i))

# ------------------------------------------------------------------------------------------------
# TEST 4
# input = numpy array of length 5


def test_integrator_input_array_len_5():

    I = IntegratorMechanism(
        name='IntegratorMechanism',
        default_variable=[0, 0, 0, 0, 0],
        function=SimpleIntegrator(
        )
    )
    # P = process(pathway=[I])
    input_array = np.array([10.0, 5.0, 2.0, 1.0, 0.0])
    val = I.execute(input_array)[0]
    expected_output = [10.0, 5.0, 2.0, 1.0, 0.0]

    for i in range(len(expected_output)):
        v = val[i]
        e = expected_output[i]
        np.testing.assert_allclose(v, e, atol=1e-08, err_msg='Failed on expected_output[{0}]'.format(i))

# ------------------------------------------------------------------------------------------------

# INVALID INPUT:

# ------------------------------------------------------------------------------------------------
# TEST 1
# input = list of length > default length


def test_integrator_input_array_greater_than_default():

    with pytest.raises(MechanismError) as error_text:
        I = IntegratorMechanism(
            name='IntegratorMechanism',
            default_variable=[0, 0, 0]
        )
        # P = process(pathway=[I])
        I.execute([10.0, 5.0, 2.0, 1.0, 0.0])
    assert "does not match required length" in str(error_text)

# ------------------------------------------------------------------------------------------------
# TEST 2
# input = list of length < default length


def test_integrator_input_array_less_than_default():

    with pytest.raises(MechanismError) as error_text:
        I = IntegratorMechanism(
            name='IntegratorMechanism',
            default_variable=[0, 0, 0, 0, 0]
        )
        # P = process(pathway=[I])
        I.execute([10.0, 5.0, 2.0])
    assert "does not match required length" in str(error_text)

# ======================================= RATE TESTS ============================================

# VALID RATE:

# ------------------------------------------------------------------------------------------------
# TEST 1
# rate = float, integration_type = simple


def test_integrator_type_simple_rate_float():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=SimpleIntegrator(
            rate=5.0
        )
    )
    # P = process(pathway=[I])
    val = float(I.execute(10.0))
    assert val == 50.0

# ------------------------------------------------------------------------------------------------
# TEST 2
# rate = float, integration_type = constant


def test_integrator_type_constant_rate_float():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function= ConstantIntegrator(
            rate=5.0
        )
    )
    # P = process(pathway=[I])
    val = float(I.execute(10.0))
    assert val == 5.0

# ------------------------------------------------------------------------------------------------
# TEST 3
# rate = float, integration_type = diffusion


def test_integrator_type_diffusion_rate_float():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function = DriftDiffusionIntegrator(
            rate=5.0
        )
    )
    # P = process(pathway=[I])
    val = float(I.execute(10.0))
    assert val == 50.0

# ------------------------------------------------------------------------------------------------
# TEST 4
# rate = list, integration_type = simple


def test_integrator_type_simple_rate_list():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        default_variable=[0, 0, 0],
        function=SimpleIntegrator(
            rate=[5.0, 5.0, 5.0]
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute([10.0, 10.0, 10.0])[0])
    assert val == [50.0, 50.0, 50.0]
# ------------------------------------------------------------------------------------------------
# TEST 5
# rate = list, integration_type = constant


def test_integrator_type_constant_rate_list():
    I = IntegratorMechanism(
        default_variable=[0, 0, 0],
        name='IntegratorMechanism',
        function= ConstantIntegrator(
            rate=[5.0, 5.0, 5.0]
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute([10.0, 10.0, 10.0])[0])
    assert val == [5.0, 5.0, 5.0]

# ------------------------------------------------------------------------------------------------
# TEST 6
# rate = list, integration_type = diffusion


def test_integrator_type_diffusion_rate_list():
    I = IntegratorMechanism(
        default_variable=[0, 0, 0],
        name='IntegratorMechanism',
        function = DriftDiffusionIntegrator(
            rate=[5.0, 5.0, 5.0]
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute([10.0, 10.0, 10.0])[0])
    assert val == [50.0, 50.0, 50.0]

# ------------------------------------------------------------------------------------------------
# TEST 7
# rate = list, integration_type = diffusion


def test_integrator_type_adaptive_rate_list():
    I = IntegratorMechanism(
        default_variable=[0, 0, 0],
        name='IntegratorMechanism',
        function=AdaptiveIntegrator(
            rate=[0.5, 0.5, 0.5]
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute([10.0, 10.0, 10.0])[0])
    assert val == [5.0, 5.0, 5.0]

# ------------------------------------------------------------------------------------------------
# TEST 8
# rate = float, integration_type = adaptive


def test_integrator_type_adaptive_rate_float_input_list():
    I = IntegratorMechanism(
        default_variable=[0, 0, 0],
        name='IntegratorMechanism',
        function=AdaptiveIntegrator(
            rate=0.5
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute([10.0, 10.0, 10.0])[0])
    assert val == [5.0, 5.0, 5.0]

# ------------------------------------------------------------------------------------------------
# TEST 9
# rate = float, integration_type = adaptive


def test_integrator_type_adaptive_rate_float():
    I = IntegratorMechanism(
        name='IntegratorMechanism',
        function=AdaptiveIntegrator(
            rate=0.5
        )
    )
    # P = process(pathway=[I])
    val = list(I.execute(10.0))
    assert val == [5.0]

# ------------------------------------------------------------------------------------------------

# INVALID INPUT:

# ------------------------------------------------------------------------------------------------
# TEST 1
# rate = list of length > default length
# integration_type = SIMPLE


def test_integrator_type_simple_rate_list_input_float():
    with pytest.raises(FunctionError) as error_text:
        I = IntegratorMechanism(
            name='IntegratorMechanism',
            function=SimpleIntegrator(

                rate=[5.0, 5.0, 5.0]
            )
        )
        # P = process(pathway=[I])
        float(I.execute(10.0))
    assert (
        "array specified for the rate parameter" in str(error_text)
        and "must match the length" in str(error_text)
        and "of the default input" in str(error_text)
    )
# ------------------------------------------------------------------------------------------------
# TEST 2
# rate = list of length > default length
# integration_type = CONSTANT


def test_integrator_type_constant_rate_list_input_float():
    with pytest.raises(FunctionError) as error_text:
        I = IntegratorMechanism(
            name='IntegratorMechanism',
            function=ConstantIntegrator(
                rate=[5.0, 5.0, 5.0]
            )
        )
        # P = process(pathway=[I])
        float(I.execute(10.0))
    assert (
        "array specified for the rate parameter" in str(error_text)
        and "must match the length" in str(error_text)
        and "of the default input" in str(error_text)
    )

# ------------------------------------------------------------------------------------------------
# TEST 3
# rate = list of length > default length
# integration_type = DIFFUSION


def test_integrator_type_diffusion_rate_list_input_float():
    with pytest.raises(FunctionError) as error_text:
        I = IntegratorMechanism(
            name='IntegratorMechanism',
            function=DriftDiffusionIntegrator(
                rate=[5.0, 5.0, 5.0]
            )
        )
        # P = process(pathway=[I])
        float(I.execute(10.0))
    assert (
        "array specified for the rate parameter" in str(error_text)
        and "must match the length" in str(error_text)
        and "of the default input" in str(error_text)
    )


## NEW INTEGRATOR FUNCTIONS ------------------------------------


# ------------------------------------------------------------------------------------------------
# TEST 1

def test_simple_integrator():
    I = IntegratorMechanism(
            function = SimpleIntegrator(
                initializer = 10.0,
                rate = 5.0,
                offset = 10,
            )
        )
    # P = process(pathway=[I])
    val = I.execute(1)
    assert val == 25


# ------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------
# TEST 2

def test_constant_integrator():
    I = IntegratorMechanism(
            function = ConstantIntegrator(
                initializer = 10.0,
                rate = 5.0,
                offset = 10
            )
        )
    # P = process(pathway=[I])
    # constant integrator does not use input value (self.variable)

    # step 1:
    val = I.execute(20000)
    # value = 10 + 5
    # adjusted_value = 15 + 10
    # previous_value = 25
    # RETURN 25

    # step 2:
    val2 = I.execute(70000)
    # value = 25 + 5
    # adjusted_value = 30 + 10
    # previous_value = 30
    # RETURN 40
    assert (val, val2) == (25, 40)


# ------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# TEST 3

def test_adaptive_integrator():
    I = IntegratorMechanism(
            function = AdaptiveIntegrator(
                initializer = 10.0,
                rate = 0.5,
                offset = 10,
            )
        )
    # P = process(pathway=[I])
    # 10*0.5 + 1*0.5 + 10
    val = I.execute(1)
    assert val == 15.5


# ------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------
# TEST 4

def test_drift_diffusion_integrator():
    I = IntegratorMechanism(
            function = DriftDiffusionIntegrator(
                initializer = 10.0,
                rate = 10,
                time_step_size = 0.5,
                offset=10,
            )
        )
    # P = process(pathway=[I])
    # 10 + 10*0.5 + 0 + 10 = 25
    val = I.execute(1)
    assert val == 25


# ------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# TEST 5

def test_ornstein_uhlenbeck_integrator():
    I = IntegratorMechanism(
            function = OrnsteinUhlenbeckIntegrator(
                initializer = 10.0,
                rate = 10,
                time_step_size=0.5,
                decay = 0.1,
                offset=10,
            )
        )
    # P = process(pathway=[I])
    # value = previous_value + decay * rate * new_value * time_step_size + np.sqrt(
            #time_step_size * noise) * np.random.normal()
    # step 1:
    val = I.execute(1)
    # value = 10 + 0.1*10*1*0.5 + 0
    # adjusted_value = 10.5 + 10
    # previous_value = 20.5
    # RETURN 20.5

    # step 2:
    val2 = I.execute(1)
    # value = 20.5 + 0.1*10*1*0.5 + 0
    # adjusted_value = 21 + 10
    # previous_value = 31
    # RETURN 31

    # step 3:
    val3 = I.execute(1)
    # value = 31 + 0.1*10*1*0.5 + 0
    # adjusted_value = 31.5 + 10
    # previous_value = 41.5
    # RETURN 41.5

    assert (val, val2, val3) == (20.5, 31, 41.5)
# ------------------------------------------------------------------------------------------------
# Test 6
# ------------------------------------------------------------------------------------------------
def test_integrator_no_function():
    I = IntegratorMechanism(time_scale=TimeScale.TIME_STEP)
    # P = process(pathway=[I])
    val = float(I.execute(10))
    assert val == 5


# # ------------------------------------------------------------------------------------------------
# # Test 7
# # ------------------------------------------------------------------------------------------------
# #
# def test_accumulator_integrator():
#     I = IntegratorMechanism(
#             function = AccumulatorIntegrator(
#                 initializer = 10.0,
#                 rate = 5.0,
#                 increment= 1.0
#             )
#         )
# #     P = process(pathway=[I])

#     # value = previous_value * rate + noise + increment
#     # step 1:
#     val = I.execute()
#     # value = 10.0 * 5.0 + 0 + 1.0
#     # RETURN 51

#     # step 2:
#     val2 = I.execute(2000)
#     # value = 51*5 + 0 + 1.0
#     # RETURN 256
#     assert (val, val2) == (51, 256)

def test_mechanisms_without_system_or_process():
    I = IntegratorMechanism(
            name='IntegratorMechanism',
            function=SimpleIntegrator(
            ),
            time_scale=TimeScale.TIME_STEP
        )
    T = TransferMechanism(function=Linear(slope=2.0, intercept=5.0))
    M = MappingProjection(sender=I, receiver=T)

    res1 = float(I.execute(10, context=EXECUTING))
    res2 = float(T.execute(context=EXECUTING))
    assert (res1, res2) == (10,25)

def test_mechanisms_without_system_or_process_no_input():
    I = IntegratorMechanism(
            name='IntegratorMechanism',
            default_variable= 10,
            function=SimpleIntegrator(
            ),
            time_scale=TimeScale.TIME_STEP
        )
    T = TransferMechanism(function=Linear(slope=2.0, intercept=5.0))
    M = MappingProjection(sender=I, receiver=T)

    res1 = float(I.execute(context=EXECUTING))
    res2 = float(T.execute(context=EXECUTING))
    assert (res1, res2) == (10, 25)