# Notes concerning the seiler_2024 conversion split by interface

 ## Behavior
 In FP Experiments/Behavior,
- G represents portEntryTs (Port Entry Times)
- E represents DurationOfPE (Duration of Port Entry)
- A represents LeftNoseTs (Left Nose Poke Times)
- C represents RightNoseTs (Right Nose Poke Times)
- D represents RightRewardTs (Reward Delivered after Active Nose Poke)
- B represents LeftRewardTs (Interleaved per animal -- probably)

In FP Experiments/Behavior/PS,
- some of the animals have csvs, but are missing the raw MEDPC Files (ex. 75.214), but some animals do have them (ex. 110.271)

In FP Experiments/Behavior/PR/028.392,
- some of the sessions (ex. 7/09/20) have ALL NaN values for Duration of Port Entry

Plan for interface:
- treat MEDPC files as fundamental, switch to secondary interface if only .csv files are available
- two different options: from_medpc and from_csv
- session_id = {animal_id}_{MM-DD-YY}
