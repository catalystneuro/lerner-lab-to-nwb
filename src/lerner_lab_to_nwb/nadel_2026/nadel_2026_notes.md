# Notes concerning the nadel_2026 conversion

Whole-cell recordings of intrinsic excitability from retrobead-labeled central amygdala (CeA) neurons in acute slices,
from Nadel et al., "Adolescent stress recruits a latent amygdala-dopamine circuit to drive punishment-resistant
reward-seeking" (bioRxiv, doi:10.64898/2026.07.29.741478). This is the reference dataset for the lab's slice
electrophysiology pipeline (Aim 3 of the 2026 scope of work). It is converted locally and not uploaded to DANDI.

Open questions for the lab are in `nadel_2026_questions.md`.

## Source data

`aCUS_ephys_raw_for_NWB/` as handed off by Jacob Nadel (README dated 9/28/26):

- `raw_data_organized/`: 32 recording days (Sept 2023 to June 2026), 191 good cell folders
- `timecourse_raw_data_organized/`: 9 recording days of the P40 vs P220 experiment, 62 good cell folders
- `tables/`: Jacob's audit tables. The conversion reads `cells_master.csv` (which folders are good cells, paper
  inclusion, cluster labels, bead status) and `subjects_from_makeMice.csv` (sex, stress group, projection target,
  age for the timecourse mice; the lab's source of truth for subjects)

Each `.h5` file is one WaveSurfer 0.945 run of one protocol on one cell, holding one or more sweeps. The six protocols
are the VC test pulse, 30 s spontaneous recording, F-I steps (500 ms, 20 pA), sag steps (500 ms, -50 pA), rheobase
steps (50 ms, 5 pA), and the VC Ih protocol.

## File organization

One NWB file per recording day (one mouse), `sub-<animal id>_ses-<date>.nwb`, 41 files in all.

- One `IntracellularElectrode` per cell, named `electrode_<cell id>`, with `cell_id`, `slice`, and `location`.
- Each sweep is its own `CurrentClampSeries`, `VoltageClampSeries`, or `IZeroClampSeries` in acquisition
  (`<file stem>_sweep_<sweep number>_response`, for example `m203_0571-0581_sweep_0575_response`) with a matching
  stimulus series (`..._stimulus`). Names include the file stem because sweep numbers repeat within a day: besides the
  cases in the README, the counter was set back in `758-L/m114 s2c2` (`m114_0422-0432.h5` and `m114_0432-0434.h5` both
  hold sweep 432) and `862-R/m405 s1c1` has sweep 1 in two files. Writing one series per
  sweep keeps `starting_time` and `rate`; one continuous series per run would need per-sample timestamps because of the
  gaps between sweeps, which would be about four times the size of the int16 data.
- Icephys tables: one intracellular recording and one simultaneous recording per sweep, one sequential recording per
  run (`stimulus_type` is the protocol file name, `source_file` the WaveSurfer file), and one repetition per cell and
  protocol (the runs of a protocol on one cell, usually three).
- Per-cell columns on the `electrodes` category of the intracellular recordings table: `cell_folder`,
  `experimenter`, `retrobead_positive`, `in_paper`, `snl_cluster`.

## Interface mapping

| Stream | Interface | Source | Status |
|---|---|---|---|
| Whole-cell recordings | `WaveSurferIntracellularInterface` (custom, this folder) | one `.h5` file per instance | Verified |
| Subject and cell metadata | `nadel_2026_convert_session.py` | `tables/*.csv`, `nadel_2026_metadata.yaml` | Verified |

NeuroConv 0.10.2 has no WaveSurfer interface. The custom interface reads the files with h5py and needs no other
dependency. Whether it generalizes enough to port to NeuroConv is to be assessed separately.

## Data decisions

- Response data are the raw int16 ADC counts. WaveSurfer scales counts to volts with a cubic polynomial
  (`AnalogScalingCoefficients`, lowest order first) and then divides by `AnalogChannelScales`. The quadratic and cubic
  terms change the result by less than one ADC count over the full int16 range, so `conversion` and `offset` use the
  linear terms. Checked against `read_wavesurfer_example.py`: largest difference 3e-5 mV in current clamp and 0.025 pA
  in voltage clamp. Scales are read per file, since the current monitor gain changes between runs.
- Stimulus series are built from the stimulus library stored in each file header (selected map, stimuli bound to
  the run's analog output channel, amplitude expressions evaluated with i = sweep position in the run). Only
  `SquarePulse` and `TwoSquarePulses` occur in this dataset; other types raise.
- The recorded command loopback (second analog input) is not written. Compared over all 3,489 files, it matches the
  library stimulus within ADC noise from May 2024 on and in MZ's Sept 2023 files, is wrong in Jacob's Sept 2023 files
  (README item 1), and is flat in the four ES folders. Where it is valid it duplicates the library stimulus.
- Voltage clamp stimuli are stored relative to the holding potential, with `offset` = -70 mV (set on the amplifier and
  not stored in the file).
- The clamp mode in the header decides the series type (README item 5): the spontaneous runs MZ recorded in VC are
  `VoltageClampSeries`, the I=0 run is an `IZeroClampSeries` with no stimulus. A protocol whose output channel has
  units that do not match the clamp mode (the two VC test pulses run in CC) gets an all-zero stimulus whose
  description says no command was delivered.
- The 20 kHz gap-free file in `m402 s1c1ES` (`AJ_Ch1_VC_test pulse.cfg`) has no stimulus bound to its output, so it
  has a response and no stimulus.
- Excluded runs are listed with reasons in `nadel_2026_excluded_runs.csv`: the Sept 2023 runs held near -60 mV
  (README "Holding"; matched from the log's sweep ranges, see question 3) and 12 byte-identical duplicates of
  `m009 s1c1` runs filed in MZ's `m009 s3c1` folder.
- `nadel_2026_misfiled_runs.csv` reassigns `m009_0001-0003.h5` and `m009_0004.h5`, which sit in MZ's folder but are
  the first test pulse and spontaneous run of Jacob's `m009 s1c1` (README item 3).
- Not converted: `bad/` folders, `pics/` (including MZ's unfiled s1c3 recording), the per-cell slice images, and the
  free-text and numeric log sheet fields (pipette and access resistance, holding current, notes), which are sparse and
  inconsistently formatted.

## Synchronization

All data in a file come from one DAQ and one WaveSurfer clock per run. Runs are placed on one timeline by
`ClockAtRunStart` (local time, America/Chicago); the session start is the earliest run of the day, and each sweep starts
at its run start plus its `timestamp`. The ES runs in `20251016 855-L` were recorded on the other rig, so their
placement relative to Jacob's runs depends on the two rig computers' clocks agreeing.

## Metadata

- Session-level text (slices, pharmacology, internal, devices, surgery) is from the preprint methods.
- Subject sex, stress group, and projection target come from `subjects_from_makeMice.csv`. Age is set only for the
  timecourse mice (P40 or P220 from makeMice); the main-tree mice have no age or date of birth yet (question 13), which
  NWB Inspector reports as critical.
- Experimenters are the people who recorded the cells in that file: JN = Jacob A. Nadel, MZ = Manhua Zhu,
  ES = Evan S. Swanson (initials matched to the preprint author list, question 23).

## Ontology annotation

`nadel_2026_external_resources.yaml`, written into each file as HERD references:

- species `Mus musculus`: NCBITaxon:10090
- institution `Northwestern University`: ROR:000e0be47 (Evanston, United States)
- electrode location `Central amygdalar nucleus`: MBA:536, and UBERON:0002883 (its cross-references include
  Allen 536)

Not annotated: strain (the preprint does not give the JAX stock number for the WT mice) and experimenters (no ORCIDs in
the preprint).
