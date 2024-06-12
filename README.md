# lerner-lab-to-nwb
NWB conversion scripts for Lerner lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
We recommend installing this package directly from Github. This option has the advantage that the source code can be modifed if you need to amend some of the code we originally provided to adapt to future experimental differences. To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains all the required machinery in a single and simple install.

From a terminal (note that conda should be installed on your system) you can do the following:

```bash
git clone https://github.com/catalystneuro/lerner-lab-to-nwb
cd lerner-lab-to-nwb
conda env create --file make_env.yml
conda activate lerner_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries.  We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```bash
git clone https://github.com/catalystneuro/lerner-lab-to-nwb
cd lerner-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).

## Helpful Definitions

This conversion project is comprised primarily by DataInterfaces, NWBConverters, and conversion scripts.

In neuroconv, a [DataInterface](https://neuroconv.readthedocs.io/en/main/user_guide/datainterfaces.html) is a class that specifies the procedure to convert a single data modality to NWB.
This is usually accomplished with a single read operation from a distinct set of files.
For example, in this conversion, the `Seiler2024FiberPhotometryInterface` contains the code that converts all of the fiber photometry data to NWB from a raw TDT output folder.

In neuroconv, a [NWBConverter](https://neuroconv.readthedocs.io/en/main/user_guide/nwbconverter.html) is a class that combines many data interfaces and specifies the relationships between them, such as temporal alignment between fiber photometry and behavioral data.
This allows users to combine multiple modalites into a single NWB file in an efficient and modular way.

In this conversion project, the conversion scripts determine which sessions to convert,
instantiate the appropriate NWBConverter object,
and convert all of the specified sessions, saving them to an output directory of .nwb files.

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
* `seiler_2024nwbconverter.py` : This module defines the primary conversion class, `Seiler2024NWBConverter`, which aggregates all of the various datainterfaces relevant for this conversion.
    This class also specifies the temporal alignment procedure in the `temporally_align_data_interfaces()` method.
    This module also defines `Seiler2024WesternBlotNWBConverter`, which converts the western blot data.
* `medpcdatainterface.py` : This module defines `MedPCInterface`, which is the data interface for MedPC output files.
* `medpc_helpers.py` : This helper module defines various functions for reading medpc output data.
    Most importantly, `read_medpc_file()` reads a single session from a raw MedPC text file into a dictionary.
* `seiler_2024csvbehaviorinterface.py` : This module defines `Seiler2024CSVBehaviorInterface`, which is the data interface for behavioral .csv files.
    This data interface is used when the medpc file for a given session is not available, but the .csv file is available.
* `seiler_2024fiberphotometryinterface.py` : This module defines `Seiler2024FiberPhotometryInterface`, which is the data interface for fiber photometry files.
* `seiler_2024optogeneticinterface.py` : This module defines `Seiler2024OptogeneticInterface`, which is the data interface for optogenetic stimulation from medpc output files or csv files.
* `seiler_2024excelmetadatainterface.py` : This module defines `Seiler2024ExcelMetadataInterface`, which is the data interface for demographic metadata from the excel file.
* `seiler_2024westernblotinterface.py` : This module defines `Seiler2024WesternBlotInterface`, which is the data interface for Western blot images.
* `seiler_2024metadata.yaml` : This metadata .yaml file provides high-level metadata for the nwb files directly as well as useful dictionaries for some of the data interfaces.
    For example, NWBFile/experimenter lists all the authors of the Seiler et al. 2022 paper as experimenters,
    MedPC/msn_to_session_description gives a mapping from MSNs to a human-readable description of the corresponding sessions,
    and Optogenetics/experimental_group_to_metadata/DMS-Excitatory provides a dictionary with all of the relevant optogenetic stim metadata (ex. injection_location, excitaiton_lambda, etc.).
* `seiler_2024notes.md` : This markdown file contains my notes from the conversion for each of the data interfaces.
    It specifically highlights various edge cases as well as questions I had for the Lerner Lab (active and resolved).

Future conversions for this repo should follow the example of seiler_2024 and create another folder of
conversion scripts and datainterfaces.  As a placeholder, here we have `src/lerner-lab-to-nwb/another_conversion`.

## Running a Conversion

To convert the 22 example sessions, simply run
```bash
python src/lerner_lab_to_nwb/seiler_2024/seiler_2024_convert_session.py
```

To convert the whole dataset, simply run
```bash
python src/lerner_lab_to_nwb/seiler_2024/seiler_2024_convert_dataset.py
```

Note that the dataset conversion uses multiprocessing, currently set to 4 workers.  To use more or fewer workers, simply
change the `max_workers` argument to `dataset_to_nwb()`.
