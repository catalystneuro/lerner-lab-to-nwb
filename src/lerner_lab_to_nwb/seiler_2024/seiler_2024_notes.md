# Notes concerning the seiler_2024 conversion split by interface

 ## Behavior
 For all medpc files,
 - MSN refers to the name of the code file used to produce this session

### FP Behavior
 In FP Experiments/Behavior,
- G represents portEntryTs (Port Entry Times)
- E represents DurationOfPE (Duration of Port Entry)
- A represents LeftNoseTs (Left Nose Poke Times)
- C represents RightNoseTs (Right Nose Poke Times)
- D represents RightRewardTs (Reward Delivered after Active Nose Poke)
- B represents LeftRewardTs (Interleaved per animal -- probably)
- H represents Footshock times

In FP Experiments/Behavior/PS,
- some of the animals have csvs, but are missing the raw MEDPC Files (ex. 75.214)
- In MEDPC_RawFilesbyDate, many of the sessions are missing Subject info (ex. 10/08/18 16:37:19)
- Some of the sessions missing Subject info are .csv sessions (ex. 75.214 11/09/18)
- For the animals missing raw med PC files, the plan is:
    - Iterate through all of the MEDPC_RawFilesbyDate, grabbing all of the session start times, dates, subject IDs, and MSNs
    - For subject IDs that match convert those sessions
    - Will need to refactor the read_medpc_file function to be able to _optionally_ handle different subject IDs in the same session
    - Sessions with missing subject info will just have to be skipped -- but will need to iterate through .csv sessions and match them to their corresponding medpc session

In FP Experiments/Behavior/PR/028.392,
- some of the sessions (ex. 7/09/20) have ALL NaN values for Duration of Port Entry

In FP Experiments/Behavior/DPR/272.396,
- some of the days (ex. 7/06/20) have two sessions per day

In FP Experiments/Behavior/DPR/334.394,
- some of the sessions (ex. 6/17/20) have both left and right rewards (MSN: FOOD_FR1 HT TTL (Both))

In FP Experiments/Behavior/PR/141.308,
- medpc file is filled with whitespace characters like \t

In FP Experiments/Behavior/PS/139.298,
- one of the sessions (ex. 09/20/19) is actually from subject 144.306
- 144.306 is a ghost -- it doesn't show up in any of the behavior folders and not in the mosue demographics google sheet

In FP Experiments/Behavior/PS/140.306,
- one of the sessions (ex. 09/06/19) has a bunch of garbage to the right of the 'A' variable

In FP Experiments/Behavior/MEDPCRawFilesbyDate/2018-11-09,
- All the sessions have the same start_date and start_time and no subject info --> need to make medpc reader support
more generic filter conditions (ex. box number)

In FP Experiments/Behavior/MEDPCRawFilesbyDate/2019-02-19,
- One of the animals (88.239) has 2 sessions in the same day, with one only 9mins long -- mistaken session?

What experimental stage (FR1, footshock probe, omission probe, etc.) does "Probe Test Habit Training TTL" correspond to?

Many MSNs (ex. 'FOOD_FR1 TTL Left', 'FOOD_FR1 TTL Right', and 'FOOD_RI 30 LEFT') list both E and U as corresponding to duration of port entry.

### Opto Behavior
- Opto Behavior files are disorganized esp. DLS Excitatory with a mix of folders, medpc files, and csv files
- File structure also contains important metadata for optogenetic interface ex. ChR2 vs EYFP
- Plan: Swing back around to opto behavior when constructing optogenetic interface

## Fiber Photometry
- 6 data streams:
    - Dv1A = array of photometry response dms 465nm
    - Dv2A = array of photometry response dms 405nm
    - Dv3B = array of photometry response dls 465nm
    - Dv4B = array of photometry response dls 405nm
    - Fi1d = 4xN array of demodulated commanded voltages: dms 465nm, dms 405nm, dls 465nm, dls 405nm
    - Fi1r = 2xN array of modulated commanded voltages: dms and dls
