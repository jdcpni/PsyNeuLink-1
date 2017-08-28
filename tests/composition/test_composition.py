import functools
import logging
import numpy as np
import pytest
import uuid

from timeit import timeit

from PsyNeuLink.Components.Functions.Function import Linear, SimpleIntegrator
from PsyNeuLink.Components.Mechanisms.Mechanism import mechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.IntegratorMechanism import IntegratorMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.RecurrentTransferMechanism import RecurrentTransferMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Process import process
from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
from PsyNeuLink.Components.States.InputState import InputState
from PsyNeuLink.Components.System import system
from PsyNeuLink.Composition import Composition, CompositionError, MechanismRole, Pathway, Systemm
from PsyNeuLink.Globals.Keywords import HARD_CLAMP, INPUT_STATE, NAME, NO_CLAMP, PULSE_CLAMP, SOFT_CLAMP
from PsyNeuLink.Scheduling.Condition import AfterNCalls, EveryNCalls, EveryNPasses
from PsyNeuLink.Scheduling.Scheduler import Scheduler
from PsyNeuLink.Scheduling.TimeScale import TimeScale

logger = logging.getLogger(__name__)

# All tests are set to run. If you need to skip certain tests,
# see http://doc.pytest.org/en/latest/skipping.html


# Unit tests for each function of the Composition class #######################
# Unit tests for Composition.Composition()
class TestConstructor:

    def test_no_args(self):
        comp = Composition()
        assert isinstance(comp, Composition)

    def test_two_calls_no_args(self):
        comp = Composition()
        assert isinstance(comp, Composition)

        comp_2 = Composition()
        assert isinstance(comp_2, Composition)

    @pytest.mark.stress
    @pytest.mark.parametrize(
        'count', [
            10000,
        ]
    )
    def test_timing_no_args(self, count):
        t = timeit('comp = Composition()', setup='from PsyNeuLink.Composition import Composition', number=count)
        print()
        logger.info('completed {0} creation{2} of Composition() in {1:.8f}s'.format(count, t, 's' if count != 1 else ''))


# Unit tests for Composition.add_mechanism
class TestAddMechanism:

    def test_add_once(self):
        comp = Composition()
        comp.add_mechanism(mechanism())

    def test_add_twice(self):
        comp = Composition()
        comp.add_mechanism(mechanism())
        comp.add_mechanism(mechanism())

    def test_add_same_twice(self):
        comp = Composition()
        mech = mechanism()
        comp.add_mechanism(mech)
        comp.add_mechanism(mech)

    @pytest.mark.stress
    @pytest.mark.parametrize(
        'count', [
            100,
        ]
    )
    def test_timing_stress(self, count):
        t = timeit(
            'comp.add_mechanism(mechanism())',
            setup='''
from PsyNeuLink.Components.Mechanisms.Mechanism import mechanism
from PsyNeuLink.Composition import Composition
comp = Composition()
''',
            number=count
        )
        print()
        logger.info('completed {0} addition{2} of a Mechanism to a Composition in {1:.8f}s'.
                    format(count, t, 's' if count != 1 else ''))

# Unit tests for Composition.add_projection


class TestAddProjection:

    def test_add_once(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(), B)

    def test_add_twice(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(), B)
        comp.add_projection(A, MappingProjection(), B)

    def test_add_same_twice(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        proj = MappingProjection()
        comp.add_projection(A, proj, B)
        comp.add_projection(A, proj, B)

    @pytest.mark.stress
    @pytest.mark.parametrize(
        'count', [
            1000,
        ]
    )
    def test_timing_stress(self, count):
        t = timeit('comp.add_projection(A, MappingProjection(), B)',
                   setup='''
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Projections.PathwayProjections.MappingProjection import MappingProjection
from PsyNeuLink.Composition import Composition
comp = Composition()
A = TransferMechanism(name='A')
B = TransferMechanism(name='B')
comp.add_mechanism(A)
comp.add_mechanism(B)
''',
                   number=count
                   )
        print()
        logger.info('completed {0} addition{2} of a projection to a composition in {1:.8f}s'.format(count, t, 's' if count != 1 else ''))


class TestAnalyzeGraph:

    def test_empty_call(self):
        comp = Composition()
        comp._analyze_graph()

    def test_singleton(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        comp.add_mechanism(A)
        comp._analyze_graph()
        assert A in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert A in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)

    def test_two_independent(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp._analyze_graph()
        assert A in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert B in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert A in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)
        assert B in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)

    def test_two_in_a_row(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(), B)
        comp._analyze_graph()
        assert A in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert B not in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert A not in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)
        assert B in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)

    # (A)<->(B)
    def test_two_recursive(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(), B)
        comp.add_projection(B, MappingProjection(), A)
        comp._analyze_graph()
        assert A not in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert B not in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert A not in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)
        assert B not in comp.get_mechanisms_by_role(MechanismRole.TERMINAL)
        assert A in comp.get_mechanisms_by_role(MechanismRole.CYCLE)
        assert B in comp.get_mechanisms_by_role(MechanismRole.RECURRENT_INIT)

    # (A)->(B)<->(C)<-(D)
    def test_two_origins_pointing_to_recursive_pair(self):
        comp = Composition()
        A = TransferMechanism(name='A')
        B = TransferMechanism(name='B')
        C = TransferMechanism(name='C')
        D = TransferMechanism(name='D')
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(), B)
        comp.add_projection(C, MappingProjection(), B)
        comp.add_projection(B, MappingProjection(), C)
        comp.add_projection(D, MappingProjection(), C)
        comp._analyze_graph()
        assert A in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert D in comp.get_mechanisms_by_role(MechanismRole.ORIGIN)
        assert B in comp.get_mechanisms_by_role(MechanismRole.CYCLE)
        assert C in comp.get_mechanisms_by_role(MechanismRole.RECURRENT_INIT)


# class TestValidateFeedDict:
#
#     def test_empty_feed_dicts(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {}
#         feed_dict_terminal = {}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_origin_and_terminal_with_mapping(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]]}
#         feed_dict_terminal = {B: [[0]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_origin_and_terminal_with_swapped_feed_dicts_1(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {B: [[0]]}
#         feed_dict_terminal = {A: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_origin_and_terminal_with_swapped_feed_dicts_2(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {B: [[0]]}
#         feed_dict_terminal = {A: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_multiple_origin_mechs(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         C = TransferMechanism(name='C')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_mechanism(C)
#         comp.add_projection(A, MappingProjection(), C)
#         comp.add_projection(B, MappingProjection(), C)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]], B: [[0]]}
#         feed_dict_terminal = {C: [[0]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_multiple_origin_mechs_only_one_in_feed_dict(self):
#         comp = Composition()
#         A = TransferMechanism(name='A')
#         B = TransferMechanism(name='B')
#         C = TransferMechanism(name='C')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_mechanism(C)
#         comp.add_projection(A, MappingProjection(), C)
#         comp.add_projection(B, MappingProjection(), C)
#         comp._analyze_graph()
#         feed_dict_origin = {B: [[0]]}
#         feed_dict_terminal = {C: [[0]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_input_state_len_3(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0, 1, 2], name='A')
#         B = TransferMechanism(default_variable=[0, 1, 2], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0, 1, 2]]}
#         feed_dict_terminal = {B: [[0, 1, 2]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_input_state_len_3_feed_dict_len_2(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0, 1, 2], name='A')
#         B = TransferMechanism(default_variable=[0, 1, 2], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0, 1]]}
#         feed_dict_terminal = {B: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_input_state_len_2_feed_dict_len_3(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0, 1], name='A')
#         B = TransferMechanism(default_variable=[0, 1], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0, 1, 2]]}
#         feed_dict_terminal = {B: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_feed_dict_includes_mechs_of_correct_and_incorrect_types(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0], name='A')
#         B = TransferMechanism(default_variable=[0], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]], B: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_input_state_len_3_brackets_extra_1(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0, 1, 2], name='A')
#         B = TransferMechanism(default_variable=[0, 1, 2], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[[0, 1, 2]]]}
#         feed_dict_terminal = {B: [[[0, 1, 2]]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_input_state_len_3_brackets_missing_1(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0, 1, 2], name='A')
#         B = TransferMechanism(default_variable=[0, 1, 2], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A:  [0, 1, 2]}
#         feed_dict_terminal = {B: [[0]]}
#         with pytest.raises(TypeError):
#             comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_empty_feed_dict_for_empty_type(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0], name='A')
#         B = TransferMechanism(default_variable=[0], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]]}
#         feed_dict_monitored = {}
#         comp._validate_feed_dict(feed_dict_monitored, comp.get_mechanisms_by_role(MechanismRole.MONITORED), "monitored")
#
#     def test_mech_in_feed_dict_for_empty_type(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0])
#         B = TransferMechanism(name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]]}
#         feed_dict_monitored = {B: [[0]]}
#         with pytest.raises(ValueError):
#             comp._validate_feed_dict(feed_dict_monitored, comp.get_mechanisms_by_role(MechanismRole.MONITORED), "monitored")
#
#     def test_one_mech_1(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0])
#         comp.add_mechanism(A)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]]}
#         feed_dict_terminal = {A: [[0]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#
#     def test_one_mech_2(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[0])
#         comp.add_mechanism(A)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0]]}
#         feed_dict_terminal = {A: [[0]]}
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_multiple_time_steps_1(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[[0, 1, 2]], name='A')
#         B = TransferMechanism(default_variable=[[0, 1, 2]], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[0, 1, 2], [0, 1, 2]]}
#         feed_dict_terminal = {B: [[0, 1, 2]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#
#     def test_multiple_time_steps_2(self):
#         comp = Composition()
#         A = TransferMechanism(default_variable=[[0, 1, 2]], name='A')
#         B = TransferMechanism(default_variable=[[0, 1, 2]], name='B')
#         comp.add_mechanism(A)
#         comp.add_mechanism(B)
#         comp.add_projection(A, MappingProjection(), B)
#         comp._analyze_graph()
#         feed_dict_origin = {A: [[[0, 1, 2]], [[0, 1, 2]]]}
#         feed_dict_terminal = {B: [[0, 1, 2]]}
#         comp._validate_feed_dict(feed_dict_origin, comp.get_mechanisms_by_role(MechanismRole.ORIGIN), "origin")
#         comp._validate_feed_dict(feed_dict_terminal, comp.get_mechanisms_by_role(MechanismRole.TERMINAL), "terminal")
#

