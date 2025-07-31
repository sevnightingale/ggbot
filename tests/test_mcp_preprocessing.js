#!/usr/bin/env node
/**
 * Test script for MCP preprocessing updates
 * Tests ATR, MFI, BBW, VWAP, and TRIX preprocessing
 */

const { spawn } = require('child_process');
const path = require('path');

async function testIndicator(tool, params = {}) {
  return new Promise((resolve, reject) => {
    const args = [
      path.join(__dirname, 'core/mcp/servers/crypto-indicators-mcp/index.js'),
      'call',
      tool,
      JSON.stringify({
        symbol: 'BTC/USDT',
        timeframe: '1h',
        limit: 50,
        format: 'preprocessed',
        ...params
      })
    ];

    const child = spawn('node', args, {
      cwd: __dirname,
      env: { ...process.env }
    });

    let output = '';
    let error = '';

    child.stdout.on('data', (data) => {
      output += data.toString();
    });

    child.stderr.on('data', (data) => {
      error += data.toString();
    });

    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Process exited with code ${code}: ${error}`));
      } else {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse output: ${output}`));
        }
      }
    });
  });
}

async function runTests() {
  console.log('🔬 Testing MCP Indicator Preprocessing\n');

  const indicators = [
    { name: 'ATR', tool: 'calculate_average_true_range', params: { period: 14 } },
    { name: 'MFI', tool: 'calculate_money_flow_index', params: { period: 14 } },
    { name: 'BBW', tool: 'calculate_bollinger_bands_width', params: { period: 20, stdDev: 2 } },
    { name: 'VWAP', tool: 'calculate_volume_weighted_average_price', params: {} },
    { name: 'TRIX', tool: 'calculate_triple_exponential_average', params: { period: 15 } },
    { name: 'Donchian', tool: 'calculate_donchian_channel', params: { period: 20 } },
    { name: 'Bollinger', tool: 'calculate_bollinger_bands', params: { period: 20, stdDev: 2 } }
  ];

  for (const indicator of indicators) {
    console.log(`\n📊 Testing ${indicator.name}:`);
    
    try {
      const result = await testIndicator(indicator.tool, indicator.params);
      
      if (result.content && result.content[0] && result.content[0].text) {
        const data = JSON.parse(result.content[0].text);
        
        // Check if we got preprocessed data
        if (data.indicator && data.summary && data.context) {
          console.log(`✅ ${indicator.name} preprocessing working!`);
          console.log(`   Indicator: ${data.indicator}`);
          console.log(`   Summary: ${data.summary}`);
          console.log(`   Current Value: ${data.current?.value || 'N/A'}`);
        } else {
          console.log(`❌ ${indicator.name} returned raw data instead of preprocessed`);
          console.log(`   Keys: ${Object.keys(data).join(', ')}`);
        }
      } else {
        console.log(`❌ ${indicator.name} returned unexpected format`);
      }
    } catch (error) {
      console.log(`❌ ${indicator.name} failed: ${error.message}`);
    }
  }

  console.log('\n✅ Test completed!');
}

runTests().catch(console.error);