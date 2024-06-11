# lerner-lab-to-nwb
NWB conversion scripts for Lerner lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
We recommend installing this package directly from Github. This option has the advantage that the source code can be modifed if you need to amend some of the code we originally provided to adapt to future experimental differences. To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains all the required machinery in a single and simple install.

From a terminal (note that conda should be installed on your system) you can do the following:

```
git clone https://github.com/catalystneuro/lerner-lab-to-nwb
cd lerner-lab-to-nwb
conda env create --file make_env.yml
conda activate lerner_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries.  We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```
git clone https://github.com/catalystneuro/lerner-lab-to-nwb
cd lerner-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

    lerner-lab-to-nwb/
    ├── .gitignore
    ├── .pre-commit-config.yaml
    ├── freeze_dependencies.py
    ├── frozen_dependencies.txt
    ├── LICENSE
    ├── make_env.yml
    ├── MANIFEST.in
    ├── pyproject.toml
    ├── README.md
    ├── requirements.txt
    ├── setup.py
    └── src
        └── lerner_lab_to_nwb
            ├── __init__.py
            ├── another_conversion
            └── seiler_2024
                ├── __init__.py
                ├── medpc_helpers.py
                ├── medpcdatainterface.py
                ├── seiler_2024_convert_dataset.py
                ├── seiler_2024_convert_session.py
                ├── seiler_2024_metadata.yaml
                ├── seiler_2024_notes.md
                ├── seiler_2024csvbehaviorinterface.py
                ├── seiler_2024excelmetadatainterface.py
                ├── seiler_2024fiberphotometryinterface.py
                ├── seiler_2024nwbconverter.py
                ├── seiler_2024optogeneticinterface.py
                └── seiler_2024westernblotinterface.py

For the conversion `seiler_2024` you can find a directory located in `src/lerner-lab-to-nwb/seiler_2024`. Inside that conversion directory you can find the following files:

* `__init__.py` : This init file imports all the datainterfaces and NWBConverters so that they can be accessed directly from lerner_lab_to_nwb.seiler_2024.
* `seiler_2024_convert_session.py` : This conversion script defines the `session_to_nwb()` function, which converts a single session of data to NWB.
    When run as a script, this file converts 22 example sessions to NWB, representing all the various edge cases in the dataset.
* `seiler_2024_convert_dataset.py` : This conversion script defines the `dataset_to_nwb()` function, which converts the entire Seiler 2024 dataset to NWB.
    When run as a script, this file calls `dataset_to_nwb()` with the appropriate arguments as well as `western_dataset_to_nwb()`, which converts all the western blot data.

Future conversions for this repo should follow the example of seiler_2024 and create another folder of
conversion scripts and datainterfaces.  As a placeholder, here we have `src/lerner-lab-to-nwb/another_conversion`.