class TestGetMechanismsByRole:

    def test_multiple_roles(self):

        comp = Composition()
        mechs = [mechanism() for x in range(4)]

        for mech in mechs:
            comp.add_mechanism(mech)

        comp._add_mechanism_role(mechs[0], MechanismRole.ORIGIN)
        comp._add_mechanism_role(mechs[1], MechanismRole.INTERNAL)
        comp._add_mechanism_role(mechs[2], MechanismRole.INTERNAL)
        comp._add_mechanism_role(mechs[3], MechanismRole.CYCLE)

        for role in list(MechanismRole):
            if role is MechanismRole.ORIGIN:
                assert comp.get_mechanisms_by_role(role) == {mechs[0]}
            elif role is MechanismRole.INTERNAL:
                assert comp.get_mechanisms_by_role(role) == set([mechs[1], mechs[2]])
            elif role is MechanismRole.CYCLE:
                assert comp.get_mechanisms_by_role(role) == {mechs[3]}
            else:
                assert comp.get_mechanisms_by_role(role) == set()

    def test_nonexistent_role(self):

        comp = Composition()

        with pytest.raises(CompositionError):
            comp.get_mechanisms_by_role(None)


class TestGraph:

    class TestProcessingGraph:

        def test_all_mechanisms(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            mechs = [A, B, C]
            for m in mechs:
                comp.add_mechanism(m)

            assert len(comp.graph_processing.vertices) == 3
            assert len(comp.graph_processing.comp_to_vertex) == 3
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert comp.graph_processing.get_parents_from_component(A) == []
            assert comp.graph_processing.get_parents_from_component(B) == []
            assert comp.graph_processing.get_parents_from_component(C) == []

            assert comp.graph_processing.get_children_from_component(A) == []
            assert comp.graph_processing.get_children_from_component(B) == []
            assert comp.graph_processing.get_children_from_component(C) == []

        def test_triangle(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            mechs = [A, B, C]
            for m in mechs:
                comp.add_mechanism(m)
            comp.add_projection(A, MappingProjection(), B)
            comp.add_projection(B, MappingProjection(), C)

            assert len(comp.graph_processing.vertices) == 3
            assert len(comp.graph_processing.comp_to_vertex) == 3
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert comp.graph_processing.get_parents_from_component(A) == []
            assert comp.graph_processing.get_parents_from_component(B) == [comp.graph_processing.comp_to_vertex[A]]
            assert comp.graph_processing.get_parents_from_component(C) == [comp.graph_processing.comp_to_vertex[B]]

            assert comp.graph_processing.get_children_from_component(A) == [comp.graph_processing.comp_to_vertex[B]]
            assert comp.graph_processing.get_children_from_component(B) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_children_from_component(C) == []

        def test_x(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            D = TransferMechanism(function=Linear(intercept=1.5), name='D')
            E = TransferMechanism(function=Linear(intercept=1.5), name='E')
            mechs = [A, B, C, D, E]
            for m in mechs:
                comp.add_mechanism(m)
            comp.add_projection(A, MappingProjection(), C)
            comp.add_projection(B, MappingProjection(), C)
            comp.add_projection(C, MappingProjection(), D)
            comp.add_projection(C, MappingProjection(), E)

            assert len(comp.graph_processing.vertices) == 5
            assert len(comp.graph_processing.comp_to_vertex) == 5
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert comp.graph_processing.get_parents_from_component(A) == []
            assert comp.graph_processing.get_parents_from_component(B) == []
            assert set(comp.graph_processing.get_parents_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[A],
                comp.graph_processing.comp_to_vertex[B],
            ])
            assert comp.graph_processing.get_parents_from_component(D) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_parents_from_component(E) == [comp.graph_processing.comp_to_vertex[C]]

            assert comp.graph_processing.get_children_from_component(A) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_children_from_component(B) == [comp.graph_processing.comp_to_vertex[C]]
            assert set(comp.graph_processing.get_children_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[D],
                comp.graph_processing.comp_to_vertex[E],
            ])
            assert comp.graph_processing.get_children_from_component(D) == []
            assert comp.graph_processing.get_children_from_component(E) == []

        def test_cycle_linear(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            mechs = [A, B, C]
            for m in mechs:
                comp.add_mechanism(m)
            comp.add_projection(A, MappingProjection(), B)
            comp.add_projection(B, MappingProjection(), C)
            comp.add_projection(C, MappingProjection(), A)

            assert len(comp.graph_processing.vertices) == 3
            assert len(comp.graph_processing.comp_to_vertex) == 3
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert comp.graph_processing.get_parents_from_component(A) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_parents_from_component(B) == [comp.graph_processing.comp_to_vertex[A]]
            assert comp.graph_processing.get_parents_from_component(C) == [comp.graph_processing.comp_to_vertex[B]]

            assert comp.graph_processing.get_children_from_component(A) == [comp.graph_processing.comp_to_vertex[B]]
            assert comp.graph_processing.get_children_from_component(B) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_children_from_component(C) == [comp.graph_processing.comp_to_vertex[A]]

        def test_cycle_x(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            D = TransferMechanism(function=Linear(intercept=1.5), name='D')
            E = TransferMechanism(function=Linear(intercept=1.5), name='E')
            mechs = [A, B, C, D, E]
            for m in mechs:
                comp.add_mechanism(m)
            comp.add_projection(A, MappingProjection(), C)
            comp.add_projection(B, MappingProjection(), C)
            comp.add_projection(C, MappingProjection(), D)
            comp.add_projection(C, MappingProjection(), E)
            comp.add_projection(D, MappingProjection(), A)
            comp.add_projection(E, MappingProjection(), B)

            assert len(comp.graph_processing.vertices) == 5
            assert len(comp.graph_processing.comp_to_vertex) == 5
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert comp.graph_processing.get_parents_from_component(A) == [comp.graph_processing.comp_to_vertex[D]]
            assert comp.graph_processing.get_parents_from_component(B) == [comp.graph_processing.comp_to_vertex[E]]
            assert set(comp.graph_processing.get_parents_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[A],
                comp.graph_processing.comp_to_vertex[B],
            ])
            assert comp.graph_processing.get_parents_from_component(D) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_parents_from_component(E) == [comp.graph_processing.comp_to_vertex[C]]

            assert comp.graph_processing.get_children_from_component(A) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_children_from_component(B) == [comp.graph_processing.comp_to_vertex[C]]
            assert set(comp.graph_processing.get_children_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[D],
                comp.graph_processing.comp_to_vertex[E],
            ])
            assert comp.graph_processing.get_children_from_component(D) == [comp.graph_processing.comp_to_vertex[A]]
            assert comp.graph_processing.get_children_from_component(E) == [comp.graph_processing.comp_to_vertex[B]]

        def test_cycle_x_multiple_incoming(self):
            comp = Composition()
            A = TransferMechanism(function=Linear(slope=5.0, intercept=2.0), name='A')
            B = TransferMechanism(function=Linear(intercept=4.0), name='B')
            C = TransferMechanism(function=Linear(intercept=1.5), name='C')
            D = TransferMechanism(function=Linear(intercept=1.5), name='D')
            E = TransferMechanism(function=Linear(intercept=1.5), name='E')
            mechs = [A, B, C, D, E]
            for m in mechs:
                comp.add_mechanism(m)
            comp.add_projection(A, MappingProjection(), C)
            comp.add_projection(B, MappingProjection(), C)
            comp.add_projection(C, MappingProjection(), D)
            comp.add_projection(C, MappingProjection(), E)
            comp.add_projection(D, MappingProjection(), A)
            comp.add_projection(D, MappingProjection(), B)
            comp.add_projection(E, MappingProjection(), A)
            comp.add_projection(E, MappingProjection(), B)

            assert len(comp.graph_processing.vertices) == 5
            assert len(comp.graph_processing.comp_to_vertex) == 5
            for m in mechs:
                assert m in comp.graph_processing.comp_to_vertex

            assert set(comp.graph_processing.get_parents_from_component(A)) == set([
                comp.graph_processing.comp_to_vertex[D],
                comp.graph_processing.comp_to_vertex[E],
            ])
            assert set(comp.graph_processing.get_parents_from_component(B)) == set([
                comp.graph_processing.comp_to_vertex[D],
                comp.graph_processing.comp_to_vertex[E],
            ])
            assert set(comp.graph_processing.get_parents_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[A],
                comp.graph_processing.comp_to_vertex[B],
            ])
            assert comp.graph_processing.get_parents_from_component(D) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_parents_from_component(E) == [comp.graph_processing.comp_to_vertex[C]]

            assert comp.graph_processing.get_children_from_component(A) == [comp.graph_processing.comp_to_vertex[C]]
            assert comp.graph_processing.get_children_from_component(B) == [comp.graph_processing.comp_to_vertex[C]]
            assert set(comp.graph_processing.get_children_from_component(C)) == set([
                comp.graph_processing.comp_to_vertex[D],
                comp.graph_processing.comp_to_vertex[E],
            ])
            assert set(comp.graph_processing.get_children_from_component(D)) == set([
                comp.graph_processing.comp_to_vertex[A],
                comp.graph_processing.comp_to_vertex[B],
            ])
            assert set(comp.graph_processing.get_children_from_component(E)) == set([
                comp.graph_processing.comp_to_vertex[A],
                comp.graph_processing.comp_to_vertex[B],
            ])


