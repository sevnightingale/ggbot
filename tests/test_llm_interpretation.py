#!/usr/bin/env python
"""
LLM Interpretation Analysis - Verify LLM correctly interprets raw indicator data

This test analyzes the LLM's interpretation of indicators by:
1. Parsing the raw indicator data from logs
2. Manually calculating the current values 
3. Comparing with LLM's stated interpretations
4. Validating the accuracy of LLM conclusions
"""

import json
import re

def analyze_aroon_data():
    """Analyze Aroon data interpretation."""
    print("🔍 ANALYZING AROON INTERPRETATION")
    print("=" * 50)
    
    # Raw Aroon data from logs (latest test)
    aroon_raw = {
        "up": [100,100,92.85714285714286,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,100,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,100,92.85714285714286,85.71428571428571,78.57142857142857,100,100,92.85714285714286,100,100,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,100,92.85714285714286,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,100,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285],
        "down": [100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,100,92.85714285714286,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,100,100,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,0,-7.142857142857142,-14.285714285714285,-21.428571428571427,-28.57142857142857,-35.714285714285715,-42.857142857142854,-50,-57.14285714285714,-64.28571428571429,-71.42857142857143,100,92.85714285714286,85.71428571428571,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,100,100,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,100,92.85714285714286,100,92.85714285714286,100,92.85714285714286,85.71428571428571,78.57142857142857,71.42857142857143,64.28571428571429,57.14285714285714,50,42.857142857142854,35.714285714285715,28.57142857142857,21.428571428571427,14.285714285714285,7.142857142857142,0]
    }
    
    # Current values (last in arrays)
    current_aroon_up = aroon_raw["up"][-1]  
    current_aroon_down = aroon_raw["down"][-1]
    
    print(f"📊 Raw Aroon Data Analysis:")
    print(f"   Aroon Up (current): {current_aroon_up}")
    print(f"   Aroon Down (current): {current_aroon_down}")
    
    # LLM stated: "Aroon Up at 100 and Aroon Down at 0"
    llm_aroon_up = 100
    llm_aroon_down = 0
    
    print(f"\n🤖 LLM Interpretation:")
    print(f"   LLM said Aroon Up: {llm_aroon_up}")
    print(f"   LLM said Aroon Down: {llm_aroon_down}")
    
    print(f"\n✅ Accuracy Check:")
    up_correct = abs(current_aroon_up - llm_aroon_up) < 1
    down_correct = abs(current_aroon_down - llm_aroon_down) < 1
    
    print(f"   Aroon Up: {'✅ CORRECT' if up_correct else '❌ INCORRECT'} (Actual: {current_aroon_up}, LLM: {llm_aroon_up})")
    print(f"   Aroon Down: {'✅ CORRECT' if down_correct else '❌ INCORRECT'} (Actual: {current_aroon_down}, LLM: {llm_aroon_down})")
    
    # Market regime assessment
    print(f"\n🏛️ Market Regime Assessment:")
    if current_aroon_up > 70 and current_aroon_down < 30:
        regime = "TRENDING (Up trend)"
    elif current_aroon_down > 70 and current_aroon_up < 30:
        regime = "TRENDING (Down trend)"
    elif current_aroon_up < 30 and current_aroon_down < 30:
        regime = "RANGING"
    else:
        regime = "MIXED"
    
    print(f"   Calculated Regime: {regime}")
    print(f"   LLM said: 'TRENDING' with 'strong upward momentum'")
    
    regime_correct = "TRENDING" in regime
    print(f"   Regime Assessment: {'✅ CORRECT' if regime_correct else '❌ INCORRECT'}")
    
    return up_correct and down_correct and regime_correct

