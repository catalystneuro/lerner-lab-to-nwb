# aCUS intrinsic ephys: questions for the lab

Questions for Jacob about `aCUS_ephys_raw_for_NWB`. The conversion covers the cells in the preprint's figures. Answered questions move to Closed with the answer and date, and keep their numbers.

## Open

### Cells and runs

1\. Which cells are in Figure 2? The README says `used cells.csv` lists the 160 cells in the paper, and that the June 2026 PAG mouse (2006-151) and the timecourse mice are not in the paper. The preprint's statistics table does not match this.
- 1A. Figs. 2D-F (P70). The cell counts in `used cells.csv` differ from the preprint in three groups: BNST unstressed (14 vs 15), BNST stressed (14 vs 13), and PAG unstressed (11 cells from 2 mice vs 14 from 3). `baseline Firing Rate.csv` in the Zenodo bundle matches the preprint's counts in all six groups and all 66 F-I means and SEMs. It has 5 cells that `used cells.csv` does not: `m108 s1c3` (BNST unstressed), `m011 s2c1 +` (SNL unstressed), and the 3 cells of 2006-151 (PAG unstressed). It does not have 2 cells that `used cells.csv` has: `m105 s1c1` (BNST stressed) and `m114 s2c2` (SNL unstressed). Are the cells in `baseline Firing Rate.csv` the cells in these panels?
- 1B. Fig. 2N (P40). The preprint reports 16 unstressed and 19 stressed cells, from 2 mice per group. The README lists the timecourse mice as not in the paper, and no P40 cell is in `used cells.csv` or the Zenodo bundle. Are the Fig. 2N cells in the shared data? If so, are they the cells in 853-L and 855-L (unstressed) and 854-L and 862-L (stressed)? Those folders hold 16 and 19 cells, not counting ES's 4 in 855-L.
- 1C. `m011 s2c1 +` has no log entry. It has 6 F-I runs, 3 before and 3 after a second spontaneous run (`m011_0339.h5`). The 9 cells the log lists with held runs also have a second spontaneous run, which the log marks as held. Were its runs from `m011_0339.h5` on held at -60 mV?

The P40 and 2006-151 parts repeat the Oct 21 email.

2\. The README says to exclude the runs held at -60 mV in Sept 2023, but the `sweep` values in `baseline Firing Rate.csv` suggest they were used in Fig. 2F for the 10 SNL cells that have them (listed in `nadel_2026_excluded_runs.csv`). Were they?

3\. `m021_0116-0118.h5`, a VC test pulse, is in the `m021 s1c1 +` folder, but the log lists sweeps 116-118 as the opening test pulse of `m021 s1c2 +`. Which cell does it belong to?

### Recording settings

4\. The log has columns for bridge balance (BB) and pipette capacitance neutralization (P Neutr), but BB is empty for every cell and P Neutr has one entry (question 14). The two MultiClamp snapshots are named with dates before the first recording day and have capacitance neutralization off. Were bridge balance and capacitance neutralization on during these recordings, and what was the low-pass filter setting?

5\. The preprint gives one internal recipe, a modified potassium gluconate internal, but the log's Internal field reads "Kgluc for CC" on 13 recording days and "Mod Kgluc" or "Modified Kgluc" on 16. Are these different solutions, and if so, what is the recipe of the unmodified one?

### Subjects

6\. The README says dates of birth and surgery dates are missing.
- 6A. The preprint says the P70 mice recovered about 3 weeks after surgery, but the log's "days since surgery" reads "7 ish" on 8 of their recording days. What were each mouse's date of birth and surgery date?
- 6B. The preprint says the P40 mice got beads at P40 and were recorded from P41, but the log's "days since surgery" reads "7 ish" for 853-L and 854-L. What were each mouse's date of birth and surgery date?

7\. README item 7 says the real ID of 611-323 (m323) is probably 611-024. Is it?

8\. The log's L or R column is empty for every cell. Is the recorded hemisphere known for any cell?

### Data and logs