class TestRun:

    def test_run_2_mechanisms_default_input_1(self):
        comp = Composition()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        sched = Scheduler(composition=comp)
        output = comp.run(
            scheduler_processing=sched
        )
        assert 25 == output[0][0]

    def test_run_2_mechanisms_input_5(self):
        comp = Composition()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [5]}
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 125 == output[0][0]

    def test_projection_assignment_mistake_swap(self):

        comp = Composition()
        A = TransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        with pytest.raises(CompositionError) as error_text:
            comp.add_projection(B, MappingProjection(sender=B, receiver=D), C)

        assert "is incompatible with the positions of these Components in their Composition" in str(error_text.value)

    def test_projection_assignment_mistake_swap2(self):
        # A ----> C --
        #              ==> E
        # B ----> D --

        comp = Composition()
        A = TransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        with pytest.raises(CompositionError) as error_text:
            comp.add_projection(B, MappingProjection(sender=B, receiver=C), D)

        assert "is incompatible with the positions of these Components in their Composition" in str(error_text.value)

    def test_run_5_mechanisms_2_origins_1_terminal(self):
        # A ----> C --
        #              ==> E
        # B ----> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = TransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [5],
            B: [5]
        }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 250 == output[0][0]

    def test_run_2_mechanisms_with_scheduling_AAB_integrator(self):
        comp = Composition()

        A = IntegratorMechanism(name="A [integrator]", default_variable=2.0, function=SimpleIntegrator(rate=1.0))
        # (1) value = 0 + (5.0 * 1.0) + 0  --> return 5.0
        # (2) value = 5.0 + (5.0 * 1.0) + 0  --> return 10.0
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        # value = 10.0 * 5.0 --> return 50.0
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [5]}
        sched = Scheduler(composition=comp)
        sched.add_condition(B, EveryNCalls(A, 2))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 50.0 == output[0][0]

    def test_run_2_mechanisms_with_scheduling_AAB_transfer(self):
        comp = Composition()

        A = TransferMechanism(name="A [transfer]", function=Linear(slope=2.0))
        # (1) value = 5.0 * 2.0  --> return 10.0
        # (2) value = 5.0 * 2.0  --> return 10.0
        # ** TransferMechanism runs with the SAME input **
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        # value = 10.0 * 5.0 --> return 50.0
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [5]}
        sched = Scheduler(composition=comp)
        sched.add_condition(B, EveryNCalls(A, 2))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 50.0 == output[0][0]

    def test_run_2_mechanisms_with_multiple_trials_of_input_values(self):
        comp = Composition()

        A = TransferMechanism(name="A [transfer]", function=Linear(slope=2.0))
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [1, 2, 3, 4]}
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 40.0 == output[0][0]

    def test_sender_receiver_not_specified(self):
        comp = Composition()

        A = TransferMechanism(name="A [transfer]", function=Linear(slope=2.0))
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(), B)
        comp._analyze_graph()
        inputs_dict = {A: [1, 2, 3, 4]}
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 40.0 == output[0][0]

    def test_run_2_mechanisms_reuse_input(self):
        comp = Composition()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [5]}
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            num_trials=5
        )
        assert 125 == output[0][0]

    def test_run_2_mechanisms_incorrect_trial_spec(self):
        comp = Composition()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [[5], [4], [3]]}
        sched = Scheduler(composition=comp)
        with pytest.raises(CompositionError) as error_text:
            comp.run(
                inputs=inputs_dict,
                scheduler_processing=sched,
                num_trials=5
            )
        assert "number of trials" in str(error_text.value) and "does not match the length" in str(error_text.value)

    def test_run_2_mechanisms_double_trial_specs(self):
        comp = Composition()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [[5], [4], [3]]}
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            num_trials=3
        )
        assert 75 == output[0][0]


