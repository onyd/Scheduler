from math import exp
from pyomo.core.base.constraint import Constraint
import pyomo.environ as pyo
import numpy as np
from pyomo.opt.results.solver import TerminationCondition


class SchedulerSolver:
    def __init__(self, n_tasks, end_index, anteriority_edges,
                 fixed_begin_times, min_begin_times, max_end_times, durations,
                 consumed_resources, capacity, horizon) -> None:
        self.n_tasks = n_tasks
        self.anteriority_edges = anteriority_edges
        self.fixed_begin_times = fixed_begin_times
        self.min_begin_times = min_begin_times
        self.max_end_times = max_end_times
        self.durations = durations
        self.consumed_resources = consumed_resources
        self.capacity = capacity
        self.end = end_index
        self.horizon = horizon

    def solve(self):
        model = pyo.ConcreteModel()

        model.x = pyo.Var([
            i * (self.horizon + 1) + t for t in range(self.horizon + 1)
            for i in range(self.n_tasks)
        ],
                          domain=pyo.Binary)

        # Fix varaible to ensure it begins at the eventually asked time
        for i, fixed_time in enumerate(self.fixed_begin_times):
            if fixed_time is not None:
                model.x[i * (self.horizon + 1) + fixed_time].fix(1)

        # Fix variables to ensure tasks begins after their minimum begin date
        for i, min_time in enumerate(self.min_begin_times):
            if min_time is not None:
                for t in range(min_time):
                    model.x[i * (self.horizon + 1) + t].fix(0)

        # Fix variables to ensure tasks ends before their maximum end date
        for i, max_time in enumerate(self.max_end_times):
            if max_time is not None:
                for t in range(max_time - self.durations[i], self.horizon + 1):
                    model.x[i * (self.horizon + 1) + t].fix(0)

        # Build anteriority constraints
        model.anteriority = pyo.Constraint(self.anteriority_edges,
                                           rule=self.build_anteriority_rule)

        # Build resources constraints
        model.resources = pyo.Constraint(range(self.horizon + 1),
                                         rule=self.build_resource_rule)

        # Build pulse variable constraints
        model.pulse = pyo.Constraint(range(self.n_tasks),
                                     rule=self.build_pulse_rule)

        # Build cost function to optimize
        model.OBJ = pyo.Objective(expr=sum([
            model.x[self.end * (self.horizon + 1) + t] * t
            for t in range(self.horizon + 1)
        ]))

        opt = pyo.SolverFactory('gurobi')
        results = opt.solve(model)

        if not results.solver.termination_condition == TerminationCondition.optimal:
            return False

        self.solution = np.zeros(shape=(self.n_tasks, self.horizon + 1))
        for i in range(self.n_tasks):
            for t in range(self.horizon + 1):
                self.solution[i, t] = model.x[i * (self.horizon + 1) + t].value
        self.end_time = int(np.argmax(self.solution[self.end]))
        self.solution = np.delete(self.solution, [self.end], axis=0)
        return True

    def build_anteriority_rule(self, model, i1, i2):
        return sum([
            model.x[i2 * (self.horizon + 1) + t] * t -
            model.x[i1 * (self.horizon + 1) + t] * t
            for t in range(self.horizon + 1)
        ]) >= self.durations[i1]

    def build_resource_rule(self, model, t):
        trivial = True
        expr = 0
        for i in range(self.n_tasks):
            for tp in range(t - self.durations[i] + 1, t + 1):
                if tp >= 0:
                    expr += model.x[i * (self.horizon + 1) +
                                    tp] * self.consumed_resources[i]
                    trivial &= self.consumed_resources[i] == 0
        if trivial:
            return Constraint.Feasible

        return expr <= self.capacity

    def build_pulse_rule(self, model, i):
        return sum([
            model.x[i * (self.horizon + 1) + t]
            for t in range(self.horizon + 1)
        ]) == 1
