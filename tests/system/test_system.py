import numpy as np

from PsyNeuLink.Components.Functions.Function import BogaczEtAl, Linear, Logistic
from PsyNeuLink.Components.Mechanisms.AdaptiveMechanisms.ControlMechanisms.EVCMechanism import EVCMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.DDM import DDM
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Process import process
from PsyNeuLink.Components.Projections.ModulatoryProjections.ControlProjection import ControlProjection
from PsyNeuLink.Components.System import system
from PsyNeuLink.Composition import MechanismRole
from PsyNeuLink.Globals.Keywords import ALLOCATION_SAMPLES
from PsyNeuLink.Globals.Keywords import CYCLE, INITIALIZE_CYCLE, INTERNAL, ORIGIN, TERMINAL


def test_danglingControlledMech():
    #
    #   first section is from Stroop Demo
    #
    Color_Input = TransferMechanism(name='Color Input', function=Linear(slope=0.2995))
    Word_Input = TransferMechanism(name='Word Input', function=Linear(slope=0.2995))

    # Processing Mechanisms (Control)
    Color_Hidden = TransferMechanism(
        name='Colors Hidden',
        function=Logistic(gain=(1.0, ControlProjection)),
    )
    Word_Hidden = TransferMechanism(
        name='Words Hidden',
        function=Logistic(gain=(1.0, ControlProjection)),
    )
    Output = TransferMechanism(
        name='Output',
        function=Logistic(gain=(1.0, ControlProjection)),
    )

    # Decision Mechanisms
    Decision = DDM(
        function=BogaczEtAl(
            drift_rate=(1.0),
            threshold=(0.1654),
            noise=(0.5),
            starting_point=(0),
            t0=0.25,
        ),
        name='Decision',
    )
    # Outcome Mechanisms:
    Reward = TransferMechanism(name='Reward')

    # Processes:
    ColorNamingProcess = process(
        default_variable=[0],
        pathway=[Color_Input, Color_Hidden, Output, Decision],
        name='Color Naming Process',
    )

    WordReadingProcess = process(
        default_variable=[0],
        pathway=[Word_Input, Word_Hidden, Output, Decision],
        name='Word Reading Process',
    )

    RewardProcess = process(
        default_variable=[0],
        pathway=[Reward],
        name='RewardProcess',
    )

    # add another DDM but do not add to system
    second_DDM = DDM(
        function=BogaczEtAl(
            drift_rate=(
                1.0,
                ControlProjection(
                    function=Linear,
                    control_signal_params={
                        ALLOCATION_SAMPLES: np.arange(0.1, 1.01, 0.3)
                    },
                ),
            ),
            threshold=(
                1.0,
                ControlProjection(
                    function=Linear,
                    control_signal_params={
                        ALLOCATION_SAMPLES: np.arange(0.1, 1.01, 0.3)
                    },
                ),
            ),
            noise=(0.5),
            starting_point=(0),
            t0=0.45
        ),
        name='second_DDM',
    )

    # System:
    mySystem = system(
        processes=[ColorNamingProcess, WordReadingProcess, RewardProcess],
        controller=EVCMechanism,
        enable_controller=True,
        # monitor_for_control=[Reward, (DDM_PROBABILITY_UPPER_THRESHOLD, 1, -1)],
        name='EVC Gratton System',
    )

    # no assert, should only complete without error