class TestPathway:

    def test_LPP(self):

        path = Pathway()
        A = TransferMechanism(name="A", function=Linear(slope=2.0))   # 1 x 2 = 2
        B = TransferMechanism(name="B", function=Linear(slope=2.0))   # 2 x 2 = 4
        C = TransferMechanism(name="C", function=Linear(slope=2.0))   # 4 x 2 = 8
        D = TransferMechanism(name="D", function=Linear(slope=2.0))   # 8 x 2 = 16
        E = TransferMechanism(name="E", function=Linear(slope=2.0))  # 16 x 2 = 32
        path.add_linear_processing_pathway([A, B, C, D, E])
        path._analyze_graph()
        inputs_dict = {A: [[1]]}
        sched = Scheduler(composition=path)
        output = path.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 32 == output[0][0]

    def test_LPP_with_projections(self):
        path = Pathway()
        A = TransferMechanism(name="A", function=Linear(slope=2.0))  # 1 x 2 = 2
        B = TransferMechanism(name="B", function=Linear(slope=2.0))  # 2 x 2 = 4
        C = TransferMechanism(name="C", function=Linear(slope=2.0))  # 4 x 2 = 8
        D = TransferMechanism(name="D", function=Linear(slope=2.0))  # 8 x 2 = 16
        E = TransferMechanism(name="E", function=Linear(slope=2.0))  # 16 x 2 = 32
        A_to_B = MappingProjection(sender=A, receiver=B)
        D_to_E = MappingProjection(sender=D, receiver=E)
        path.add_linear_processing_pathway([A, A_to_B, B, C, D, D_to_E, E])
        path._analyze_graph()
        inputs_dict = {A: [[1]]}
        sched = Scheduler(composition=path)
        output = path.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 32 == output[0][0]

    def test_LPP_end_with_projection(self):
        path = Pathway()
        A = TransferMechanism(name="A", function=Linear(slope=2.0))
        B = TransferMechanism(name="B", function=Linear(slope=2.0))
        C = TransferMechanism(name="C", function=Linear(slope=2.0))
        D = TransferMechanism(name="D", function=Linear(slope=2.0))
        E = TransferMechanism(name="E", function=Linear(slope=2.0))
        A_to_B = MappingProjection(sender=A, receiver=B)
        D_to_E = MappingProjection(sender=D, receiver=E)
        with pytest.raises(CompositionError) as error_text:
            path.add_linear_processing_pathway([A, A_to_B, B, C, D, E, D_to_E])

        assert "A projection cannot be the last item in a linear processing pathway." in str(error_text.value)

    def test_LPP_two_projections_in_a_row(self):
        path = Pathway()
        A = TransferMechanism(name="A", function=Linear(slope=2.0))
        B = TransferMechanism(name="B", function=Linear(slope=2.0))
        C = TransferMechanism(name="C", function=Linear(slope=2.0))
        A_to_B = MappingProjection(sender=A, receiver=B)
        B_to_C = MappingProjection(sender=B, receiver=C)
        with pytest.raises(CompositionError) as error_text:
            path.add_linear_processing_pathway([A, B_to_C, A_to_B, B, C])

        assert "is not between two mechanisms" in str(error_text.value)

    def test_LPP_start_with_projection(self):
        path = Pathway()
        Nonsense_Projection = MappingProjection()
        A = TransferMechanism(name="A", function=Linear(slope=2.0))
        B = TransferMechanism(name="B", function=Linear(slope=2.0))
        with pytest.raises(CompositionError) as error_text:
            path.add_linear_processing_pathway([Nonsense_Projection, A, B])

        assert "The first item in a linear processing pathway must be a Mechanism." in str(error_text.value)

    def test_LPP_wrong_component(self):
        path = Pathway()
        Nonsense = "string"
        A = TransferMechanism(name="A", function=Linear(slope=2.0))
        B = TransferMechanism(name="B", function=Linear(slope=2.0))
        with pytest.raises(CompositionError) as error_text:
            path.add_linear_processing_pathway([A, Nonsense, B])

        assert "A linear processing pathway must be made up of projections and mechanisms." in str(
            error_text.value)

    def test_LPP_two_origins_one_terminal(self):
        # A ----> C --
        #              ==> E
        # B ----> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        path = Pathway()
        A = TransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        path.add_linear_processing_pathway([A, C, E])
        path.add_linear_processing_pathway([B, D, E])
        path._analyze_graph()
        inputs_dict = {
            A: [5],
            B: [5]
        }
        sched = Scheduler(composition=path)
        output = path.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 250 == output[0][0]


class TestClampInput:

    def test_run_5_mechanisms_2_origins_1_terminal_hard_clamp(self):
        # HARD_CLAMP

        # recurrent projection ignored on the second execution of A
        #          __
        #         |  |
        # 5 -#2-> x  |
        # 5 -#1-> A -^--> C --
        #                       ==> E
        # 5 ----> B ----> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = RecurrentTransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [5],
            B: [5]
        }
        sched = Scheduler(composition=comp)
        sched.add_condition(A, EveryNPasses(1))
        sched.add_condition(B, EveryNCalls(A, 2))
        sched.add_condition(C, AfterNCalls(A, 2))
        sched.add_condition(D, AfterNCalls(A, 2))
        sched.add_condition(E, AfterNCalls(C, 1))
        sched.add_condition(E, AfterNCalls(D, 1))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            clamp_input=HARD_CLAMP
        )
        assert 250 == output[0][0]

    def test_run_5_mechanisms_2_origins_1_terminal_soft_clamp(self):
        # recurrent projection combines with input on the second execution of A
        #          _r_
        #         |   |
        # 5 -#2-> V   |
        # 5 -#1-> A --^ --> C --
        #                       ==> E
        # 5 ----> B ------> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = RecurrentTransferMechanism(name="A", function=Linear(slope=1.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [[[5.]]],
            B: [[[5.]]]
        }
        sched = Scheduler(composition=comp)
        sched.add_condition(A, EveryNPasses(1))
        sched.add_condition(B, EveryNCalls(A, 2))
        sched.add_condition(C, AfterNCalls(A, 2))
        sched.add_condition(D, AfterNCalls(A, 2))
        sched.add_condition(E, AfterNCalls(C, 1))
        sched.add_condition(E, AfterNCalls(D, 1))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            clamp_input=SOFT_CLAMP
        )
        assert 375 == output[0][0]

    def test_run_5_mechanisms_2_origins_1_terminal_pulse_clamp(self):
        # input ignored on the second execution of A
        #          __
        #         |  |
        #         V  |
        # 5 -#1-> A -^--> C --
        #                       ==> E
        # 5 ----> B ----> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = RecurrentTransferMechanism(name="A", function=Linear(slope=2.0))
        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [5],
            B: [5]
        }
        sched = Scheduler(composition=comp)
        sched.add_condition(A, EveryNPasses(1))
        sched.add_condition(B, EveryNCalls(A, 2))
        sched.add_condition(C, AfterNCalls(A, 2))
        sched.add_condition(D, AfterNCalls(A, 2))
        sched.add_condition(E, AfterNCalls(C, 1))
        sched.add_condition(E, AfterNCalls(D, 1))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            clamp_input=PULSE_CLAMP
        )
        assert 625 == output[0][0]

    def test_run_5_mechanisms_2_origins_1_hard_clamp_1_soft_clamp(self):

        #          __
        #         |  |
        #         V  |
        # 5 -#1-> A -^--> C --
        #                       ==> E
        # 5 ----> B ----> D --

        #         v Recurrent
        # 5 * 1 = (5 + 5) x 1 = 10
        # 5 x 1 = 5 ---->      10 x 5 = 50 --
        #                                       50 + 25 = 75  ==> 75 * 5 = 375
        # 5 * 1 = 5 ---->       5 x 5 = 25 --

        comp = Composition()
        A = RecurrentTransferMechanism(name="A", function=Linear(slope=1.0))
        B = RecurrentTransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [5],
            B: [5]
        }
        sched = Scheduler(composition=comp)
        sched.add_condition(A, EveryNPasses(1))
        sched.add_condition(B, EveryNPasses(1))
        sched.add_condition(B, EveryNCalls(A, 1))
        sched.add_condition(C, AfterNCalls(A, 2))
        sched.add_condition(D, AfterNCalls(A, 2))
        sched.add_condition(E, AfterNCalls(C, 1))
        sched.add_condition(E, AfterNCalls(D, 1))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            clamp_input={A: SOFT_CLAMP,
                         B: HARD_CLAMP}
        )
        assert 375 == output[0][0]

    def test_run_5_mechanisms_2_origins_1_terminal_no_clamp(self):
        # input ignored on all executions
        #          _r_
        #         |   |
        # 0 -#2-> V   |
        # 0 -#1-> A -^--> C --
        #                       ==> E
        # 0 ----> B ----> D --

        # 1 * 2 + 1 = 3
        # 0 x 2 + 1 = 1 ----> 4 x 5 = 20 --
        #                                   20 + 5 = 25  ==> 25 * 5 = 125
        # 0 x 1 + 1 = 1 ----> 1 x 5 = 5 --

        comp = Composition()
        A = RecurrentTransferMechanism(name="A", function=Linear(slope=2.0, intercept=1.0))
        B = RecurrentTransferMechanism(name="B", function=Linear(slope=1.0, intercept=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [1],
            B: [1]
        }
        sched = Scheduler(composition=comp)
        sched.add_condition(A, EveryNPasses(1))
        sched.add_condition(B, EveryNCalls(A, 2))
        sched.add_condition(C, AfterNCalls(A, 2))
        sched.add_condition(D, AfterNCalls(A, 2))
        sched.add_condition(E, AfterNCalls(C, 1))
        sched.add_condition(E, AfterNCalls(D, 1))
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            clamp_input=NO_CLAMP
        )
        assert 125 == output[0][0]


