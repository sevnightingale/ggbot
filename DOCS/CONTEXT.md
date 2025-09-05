1) no it's not currenlty running, I turned it off for now, and we consolidated the custom table it was using into the new v2 'decisions' table. 
2) yes, Signal Validation should be a config_type. OH important update, this needs to be reflected based on teh decision in the ggbot config on the frontend, needs to reflect the config type.
3) separete. We added the 'paid_data_points' field to the user profiles table for just this. So that the logic can be 'does current user have paid_data_point = ggShot?' in order to unlock the ggshot signal in the frontend, please check if that's the case already.
4) no migrations necessary. We didn't keep any data when we switched to Supabase, we still have our existing postgres with the old data but we won't worry about migrating any of it. 
5) not a priority, I will get to stripe later.
6) not yet, i'll get to it later.
7) I'm not sure... I have to do more research there. For now let's foucs on getting the free tier up and running with paper trading. That's prioriy #1. Then we'll figure out telegram and stripe later, you can add steps here to the end of TODO_V2. 
8) Idk the difference between websockets vs supabase, can you explain the consdierations?
9) I think we want to keep the messages really short, 4 or 5 words max... we should think through the status messages more... we should look more closely at the logs and see what is printed as updates... 
10) let's just focus on getting one full comphrensive e2e test. the full lifecycle. one test to rule them all. no mock data. no placeholders. 
11) Uhm.... not sure yet.. not that I can think of at this moment but they'll come I'm sure. 
12) no need for now. 
13) yes. updating documentation regularly is so so so important. 

