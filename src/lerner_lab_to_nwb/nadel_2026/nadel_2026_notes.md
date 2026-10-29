# Notes concerning the nadel_2026 conversion

Whole-cell recordings of intrinsic excitability from retrobead-labeled central amygdala (CeA) neurons in acute slices,
from Nadel et al., "Adolescent stress recruits a latent amygdala-dopamine circuit to drive punishment-resistant
reward-seeking" (bioRxiv, doi:10.64898/2026.07.29.741478). This is the reference dataset for the lab's slice
electrophysiology pipeline (Aim 3 of the 2026 scope of work). It is converted locally and not uploaded to DANDI.

Open questions for the lab are in `nadel_2026_lab_questions.md`, and open decisions about the conversion are in
`nadel_2026_curator_questions.md`.

## Source data

`aCUS_ephys_raw_for_NWB/` as handed off by Jacob Nadel (README dated 9/28/26):

- `raw_data_organized/`: 32 recording days (Sept 2023 to June 2026), 191 good cell folders
- `timecourse_raw_data_organized/`: 9 recording days of the P40 vs P220 experiment, 62 good cell folders
- `tables/`: Jacob's audit tables. The conversion reads `cells_master.csv` (cell IDs, cluster labels, bead status)
  and `subjects_from_makeMice.csv` (sex, stress group, projection target, age for the timecourse mice; the lab's
  source of truth for subjects)

## Cells converted

Only the cells in the preprint's figures, 198 in all, listed in `nadel_2026_paper_cells.csv` with the evidence for
each (curator decision 2). `used cells.csv` lists 160 of them. The figures' source data add the 3 cells of the June
2026 PAG mouse 2006-151 (Fig. 2E and 2H) and the 35 P40 cells Jacob recorded (Fig. 2N); F-I curves computed from the
converted files reproduce those panels' values. Which cells make up Fig. 2D (BNST) is still open (lab question 18).
The P220 cohort, ES's four P40 cells, 610-005, the bead-negative 2023 cells, and the cells dropped in QC are not
converted.

Each `.h5` file is one WaveSurfer 0.945 run of one protocol on one cell, holding one or more sweeps. The six protocols
are the VC test pulse, 30 s spontaneous recording, F-I steps (500 ms, 20 pA), sag steps (500 ms, -50 pA), rheobase
steps (50 ms, 5 pA), and the VC Ih protocol.

## File organization

One NWB file per recording day (one mouse), `sub-<animal id>_ses-<date>.nwb`, 34 files in all (480 MB).

- One `IntracellularElectrode` per cell, named `electrode_<cell id>`, with `cell_id`, `slice`, and `location`.
- Each sweep is its own `CurrentClampSeries`, `VoltageClampSeries`, or `IZeroClampSeries` in acquisition
  (`<file stem>_sweep_<sweep number>_response`, for example `m203_0571-0581_sweep_0575_response`) with a matching
  stimulus series (`..._stimulus`). Names include the file stem because sweep numbers repeat within a day: besides the
  cases in the README, the counter was set back in `758-L/m114 s2c2` (`m114_0422-0432.h5` and `m114_0432-0434.h5` both
  hold sweep 432). Writing one series per
  sweep keeps `starting_time` and `rate`; one continuous series per run would need per-sample timestamps because of the
  gaps between sweeps, which would be about four times the size of the int16 data.
- Icephys tables: one intracellular recording and one simultaneous recording per sweep, one sequential recording per
  run (`stimulus_type` is the protocol file name, `source_file` the WaveSurfer file), and one repetition per cell and
  protocol (the runs of a protocol on one cell, usually three).
- Per-cell columns on the `electrodes` category of the intracellular recordings table: `cell_folder`,
  `experimenter`, `retrobead_positive`, `snl_cluster`.

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
- The clamp mode in the header decides the series type (README item 5): the spontaneous run MZ recorded in VC in
  `m006 s4c1` is a `VoltageClampSeries`, and the I=0 run in `m401 s2c3` is an `IZeroClampSeries` with no stimulus. The
  VC test pulse run in CC in `m114 s2c2` drives an output channel whose units do not match the clamp mode, so it gets
  an all-zero stimulus whose description says no command was delivered.
- Excluded runs are listed with reasons in `nadel_2026_excluded_runs.csv`: the Sept 2023 runs held near -60 mV
  (README "Holding"; matched from the log's sweep ranges, see lab question 1), 86 files from 10 cells.
- `nadel_2026_misfiled_runs.csv` reassigns `m009_0001-0003.h5` and `m009_0004.h5`, which sit in MZ's `m009 s3c1`
  folder but are the first test pulse and spontaneous run of Jacob's `m009 s1c1` (README item 3). The 12 copies of
  other `m009 s1c1` runs in that folder are not read, since MZ's cell is not in the paper.
- Not converted: `bad/` folders, `pics/`, the per-cell slice images, and the free-text and numeric log sheet fields
  (pipette and access resistance, holding current, notes), which are sparse and inconsistently formatted.

## Synchronization

All data in a file come from one DAQ and one WaveSurfer clock per run. Runs are placed on one timeline by
`ClockAtRunStart` (local time, America/Chicago); the session start is the earliest run of the day, and each sweep starts
at its run start plus its `timestamp`.

## Metadata

- Session-level text (slices, pharmacology, internal, devices, surgery) is from the preprint methods.
- Subject sex, stress group, and projection target come from `subjects_from_makeMice.csv`. Age is set only for the
  P40 mice (from makeMice); the P70 mice have no age or date of birth yet (lab question 10), which NWB Inspector
  reports as critical for those 30 files.
- Experimenters are the people who recorded the cells in that file: JN = Jacob A. Nadel and MZ = Manhua Zhu
  (initials matched to the preprint author list, lab question 17).

## Ontology annotation

`nadel_2026_external_resources.yaml`, written into each file as HERD references:

- species `Mus musculus`: NCBITaxon:10090
- institution `Northwestern University`: ROR:000e0be47 (Evanston, United States)
- electrode location `Central amygdalar nucleus`: MBA:536, and UBERON:0002883 (its cross-references include
  Allen 536)

Not annotated: strain (the preprint does not give the JAX stock number for the WT mice) and experimenters (no ORCIDs in
the preprint).