class TestCallBeforeAfterTimescale:

    def test_call_before_record_timescale(self):
        time_step_array = []
        trial_array = []
        pass_array = []

        def cb_timestep(composition, scheduler, arr):
            def record_timestep():

                arr.append(scheduler.times[composition._execution_id][TimeScale.TIME_STEP][TimeScale.TIME_STEP])

            return record_timestep

        def cb_pass(composition, scheduler, arr):

            def record_pass():

                arr.append(scheduler.times[composition._execution_id][TimeScale.RUN][TimeScale.PASS])

            return record_pass

        def cb_trial(composition, scheduler, arr):

            def record_trial():

                arr.append(scheduler.times[composition._execution_id][TimeScale.LIFE][TimeScale.TRIAL])

            return record_trial

        comp = Composition()

        A = TransferMechanism(name="A [transfer]", function=Linear(slope=2.0))
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [1, 2, 3, 4]}
        sched = Scheduler(composition=comp)

        comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            call_before_time_step=cb_timestep(comp, sched, time_step_array),
            call_before_trial=cb_trial(comp, sched, trial_array),
            call_before_pass=cb_pass(comp, sched, pass_array)
        )

        assert time_step_array == [0, 1, 0, 1, 0, 1, 0, 1]
        assert trial_array == [0, 1, 2, 3]
        assert pass_array == [0, 1, 2, 3]


class TestSystemm:

    def test_run_2_mechanisms_default_input_1(self):
        sys = Systemm()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        sys.add_mechanism(A)
        sys.add_mechanism(B)
        sys.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        sys._analyze_graph()
        sched = Scheduler(composition=sys)
        output = sys.run(
            scheduler_processing=sched
        )
        assert 25 == output[0][0]

    def test_run_2_mechanisms_input_5(self):
        sys = Systemm()
        A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
        B = TransferMechanism(function=Linear(slope=5.0))
        sys.add_mechanism(A)
        sys.add_mechanism(B)
        sys.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        sys._analyze_graph()
        inputs_dict = {A: [5]}
        sched = Scheduler(composition=sys)
        output = sys.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 125 == output[0][0]

    def test_call_beforeafter_values_onepass(self):

        def record_values(d, time_scale, *mechs):
            if time_scale not in d:
                d[time_scale] = {}
            for mech in mechs:
                if mech not in d[time_scale]:
                    d[time_scale][mech] = []
                if mech.value is None:
                    d[time_scale][mech].append(np.nan)
                else:
                    d[time_scale][mech].append(mech.value)

        comp = Composition()

        A = TransferMechanism(name="A [transfer]", function=Linear(slope=2.0))
        B = TransferMechanism(name="B [transfer]", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [1, 2, 3, 4]}
        sched = Scheduler(composition=comp)

        before = {}
        after = {}

        before_expected = {
            TimeScale.TIME_STEP: {
                A: [np.nan, 2, 2, 4, 4, 6, 6, 8],
                B: [np.nan, np.nan, 10, 10, 20, 20, 30, 30]
            },
            TimeScale.PASS: {
                A: [np.nan, 2, 4, 6],
                B: [np.nan, 10, 20, 30]
            },
            TimeScale.TRIAL: {
                A: [np.nan, 2, 4, 6],
                B: [np.nan, 10, 20, 30]
            },
        }

        after_expected = {
            TimeScale.TIME_STEP: {
                A: [2, 2, 4, 4, 6, 6, 8, 8],
                B: [np.nan, 10, 10, 20, 20, 30, 30, 40]
            },
            TimeScale.PASS: {
                A: [2, 4, 6, 8],
                B: [10, 20, 30, 40]
            },
            TimeScale.TRIAL: {
                A: [2, 4, 6, 8],
                B: [10, 20, 30, 40]
            },
        }

        comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            call_before_time_step=functools.partial(record_values, before, TimeScale.TIME_STEP, A, B),
            call_before_pass=functools.partial(record_values, before, TimeScale.PASS, A, B),
            call_before_trial=functools.partial(record_values, before, TimeScale.TRIAL, A, B),
            call_after_time_step=functools.partial(record_values, after, TimeScale.TIME_STEP, A, B),
            call_after_pass=functools.partial(record_values, after, TimeScale.PASS, A, B),
            call_after_trial=functools.partial(record_values, after, TimeScale.TRIAL, A, B),
        )

        for ts in before_expected:
            for mech in before_expected[ts]:
                np.testing.assert_allclose(before[ts][mech], before_expected[ts][mech], err_msg='Failed on before[{0}][{1}]'.format(ts, mech))

        for ts in after_expected:
            for mech in after_expected[ts]:
                comp = []
                for x in after[ts][mech]:
                    try:
                        comp.append(x[0][0])
                    except TypeError:
                        comp.append(x)
                np.testing.assert_allclose(comp, after_expected[ts][mech], err_msg='Failed on after[{0}][{1}]'.format(ts, mech))

    def test_call_beforeafter_values_twopass(self):

        def record_values(d, time_scale, *mechs):
            if time_scale not in d:
                d[time_scale] = {}
            for mech in mechs:
                if mech not in d[time_scale]:
                    d[time_scale][mech] = []
                if mech.value is None:
                    d[time_scale][mech].append(np.nan)
                else:
                    d[time_scale][mech].append(mech.value)

        comp = Composition()

        A = IntegratorMechanism(name="A [transfer]", function=SimpleIntegrator(rate=1))
        B = IntegratorMechanism(name="B [transfer]", function=SimpleIntegrator(rate=2))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp._analyze_graph()
        inputs_dict = {A: [1, 2]}
        sched = Scheduler(composition=comp)
        sched.add_condition(B, EveryNCalls(A, 2))

        before = {}
        after = {}

        before_expected = {
            TimeScale.TIME_STEP: {
                A: [
                    np.nan, 1, 2,
                    2, 4, 6,
                ],
                B: [
                    np.nan, np.nan, np.nan,
                    4, 4, 4,
                ]
            },
            TimeScale.PASS: {
                A: [
                    np.nan, 1,
                    2, 4,
                ],
                B: [
                    np.nan, np.nan,
                    4, 4,
                ]
            },
            TimeScale.TRIAL: {
                A: [np.nan, 2],
                B: [np.nan, 4]
            },
        }

        after_expected = {
            TimeScale.TIME_STEP: {
                A: [
                    1, 2, 2,
                    4, 6, 6,
                ],
                B: [
                    np.nan, np.nan, 4,
                    4, 4, 16,
                ]
            },
            TimeScale.PASS: {
                A: [
                    1, 2,
                    4, 6,
                ],
                B: [
                    np.nan, 4,
                    4, 16,
                ]
            },
            TimeScale.TRIAL: {
                A: [2, 6],
                B: [4, 16]
            },
        }

        comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched,
            call_before_time_step=functools.partial(record_values, before, TimeScale.TIME_STEP, A, B),
            call_before_pass=functools.partial(record_values, before, TimeScale.PASS, A, B),
            call_before_trial=functools.partial(record_values, before, TimeScale.TRIAL, A, B),
            call_after_time_step=functools.partial(record_values, after, TimeScale.TIME_STEP, A, B),
            call_after_pass=functools.partial(record_values, after, TimeScale.PASS, A, B),
            call_after_trial=functools.partial(record_values, after, TimeScale.TRIAL, A, B),
        )

        for ts in before_expected:
            for mech in before_expected[ts]:
                np.testing.assert_allclose(before[ts][mech], before_expected[ts][mech], err_msg='Failed on before[{0}][{1}]'.format(ts, mech))

        for ts in after_expected:
            for mech in after_expected[ts]:
                comp = []
                for x in after[ts][mech]:
                    try:
                        comp.append(x[0][0])
                    except TypeError:
                        comp.append(x)
                np.testing.assert_allclose(comp, after_expected[ts][mech], err_msg='Failed on after[{0}][{1}]'.format(ts, mech))

    # when self.sched is ready:
    # def test_run_default_scheduler(self):
    #     comp = Composition()
    #     A = IntegratorMechanism(default_variable=1.0, function=Linear(slope=5.0))
    #     B = TransferMechanism(function=Linear(slope=5.0))
    #     comp.add_mechanism(A)
    #     comp.add_mechanism(B)
    #     comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
    #     comp._analyze_graph()
    #     inputs_dict = {A: [[5], [4], [3]]}
    #     output = comp.run(
    #         inputs=inputs_dict,
    #         num_trials=3
    #     )
    #     assert 75 == output[0][0]

    # def test_multilayer_no_learning(self):
    #     Input_Layer = TransferMechanism(
    #         name='Input Layer',
    #         function=Logistic,
    #         default_variable=np.zeros((2,)),
    #     )
    #
    #     Hidden_Layer_1 = TransferMechanism(
    #         name='Hidden Layer_1',
    #         function=Logistic(),
    #         default_variable=np.zeros((5,)),
    #     )
    #
    #     Hidden_Layer_2 = TransferMechanism(
    #         name='Hidden Layer_2',
    #         function=Logistic(),
    #         default_variable=[0, 0, 0, 0],
    #     )
    #
    #     Output_Layer = TransferMechanism(
    #         name='Output Layer',
    #         function=Logistic,
    #         default_variable=[0, 0, 0],
    #     )
    #
    #     Input_Weights_matrix = (np.arange(2 * 5).reshape((2, 5)) + 1) / (2 * 5)
    #
    #     Input_Weights = MappingProjection(
    #         name='Input Weights',
    #         matrix=Input_Weights_matrix,
    #     )
    #
    #     comp = Composition()
    #     comp.add_mechanism(Input_Layer)
    #     comp.add_mechanism(Hidden_Layer_1)
    #     comp.add_mechanism(Hidden_Layer_2)
    #     comp.add_mechanism(Output_Layer)
    #
    #     comp.add_projection(Input_Layer, Input_Weights, Hidden_Layer_1)
    #     comp.add_projection(Hidden_Layer_1, MappingProjection(), Hidden_Layer_2)
    #     comp.add_projection(Hidden_Layer_2, MappingProjection(), Output_Layer)
    #
    #     comp._analyze_graph()
    #     stim_list = {Input_Layer: [[-1, 30]]}
    #     sched = Scheduler(composition=comp)
    #     output = comp.run(
    #         inputs=stim_list,
    #         scheduler_processing=sched,
    #         num_trials=10
    #     )
    #
    #     # p = process(
    #     #     default_variable=[0, 0],
    #     #     pathway=[
    #     #         Input_Layer,
    #     #         # The following reference to Input_Weights is needed to use it in the pathway
    #     #         #    since it's sender and receiver args are not specified in its declaration above
    #     #         Input_Weights,
    #     #         Hidden_Layer_1,
    #     #         # No projection specification is needed here since the sender arg for Middle_Weights
    #     #         #    is Hidden_Layer_1 and its receiver arg is Hidden_Layer_2
    #     #         # Middle_Weights,
    #     #         Hidden_Layer_2,
    #     #         # Output_Weights does not need to be listed for the same reason as Middle_Weights
    #     #         # If Middle_Weights and/or Output_Weights is not declared above, then the process
    #     #         #    will assign a default for missing projection
    #     #         # Output_Weights,
    #     #         Output_Layer
    #     #     ],
    #     #     clamp_input=SOFT_CLAMP,
    #     #     target=[0, 0, 1]
    #     #
    #     #
    #     # )
    #     #
    #     # s.run(
    #     #     num_executions=10,
    #     #     inputs=stim_list,
    #     # )
    #
    #     expected_Output_Layer_output = [np.array([0.97988347, 0.97988347, 0.97988347])]
    #
    #     np.testing.assert_allclose(expected_Output_Layer_output, Output_Layer.output_values)


