# Scheduler

This is a scheduling app built with the kivy, kivymd API for GUI stuff and use Gurobi optimizer to solve the RCPSP (Resource-Constrained Project Scheduling Problem)

## Features
- PERT chart editor to edit task constarints, add description ...
- Gantt chart automatically generated and updated after modification to keep an optimal planning through the progress of the project
- Burndown chart to monitor the progress of the project (velocity, planned end day by RCPSP, linear regression for comparison, over/under-estimation indicators)
- Backlog to see what have been done and remain to do, and assign people to tasks 
- Exporting of Gantt planning and Burndown chart as png
- Sorting of task by begin time
- Load/Save multiple projects 

![Alt text](images/pert_editor.png?raw=true "PERT chart screen")
![Alt text](images/gantt_chart.png?raw=true "Gantt chart screen")
![Alt text](images/burndown_chart.png?raw=true "Burndown chart screen")
![Alt text](images/backlog.png?raw=true "Backlog screen")