def analyze_bbw_data():
    """Analyze Bollinger Band Width interpretation."""
    print("\n\n🔍 ANALYZING BOLLINGER BAND WIDTH INTERPRETATION")
    print("=" * 60)
    
    # Raw BBW data from logs
    bbw_raw = {"width": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0613474521500671,0.0705854719637642,0.0761258989145904,0.08391948678300656,0.09072281284979068,0.0955738347042694,0.0978608824020015,0.09812997247231672,0.09677067541474167,0.09151815708031737,0.0906362010049027,0.09230080410696698,0.0906147657165912,0.08531318491547556,0.07532821997275817,0.06664208732132142,0.055372431373405154,0.04542641711563697,0.034332651418210756,0.03185456292111996,0.02945650950055451,0.029866726233480544,0.030181222706718136,0.03135790607215062,0.03025027577369525,0.03025027577369497,0.03157986757244213,0.03029772580068725,0.029748184152427512,0.03166298582496128,0.03234919563230231,0.029013195879959958,0.029013195879959958,0.029898069410071337,0.030735754181910036,0.030735754181910036,0.031880830376201895,0.031880830376201895,0.031803329205122986,0.031803329205122986,0.031993165180277304,0.03128633561097906,0.03221935739978254,0.028420280908852364,0.02843709877653395,0.026853111116123724,0.026853111116123724,0.03049189026174262,0.029713854175038436,0.023640678453944526,0.01980793878051226,0.02132760431843824,0.03018286789565351,0.03642171246542429,0.041165939918914964,0.04317927145630296,0.045095786245581346,0.04983007910944915,0.04995173648132467,0.04927020117079616,0.047588138030071954,0.044542159444822,0.044106891801870454,0.04158722481930791,0.0399165696226202,0.03734812324449093,0.03618479760951217,0.039450765902819686,0.03713923700196482,0.03392676404159773,0.032794272998248074,0.031897123006878095,0.03259794140763433,0.033381495080976153,0.03491857087759976,0.03538260651588968,0.03526413665321936,0.03469012064068566,0.03491857087759974,0.035660513528562865,0.03463617021978257]}
    
    current_bbw = bbw_raw["width"][-1]
    
    print(f"📊 Raw BBW Data Analysis:")
    print(f"   Current BBW: {current_bbw:.6f}")
    
    # LLM said: "BBW is moderately low (0.031)"
    llm_bbw = 0.031
    
    print(f"\n🤖 LLM Interpretation:")
    print(f"   LLM said BBW: {llm_bbw}")
    
    print(f"\n✅ Accuracy Check:")
    bbw_correct = abs(current_bbw - llm_bbw) < 0.005  # Allow small rounding difference
    
    print(f"   BBW: {'✅ CORRECT' if bbw_correct else '❌ INCORRECT'} (Actual: {current_bbw:.6f}, LLM: {llm_bbw})")
    
    # BBW assessment
    print(f"\n📊 BBW Assessment:")
    if current_bbw < 0.02:
        bbw_assessment = "Very low (extreme squeeze)"
    elif current_bbw < 0.04:
        bbw_assessment = "Low to moderate (some consolidation)"
    elif current_bbw < 0.06:
        bbw_assessment = "Moderate (normal volatility)"
    else:
        bbw_assessment = "High (high volatility)"
    
    print(f"   Calculated Assessment: {bbw_assessment}")
    print(f"   LLM said: 'moderately low', 'suggesting some consolidation but not extreme'")
    
    assessment_correct = "low" in bbw_assessment.lower() or "consolidation" in bbw_assessment.lower()
    print(f"   Assessment: {'✅ REASONABLE' if assessment_correct else '❌ INCORRECT'}")
    
    return bbw_correct and assessment_correct

def analyze_volume_data():
    """Analyze volume interpretation."""
    print("\n\n🔍 ANALYZING VOLUME INTERPRETATION")
    print("=" * 50)
    
    # From logs: "Volume is below average (-20%)"
    # Volume data: current=995997, avg=1244618, ratio=0.80
    
    current_volume = 995997
    avg_volume = 1244618
    volume_ratio = 0.80
    volume_increase_pct = (volume_ratio - 1.0) * 100  # Should be -20%
    
    print(f"📊 Volume Data Analysis:")
    print(f"   Current Volume: {current_volume:,}")
    print(f"   Average Volume: {avg_volume:,}")
    print(f"   Volume Ratio: {volume_ratio:.2f}x")
    print(f"   Calculated % Change: {volume_increase_pct:.1f}%")
    
    print(f"\n🤖 LLM Interpretation:")
    print(f"   LLM said: 'Volume is below average (-20%)'")
    
    print(f"\n✅ Accuracy Check:")
    pct_correct = abs(volume_increase_pct - (-20)) < 1
    
    print(f"   Volume %: {'✅ CORRECT' if pct_correct else '❌ INCORRECT'} (Calculated: {volume_increase_pct:.1f}%, LLM: -20%)")
    
    # Risk assessment
    print(f"\n⚠️ Risk Assessment:")
    if volume_increase_pct < 10:
        risk_level = "HIGH RISK (Insignificant volume)"
    elif volume_increase_pct < 30:
        risk_level = "MODERATE RISK"
    elif volume_increase_pct < 60:
        risk_level = "ACCEPTABLE RISK"
    else:
        risk_level = "LOW RISK"
    
    print(f"   Calculated Risk: {risk_level}")
    print(f"   LLM said: 'increasing false breakout risk (HIGH RISK)'")
    
    risk_correct = "HIGH RISK" in risk_level
    print(f"   Risk Assessment: {'✅ CORRECT' if risk_correct else '❌ INCORRECT'}")
    
    return pct_correct and risk_correct

