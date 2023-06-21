# CAshflow Optimization System

## Description

CAOS is a prototype simulation-based decision support system for cash-flow planning. CAOS has been designed to assist enterprises with the management of their financial negotiations and transaction and thus, balancing their corporate debt. 

## How to Use

To start the interactive interface of CAOS, execute the following command from a command line terminal:

```bash
python caos_cli.py
```
This should initiate the CLI mode of the system that allows the user to interact with the system and perform all supported functions. 

The system can also be integrated to other Python projects. For this, you should import the project files into your new project. Full system functionality is exposed via the `CAOSProblem` class included in `problem.py`.

More details on both the CLI but also the programmatic usage of the module can be found in the module [Documentation](caos.ipynb).

## Demo

A demonstration that showcases the usage and the main functionality of the system can be found [Here](case_study.ipynb)


