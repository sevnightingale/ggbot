// Test script to fetch timeline data for debugging
const configId = 'bb2560fd-b053-464f-8a58-8e254e4d36fa';

async function fetchTimelineData() {
  console.log('Fetching data for config:', configId);
  console.log('='.repeat(80));

  try {
    // Fetch all three endpoints in parallel (same as component)
    const [activitiesRes, balanceSeriesRes, metadataRes] = await Promise.all([
      fetch(`http://localhost:8000/api/v2/activities/${configId}`),
      fetch(`http://localhost:8000/api/v2/activities/${configId}/balance-series`),
      fetch(`http://localhost:8000/api/v2/activities/${configId}/metadata`)
    ]);

    console.log('\nResponse status codes:');
    console.log('  Activities:', activitiesRes.status);
    console.log('  Balance series:', balanceSeriesRes.status);
    console.log('  Metadata:', metadataRes.status);

    const activities = await activitiesRes.json();
    const balanceSeries = await balanceSeriesRes.json();
    const metadata = await metadataRes.json();

    console.log('\n' + '='.repeat(80));
    console.log('ACTIVITIES:', activities.activities?.length || 0, 'items');
    if (activities.activities?.length > 0) {
      console.log('  First activity:', {
        timestamp: activities.activities[0].timestamp,
        type: activities.activities[0].type
      });
      console.log('  Last activity:', {
        timestamp: activities.activities[activities.activities.length - 1].timestamp,
        type: activities.activities[activities.activities.length - 1].type
      });
    }

    console.log('\n' + '='.repeat(80));
    console.log('BALANCE SERIES:', balanceSeries.balance_series?.length || 0, 'points');
    if (balanceSeries.balance_series?.length > 0) {
      console.log('  First point:', balanceSeries.balance_series[0]);
      console.log('  Last point:', balanceSeries.balance_series[balanceSeries.balance_series.length - 1]);
    }

    console.log('\n' + '='.repeat(80));
    console.log('METADATA:', metadata.metadata);

    // Calculate what seriesMs and seriesVal would be
    console.log('\n' + '='.repeat(80));
    console.log('WHAT THE COMPONENT WOULD CALCULATE:');

    const seriesMs = balanceSeries.balance_series?.map(p => new Date(p.timestamp).getTime()) || [];
    const seriesVal = balanceSeries.balance_series?.map(p => p.balance) || [];

    console.log('  seriesMs length:', seriesMs.length);
    console.log('  seriesVal length:', seriesVal.length);

    if (seriesMs.length > 0) {
      const dataFirst = seriesMs[0];
      const dataLast = seriesMs[seriesMs.length - 1];
      console.log('  dataFirst:', new Date(dataFirst).toISOString());
      console.log('  dataLast:', new Date(dataLast).toISOString());
      console.log('  Time span:', ((dataLast - dataFirst) / 3600000).toFixed(2), 'hours');
    }

    if (seriesVal.length > 0) {
      console.log('  Balance range:', Math.min(...seriesVal), 'to', Math.max(...seriesVal));
    }

    // Check if there's a mismatch
    console.log('\n' + '='.repeat(80));
    console.log('POTENTIAL ISSUES:');
    if (activities.activities?.length > 0 && balanceSeries.balance_series?.length === 0) {
      console.log('  ⚠️  Activities exist but balance series is empty!');
      console.log('  This means synthetic $0 baseline should be used');
    }
    if (balanceSeries.balance_series?.length > 0 && activities.activities?.length === 0) {
      console.log('  ⚠️  Balance series exists but no activities!');
    }

  } catch (error) {
    console.error('ERROR:', error.message);
  }
}

fetchTimelineData();
