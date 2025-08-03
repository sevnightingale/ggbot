1) Go ahead and remove those unused MCP indicator files. 
2) we DO have a .env in the project root, you may not see it because it's not tracked? idk? but we do.
3) update DOCS/CONFIG.md with your recommendations. 
4) Option C, hummingbot is jsut the execution layer for us for now (we may expand that in the future but for now we're only concerend with trade exeuction) but we need to be able to query by user+config_id (hummingbot has their own config system too so this might get confusing) so that we can dispaly active trades + historical performance on our frontend... Please update DOCS/TRADING_UPDATE.md to include next steps for assessing the schema and determining how our databases will interact. (there might actually be some stuff in there on this already). We should also include steps for cleaning up our legacy db schema after this transition (with no need to migrate data as we don't have any important trades data yet)
5) can you go ahead and remove the bubble.io references form documentation as well. 

So the three things you can take action on now are remoivng the legacy mcp indicator files, and removing the bubble.io mentions from teh doucmentaiton, then update the DOCS/TRADING_UPDATE.md file. 

After that let's stop and discuss more before we begin work on a ggbot project README.md 
