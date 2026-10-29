# lerner-lab-to-nwb
NWB conversion scripts for Lerner lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
Each conversion in this repository has its own requirements file in its folder, for example `src/lerner_lab_to_nwb/seiler_2024/seiler_2024_requirements.txt`. The package itself declares no dependencies, so set up a separate environment for each conversion: install that conversion's requirements, then install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs) without dependencies.

For example, to set up the `seiler_2024` conversion with Python 3.11:

```bash
git clone https://github.com/catalystneuro/lerner-lab-to-nwb
cd lerner-lab-to-nwb
python3.11 -m venv seiler_2024_env
source seiler_2024_env/bin/activate
pip install -r src/lerner_lab_to_nwb/seiler_2024/seiler_2024_requirements.txt
pip install -e . --no-deps
```

Any environment manager works the same way. With [uv](https://docs.astral.sh/uv/), replace the venv and pip lines with `uv venv --python 3.11`, `uv pip install -r ...`, and `uv pip install -e . --no-deps`. The `seiler_2024` requirements are pinned to the versions used for the original conversion.

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
    ├── LICENSE
    ├── MANIFEST.in
    ├── pyproject.toml
    ├── README.md
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
                ├── seiler_2024_requirements.txt
                ├── seiler_2024csvbehaviorinterface.py
                ├── seiler_2024excelmetadatainterface.py
                ├── seiler_2024fiberphotometryinterface.py
                ├── seiler_2024nwbconverter.py
                ├── seiler_2024optogeneticinterface.py
                └── seiler_2024westernblotinterface.py

For the conversion `seiler_2024` you can find a directory located in `src/lerner-lab-to-nwb/seiler_2024`. Inside that conversion directory you can find the following files:

* `__init__.py` : This init file imports all the datainterfaces and NWBConverters so that they can be accessed directly from lerner_lab_to_nwb.seiler_2024.
* `seiler_2024_convert_session.py` : This conversion script defines the `session_to_nwb()` function, which converts a single session of data to NWB.
    When run as a script, this file converts 23 example sessions to NWB, representing all the various edge cases in the dataset.
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
* `seiler_2024_requirements.txt` : This file pins the dependencies for this conversion (see Installation).

Future conversions for this repo should follow the example of seiler_2024 and create another folder of
conversion scripts and datainterfaces.  As a placeholder, here we have `src/lerner-lab-to-nwb/another_conversion`.

## Running a Conversion

To convert the 23 example sessions, simply run
```bash
python src/lerner_lab_to_nwb/seiler_2024/seiler_2024_convert_session.py
```

To convert the whole dataset, simply run
```bash
python src/lerner_lab_to_nwb/seiler_2024/seiler_2024_convert_dataset.py
```

Note that the dataset conversion uses multiprocessing, currently set to 4 workers.  To use more or fewer workers, simply
change the `max_workers` argument to `dataset_to_nwb()`.

## nadel_2026: slice electrophysiology

`src/lerner_lab_to_nwb/nadel_2026` converts the whole-cell recordings from Nadel et al. 2026
(bioRxiv, doi:10.64898/2026.07.29.741478), recorded with WaveSurfer, to one NWB file per recording day.
`WaveSurferIntracellularInterface` reads one WaveSurfer `.h5` file (one run of one protocol on one cell), and
`Nadel2026NWBConverter` combines the runs of a day. Only the 198 cells in the preprint's figures are converted
(`nadel_2026_paper_cells.csv`). Notes on the data and the conversion decisions are in
`nadel_2026_notes.md`, open questions for the lab are in `nadel_2026_lab_questions.md`, and open decisions about the conversion are in
`nadel_2026_curator_questions.md`.

To convert the three example days, run
```bash
python src/lerner_lab_to_nwb/nadel_2026/nadel_2026_convert_session.py
```

To convert all 34 days with cells in the preprint, run
```bash
python src/lerner_lab_to_nwb/nadel_2026/nadel_2026_convert_dataset.py
```

Both scripts set the data and output paths in their `__main__` block. `notebooks/nadel_2026_slice_ephys.ipynb`
shows how to convert a day and read the converted files.
