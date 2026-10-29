# aCUS intrinsic ephys: questions for the lab

Questions for Jacob about `aCUS_ephys_raw_for_NWB`. The conversion covers the 198 cells in the preprint's figures (`nadel_2026_paper_cells.csv`). "Current behavior" is what the conversion does until we hear back. Answered questions move to Closed with the answer and date, and keep their numbers.

## Open

### Cells and runs

1\. Which cells are in each Figure 2 panel?
- Figs. 2D-F (P70): `baseline Firing Rate.csv` in the Zenodo bundle reproduces the figures' means and SEMs exactly, but its cells differ from `used cells.csv`. It adds the 3 m410 cells, `m108 s1c3`, and `m011 s2c1 +`, and leaves out `m105 s1c1` and `m114 s2c2`. Is that table the right list?
- Fig. 2N (P40): the counts (16 unstressed, 19 stressed) match your cells in 853-L, 854-L, 855-L, and 862-L. Are those the cells?
- `m011 s2c1 +`: the table's F-I sweeps (297-307) are in its rheobase runs, not its F-I runs. Are the paper's values from the right sweeps? The cell has no log entry, so which of its runs were held at -60 mV?

The P40 and m410 parts repeat our Oct 21 email.

Current behavior: the 160 cells in `used cells.csv`, the 3 m410 cells, and the 35 P40 cells.

2\. The README says to exclude the Sept 2023 runs held at -60 mV, but the Zenodo bundle analyzes them (`firing rate from -60.csv`). Should they stay out? The files don't mark these runs, so we found them from the log's sweep ranges. Is that reliable? For `m009 s1c1` we read the log as the third F-I run and third rheobase run being at -60 mV.

Current behavior: 86 runs from 10 cells excluded (`nadel_2026_excluded_runs.csv`).

3\. `m009_0001-0003.h5` and `m009_0004.h5` are in MZ's `m009 s3c1` folder. Per the README they belong to `m009 s1c1`. Is that right?

Current behavior: converted as runs of `m009 s1c1`.

4\. Sweep numbers repeat in `m114 s2c2` (for example, `m114_0422-0432.h5` and `m114_0432-0434.h5` both hold sweep 432). Was the counter reset by hand?

Current behavior: every file is converted.

### Recording settings

5\. Was the VC holding potential -70 mV for every VC run, including test pulses and Ih, in all years?

Current behavior: -70 mV.

6\. Which MultiClamp settings file (`ashley mc setup on 20230301.mcc` or `rig 2 mc setup on 2023 08 04.mcc`) applies to which days? We need the low-pass filter setting, and whether bridge balance and pipette capacitance neutralization were on. The log has values for both, but the snapshots say off.

7\. Is slice thickness recorded per day, or should we use the preprint's 250-300 µm?

8\. The log says "Kgluc" for 2023 and "Mod Kgluc" from 2024. Is the preprint's internal the modified one, and if so, what was the 2023 recipe?

### Subjects

9\. Can dates of birth for the P70 mice be recovered from colony records?

Current behavior: no age. NWB Inspector flags this as critical in 30 files.

10\. Does age 40 in makeMice mean the bead surgery day or the recording day? The preprint says recordings started at P41.

Current behavior: P40.

11\. What was the bead surgery date for each mouse, or the number of days from surgery to recording?

12\. Is P28-P40 the stress window for every stressed mouse, including the P40 cohort?

13\. Is 611-323 (m323) actually 611-024? Do the sex discrepancies in `subject_discrepancies.csv` all resolve to makeMice?

Current behavior: makeMice is the source for ID and sex.

14\. Are all mice C57BL/6J, JAX stock 000664?

Current behavior: C57BL/6J, with no stock number.

15\. The log's hemisphere column is empty. Is the recorded hemisphere known for any cells?

Current behavior: not recorded.

### People

16\. Is MZ Manhua Zhu? Can we have ORCIDs for both of you?

### Data and logs

17\. In your Sept 2023 files, the second analog input records membrane potential a second time, not the command (it tracks the voltage channel with slope 0.92-1.00 and r 0.96-1.00). MZ's files from the same month have identical headers and record the command, so this looks like a cabling difference. Were you on a different rig or cabling? We suggest README item 1 say this channel is membrane potential and the command was not recorded in those files.

Current behavior: those 263 runs have a stimulus template only.

18\. The log sheet notes mix useful experimental information with informal wording. We propose keeping the experimental content, removing expletives and personal remarks, and dropping notes with no experimental content. We would send you the edited notes to review. Is that OK, or would you prefer them verbatim or left out?

Current behavior: notes are not converted.

19\. Were all analyzed cells retrobead-positive? The log's Retrob+ column is blank for 79 of the 198 cells, and `m103 s3c5` is marked "y?".

Current behavior: every cell is described as retrobead-positive.

20\. Can you check how we read these log entries? Every case is listed in `nadel_2026_extract_log_sheets.py`.
- Read as typos: Cp fast "14/106" as 14.106 (`m022 s3c2`), holding "-100\\" as -100 (`m103 s3c4`), "2L46" as 2:46 and "(19,5)" as 19.5 (`m410 s2c1`), and "35!!" as 35.
- Left blank: Rt 4.5 (`m323 s3c2`), Er 34.05 (`m403 s2c3`), P Neutr -150 (`m202 s1c4`), resting "60" (`m113 s4c2`), and access "(15ish?)" (MZ's s2c1).
- Test pulses we could not match to a file: `m021 s1c2` (its first test pulse file is in the `m021 s1c1` folder), `m203 s1c1` ("1-3", no file), and `m114 s2c2` (three candidate files).
- Day fields left blank: Internal "021" (m021) and Surgery "s" (m106). The Date fields on the m104 to m107, m204, and m403 tabs don't match the recording days.

## Closed

None yet.