- Folders are named 'Photo_<subject_id>-YYMMDD-HHMMSS' --> match with same day behavior session
- some folders have subject_id with multiple session folders for each subject
- For DPR/334.394/07/02/20, no right nosepokes were made --> photometry object doesn't have a RNPS object
- Questions for Lerner Lab:
    - The TTL for 'unrewarded right nose pokes' (RNnR), corresponds to the nose pokes variable in medpc, which supposedly
    records *all* nosepokes. Which is correct?
    - Mistaken session 88.239?
    - PS/271.396_07/07/20 has two behavioral sessions but only 1 fp session folder
    - PS/332.393_07/28/20 has 2 fp sessions but no matching behavior session
    - The RR20 folder only has .mat files rather than tdt synapse output folders -- pls provide?
    - Several sessions don't have fi1d -- see printout
    - Delayed Punishment Resistant/Late/Photo_334_394-200721-131257 throws an error from tdt.read_block, but loads fine if t2 <= 824
        - Solution: just load with t2<=824
        - This session also is missing RNPS TTL
    - Punishment Sensitive/Late RI60/Photo_139_298-190912-095034 throws an error from tdt.read_block, but loads fine if t2 <= 2267
        - Solution: just load with t2<=2267
        - This session is also Fi1r-only
    - Punishment Sensitive/Early RI60/Photo_140_306-190809-121107 has msn FOOD_RI 60 LEFT TTL, but epocs
    PrtN, RNnR, PrtR, LNPS, RNRW -- why is this mismatched with the expected epocs?
        - Answer: Per my notes, this animal was accidentally run on the wrong TDT program.
        - Solution: Manually correct this session (essentially everything that says right is actually left, and vice versa).
        - This sesison is also Fi1r-only
    - Some of the animals/days have 2 photometry sessions but only 1 behavior session
    (ex. Punishment Sensitive/Late RI60/Photo_139_298-190912-095034 and Photo_139_298-190912-103544) is the photometry
    for that 1 session split across the two folders?
    - List of missing Fi1d sessions:
    Delayed Punishment Resistant/Early/Photo_333_393-200713-121027
    Delayed Punishment Resistant/Early/Photo_346_394-200707-141513
    Delayed Punishment Resistant/Early/Photo_64_205-181017-094913
    Delayed Punishment Resistant/Early/Photo_81_236-190117-102128
    Delayed Punishment Resistant/Early/Photo_87_239-190228-111317
    Delayed Punishment Resistant/Late/64.205/Photo_64_205-181017-094913
    Delayed Punishment Resistant/Late/81.236/Photo_81_236-190117-102128
    Delayed Punishment Resistant/Late/81.236/Photo_81_236-190207-101451
    Delayed Punishment Resistant/Late/87.239/Photo_87_239-190228-111317
    Delayed Punishment Resistant/Late/87.239/Photo_87_239-190321-110120
    Delayed Punishment Resistant/Late/88.239/Photo_88_239-190311-112034
    Delayed Punishment Resistant/Late/Photo_333_393-200729-115506
    Delayed Punishment Resistant/Late/Photo_346_394-200722-132345
    Delayed Punishment Resistant/Late/Photo_349_393-200717-123319
    Punishment Resistant/Early RI60/Photo_111_285-190605-142759
    Punishment Resistant/Early RI60/Photo_141_308-190809-143410
    Punishment Resistant/Early RI60/Photo_80_236-190121-093425
    Punishment Resistant/Late RI60/61.207/Photo_61_207-181017-105639
    Punishment Resistant/Late RI60/63.207/Photo_63_207-181015-093910
    Punishment Resistant/Late RI60/63.207/Photo_63_207-181030-103332
    Punishment Resistant/Late RI60/80.236/Photo_80_236-190121-093425
    Punishment Resistant/Late RI60/89.247/Photo_89_247-190328-125515
    Punishment Resistant/Late RI60/Photo_028_392-200724-130323
    Punishment Resistant/Late RI60/Photo_048_392-200728-121222
    Punishment Sensitive/Early RI60/Photo_112_283-190620-093542
    Punishment Sensitive/Early RI60/Photo_113_283-190605-115438
    Punishment Sensitive/Early RI60/Photo_114_273-190607-140822
    Punishment Sensitive/Early RI60/Photo_115_273-190611-115654
    Punishment Sensitive/Early RI60/Photo_139_298-190809-132427
    Punishment Sensitive/Early RI60/Photo_75_214-181029-124815
    Punishment Sensitive/Early RI60/Photo_92_246-190227-143210
    Punishment Sensitive/Early RI60/Photo_78_214-181031-131820
    Punishment Sensitive/Early RI60/Photo_92_246-190227-150307
    Punishment Sensitive/Early RI60/Photo_93_246-190222-130128
    Punishment Sensitive/Late RI60/75.214/Photo_75_214-181029-124815
    Punishment Sensitive/Late RI60/78.214/Photo_78_214-181031-131820
    Punishment Sensitive/Late RI60/90.247/Photo_90_247-190328-103249
    Punishment Sensitive/Late RI60/92.246/Photo_92_246-190228-132737
    Punishment Sensitive/Late RI60/92.246/Photo_92_246-190319-114357
    Punishment Sensitive/Late RI60/93.246/Photo_93_246-190222-130128
    Punishment Sensitive/Late RI60/94.246/Photo_94_246-190328-113641
    Punishment Sensitive/Late RI60/Photo_140_306-190903-102551
    Punishment Sensitive/Late RI60/Photo_271_396-200722-121638
    Punishment Sensitive/Late RI60/Photo_347_393-200723-113530
    Punishment Sensitive/Late RI60/Photo_348_393-200730-113125

## Optogenetics
### Notes
- Optogenetic pulses are either paired directly with reward times or optogenetic_stimulus_times variable in medpc file
    for "scrambled" trials.
- timing info can be found in paper (460nm, 1 s, 20 Hz, 15 mW for excitatory and 625nm, 1 s, 15 mW for inhibitory)
- Some of the opto csv sessions have start times (ex. DLS Excitatory/ChR2/290.407/290.407_09-23-20.csv) -- added optional parsing
- Some of the sessions (ex. DLS-Excitatory/079.402/06/27/20) don't have any reward/stim times

### Questions
- need to ask for more specific info about the device (data sheet)
- Need pulse width for excitatory optogenetics
- DMS-Inhibitory Group 2 is missing
- DLS-Excitatory has a bunch of files (medpc and csv) organized by date not belonging to any optogenetic treatment group folder
    (ChR2, EYFP, Scrambled).  Which treatment did these sessions receive?
- DMS-Excitatory has some csv files w/ only session-aggregated info (total right rewards but not right reward times)
    ex. ChR2/121_280.CSV -- do you have individual session info for these animals?
- RI 60 LEFT_STIM, RI 30 LEFT_STIM, and RK_C_FR1_BOTH_1hr msns show up in opto data but don't have associated files -- assumed to be the same as their right counterparts?
