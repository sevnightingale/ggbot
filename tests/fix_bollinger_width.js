const { bollingerBands } = require("indicatorts");

// Test data (some sample closing prices)
const testClosings = [
  107139.81, 107242.62, 107282.92, 107441.69, 107481.59,
  107493.09, 107476.79, 107465.95, 107450.29, 107470.60,
  107520.99, 107557.24, 107574.48, 107576.65, 107638.87,
  107674.00, 107698.04, 107640.07, 107617.44, 107599.20,
  107580.07, 107512.17, 107515.27, 107486.59, 107440.07
];

console.log("Manual BollingerBandsWidth calculation:");

try {
  // Get bollinger bands first
  const bb = bollingerBands(testClosings, { period: 20, stdDev: 2 });
  console.log("✅ bollingerBands result:", Object.keys(bb));
  
  if (bb && bb.upper && bb.lower && bb.middle) {
    // Calculate width manually: (upper - lower) / middle
    const width = bb.upper.map((upper, i) => {
      const lower = bb.lower[i];
      const middle = bb.middle[i];
      return middle > 0 ? (upper - lower) / middle : 0;
    });
    
    console.log("✅ Manual width calculation successful!");
    console.log("Width array length:", width.length);
    console.log("Last few width values:", width.slice(-5));
    
    // Return as JSON like other indicators
    const result = { width };
    console.log("Result:", JSON.stringify(result));
    
  } else {
    console.log("❌ Bollinger Bands result missing required properties");
  }
  
} catch (error) {
  console.log("❌ Manual calculation error:", error.message);
}