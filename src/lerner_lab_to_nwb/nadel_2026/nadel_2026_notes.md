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

The 198 cells in the preprint's figures, plus the 2 cells of `used cells.csv` that the figures leave out, 200 in all,
listed in `nadel_2026_paper_cells.csv` with the evidence for each (curator decision 2). The figures' cells are the cells
of the lab's per-cell analysis tables in the Zenodo bundle, which match the preprint's cell counts and F-I values in
every group of Figs. 2D to 2F: the 158 cells they share with `used cells.csv`, `m108 s1c3` (BNST, unstressed) and
`m011 s2c1 +` (SNL, unstressed), the 3 cells of the June 2026 PAG mouse 2006-151 (Fig. 2E and 2H), and the 35 P40
cells Jacob recorded (Fig. 2N). `m105 s1c1` (BNST, stressed) and `m114 s2c2` (SNL, unstressed) are in `used cells.csv`
but not in the analysis tables; they are converted with `in_preprint_figures` False. Which list is right is lab
question 1.
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
  stimulus template (`..._stimulus_template`) and, where the command was recorded, a stimulus (`..._stimulus`). Names include the file stem because sweep numbers repeat within a day: besides the
  cases in the README, the counter was set back in `758-L/m114 s2c2` (`m114_0422-0432.h5` and `m114_0432-0434.h5` both
  hold sweep 432). Writing one series per
  sweep keeps `starting_time` and `rate`; one continuous series per run would need per-sample timestamps because of the
  gaps between sweeps, which would be about four times the size of the int16 data.
- Icephys tables: one intracellular recording and one simultaneous recording per sweep, one sequential recording per
  run (`stimulus_type` is the protocol file name, `source_file` the WaveSurfer file, `held_near_minus_60_mV` whether
  the cell was held near -60 mV with DC current during the run).
- Per-cell columns on the `electrodes` category of the intracellular recordings table: `cell_folder`,
  `experimenter`, `snl_cluster`, `stress_group`, `projection_target` (curator decision 12; the latter two repeat what the
  subject and session descriptions say), and `in_preprint_figures`. Every converted cell is retrobead-positive (curator decision 10), which the
  electrode description states.

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
- The library waveform is written as each sweep's stimulus template (`/stimulus/templates`). The command loopback
  recorded on the second analog input is written as the delivered stimulus (`/stimulus/presentation`, raw int16 with
  that channel's scaling) wherever it exists (curator decision 7). Where it is valid it matches the library waveform
  within ADC noise.
- Jacob's Sept 2023 runs have no recorded command: README item 1 says their second analog input does not track the
  stimulus. Those runs have a template only, and the duplicate voltage channel is not written. Runs whose
  second input has units that do not match the clamp mode, and the I=0 run, also have no recorded command.
- Voltage clamp stimuli are stored relative to the holding potential, with `offset` = -70 mV (set on the amplifier and
  not stored in the file).
- The clamp mode in the header decides the series type (README item 5): the spontaneous run MZ recorded in VC in
  `m006 s4c1` is a `VoltageClampSeries`, and the I=0 run in `m401 s2c3` is an `IZeroClampSeries` with no stimulus. The
  VC test pulse run in CC in `m114 s2c2` drives an output channel whose units do not match the clamp mode, so it gets
  an all-zero stimulus whose description says no command was delivered.
- Runs held near -60 mV with DC current are converted and marked (`held_near_minus_60_mV`), 107 files from 13 SNL
  cells, listed in `nadel_2026_log_held_runs.csv` from the log's "holding at -60 mV" rows and notes (README "Holding").
  The logged holding current, where the log gives one per run, is the `bias_current` of each response series. The
  lab's per-cell values average these runs with the runs at rest (for `m021 s1c2`, the F-I `sweep` value 200.5 in
  `baseline Firing Rate.csv` is the mean of sweeps 120, 131, 142 at rest and 259, 270, 281 held), so keeping them
  reproduces the figures. The README asks for them to be excluded; whether they belong in the analysis is lab
  question 2.
- `nadel_2026_misfiled_runs.csv` reassigns `m009_0001-0003.h5` and `m009_0004.h5`, which sit in MZ's `m009 s3c1`
  folder but are the first test pulse and spontaneous run of Jacob's `m009 s1c1` (README item 3). The 12 copies of
  other `m009 s1c1` runs in that folder are not read, since MZ's cell is not in the paper.
- Not converted: `bad/` folders, `pics/`, the per-cell slice images, and the free-text notes in the log sheets (lab
  question 9).

