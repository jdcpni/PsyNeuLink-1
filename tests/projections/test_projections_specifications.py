import psyneulink as pnl

class TestProjectionSpecificationFormats:

    def test_multiple_modulatory_projection_specs(self):

        M = pnl.DDM(name='MY DDM')
        C = pnl.ControlMechanism(control_signals=[{pnl.PROJECTIONS: [M.parameter_states[pnl.DRIFT_RATE],
                                                                     M.parameter_states[pnl.THRESHOLD]]}])
        G = pnl.GatingMechanism(gating_signals=[{pnl.PROJECTIONS: [M.output_states[pnl.DECISION_VARIABLE],
                                                                     M.output_states[pnl.RESPONSE_TIME]]}])
        
        assert len(C.control_signals)==1
        assert len(C.control_signals[0].efferents)==2
        assert M.parameter_states[pnl.DRIFT_RATE].mod_afferents[0]==C.control_signals[0].efferents[0]
        assert M.parameter_states[pnl.THRESHOLD].mod_afferents[0]==C.control_signals[0].efferents[1]
        assert len(G.gating_signals)==1
        assert len(G.gating_signals[0].efferents)==2
        assert M.output_states[pnl.DECISION_VARIABLE].mod_afferents[0]==G.gating_signals[0].efferents[0]
        assert M.output_states[pnl.RESPONSE_TIME].mod_afferents[0]==G.gating_signals[0].efferents[1]

    def test_multiple_modulatory_projections_with_state_name(self):
        
        M = pnl.DDM(name='MY DDM')
        C = pnl.ControlMechanism(control_signals=[{'DECISION_CONTROL':[M.parameter_states[pnl.DRIFT_RATE],
                                                                       M.parameter_states[pnl.THRESHOLD]]}])
        G = pnl.GatingMechanism(gating_signals=[{'DDM_OUTPUT_GATE':[M.output_states[pnl.DECISION_VARIABLE],
                                                                    M.output_states[pnl.RESPONSE_TIME]]}])
        assert len(C.control_signals)==1
        assert C.control_signals[0].name=='DECISION_CONTROL'
        assert len(C.control_signals[0].efferents)==2
        assert M.parameter_states[pnl.DRIFT_RATE].mod_afferents[0]==C.control_signals[0].efferents[0]
        assert M.parameter_states[pnl.THRESHOLD].mod_afferents[0]==C.control_signals[0].efferents[1]
        assert len(G.gating_signals)==1
        assert G.gating_signals[0].name=='DDM_OUTPUT_GATE'
        assert len(G.gating_signals[0].efferents)==2
        assert M.output_states[pnl.DECISION_VARIABLE].mod_afferents[0]==G.gating_signals[0].efferents[0]
        assert M.output_states[pnl.RESPONSE_TIME].mod_afferents[0]==G.gating_signals[0].efferents[1]

    def test_multiple_modulatory_projections_with_mech_and_state_name_specs(self):

        M = pnl.DDM(name='MY DDM')
        C = pnl.ControlMechanism(control_signals=[{pnl.MECHANISM: M,
                                                   pnl.PARAMETER_STATES: [pnl.DRIFT_RATE, pnl.THRESHOLD]}])
        G = pnl.GatingMechanism(gating_signals=[{pnl.MECHANISM: M,
                                                 pnl.OUTPUT_STATES: [pnl.DECISION_VARIABLE, pnl.RESPONSE_TIME]}])
        assert len(C.control_signals)==1
        assert len(C.control_signals[0].efferents)==2
        assert M.parameter_states[pnl.DRIFT_RATE].mod_afferents[0]==C.control_signals[0].efferents[0]
        assert M.parameter_states[pnl.THRESHOLD].mod_afferents[0]==C.control_signals[0].efferents[1]
        assert len(G.gating_signals)==1
        assert len(G.gating_signals[0].efferents)==2
        assert M.output_states[pnl.DECISION_VARIABLE].mod_afferents[0]==G.gating_signals[0].efferents[0]
        assert M.output_states[pnl.RESPONSE_TIME].mod_afferents[0]==G.gating_signals[0].efferents[1]

    def test_mapping_projection_with_mech_and_state_name_specs(self):
         R1 = pnl.TransferMechanism(output_states=['OUTPUT_1', 'OUTPUT_2'])
         R2 = pnl.TransferMechanism(default_variable=[[0],[0]],
                                    input_states=['INPUT_1', 'INPUT_2'])
         T = pnl.TransferMechanism(input_states=[{pnl.MECHANISM: R1,
                                                  pnl.OUTPUT_STATES: ['OUTPUT_1', 'OUTPUT_2']}],
                                   output_states=[{pnl.MECHANISM:R2,
                                                   pnl.INPUT_STATES: ['INPUT_1', 'INPUT_2']}])
         assert len(R1.output_states)==2
         assert len(R2.input_states)==2
         assert len(T.input_states)==1
         for input_state in T.input_states:
             for projection in input_state.path_afferents:
                 assert projection.sender.owner is R1
         assert len(T.output_states)==1
         for output_state in T.output_states:
             for projection in output_state.efferents:
                 assert projection.receiver.owner is R2