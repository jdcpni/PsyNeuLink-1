# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
#
# ***************************************************  DDM *************************************************************
#

import numpy as np
# from numpy import sqrt, random, abs, tanh, exp
from numpy import sqrt, abs, tanh, exp
from PsyNeuLink.Functions.Mechanisms.ProcessingMechanisms.ProcessingMechanism import *

# DDM parameter keywords:
kwDDM_DriftRate = "DDM_DriftRate"
kwDDM_DriftRateVariability = 'DDM_DriftRateVariability'
kwDDM_Threshold = "DDM_Threshold"
kwDDM_ThresholdVariability = 'DDM_ThresholdRateVariability'
kwKwDDM_StartingPoint = "KwDDM_StartingPoint"
kwKwDDM_StartingPointVariability = "KwDDM_StartingPointVariability"
kwDDM_Noise = "DDM_Noise"
kwDDM_T0 = "DDM_T0"
kwDDM_AnalyticSolution = "DDM_AnalyticSolution"

# DDM solution options:
kwDDM_BogaczEtAl = "DDM_BogaczEtAl"
kwDDM_NavarroAndFuss = "DDM_NavarroAndFuss"
AnalyticSolutions = [kwDDM_BogaczEtAl, kwDDM_NavarroAndFuss]

# DDM outputs (used to create and name outputStates):
kwDDM_DecisionVariable = "DDM_DecisionVariable"
kwDDM_Error_Rate = "DDM_Error_Rate"
kwDDM_Probability_upperBound = "DDM_Probability_upperBound"
kwDDM_Probability_lowerBound = "DDM_Probability_lowerBound"
kwDDM_RT_Mean = "DDM_RT_Mean"
kwDDM_RT_Correct_Mean = "DDM_RT_Correct_Mean"
kwDDM_RT_Correct_Variance = "DDM_RT_Correct_Variance"
kwDDM_Total_Allocation = "DDM_Total_Allocation"
kwDDM_Total_Cost = "DDM_Total_Cost"

# TBI:
# # DDM variability parameter structure
# DDM_ParamVariabilityTuple = namedtuple('DDMParamVariabilityTuple', 'variability distribution')

# DDM default parameter values:
DDM_DEFAULT_DRIFT_RATE = 1.0
DDM_DEFAULT_THRESHOLD = 1.0
DDM_DEFAULT_STARTING_POINT = 0.0
DDM_DEFAULT_T0 = .200
DDM_DEFAULT_NOISE = 0.5

class DDM_Output(AutoNumber):
    DECISION_VARIABLE = ()
    RT_MEAN = ()
    ER_MEAN = ()
    P_UPPER_MEAN = ()
    P_LOWER_MEAN = ()
    RT_CORRECT_MEAN = ()
    RT_CORRECT_VARIANCE = ()
    TOTAL_COST = ()
    TOTAL_ALLOCATION = ()
    NUM_OUTPUT_VALUES = ()

# Results from Navarro and Fuss DDM solution (indices for return value tuple)
class NF_Results(AutoNumber):
    MEAN_ER = ()
    MEAN_DT = ()
    PLACEMARKER = ()
    MEAN_CORRECT_RT = ()
    MEAN_CORRECT_VARIANCE = ()
    MEAN_CORRECT_SKEW_RT = ()


