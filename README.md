# Scheduler

This is a scheduling app built with the kivy, kivymd API for GUI stuff and use Gurobi optimizer to solve the RCPSP (Resource-Constrained Project Scheduling Problem)

## Features
- PERT chart editor
- Gantt chart automaticcally generated and updated after modification to keep an optimal planning through the progress of the project
- Burndown chart to monitor the progress of the project (velocity, planned end day by RCPSP, linear regression for comparison, over/under-estimation indicators)
- Backlog to see what have been done and remain to do, and assign people to tasks 
