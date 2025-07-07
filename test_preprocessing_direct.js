#!/usr/bin/env node
/**
 * Direct test of preprocessing functionality
 */

const path = require('path');

// Change to crypto-indicators-mcp directory
process.chdir(path.join(__dirname, 'core/mcp/servers/crypto-indicators-mcp'));

// Now require the modules
const { averageTrueRange, moneyFlowIndex, bollingerBands, volumeWeightedAveragePrice, tripleExponentialAverage, donchianChannel } = require('indicatorts');
const { preprocessIndicatorData } = require('./preprocessors');
const fetchOhlcvData = require('./utils/fetchOhlcvData');

async function testPreprocessing() {
  console.log('🔬 Testing Indicator Preprocessing\n');

  try {
    // Fetch real market data
    console.log('📊 Fetching BTC/USDT 1h data...');
    const asset = await fetchOhlcvData('BTC/USDT', '1h', 100);
    
    console.log(`✅ Fetched ${asset.closings.length} data points`);
    console.log(`Current price: $${asset.closings[asset.closings.length - 1].toFixed(2)}\n`);

    // Test ATR preprocessing
    console.log('🔧 Testing ATR Preprocessing:');
    const atrResult = averageTrueRange(asset.highs, asset.lows, asset.closings, { period: 14 });
    const atrProcessed = preprocessIndicatorData('atr', atrResult.atrLine, {
      prices: asset.closings,
      period: 14,
      currentPrice: asset.closings[asset.closings.length - 1]
    });
    
    console.log('✅ ATR Preprocessing:');
    console.log(`  Summary: ${atrProcessed.summary}`);
    console.log(`  Volatility Level: ${atrProcessed.context.volatilityLevel}`);
    console.log(`  Risk Level: ${atrProcessed.risk.assessment.level}\n`);

    // Test MFI preprocessing
    console.log('🔧 Testing MFI Preprocessing:');
    const mfiResult = moneyFlowIndex(asset.highs, asset.lows, asset.closings, asset.volumes, { period: 14 });
    const mfiProcessed = preprocessIndicatorData('mfi', mfiResult, {
      prices: asset.closings,
      volumes: asset.volumes,
      period: 14,
      currentPrice: asset.closings[asset.closings.length - 1]
    });
    
    console.log('✅ MFI Preprocessing:');
    console.log(`  Summary: ${mfiProcessed.summary}`);
    console.log(`  Volume Flow: ${mfiProcessed.context.volumeFlow}`);
    console.log(`  Position: ${mfiProcessed.context.position}\n`);

    // Test BBW preprocessing
    console.log('🔧 Testing Bollinger Bands Width Preprocessing:');
    const bb = bollingerBands(asset.closings, { period: 20, stdDev: 2 });
    const bbwValues = bb.upper.map((upper, i) => {
      const lower = bb.lower[i];
      const middle = bb.middle[i];
      return middle > 0 ? (upper - lower) / middle : 0;
    });
    
    const bbwProcessed = preprocessIndicatorData('bollingerBandsWidth', bbwValues, {
      prices: asset.closings,
      period: 20,
      stdDev: 2,
      currentPrice: asset.closings[asset.closings.length - 1]
    });
    
    console.log('✅ BBW Preprocessing:');
    console.log(`  Summary: ${bbwProcessed.summary}`);
    console.log(`  Squeeze Status: ${bbwProcessed.context.squeezeStatus}`);
    console.log(`  Volatility Phase: ${bbwProcessed.context.phase}\n`);

    // Test VWAP preprocessing
    console.log('🔧 Testing VWAP Preprocessing:');
    const vwapResult = volumeWeightedAveragePrice(asset.highs, asset.lows, asset.closings, asset.volumes);
    const vwapProcessed = preprocessIndicatorData('vwap', vwapResult, {
      prices: asset.closings,
      volumes: asset.volumes,
      currentPrice: asset.closings[asset.closings.length - 1]
    });
    
    console.log('✅ VWAP Preprocessing:');
    console.log(`  Summary: ${vwapProcessed.summary}`);
    console.log(`  Position: ${vwapProcessed.context.position}`);
    console.log(`  Institutional Flow: ${vwapProcessed.context.institutionalFlow}\n`);

    // Test TRIX preprocessing
    console.log('🔧 Testing TRIX Preprocessing:');
    const trixResult = tripleExponentialAverage(asset.closings, { period: 15 });
    const trixProcessed = preprocessIndicatorData('trix', trixResult, {
      prices: asset.closings,
      period: 15
    });
    
    console.log('✅ TRIX Preprocessing:');
    console.log(`  Summary: ${trixProcessed.summary}`);
    console.log(`  Momentum: ${trixProcessed.context.momentum}`);
    console.log(`  Trend Strength: ${trixProcessed.context.trendStrength}\n`);

    // Test Donchian Channel preprocessing
    console.log('🔧 Testing Donchian Channel Preprocessing:');
    const dcResult = donchianChannel(asset.highs, asset.lows, { period: 20 });
    const dcProcessed = preprocessIndicatorData('donchianChannel', dcResult, {
      prices: asset.closings,
      period: 20,
      currentPrice: asset.closings[asset.closings.length - 1]
    });
    
    console.log('✅ Donchian Channel Preprocessing:');
    console.log(`  Summary: ${dcProcessed.summary}`);
    console.log(`  Position: ${dcProcessed.context.position}`);
    console.log(`  Breakout Status: ${dcProcessed.patterns.breakout ? dcProcessed.patterns.breakout.type : 'None'}\n`);

    console.log('✅ All preprocessing tests completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testPreprocessing();