I now want to make 
  sure the indicators MCP is working, and then I 
  want to get a basic version of the Decision 
  Agent working, and then I want to test the 
  entire thing working together, where the 
  Extraction Agent gathers some indicator data and
   stores it in our market data table, then the 
  decision agent uses that market data + a basic 
  trading strategy to make a decision to enter a 
  trade, and then that decision gets sent to the 
  Trading Agent as the prompt for the LLM that 
  makes the CCXT tool call and executes the trade 
  on our BitMEX test account!