class TestOldSyntax:

    # new syntax pathway, old syntax system
    def test_one_pathway_inside_one_system_old_syntax(self):
        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()

        # Create a system using the old factory method syntax
        sys = system(processes=[myPath])

        # assign input to origin mech
        stimulus = {myMech1: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 8 == output[0][0]

    # old syntax pathway (process)
    def test_one_process_old_syntax(self):

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # create a Pathway | blank slate for composition
        myPath = process(pathway=[myMech1, myMech2, myMech3])

        # assign input to origin mech
        stimulus = {myMech1: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = myPath.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 8 == output[0][0]

    # old syntax pathway (process), old syntax system
    def test_one_process_inside_one_system_old_syntax(self):
        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # create a Pathway | blank slate for composition
        myPath = process(pathway=[myMech1, myMech2, myMech3])

        # Create a system using the old factory method syntax
        sys = system(processes=[myPath])

        # assign input to origin mech
        stimulus = {myMech1: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 8 == output[0][0]

    # old syntax pathway (process), old syntax system; 2 processes in series
    def test_two_processes_in_series_in_system_old_syntax(self):

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8
        # create a Pathway | blank slate for composition
        myPath = process(pathway=[myMech1, myMech2, myMech3])

        # create a Pathway | blank slate for composition
        myPath2 = Pathway()

        # create mechanisms to add to myPath2
        myMech4 = TransferMechanism(function=Linear(slope=2.0))  # 8 x 2 = 16
        myMech5 = TransferMechanism(function=Linear(slope=2.0))  # 16 x 2 = 32
        myMech6 = TransferMechanism(function=Linear(slope=2.0))  # 32 x 2 = 64

        # add mechanisms to myPath2 with default MappingProjections between them
        myPath2.add_linear_processing_pathway([myMech4, myMech5, myMech6])

        # analyze graph (assign roles)
        myPath2._analyze_graph()

        # Create a system using the old factory method syntax
        sys = system(processes=[myPath, myPath2])

        # connect the two pathways in series
        sys.add_projection(sender=myMech3,
                           projection=MappingProjection(sender=myMech3, receiver=myMech4),
                           receiver=myMech4)
        # assign input to origin mech
        stimulus = {myMech1: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 64 == output[0][0]

    # old syntax pathway (process), old syntax system; 2 processes converge
    def test_two_processes_converge_in_system_old_syntax(self):
        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()

        # create a Pathway | blank slate for composition
        myPath2 = Pathway()

        # create mechanisms to add to myPath2
        myMech4 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech5 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4

        # add mechanisms to myPath2 with default MappingProjections between them
        myPath2.add_linear_processing_pathway([myMech4, myMech5, myMech3])

        # analyze graph (assign roles)
        myPath2._analyze_graph()

        # Create a system using the old factory method syntax
        sys = system(processes=[myPath, myPath2])

        # assign input to origin mech
        stimulus = {myMech1: [[1]],
                    myMech4: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 16 == output[0][0]


class TestNestedCompositions:

    def test_one_pathway_inside_one_system(self):
        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()

        # assign input to origin mech
        stimulus = {myMech1: [[1]]}

        # execute path (just for comparison)
        print("EXECUTING PATH: ")
        myPath.run(inputs=stimulus)

        # create a Systemm | blank slate for composition
        sys = Systemm()

        # add a Pathway [myPath] to the Systemm [sys]
        sys.add_pathway(myPath)

        # execute the Systemm
        output = sys.run(
            inputs=stimulus,
        )
        assert 8 == output[0][0]

    def test_two_paths_converge_one_system(self):

        # mech1 ---> mech2 --
        #                   --> mech3
        # mech4 ---> mech5 --

        # 1x2=2 ---> 2x2=4 --
        #                   --> (4+4)x2=16
        # 1x2=2 ---> 2x2=4 --

        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()

        myPath2 = Pathway()
        myMech4 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech5 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myPath.add_linear_processing_pathway([myMech4, myMech5, myMech3])
        myPath._analyze_graph()

        sys = Systemm()
        sys.add_pathway(myPath)
        sys.add_pathway(myPath2)
        # assign input to origin mechs
        stimulus = {myMech1: [[1]], myMech4: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 16 == output[0][0]

    def test_two_paths_in_series_one_system(self):

        # [ mech1 --> mech2 --> mech3 ] -->   [ mech4  -->  mech5  -->  mech6 ]
        #   1x2=2 --> 2x2=4 --> 4x2=8   --> (8+1)x2=18 --> 18x2=36 --> 36*2=64
        #                                X
        #                                |
        #                                1
        # (if mech4 were recognized as an origin mech, and used SOFT_CLAMP, we would expect the final result to be 72)
        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()

        myPath2 = Pathway()
        myMech4 = TransferMechanism(function=Linear(slope=2.0))
        myMech5 = TransferMechanism(function=Linear(slope=2.0))
        myMech6 = TransferMechanism(function=Linear(slope=2.0))
        myPath.add_linear_processing_pathway([myMech4, myMech5, myMech6])
        myPath._analyze_graph()

        sys = Systemm()
        sys.add_pathway(myPath)
        sys.add_pathway(myPath2)
        sys.add_projection(sender=myMech3, projection=MappingProjection(sender=myMech3,
                                                                        receiver=myMech4), receiver=myMech4)
        # assign input to origin mechs
        # myMech4 ignores its input from the outside world because it is no longer considered an origin!
        stimulus = {myMech1: [[1]]}
        sys._analyze_graph()
        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 64 == output[0][0]

    def test_two_paths_converge_one_system_scheduling_matters(self):

        # mech1 ---> mech2 --
        #                   --> mech3
        # mech4 ---> mech5 --

        # 1x2=2 ---> 2x2=4 --
        #                   --> (4+4)x2=16
        # 1x2=2 ---> 2x2=4 --

        # create a Pathway | blank slate for composition
        myPath = Pathway()

        # create mechanisms to add to myPath
        myMech1 = IntegratorMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech2 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myMech3 = TransferMechanism(function=Linear(slope=2.0))  # 4 x 2 = 8

        # add mechanisms to myPath with default MappingProjections between them
        myPath.add_linear_processing_pathway([myMech1, myMech2, myMech3])

        # analyze graph (assign roles)
        myPath._analyze_graph()
        myPathScheduler = Scheduler(composition=myPath)
        myPathScheduler.add_condition(myMech2, AfterNCalls(myMech1, 2))

        myPath.run(inputs={myMech1: 1}, scheduler_processing=myPathScheduler)
        myPath.run(inputs={myMech1: [[1]]}, scheduler_processing=myPathScheduler)
        myPath2 = Pathway()
        myMech4 = TransferMechanism(function=Linear(slope=2.0))  # 1 x 2 = 2
        myMech5 = TransferMechanism(function=Linear(slope=2.0))  # 2 x 2 = 4
        myPath.add_linear_processing_pathway([myMech4, myMech5, myMech3])
        myPath._analyze_graph()

        sys = Systemm()
        sys.add_pathway(myPath)
        sys.add_pathway(myPath2)
        # assign input to origin mechs
        stimulus = {myMech1: [[1]], myMech4: [[1]]}

        # schedule = Scheduler(composition=sys)
        output = sys.run(
            inputs=stimulus,
            # scheduler_processing=schedule
        )
        assert 16 == output[0][0]


class TestCompositionInterface:

    def test_one_input_state_per_origin_two_origins(self):

        # 5 -#1-> A --^ --> C --
        #                       ==> E
        # 5 ----> B ------> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = TransferMechanism(name="A",
                              function=Linear(slope=1.0)
                              )

        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [[[5.]]],
            # two trials of one input state each
            #        TRIAL 1     TRIAL 2
            # A : [ [ [0,0] ] , [ [0, 0] ]  ]

            # two trials of multiple input states each
            #        TRIAL 1     TRIAL 2

            #       TRIAL1 IS1      IS2      IS3     TRIAL2    IS1      IS2
            # A : [ [     [0,0], [0,0,0], [0,0,0,0] ] ,     [ [0, 0],   [0] ]  ]
            B: [[[5.]]]
        }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 250 == output[0][0]

    def test_updating_input_values_for_second_execution(self):
        # 5 -#1-> A --^ --> C --
        #                       ==> E
        # 5 ----> B ------> D --

        # 5 x 1 = 5 ----> 5 x 5 = 25 --
        #                                25 + 25 = 50  ==> 50 * 5 = 250
        # 5 * 1 = 5 ----> 5 x 5 = 25 --

        comp = Composition()
        A = TransferMechanism(name="A",
                              function=Linear(slope=1.0)
                              )

        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [[[5.]]],
            B: [[[5.]]]
        }
        sched = Scheduler(composition=comp)

        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        inputs_dict2 = {
            A: [[[2.]]],
            B: [[[2.]]]
        }
        output2 = comp.run(
            inputs=inputs_dict2,
            scheduler_processing=sched
        )

        assert 250 == output[0][0]
        assert 100 == output2[0][0]

    def test_adding_origin_for_second_execution(self):

        comp = Composition()
        A = TransferMechanism(name="A",
                              function=Linear(slope=1.0)
                              )

        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        D = TransferMechanism(name="D", function=Linear(slope=5.0))
        E = TransferMechanism(name="E", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_mechanism(D)
        comp.add_projection(A, MappingProjection(sender=A, receiver=C), C)
        comp.add_projection(B, MappingProjection(sender=B, receiver=D), D)
        comp.add_mechanism(E)
        comp.add_projection(C, MappingProjection(sender=C, receiver=E), E)
        comp.add_projection(D, MappingProjection(sender=D, receiver=E), E)
        comp._analyze_graph()
        inputs_dict = {
            A: [[[5.]]],
            # two trials of one input state each
            #        TRIAL 1     TRIAL 2
            # A : [ [ [0,0] ] , [ [0, 0] ]  ]

            # two trials of multiple input states each
            #        TRIAL 1     TRIAL 2

            #       TRIAL1 IS1      IS2      IS3     TRIAL2    IS1      IS2
            # A : [ [     [0,0], [0,0,0], [0,0,0,0] ] ,     [ [0, 0],   [0] ]  ]
            B: [[[5.]]]
        }
        sched = Scheduler(composition=comp)

        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        # add a new branch to the composition
        F = TransferMechanism(name="F", function=Linear(slope=2.0))
        G = TransferMechanism(name="G", function=Linear(slope=2.0))
        comp.add_mechanism(F)
        comp.add_mechanism(G)
        comp.add_projection(sender=F, projection=MappingProjection(sender=F, receiver=G), receiver=G)
        comp.add_projection(sender=G, projection=MappingProjection(sender=G, receiver=E), receiver=E)

        # reassign roles
        comp._analyze_graph()

        # execute the updated composition
        inputs_dict2 = {
            A: [[[1.]]],
            B: [[[2.]]],
            F: [[[3.]]]
        }

        sched = Scheduler(composition=comp)
        output2 = comp.run(
            inputs=inputs_dict2,
            scheduler_processing=sched
        )

        assert 250 == output[0][0]
        assert 135 == output2[0][0]

    def test_changing_origin_for_second_execution(self):

        comp = Composition()
        A = TransferMechanism(name="A",
                              function=Linear(slope=1.0)
                              )

        B = TransferMechanism(name="B", function=Linear(slope=1.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp.add_projection(B, MappingProjection(sender=B, receiver=C), C)
        comp._analyze_graph()
        inputs_dict = {A: [[[5.]]]}
        sched = Scheduler(composition=comp)

        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 25 == output[0][0]

        # add a new origin to the composition
        F = TransferMechanism(name="F", function=Linear(slope=2.0))
        comp.add_mechanism(F)
        comp.add_projection(sender=F, projection=MappingProjection(sender=F, receiver=A), receiver=A)

        # reassign roles
        comp._analyze_graph()

        # execute the updated composition
        inputs_dict2 = {F: [[[3.]]]}

        sched = Scheduler(composition=comp)
        output2 = comp.run(
            inputs=inputs_dict2,
            scheduler_processing=sched
        )

        projections_to_A = []
        expected_projections_to_A = [("(OutputState RESULT)", "(InputState Default_InputStat)")]
        for input_state in A.input_states:
            for p_a in input_state.path_afferents:
                projections_to_A.append((str(p_a.sender), str(p_a.receiver)))

        assert projections_to_A == expected_projections_to_A
        assert 30 == output2[0][0]

    def test_two_input_states_new_inputs_second_trial(self):

        comp = Composition()
        my_fun = Linear(
            # default_variable=[[0], [0]],
            # ^ setting default_variable on the function actually does not matter -- does the mechanism update it?
            slope=1.0)
        A = TransferMechanism(name="A",
                              default_variable=[[0], [0]],
                              input_states=[{NAME: "Input State 1",
                                             },
                                            {NAME: "Input State 2",
                                             }],
                              function=my_fun
                              )
        comp.add_mechanism(A)
        comp._analyze_graph()
        inputs_dict = {A: [[[5.], [5.]]], }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        inputs_dict2 = {A: [[[2.], [4.]]], }
        output2 = comp.run(
            inputs=inputs_dict2,
            scheduler_processing=sched
        )
        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]
        assert 5 == output[0][0]
        assert 2 == output2[0][0]

    def test_two_input_states_new_origin_second_trial(self):

        # A --> B --> C

        comp = Composition()
        my_fun = Linear(
            # default_variable=[[0], [0]],
            # ^ setting default_variable on the function actually does not matter -- does the mechanism update it?
            slope=1.0)
        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=[
                {NAME: "Input State 1", },
                {NAME: "Input State 2", }
            ],
            function=my_fun
        )

        B = TransferMechanism(name="B", function=Linear(slope=2.0))
        C = TransferMechanism(name="C", function=Linear(slope=5.0))
        comp.add_mechanism(A)
        comp.add_mechanism(B)
        comp.add_mechanism(C)
        comp.add_projection(A, MappingProjection(sender=A, receiver=B), B)
        comp.add_projection(B, MappingProjection(sender=B, receiver=C), C)
        comp._analyze_graph()
        inputs_dict = {A: [[[5.], [5.]]],
                       }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 5. == A.input_states[0].value
        assert 5. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 5. == A.variable[0]
        assert 5. == A.variable[1]
        assert 50 == output[0][0]

        # A --> B --> C
        #     ^
        # D __|

        D = TransferMechanism(
            name="D",
            default_variable=[[0], [0]],
            input_states=[
                {NAME: "Input State 1", },
                {NAME: "Input State 2", }
            ],
            function=my_fun
        )
        comp.add_mechanism(D)
        comp.add_projection(D, MappingProjection(sender=D, receiver=B), B)
        # Need to analyze graph again (identify D as an origin so that we can assign input) AND create the scheduler
        # again (sched, even though it is tied to comp, will not update according to changes in comp)
        comp._analyze_graph()
        sched = Scheduler(composition=comp)
        inputs_dict2 = {
            A: [[[2.], [4.]]],
            D: [[[2.], [4.]]]
        }
        output2 = comp.run(
            inputs=inputs_dict2,
            scheduler_processing=sched
        )
        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]
        assert 2. == D.input_states[0].value
        assert 4. == D.input_states[1].value
        assert "Input State 1" == D.input_states[0].name
        assert "Input State 2" == D.input_states[1].name
        assert 2. == D.variable[0]
        assert 4. == D.variable[1]
        assert 40 == output2[0][0]


class TestInputStateSpecifications:

    def test_two_input_states_created_with_dicionaries(self):

        comp = Composition()
        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=[
                {NAME: "Input State 1", },
                {NAME: "Input State 2", }
            ],
            function=Linear(slope=1.0)
            # specifying default_variable on the function doesn't seem to matter?
        )

        comp.add_mechanism(A)

        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]],
                       }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )
        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]

    # def test_two_input_states_one_origin_different_shapes(self):
    #
    #     comp = Composition()
    #     A = TransferMechanism(name="A",
    #                           default_variable=[[0], [0,0,0]],
    #                           input_states=[{NAME: "Input State 1",
    #                                          },
    #                                         {NAME: "Input State 2",
    #                                          }],
    #                           function=Linear(slope=1.0, default_variable=[[0], [0,0,0]])
    #                           # specifying default_variable on the function doesn't seem to matter?
    #                           )
    #
    #     comp.add_mechanism(A)
    #
    #     comp._analyze_graph()
    #     inputs_dict = {A: [[[2.], [4., 5., 6.]]],
    #                   }
    #     sched = Scheduler(composition=comp)
    #     output = comp.run(
    #         inputs=inputs_dict,
    #         scheduler_processing=sched
    #         )
    #
    #     assert 2. == A.input_states[0].value
    #     assert [4.,5.,6.] == A.input_states[1].value
    #     assert "Input State 1" == A.input_states[0].name
    #     assert "Input State 2" == A.input_states[1].name
    #     assert 2. == A.variable[0]
    #     assert [4.,5.,6.] == A.variable[1]
    #
    #     assert 2 == output[0][0]

    def test_two_input_states_created_first_with_deferred_init(self):
        comp = Composition()

        # create mechanism A
        I1 = InputState(
            name="Input State 1",
            reference_value=[0]
        )
        I2 = InputState(
            name="Input State 2",
            reference_value=[0]
        )
        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=[I1, I2],
            function=Linear(slope=1.0)
        )

        # add mech A to composition
        comp.add_mechanism(A)

        # get comp ready to run (identify roles, create sched, assign inputs)
        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]],
                       }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]

    def test_two_input_states_created_with_keyword(self):
        comp = Composition()

        # create mechanism A

        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=[INPUT_STATE, INPUT_STATE],
            function=Linear(slope=1.0)
        )

        # add mech A to composition
        comp.add_mechanism(A)

        # get comp ready to run (identify roles, create sched, assign inputs)
        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]],
                       }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "InputState" == A.input_states[0].name
        assert "InputState-1" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]

    def test_two_input_states_created_with_strings(self):
        comp = Composition()

        # create mechanism A

        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=["Input State 1", "Input State 2"],
            function=Linear(slope=1.0)
        )

        # add mech A to composition
        comp.add_mechanism(A)

        # get comp ready to run (identify roles, create sched, assign inputs)
        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]], }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Input State 1" == A.input_states[0].name
        assert "Input State 2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]

    def test_two_input_states_created_with_values(self):
        comp = Composition()

        # create mechanism A

        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            input_states=[[0.], [0.]],
            function=Linear(slope=1.0)
        )

        # add mech A to composition
        comp.add_mechanism(A)

        # get comp ready to run (identify roles, create sched, assign inputs)
        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]], }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Default_InputStat-1" == A.input_states[0].name
        assert "Default_InputStat-2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]

    def test_two_input_states_implied_by_default_variable(self):
        comp = Composition()

        # create mechanism A

        A = TransferMechanism(
            name="A",
            default_variable=[[0], [0]],
            function=Linear(slope=1.0)
        )

        # add mech A to composition
        comp.add_mechanism(A)

        # get comp ready to run (identify roles, create sched, assign inputs)
        comp._analyze_graph()
        inputs_dict = {A: [[[2.], [4.]]], }
        sched = Scheduler(composition=comp)
        output = comp.run(
            inputs=inputs_dict,
            scheduler_processing=sched
        )

        assert 2. == A.input_states[0].value
        assert 4. == A.input_states[1].value
        assert "Default_InputStat-1" == A.input_states[0].name
        assert "Default_InputStat-2" == A.input_states[1].name
        assert 2. == A.variable[0]
        assert 4. == A.variable[1]

        assert 2 == output[0][0]