## Reproduction of the preprint figures

`notebooks/nadel_2026_figure_2_reproduction.ipynb` recomputes every data panel of Fig. 2 and Fig. S4 from the NWB
files, to compare with the preprint's panels. Every curve panel (2D to 2I, 2N, and S4A to S4I) matches the values in
the preprint's statistics tables. The lab's measurement rules that this required, found by
matching the lab's per-cell tables in the Zenodo bundle:

- Firing rate counts upward crossings of 0 mV at least 5 ms apart over the whole 2 s sweep and divides by the 0.5 s
  step, so spikes after the step count toward the rate.
- Latency, mean ISI, and adaptation index come from ipfx 2.1.2 with no filter and spikes detected over the whole sweep.
  A cell's latency at a current is the mean over its runs, including runs whose first spike precedes the step
  (negative latency), and is left out when that mean is negative.
- Runs held near -60 mV are averaged with the runs at rest, and only cells with `in_preprint_figures` True are used.
- The bar panels (2J to 2M) remove outliers within each group with ROUT (Q = 0.1%), as the preprint describes; the curve
  panels keep every cell.
- A rheobase run that never fires counts as its largest step plus 5 pA, and the runs of a cell are averaged.

Two bar panels are not reproduced. In 2M the lab averaged only some rheobase runs for seven cells and used the F-I
steps for eight cells that have the 5 pA protocol, with no rule the files show. In 2K the charge of the test pulse
transient gives about half the lab's capacitance values, and the lab's method is not described.

## Log sheet metadata

The three Excel log sheets in `metadata/log_sheets/` are read directly by `nadel_2026_extract_log_sheets.py`, which
writes `nadel_2026_log_cells.csv`, `nadel_2026_log_test_pulses.csv`, `nadel_2026_log_held_runs.csv`, and
`nadel_2026_log_sessions.csv` (curator
decision 9). Each row records its source sheet and rows, and every typo fix or blanked entry is listed in the script
and in the `extraction_note` column. Cells are matched to their log block by the sweep numbers of their files, since
many blocks are mislabeled or unlabeled; MZ's cells are read from his own sheet under his numbering.

- On the electrode: `resistance` (pipette resistance) where the log has it, as text such as "4.1 MOhm".
  `initial_access_resistance` would hold access at break-in, but that column is empty for every paper cell.
- Per-cell columns: `time_of_recording`, `pipette_offset`, `fast_capacitance_compensation`,
  `holding_current_to_minus_70_mV`, `resting_potential`, `bath_drugs`. Holding current and resting potential are text,
  since some entries hold two readings. The log states no units; descriptions give units only where Jacob's README
  does. A column is left out of a file when no cell that day has a value.
- Per run: `access_resistance` (MOhm) on the sequential recordings table for the 373 test-pulse runs with a logged
  value.
- Per day: the NWBFile `notes` field holds the internal, surgery, slicing outcome, and days since surgery.
- Coverage is better than Jacob's scraped CSVs (for example time of recording 193 vs 173 cells, pipette offset 84 vs
  70), but several fields stay sparse because the sheets are.

## Synchronization

All data in a file come from one DAQ and one WaveSurfer clock per run. Runs are placed on one timeline by
`ClockAtRunStart` (local time, America/Chicago); the session start is the earliest run of the day, and each sweep starts
at its run start plus its `timestamp`.

## Metadata

- Session-level text (slices, pharmacology, internal, devices, surgery) is from the preprint methods.
- Subject sex, stress group, and projection target come from `subjects_from_makeMice.csv`. Age is set only for the
  P40 mice (from makeMice); the P70 mice have no age or date of birth yet (lab question 6), which NWB Inspector
  reports as critical for those 30 files.
- Experimenters are the preprint's authors, in author order, for every file. The per-cell `experimenter` column keeps
  the initials of the person who recorded the cell (JN or MZ), as in the folder names.

## Ontology annotation

`nadel_2026_external_resources.yaml`, written into each file as HERD references:

- species `Mus musculus`: NCBITaxon:10090
- strain `C57BL/6J`: RRID:IMSR_JAX:000664 (Jackson Laboratory strain 000664, from the preprint's key resources table)
- institution `Northwestern University`: ROR:000e0be47 (Evanston, United States)
- electrode location `Central amygdalar nucleus`: MBA:536, and UBERON:0002883 (its cross-references include
  Allen 536)

Not annotated: experimenters (no ORCIDs in the preprint).