9\. The log notes mix experimental information with informal wording, for example "sliced @ 250, not so good lol". Proposed: keep the experimental content and remove the rest ("Sliced at 250 µm, not so good."), with the edited notes sent for review first. Is that OK, or should the notes be verbatim or left out?

10\. The preprint says recordings targeted bead-positive cells, but the log's Retrob+ column is blank for 79 of the 198 cells, and `m103 s3c5` is marked "y?". Were all of these cells bead-positive?

### Log sheet entries

11\. Some log values look like typos and were read as follows. Are these right?
- 11A. Cp fast "14/106" as 14.106 (`m022 s3c2 +`).
- 11B. Holding current "-100\\" as -100 (`m103 s3c4`).
- 11C. Time "2L46" as 2:46 (`m410 s2c1`).
- 11D. Access "(19,5)" as 19.5 (`m410 s2c1`).

12\. In MZ's log for 20230918, the Er column is empty for every cell, and the Rt values (4.5, 5.5, and 4.5 MΩ) are low for access resistance. Could you double-check that these are access resistances and not pipette resistances?

13\. The log has Er 34.05 for `m403 s2c3`. The other pipette resistances in the log are 3.8 to 5.8 MΩ, and 34.05 is in the range of the P off values (19 to 43). Could you double-check whether it is a pipette offset?

14\. The log's only P Neutr entry is -150, for `m202 s1c4`, which is in the range of the holding currents. Could you double-check whether it is a holding current?

15\. The log has a resting potential of "60" for `m113 s4c2`. Could you double-check whether it is -60 mV?

16\. MZ's log has access "(15ish?)" for the first test pulse of `m006 s4c1 +`. Is 15 MΩ close enough to record?

17\. These end test pulses are logged with sweep numbers that no file of the cell holds. Each cell has two test pulses in the log and two test pulse files, so each was matched to the cell's second file. Are these right?
- 17A. `m006 s2c2 +`: logged 1240-1242, matched to `m006_1235-1237.h5`.
- 17B. `m021 s1c3 +`: logged 501-503, matched to `m021_0518-0520.h5`.
- 17C. `m021 s2c2 +`: logged 647-649, matched to `m021_0643-0645.h5`.
- 17D. `m103 s2c1`: logged 247-249, matched to `m103_0264-0266.h5`.
- 17E. `m105 s2c3`: logged 470-472, matched to `m105_0449-0451.h5`.
- 17F. `m105 s3c2`: logged 594-596, matched to `m105_0583-0585.h5`.
- 17G. `m107 s5c1`: logged 927-929, matched to `m107_0937-0939.h5`.
- 17H. `m201 s2c2`: logged 423-425, matched to `m201_0433-0435.h5`.
- 17I. `m205 s2c3`: logged 243-245, matched to `m205_0247-0249.h5`.
- 17J. `m208 s1c3`: logged 164-166, matched to `m208_0160-0162.h5`.
- 17K. `m113 s3c1`: logged 552-554, matched to `m113_0582-0584.h5`.
- 17L. `m114 s2c5`: logged 819-821, matched to `m114_0834-0836.h5`.
- 17M. `m404 s1c4`: logged 1133-115, matched to `m404_s1c4_0113-0115.h5`.

18\. The log lists the first test pulse of `m203 s1c1` as sweeps 1-3, but no file in the hand-off holds those sweeps. Is there a file for it?

19\. The log lists the end test pulse of `m114 s2c2` as sweeps 436-438, but no file holds those sweeps. Is it `m114_0433-0435.h5` (recorded in CC) or `m114_0432-0434.h5` (VC)?

20\. The Date field on these log tabs differs from the date in the folder name. The conversion uses the folder dates. Are those right?
- 20A. 671-0: Date field "05/29/2024", folder 20240530.
- 20B. 674-L: Date field "05/29/2024", folder 20240531.
- 20C. 675-R: Date field "05/29/2024", folder 20240603.
- 20D. 674-0: Date field "05/29/2024", folder 20240604.
- 20E. 752-0: Date field "2/13", folder 20250220.
- 20F. 854-L: Date field "10/1/25", folder 20251017.

## Closed

None yet.