class TestParamsDict:

    def test_get_function_param_on_mechanism_by_Param(self):
        A = TransferMechanism(
            function=Linear(
                slope=2,
                intercept=3,
            ),
        )

        assert A.get_param_value(Linear.Params.slope) == 2
        assert A.get_param_value(Linear.Params.intercept) == 3

    def test_get_function_param_on_mechanism_by_string(self):
        A = TransferMechanism(
            function=Linear(
                slope=2,
                intercept=3,
            ),
        )

        assert A.get_param_value('slope') == 2
        assert A.get_param_value('intercept') == 3

    def test_run_integrator_two_contexts(self):
        comp1 = Composition()
        comp2 = Composition()
        A = IntegratorMechanism(default_variable=1.0)
        comp1.add_mechanism(A)
        comp2.add_mechanism(A)
        inputs_dict = {A: [[5], [5], [5]]}
        output1 = comp1.run(
            inputs=inputs_dict,
        )
        output2 = comp2.run(
            inputs=inputs_dict,
        )
        assert 4.375 == output1[0][0]
        assert 4.375 == output2[0][0]

    def test_run_integrator_two_contexts_with_base(self):
        comp1 = Composition()
        A = IntegratorMechanism(default_variable=1.0)
        comp1.add_mechanism(A)
        inputs_dict = {A: [[5], [5], [5]]}
        output1 = comp1.run(
            inputs=inputs_dict,
        )
        output2 = comp1.run(
            inputs=inputs_dict,
            execution_id=uuid.uuid4(),
            base_execution_id=comp1.default_execution_id,
        )
        assert 4.375 == output1[0][0]
        assert 4.921875 == output2[0][0]

        output1 = comp1.run(
            inputs=inputs_dict,
        )
        assert 4.921875 == output1[0][0]