class DDMError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class DDM(ProcessingMechanism_Base):
# DOCUMENT:   COMBINE WITH INITIALIZATION WITH PARAMETERS
#                    ADD INFO ABOUT B VS. N&F
#                    ADD instantiate_output_states TO INSTANCE METHODS, AND EXPLAIN RE: NUM OUTPUT VALUES FOR B VS. N&F
    """Implement DDM subclass

    Description:
        DDM is a subclass Type of the Mechanism Category of the Function class
        It implements a Mechanism for several forms of the Drift Diffusion Model (DDM) for
            two alternative forced choice (2AFC) decision making:
            - Bogacz et al. (2006) analytic solution (see kwDDM_BogaczEtAl option below):
                generates error rate (ER) and decision time (DT);
                ER is used to stochastically generate a decision outcome (+ or - valued) on every run
            - Navarro and Fuss (2009) analytic solutoin (see kwDDM_NavarroAndFuss:
                generates error rate (ER), decision time (DT) and their distributions;
                ER is used to stochastically generate a decision outcome (+ or - valued) on every run
            [TBI: - stepwise integrator that simulates each step of the integration process

    Instantiation:
        - A DDM mechanism can be instantiated in several ways:
            - directly, by calling DDM()
            - as the default mechanism (by calling mechanism())

    Initialization arguments:
        In addition to standard arguments params (see Mechanism), DDM also implements the following params:
        - params (dict):
            + kwDDM_AnalyticSolution (str keyword):
                specifies analytic solution of the DDM to use;
                value must also be one of the following keywords:
                + kwDDM_BogaczEtAl: generates mean reaction time (RT) and mean error rate (ER) as described in:
                    Bogacz, R., Brown, E., Moehlis, J., Holmes, P., & Cohen, J. D. (2006). The physics of optimal
                        decision making: a formal analysis of models of performance in two-alternative forced-choice
                        tasks.  Psychological review, 113(4), 700.
                    Notes:
                    * requires that DDM.execute be called with time_scale = TimeScale.TRIAL
                + kwDDM_NavarroAndFuss:  gives mean RT and ER as well as distributions as described in:
                    Navarro, D. J., and Fuss, I. G. "Fast and accurate calculations for first-passage times in
                        Wiener diffusion models." Journal of Mathematical Psychology 53.4 (2009): 222-230.
                    Notes:
                    * requires that matLab engine be installed
                    * requires that DDM.execute be called with time_scale = TimeScale.TRIAL
                [TBI: + kwIntegrate: executes step-wise intregation process, one step per CentralClock.time_step
                    Notes:
                    * requires that matLab engine be installed
                    * requires that DDM.execute be called with time_scale = TimeScale.REAL_TIME]
            + kwExecuteMethodParams (dict):
                + kwDDM_DriftRate (float):   (default: DDM_DEFAULT_DRIFT_RATE)
                    specifies internal ("attentional") component of the drift rate
                    that is added to the input (self.variable) on every call to DDM.execute()
                + kwKwDDM_StartingPoint (float): (default: DDM_DEFAULT_STARTING_POINT)
                    specifies intitial value of decision variable, converted to "bias" term in DDM
                + kwDDM_Threshold (float): (default: DDM_DEFAULT_THRESHOLD)
                    specifies stopping value of decision variable for integration process
                + kwDDM_Noise (float): (default: DDM_DEFAULT_NOISE)
                    specifies internal noise term for integration process
                + kwDDM_T0 (float): (default: DDM_DEFAULT_T0
                    specifies non-decision time added to total response time
        Notes:
        *  params can be set in the standard way for any Function subclass:
            - params provided in param_defaults at initialization will be assigned as paramInstanceDefaults
                 and used for paramsCurrent unless and until the latter are changed in a function call
            - paramInstanceDefaults can be later modified using assign_defaults
            - params provided in a function call (to execute or adjust) will be assigned to paramsCurrent

    MechanismRegistry:
        All instances of DDM are registered in MechanismRegistry, which maintains an entry for the subclass,
          a count for all instances of it, and a dictionary of those instances

    Naming:
        Instances of DDM can be named explicitly (using the name='<name>' argument).
        If this argument is omitted, it will be assigned "DDM" with a hyphenated, indexed suffix ('DDM-n')

    Execution:
        - Calculates either:
            analytic solutions:  estimated outcome for a run of the integration process (time_scale = TimeScale.TRIAL)
            integration process: step-wise trajectory of the integration process (time_scale = TimeScale.REAL_TIME)
        - self.value (and values of outputStates) contain each outcome value (e.g., ER, DT, etc.)
        - self.execute returns self.value
        Notes:
        * DDM handles "runtime" parameters (specified in call to execute method) differently than standard Functions:
            any specified params are kept separate from paramsCurrent (Which are not overridden)
            if the EXECUTE_METHOD_RUN_TIME_PARMS option is set, they are added to the current value of the
                corresponding ParameterState;  that is, they are combined additively with controlSignal output

    Class attributes:
        + functionType (str): DDM
        + classPreference (PreferenceSet): DDM_PreferenceSet, instantiated in __init__()
        + classPreferenceLevel (PreferenceLevel): PreferenceLevel.TYPE
        + variableClassDefault (value):  DDM_DEFAULT_STARTING_POINT
        + paramClassDefaults (dict): {kwTimeScale: TimeScale.TRIAL,
                                      kwDDM_AnalyticSolution: kwDDM_BogaczEtAl,
                                      kwExecuteMethodParams:{kwDDM_DriftRate: DDM_DEFAULT_DRIFT_RATE
                                                                 kwKwDDM_StartingPoint: DDM_DEFAULT_STARTING_POINT
                                                                 kwDDM_Threshold: DDM_DEFAULT_THRESHOLD
                                                                 kwDDM_Noise: DDM_DEFAULT_NOISE
                                                                 kwDDM_T0: DDM_DEFAULT_T0}}
        + paramNames (dict): names as above

    Class methods:
        None

    Instance attributes: none
        + variable (value) - input to mechanism's execute method (default:  DDM_DEFAULT_STARTING_POINT)
        + value (value) - output of execute method
        + name (str) - if it is not specified as an arg, a default based on the class is assigned in register_category
        + prefs (PreferenceSet) - if not specified as an arg, a default set is created by copying DDM_PreferenceSet

    Instance methods:
        - instantiate_execute_method(context)
            deletes params not in use, in order to restrict outputStates to those that are computed for specified params
        - execute(variable, time_scale, params, context)
            executes specified version of DDM and returns outcome values (in self.value and values of self.outputStates)
        - ou_update(particle, drift, noise, time_step_size, decay)
            single update for OU (special case l=0 is DDM) -- from Michael Shvartsman
        - ddm_update(particle, a, s, dt)
            DOCUMENTATION NEEDED
            from Michael Shvartsman
        - ddm_rt(x0, t0, a, s, z, dt)
            DOCUMENTATION NEEDED
            from Michael Shvartsman
        - ddm_distr(n, x0, t0, a, s, z, dt)
            DOCUMENTATION NEEDED
            from Michael Shvartsman
        - ddm_analytic(bais, T0, drift_rate, noise, threshold)
            DOCUMENTATION NEEDED
            from Michael Shvartsman

    """

    functionType = "DDM"

    classPreferenceLevel = PreferenceLevel.SUBTYPE
    # These will override those specified in SubtypeDefaultPreferences
    classPreferences = {
        kwPreferenceSetName: 'DDMCustomClassPreferences',
        kpReportOutputPref: PreferenceEntry(True, PreferenceLevel.SUBTYPE)}

    variableClassDefault = DDM_DEFAULT_STARTING_POINT # Sets template for variable (input)
                                                      # to be compatible with DDM_DEFAULT_STARTING_POINT

    # DDM parameter and control signal assignments):
    paramClassDefaults = Mechanism_Base.paramClassDefaults.copy()
    paramClassDefaults.update({
        kwTimeScale: TimeScale.TRIAL,
        kwDDM_AnalyticSolution: kwDDM_BogaczEtAl,
        # executeMethod is hard-coded in self.execute, but can be overridden by assigning following param:
        # kwExecuteMethod: None
        kwExecuteMethodParams:{
            kwDDM_DriftRate: DDM_DEFAULT_DRIFT_RATE, # "attentional" component
            kwKwDDM_StartingPoint: DDM_DEFAULT_STARTING_POINT,            # used as starting point
            kwDDM_Threshold: DDM_DEFAULT_THRESHOLD,  # assigned as output
            kwDDM_Noise: DDM_DEFAULT_NOISE,
            kwDDM_T0: DDM_DEFAULT_T0,
            # TBI:
            # kwDDM_DriftRateVariability: DDM_ParamVariabilityTuple(variability=0, distribution=NotImplemented),
            # kwKwDDM_StartingPointVariability: DDM_ParamVariabilityTuple(variability=0, distribution=NotImplemented),
            # kwDDM_ThresholdVariability: DDM_ParamVariabilityTuple(variability=0, distribution=NotImplemented),
        },
        kwOutputStates:[kwDDM_DecisionVariable,      # Full set specified to include Navarro and Fuss outputs
                                 kwDDM_Error_Rate,            # If Bogacz is implemented, last four are deleted
                                 kwDDM_Probability_upperBound, # Probability of hitting upper bound
                                 kwDDM_Probability_lowerBound, # Probability of hitting lower bound
                                 kwDDM_RT_Mean,               #    in instantiate_execute_method (see below)
                                 kwDDM_RT_Correct_Mean,
                                 kwDDM_RT_Correct_Variance,
                                 kwDDM_Total_Allocation,
                                 kwDDM_Total_Cost],
        # kwMonitoredOutputStates:[kwDDM_Error_Rate,(kwDDM_RT_Mean, -1, 1)]
    })

    # Set default input_value to default bias for DDM
    paramNames = paramClassDefaults.keys()

    def __init__(self,
                 default_input_value=NotImplemented,
                 params=NotImplemented,
                 name=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """Assign type-level preferences, default input value (DDM_DEFAULT_STARTING_POINT) and call super.__init__

        :param default_input_value: (value)
        :param params: (dict)
        :param name: (str)
        :param prefs: (PreferenceSet)
        """

        # Assign functionType to self.name as default;
        #  will be overridden with instance-indexed name in call to super
        if name is NotImplemented:
            self.name = self.functionType
        else:
            self.name = name
        self.functionName = self.functionType

        if default_input_value is NotImplemented:
            default_input_value = DDM_DEFAULT_STARTING_POINT

        super(DDM, self).__init__(variable=default_input_value,
                                  params=params,
                                  name=name,
                                  prefs=prefs,
                                  # context=context,
                                  context=self)

    def instantiate_execute_method(self, context=NotImplemented):
        """Delete params not in use, call super.instantiate_execute_method
        :param context:
        :return:
        """

        # If not using Navarro and Fuss, get rid of extra params:
        if self.paramsCurrent[kwDDM_AnalyticSolution] is kwDDM_BogaczEtAl:
            params = self.paramInstanceDefaults[kwOutputStates]
            try:
                del params[params.index(kwDDM_RT_Correct_Mean)]
                del params[params.index(kwDDM_RT_Correct_Variance)]
                del params[params.index(kwDDM_Total_Allocation)]
                del params[params.index(kwDDM_Total_Cost)]
            except ValueError:
                pass

        super(DDM, self).instantiate_execute_method(context=context)

    def execute(self,
                variable=NotImplemented,
                params=NotImplemented,
                time_scale = TimeScale.TRIAL,
                context=NotImplemented):
        """Execute DDM function (currently only trial-level, analytic solution)

        Execute DDM and estimate outcome or calculate trajectory of decision variable
        Currently implements only trial-level DDM (analytic solution) and returns:
            - stochastically estimated decion outcome (convert mean ER into value between 1 and -1)
            - mean ER
            - mean DT
            - mean ER and DT variabilty (kwNavarroAndFuss ony)
        Return current decision variable (self.outputState.value) and other output values (self.outputStates[].value

        Arguments:

        # CONFIRM:
        variable (float): set to self.value (= self.inputValue)
        - params (dict):  runtime_params passed from Mechanism, used as one-time value for current execution:
            + kwDDM_DriftRate (float)
            + kwDDM_Threshold (float)
            + kwDDM_Bias (float)
            + kwDDM_T0 (float)
            + kwDDM_Noise (float)
        - time_scale (TimeScale): determines "temporal granularity" with which mechanism is executed
        - context (str)

        Returns the following values in self.value (2D np.array) and in
            the value of the corresponding outputState in the self.outputStates dict:
            - decision variable (float)
            - mean error rate (float)
            - mean RT (float)
            - correct mean RT (float) - Navarro and Fuss only
            - correct mean ER (float) - Navarro and Fuss only

        :param self:
        :param variable (float)
        :param params: (dict)
        :param time_scale: (TimeScale)
        :param context: (str)
        :rtype self.outputState.value: (number)
        """

        #region GET PARAMETER VALUES
        # - convolve inputState.value (signal) w/ driftRate param value (attentional contribution to the process)
        # - assign convenience names to each param
        drift_rate = float((self.inputState.value * self.executeMethodParameterStates[kwDDM_DriftRate].value))
        bias = float(self.executeMethodParameterStates[kwKwDDM_StartingPoint].value)
        threshold = float(self.executeMethodParameterStates[kwDDM_Threshold].value)
        noise = float(self.executeMethodParameterStates[kwDDM_Noise].value)
        T0 = float(self.executeMethodParameterStates[kwDDM_T0].value)
        #endregion

        # # TEST PRINT:
        # print ("\nTRIAL {}:\n\tDDM Drift Rate param {}".
        #        format(CentralClock.trial, self.executeMethodParameterStates[kwDDM_DriftRate].value))
        # try:
        #     print ("\tEVC outputState: {}".
        #            format(self.executeMethodParameterStates['DDM_DriftRate'].receivesFromProjections[0].sender.value))
        # except:
        #     pass

        #region EXECUTE INTEGRATOR SOLUTION (REAL_TIME TIME SCALE) -----------------------------------------------------
        if time_scale == TimeScale.REAL_TIME:
            raise MechanismError("REAL_TIME mode not yet implemented for DDM")
            # IMPLEMENTATION NOTES:
            # Implement with calls to a step_function, that does not reset output
            # Should be sure that initial value of self.outputState.value = self.executeMethodParameterStates[kwBias]
            # Implement terminate() below
        #endregion

        #region EXECUTE ANALYTIC SOLUTION (TRIAL TIME SCALE) -----------------------------------------------------------
        elif time_scale == TimeScale.TRIAL:

            # Get length of output from kwMechansimOutputState
            # Note: use paramsCurrent here (instead of outputStates), as during initialization the execute method
            #       is run (to evaluate output) before outputStates have been instantiated
            output = [None] * len(self.paramsCurrent[kwOutputStates])
        #     output = np.array([[None]]*len(self.paramsCurrent[kwOutputStates]))

            self.outputStateValueMapping = {}
            self.outputStateValueMapping[kwDDM_DecisionVariable] = DDM_Output.DECISION_VARIABLE.value
            self.outputStateValueMapping[kwDDM_RT_Mean] = DDM_Output.RT_MEAN.value
            self.outputStateValueMapping[kwDDM_Error_Rate] = DDM_Output.ER_MEAN.value
            self.outputStateValueMapping[kwDDM_Probability_upperBound] = DDM_Output.P_UPPER_MEAN.value
            self.outputStateValueMapping[kwDDM_Probability_lowerBound] = DDM_Output.P_LOWER_MEAN.value

            #region Bogacz et al. (2006) solution:
            if self.paramsCurrent[kwDDM_AnalyticSolution] is kwDDM_BogaczEtAl:
                # FIX: ??CHANGE "BIAS" (IN PARENS BELOW) TO STARTING_POINT
                # FIX: DIVIDE BY ZERO IF threshold == 0
                bias = (bias + threshold) / (2 * threshold)
                # MODIFIED BY Amitai
                # Prevents div by 0 issue below:
                if bias <= 0:
                    bias = 1e-8
                if bias >= 1:
                    bias = 1-1e-8
                output[DDM_Output.RT_MEAN.value], output[DDM_Output.ER_MEAN.value] = self.ddm_analytic(bias,
                                                                                                       T0,
                                                                                                       drift_rate,
                                                                                                       noise,
                                                                                                       threshold)
                output[DDM_Output.P_UPPER_MEAN.value] = 1 - output[DDM_Output.ER_MEAN.value]
                output[DDM_Output.P_LOWER_MEAN.value] = output[DDM_Output.ER_MEAN.value]

                # print("DDM bias: {}, T0: {}, drift: {}, noise: {}, thresh: {}".format(bias, T0, drift_rate, noise, threshold))
                # print(output[DDM_Output.P_UPPER_MEAN.value])
                # print(output[DDM_Output.RT_MEAN.value])

            #endregion

            #region Navarro and Fuss solution:
            elif self.paramsCurrent[kwDDM_AnalyticSolution] is kwDDM_NavarroAndFuss:
                print("\nimporting matlab...")
                import matlab.engine
                eng1 = matlab.engine.start_matlab('-nojvm')
                print("matlab imported\n")
                results = eng1.ddmSim(drift_rate, bias, threshold, noise, T0, 1, nargout=5)
                output[DDM_Output.RT_MEAN.value] = results[NF_Results.MEAN_DT.value]
                output[DDM_Output.ER_MEAN.value] = 1-results[NF_Results.MEAN_ER.value]
                output[DDM_Output.P_UPPER_MEAN.value] = results[NF_Results.MEAN_ER.value]
                output[DDM_Output.P_LOWER_MEAN.value] = 1 - results[NF_Results.MEAN_ER.value]
                output[DDM_Output.RT_CORRECT_MEAN.value] = results[NF_Results.MEAN_CORRECT_RT.value]
                output[DDM_Output.RT_CORRECT_VARIANCE.value] = results[NF_Results.MEAN_CORRECT_VARIANCE.value]
                # CORRECT_RT_SKEW = results[DDMResults.MEAN_CORRECT_SKEW_RT.value]

                self.outputStateValueMapping[kwDDM_Probability_upperBound] = DDM_Output.P_UPPER_MEAN.value
                self.outputStateValueMapping[kwDDM_Probability_lowerBound] = DDM_Output.P_LOWER_MEAN.value
                self.outputStateValueMapping[kwDDM_RT_Correct_Mean] = DDM_Output.RT_CORRECT_MEAN.value
                self.outputStateValueMapping[kwDDM_RT_Correct_Variance] = DDM_Output.RT_CORRECT_VARIANCE.value

            #endregion

            else:
                raise MechanismError("{0} must be specified for TimeScale.TRIAL mode, "
                                     "from one of the following options".
                                     format(kwDDM_AnalyticSolution, AnalyticSolutions))

            #region Convert ER to decision variable:
            if random() < output[DDM_Output.ER_MEAN.value]:
                output[DDM_Output.DECISION_VARIABLE.value] = -1 * threshold
            else:
                output[DDM_Output.DECISION_VARIABLE.value] = threshold
            #endregion

            #region Print results
            # if (self.prefs.reportOutputPref and kwFunctionInit not in context):
            if self.prefs.reportOutputPref and kwExecuting in context:
                print ("\n{0} execute method:\n- input: {1}\n- params:".
                       format(self.name, self.inputState.value.__str__().strip("[]")))
                print ("    drift:", drift_rate,
                       "\n    bias:", bias,
                       "\n    thresh:", threshold,
                       "\n    T0:", T0,
                       "\n    noise:", noise,
                       "\n- output:",
                       # "\n    mean ER: {:.3f}".format(output[DDM_Output.ER_MEAN.value]),
                       # "\n    mean RT: {:.3f}".format(output[DDM_Output.RT_MEAN.value]))
                       "\n    mean P(upper bound): {:.3f}".format(float(output[DDM_Output.P_UPPER_MEAN.value])),
                       "\n    mean P(lower bound): {:.3f}".format(float(output[DDM_Output.P_LOWER_MEAN.value])),
                       "\n    mean ER: {:.3f}".format(float(output[DDM_Output.ER_MEAN.value])),
                       "\n    mean RT: {:.3f}".format(float(output[DDM_Output.RT_MEAN.value])))
                if self.paramsCurrent[kwDDM_AnalyticSolution] is kwDDM_NavarroAndFuss:
                    print(
                        "Correct RT Mean: {:.3f}".format(output[DDM_Output.RT_CORRECT_MEAN.value]),
                        "\nCorrect RT Variance: {:.3f}".format(output[DDM_Output.RT_CORRECT_VARIANCE.value]))
                        # "\nMean Correct RT Skewy:", CORRECT_RT_SKEW)
                print ("Output: ", output[DDM_Output.DECISION_VARIABLE.value].__str__().strip("[]"))
            #endregion

            # TEST PRINT
            # if('SIM' in context):
            #     print("drift: {}".format(drift_rate))
            #     print("bias: {}".format(bias))
            #     print("thresh: {}".format(threshold))
            #     print("DDM P(upper): {}".format(float(output[DDM_Output.P_UPPER_MEAN.value])))
            #     print("DDM P(lower): {}".format(float(output[DDM_Output.P_LOWER_MEAN.value])))
            #     print("DDM RT: {}".format(float(output[DDM_Output.RT_MEAN.value])))


            return output
        #endregion

        else:
            raise MechanismError("time_scale not specified for DDM")



    def ou_update(self, particle, drift, noise, time_step_size, decay):
        ''' Single update for OU (special case l=0 is DDM)'''
        return particle + time_step_size * (decay * particle + drift) + random.normal(0, noise) * sqrt(time_step_size)


    def ddm_update(self, particle, a, s, dt):
        return self.ou_update(particle, a, s, dt, decay=0)


    def ddm_rt(self, x0, t0, a, s, z, dt):
        samps = 0
        particle = x0
        while abs(particle) < z:
            samps = samps + 1
            particle = self.ou_update(particle, a, s, dt, decay=0)
        # return -rt for errors as per convention
        return (samps * dt + t0) if particle > 0 else -(samps * dt + t0)

    def ddm_distr(self, n, x0, t0, a, s, z, dt):
        return np.fromiter((self.ddm_rt(x0, t0, a, s, z, dt) for i in range(n)), dtype='float64')

    def ddm_analytic(self, bias, T0, drift_rate, noise, threshold):
        # drift_rate close to or at 0 (avoid float comparison)
        if abs(drift_rate) < 1e-8:
            # FIX FROM SEBASTIAN: converting normalized bias (ranging from 0-1)
            # back to absolute bias in order to apply limit
            bias_abs = bias * 2 * threshold - threshold
            # use expression for limit a->0 from Srivastava et al. 2016
            rt = T0 + (threshold**2 - bias_abs**2)/(noise**2)
            er = (threshold - bias_abs)/(2*threshold)
        else:
            # Previous:
            # ztilde = threshold/drift_rate
            # atilde = (drift_rate/threshold)**2
            # x0tilde = bias/drift_rate

            #### New (6/23/16, AS):
            drift_rate_normed = abs(drift_rate)
            ztilde = threshold/drift_rate_normed
            atilde = (drift_rate_normed/noise)**2

            is_neg_drift = drift_rate<0
            bias_adj = (is_neg_drift==1)*(1 - bias) + (is_neg_drift==0)*bias
            y0tilde = ((noise**2)/2) * np.log(bias_adj / (1 - bias_adj))
            if abs(y0tilde) > threshold:    y0tilde = -1*(is_neg_drift==1)*threshold + (is_neg_drift==0)*threshold
            x0tilde = y0tilde/drift_rate_normed
            ####

            import warnings
            warnings.filterwarnings('error')

            try:
                rt = ztilde * tanh(ztilde * atilde) + \
                     ((2*ztilde*(1-exp(-2*x0tilde*atilde)))/(exp(2*ztilde*atilde)-exp(-2*ztilde*atilde))-x0tilde) + T0
                er = 1/(1+exp(2*ztilde*atilde)) - ((1-exp(-2*x0tilde*atilde))/(exp(2*ztilde*atilde)-exp(-2*ztilde*atilde)))

            except (Warning):
                # Per Mike Shvartsman:
                # If ±2*ztilde*atilde (~ 2*z*a/(c^2) gets very large, the diffusion vanishes relative to drift
                # and the problem is near-deterministic. Without diffusion, error rate goes to 0 or 1
                # depending on the sign of the drift, and so decision time goes to a point mass on z/a – x0, and
                # generates a "RuntimeWarning: overflow encountered in exp"
                er = 0
                rt = ztilde/atilde - x0tilde + T0

            # This last line makes it report back in terms of a fixed reference point
            #    (i.e., closer to 1 always means higher p(upper boundary))
            # If you comment this out it will report errors in the reference frame of the drift rate
            #    (i.e., reports p(upper) if drift is positive, and p(lower if drift is negative)
            er = (is_neg_drift==1)*(1 - er) + (is_neg_drift==0)*(er)

        return rt, er

    def terminate_function(self, context=NotImplemented):
        """Terminate the process

        called by process.terminate() - MUST BE OVERRIDDEN BY SUBCLASS IMPLEMENTATION
        returns output

        :rtype CurrentStateTuple(state, confidence, duration, controlModulatedParamValues)
        """
        # IMPLEMENTATION NOTE:  TBI when time_step is implemented for DDM