class TestGraphAndInput:

    def test_branch(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b')
        c = TransferMechanism(name='c')
        d = TransferMechanism(name='d')

        p1 = process(pathway=[a, b, c], name='p1')
        p2 = process(pathway=[a, b, d], name='p2')

        s = system(
            processes=[p1, p2],
            name='Branch System',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [2, 2]}
        s.run(inputs)

        assert {a} == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert set([c, d]) == set(s.get_mechanisms_by_role(MechanismRole.TERMINAL))

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.TERMINAL}
        assert s.get_roles_by_mechanism(d) == {MechanismRole.TERMINAL}

    def test_bypass(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b', default_variable=[0, 0])
        c = TransferMechanism(name='c')
        d = TransferMechanism(name='d')

        p1 = process(pathway=[a, b, c, d], name='p1')
        p2 = process(pathway=[a, b, d], name='p2')

        s = system(
            processes=[p1, p2],
            name='Bypass System',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [[2, 2], [0, 0]]}
        s.run(inputs=inputs)

        assert {a} == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert {d} == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(d) == {MechanismRole.TERMINAL}

    def test_chain(self):
        a = TransferMechanism(name='a', default_variable=[0, 0, 0])
        b = TransferMechanism(name='b')
        c = TransferMechanism(name='c')
        d = TransferMechanism(name='d')
        e = TransferMechanism(name='e')

        p1 = process(pathway=[a, b, c], name='p1')
        p2 = process(pathway=[c, d, e], name='p2')

        s = system(
            processes=[p1, p2],
            name='Chain System',
            initial_values={a: [1, 1, 1]},
        )

        inputs = {a: [[2, 2, 2], [0, 0, 0]]}
        s.run(inputs=inputs)

        assert {a} == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert {e} == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(d) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(e) == {MechanismRole.TERMINAL}

    def test_convergent(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b')
        c = TransferMechanism(name='c')
        c = TransferMechanism(name='c', default_variable=[0])
        d = TransferMechanism(name='d')
        e = TransferMechanism(name='e')

        p1 = process(pathway=[a, b, e], name='p1')
        p2 = process(pathway=[c, d, e], name='p2')

        s = system(
            processes=[p1, p2],
            name='Convergent System',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [[2, 2]], c: [[0]]}
        s.run(inputs=inputs)

        assert set([a, c]) == set(s.get_mechanisms_by_role(MechanismRole.ORIGIN))
        assert {e} == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(d) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(e) == {MechanismRole.TERMINAL}

    def cyclic_one_process(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b', default_variable=[0, 0])

        p1 = process(pathway=[a, b, a], name='p1')

        s = system(
            processes=[p1],
            name='Cyclic System with one Process',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [1, 1]}
        s.run(inputs=inputs)

        assert {a} == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert [] == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INITIALIZE_CYCLE}

    def cyclic_two_processes(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b', default_variable=[0, 0])
        c = TransferMechanism(name='c', default_variable=[0, 0])

        p1 = process(pathway=[a, b, a], name='p1')
        p2 = process(pathway=[a, c, a], name='p2')

        s = system(
            processes=[p1, p2],
            name='Cyclic System with two Processes',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [1, 1]}
        s.run(inputs=inputs)

        assert {a} == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert {} == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.INITIALIZE_CYCLE}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.INITIALIZE_CYCLE}

    def cyclic_extended_loop(self):
        a = TransferMechanism(name='a', default_variable=[0, 0])
        b = TransferMechanism(name='b')
        c = TransferMechanism(name='c')
        d = TransferMechanism(name='d')
        e = TransferMechanism(name='e', default_variable=[0])
        f = TransferMechanism(name='f')

        p1 = process(pathway=[a, b, c, d], name='p1')
        p2 = process(pathway=[e, c, f, b, d], name='p2')

        s = system(
            processes=[p1, p2],
            name='Cyclic System with Extended Loop',
            initial_values={a: [1, 1]},
        )

        inputs = {a: [2, 2], e: [0]}
        s.run(inputs=inputs)

        assert set([a, c]) == s.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert {d} == s.get_mechanisms_by_role(MechanismRole.TERMINAL)

        assert s.get_roles_by_mechanism(a) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(b) == {MechanismRole.CYCLE}
        assert s.get_roles_by_mechanism(c) == {MechanismRole.INTERNAL}
        assert s.get_roles_by_mechanism(d) == {MechanismRole.TERMINAL}
        assert s.get_roles_by_mechanism(e) == {MechanismRole.ORIGIN}
        assert s.get_roles_by_mechanism(f) == {MechanismRole.INITIALIZE_CYCLE}
