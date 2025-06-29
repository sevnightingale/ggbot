const { bollingerBands, bollingerBandsWidth } = require("indicatorts");

// Test data (some sample closing prices)
const testClosings = [
  107139.81, 107242.62, 107282.92, 107441.69, 107481.59,
  107493.09, 107476.79, 107465.95, 107450.29, 107470.60,
  107520.99, 107557.24, 107574.48, 107576.65, 107638.87,
  107674.00, 107698.04, 107640.07, 107617.44, 107599.20,
  107580.07, 107512.17, 107515.27, 107486.59, 107440.07
];

console.log("Testing indicatorts library...");
console.log("Test data length:", testClosings.length);

try {
  console.log("\n1. Testing bollingerBands (working):");
  const bbResult = bollingerBands(testClosings, { period: 20, stdDev: 2 });
  console.log("✅ bollingerBands result:", typeof bbResult, Object.keys(bbResult || {}));
  if (bbResult && bbResult.upper) {
    console.log("   Upper band length:", bbResult.upper.length);
  }
} catch (error) {
  console.log("❌ bollingerBands error:", error.message);
}

try {
  console.log("\n2. Testing bollingerBandsWidth (failing):");
  const bbwResult = bollingerBandsWidth(testClosings, { period: 20, stdDev: 2 });
  console.log("✅ bollingerBandsWidth result:", typeof bbwResult, bbwResult);
} catch (error) {
  console.log("❌ bollingerBandsWidth error:", error.message);
  console.log("Error stack:", error.stack);
}

// Test with different parameters
try {
  console.log("\n3. Testing with minimal parameters:");
  const bbwMinimal = bollingerBandsWidth(testClosings);
  console.log("✅ bollingerBandsWidth (minimal) result:", typeof bbwMinimal, bbwMinimal);
} catch (error) {
  console.log("❌ bollingerBandsWidth (minimal) error:", error.message);
}

// Test with different data format
try {
  console.log("\n4. Testing with undefined closings:");
  const bbwUndefined = bollingerBandsWidth(undefined, { period: 20, stdDev: 2 });
  console.log("✅ bollingerBandsWidth (undefined) result:", bbwUndefined);
} catch (error) {
  console.log("❌ bollingerBandsWidth (undefined) error:", error.message);
}