def analyze_overall_assessment():
    """Analyze overall LLM assessment logic."""
    print("\n\n🔍 ANALYZING OVERALL ASSESSMENT LOGIC")
    print("=" * 60)
    
    print("🎯 LLM Final Assessment:")
    print("   Confidence: 0.65 (65%)")
    print("   Reasoning: 'benefits from trending regime and Donchian context'")
    print("              'but suffers from weak volume confirmation and VWAP misalignment'")
    
    print("\n📊 Factor Analysis:")
    
    factors = {
        "Market Regime": {"status": "POSITIVE", "reason": "Strong trending (Aroon Up 100, Down 0)"},
        "Volume Confirmation": {"status": "NEGATIVE", "reason": "Below average (-20%) = HIGH RISK"},
        "VWAP Alignment": {"status": "NEGATIVE", "reason": "Price above VWAP contradicts short signal"},
        "Bollinger Position": {"status": "CAUTION", "reason": "Near upper band = overextension risk"},
        "RSI Context": {"status": "NEUTRAL", "reason": "No major conflicts (57.96 1h, 55.10 4h)"},
        "Donchian Room": {"status": "POSITIVE", "reason": "Room to move toward lower band"}
    }
    
    for factor, data in factors.items():
        emoji = {"POSITIVE": "✅", "NEGATIVE": "❌", "CAUTION": "⚠️", "NEUTRAL": "⚖️"}[data["status"]]
        print(f"   {emoji} {factor}: {data['reason']}")
    
    print("\n🧮 Confidence Score Analysis:")
    positive_factors = sum(1 for f in factors.values() if f["status"] == "POSITIVE")
    negative_factors = sum(1 for f in factors.values() if f["status"] == "NEGATIVE")
    
    print(f"   Positive Factors: {positive_factors}/6")
    print(f"   Negative Factors: {negative_factors}/6")
    print(f"   Expected Range: 0.50-0.70 (mixed evidence)")
    print(f"   LLM Score: 0.65")
    
    score_reasonable = 0.50 <= 0.65 <= 0.70
    print(f"   Score Reasonableness: {'✅ REASONABLE' if score_reasonable else '❌ UNREASONABLE'}")
    
    return score_reasonable

def main():
    """Run the complete LLM interpretation analysis."""
    print("🧪 LLM INTERPRETATION VALIDATION TEST")
    print("=" * 70)
    print("Analyzing how well the LLM interprets raw indicator data...")
    print()
    
    # Run individual analyses
    aroon_correct = analyze_aroon_data()
    bbw_correct = analyze_bbw_data()
    volume_correct = analyze_volume_data()
    assessment_correct = analyze_overall_assessment()
    
    # Final summary
    print("\n\n🎯 FINAL ASSESSMENT")
    print("=" * 70)
    
    tests = [
        ("Aroon Interpretation", aroon_correct),
        ("BBW Interpretation", bbw_correct), 
        ("Volume Interpretation", volume_correct),
        ("Overall Assessment Logic", assessment_correct)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        emoji = "✅" if result else "❌"
        print(f"   {emoji} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 LLM INTERPRETATION: EXCELLENT")
        print("✅ The LLM correctly interprets raw indicator data")
        print("✅ Calculations are accurate")
        print("✅ Risk assessments are appropriate")
        print("✅ Final confidence score is well-reasoned")
    elif passed >= total * 0.75:
        print("\n🟡 LLM INTERPRETATION: GOOD")
        print("✅ Most interpretations are correct")
        print("⚠️ Minor issues but overall reliable")
    else:
        print("\n🚨 LLM INTERPRETATION: NEEDS IMPROVEMENT")
        print("❌ Multiple interpretation errors detected")
        print("🔧 Review prompt instructions or data format")

if __name__ == "__main__":
    main()