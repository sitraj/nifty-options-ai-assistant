# NIFTY Options AI Assistant

An AI-powered analysis tool designed to help beginners make more informed decisions when trading NIFTY 50 options by providing clear, educational signals and comprehensive risk warnings.

## 📋 Problem Statement

Options trading in the Indian market, particularly NIFTY 50 options, has become increasingly popular among retail traders. However, the complexity of options, combined with emotional decision-making and lack of proper risk management, leads to significant losses for beginners.

**The Challenge:**
- Beginners struggle to interpret complex option chain data
- Lack of understanding of key metrics (PCR, OI, IV, etc.)
- Emotional trading decisions without systematic analysis
- Insufficient risk management leading to large losses
- No clear guidance on when to trade vs. when to stay out

## 💸 Why Beginners Lose Money

Based on market research and trading psychology studies, beginners typically lose money due to:

1. **Lack of Systematic Analysis**: Trading on gut feeling or random tips without analyzing option chain data
2. **Poor Risk Management**: Not using stop-losses, trading too large positions, or holding losing trades too long
3. **Time Decay Ignorance**: Not understanding how time decay erodes option value, especially in weekly expiries
4. **Volatility Misunderstanding**: Trading during low IV periods or not understanding IV crush
5. **Far OTM Gambling**: Buying far out-of-the-money options with low probability of profit
6. **No Clear Entry/Exit Rules**: Entering and exiting trades without defined criteria
7. **Emotional Trading**: FOMO (Fear of Missing Out) and revenge trading after losses

## 🤖 How This AI Helps

This AI assistant addresses these problems by providing:

### 1. **Systematic Analysis**
- Automatically fetches and analyzes real-time NIFTY option chain data
- Calculates key metrics: PCR, OI build-up, support/resistance levels, ATM strikes
- Evaluates multiple technical indicators simultaneously

### 2. **Beginner-Friendly Signals**
- Clear market bias (Bullish/Bearish/Sideways/No-Trade)
- Confidence scores to indicate signal strength
- Simple trade recommendations (Call/Put/No Trade)
- Educational explanations in plain language

### 3. **Safety Layer**
- Blocks weekly expiry options (high time decay risk)
- Warns against far OTM options
- Alerts on low IV conditions
- Capital risk disclaimers

### 4. **Risk Assessment**
- Risk level classification (Low/Medium/High)
- Detailed "What Can Go Wrong" explanations
- Multiple warning categories (blocking, warning, info)

### 5. **Educational Approach**
- Explains WHY signals are generated
- Translates technical jargon into simple language
- Non-hype, calm tone to prevent emotional trading

## ⚠️ What This AI Does NOT Do

**Important Limitations:**

1. **❌ Does NOT Guarantee Profits**: This is an analysis tool, not a profit guarantee. Markets are unpredictable.

2. **❌ Does NOT Replace Learning**: You still need to understand options basics. This tool assists, not replaces education.

3. **❌ Does NOT Provide Financial Advice**: This is educational software. Consult a SEBI-registered advisor for financial advice.

4. **❌ Does NOT Account for All Market Conditions**: The analysis is based on option chain data only. News, events, and other factors are not considered.

5. **❌ Does NOT Manage Your Trades**: You are responsible for executing trades, setting stop-losses, and managing positions.

6. **❌ Does NOT Predict Future Prices**: The tool analyzes current market sentiment, not future price movements.

7. **❌ Does NOT Work for All Strategies**: Designed for beginner-friendly option buying. Not suitable for advanced strategies like spreads, straddles, etc.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface Layer                        │
├──────────────────────┬──────────────────────────────────────────┤
│   Streamlit UI       │          FastAPI REST API                │
│   (Web Interface)    │          (Programmatic Access)           │
└──────────┬───────────┴──────────────────┬──────────────────────┘
           │                                │
           └────────────┬───────────────────┘
                        │
        ┌───────────────▼───────────────────────┐
        │         Analysis Pipeline              │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────┴───────────────────────┐
        │                                         │
┌───────▼────────┐                    ┌───────────▼──────────┐
│  Data Layer   │                    │   Rules Engine      │
├───────────────┤                    ├─────────────────────┤
│ • NSE Fetcher │                    │ • Rule Evaluator    │
│ • Validator   │                    │ • Scoring Engine    │
│ • Converter   │                    │ • Safety Layer     │
│ • Features    │                    │ • Explainer        │
└───────┬───────┘                    └───────────┬────────┘
        │                                         │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────▼───────────────────────┐
        │      Output Generation                 │
        ├───────────────────────────────────────┤
        │ • Market Bias                          │
        │ • Trade Recommendation                 │
        │ • Confidence Score                     │
        │ • Risk Warnings                        │
        │ • Educational Explanations              │
        └───────────────────────────────────────┘
```

### Component Overview

- **Data Layer**: Fetches, validates, and processes NSE option chain data
- **Rules Engine**: Evaluates multiple technical rules and generates signals
- **Safety Layer**: Applies beginner-friendly safety checks
- **Explainer**: Converts technical signals into beginner-friendly language
- **UI Layer**: Provides web interface (Streamlit) and API (FastAPI)

## 🚀 Features

### Core Capabilities

- ✅ **Real-time Data Fetching**: Automatically fetches live NIFTY option chain data from NSE
- ✅ **Multi-Rule Analysis**: Evaluates PCR, OI build-up, Max OI strikes, Support/Resistance
- ✅ **Weighted Scoring**: Combines multiple signals with configurable weights
- ✅ **Safety Checks**: Blocks risky trades (weekly expiry, far OTM, low IV)
- ✅ **Risk Assessment**: Categorizes risk levels and explains potential downsides
- ✅ **Educational Explanations**: Translates technical analysis into simple language
- ✅ **Backtesting Engine**: Test strategies on historical data (one trade per day, fixed SL/Target)

### Output Metrics

- Market Bias (Bullish/Bearish/Sideways/No-Trade)
- Signal Score (-1.0 to +1.0)
- Confidence Score (0% to 100%)
- Risk Level (Low/Medium/High)
- Trade Recommendation (Call/Put/No Trade)
- Detailed Explanations (Why, What Can Go Wrong)
- Safety Warnings

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nifty-options-ai-assistant.git
   cd nifty-options-ai-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -c "from core.nse_option_chain import fetch_nifty_option_chain; print('Installation successful!')"
   ```

### Troubleshooting

**urllib3/OpenSSL Warning on macOS:**
If you see a warning about urllib3 and OpenSSL/LibreSSL compatibility:
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```

This is a harmless warning. The code automatically suppresses it, but if it persists:

1. Reinstall with pinned urllib3 version:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. Or manually install urllib3 v1.x:
   ```bash
   pip install "urllib3<2.0"
   ```

The warning doesn't affect functionality - it's just a compatibility notice.

**Streamlit Command Not Found:**
If you see `zsh: command not found: streamlit`, use the module syntax instead:
```bash
python3 -m streamlit run streamlit_app.py
```

To fix permanently, add Python's user bin directory to your PATH:
```bash
# Add to ~/.zshrc (for zsh) or ~/.bash_profile (for bash)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

**403 Forbidden Error from NSE:**
If you see `HTTP error 403: Forbidden`, this is due to NSE's anti-scraping measures. **You do NOT need to create an NSE account** - the data is publicly available.

**Common Causes:**
1. **Market is closed**: NSE is more restrictive outside trading hours
   - Trading hours: **9:15 AM - 3:30 PM IST, Monday to Friday**
   - If it's a weekend, holiday, or outside these hours, 403 errors are more common
2. **Rate limiting**: Too many requests from your IP address
3. **Anti-scraping detection**: NSE detected automated access patterns

**Solutions:**

1. **Try during market hours** (Most effective):
   - NSE trading hours: 9:15 AM - 3:30 PM IST, Monday-Friday
   - The API is most accessible during active trading

2. **Wait and retry**: 
   - If you got 403, wait 10-15 minutes before trying again
   - NSE may temporarily block rapid requests

3. **Check your network**: 
   - Ensure you're not behind a VPN or proxy that NSE blocks
   - Some corporate networks may be blocked

4. **Reduce request frequency**: 
   - Don't make too many requests in quick succession
   - The code includes retry logic with increasing delays

5. **If market is closed**: 
   - The API may still work but be more restrictive
   - Try during market hours for best results
   - Some data may not be available when markets are closed

**Note**: The code now visits the option chain web page first to establish a proper session, which helps reduce 403 errors.

## 🎯 Usage

### Streamlit Web Interface

Launch the user-friendly web interface:

```bash
# Method 1: Using python -m (recommended if 'streamlit' command not found)
python3 -m streamlit run streamlit_app.py

# Method 2: Direct command (if streamlit is in PATH)
streamlit run streamlit_app.py

# Method 3: Specify a custom port
python3 -m streamlit run streamlit_app.py --server.port 8502
```

The app will open at `http://localhost:8501` (default port)

**Note:** 
- If you get "command not found: streamlit", use Method 1 (`python3 -m streamlit`)
- Port 8501 is configured in `.streamlit/config.toml` - you can change it there or use `--server.port` flag
- If port 8501 is already in use, Streamlit will automatically try the next available port

**Features:**
- Live data fetching with one-click refresh
- Key metrics dashboard
- AI recommendations with explanations
- Risk warnings highlighted
- Professional, minimal design

### FastAPI REST API

Start the API server:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoint:**

```bash
POST /analyze/nifty-options
Content-Type: application/json

{
  "block_weekly_expiry": true
}
```

**Response:**
```json
{
  "bias": "Bullish",
  "score": 0.65,
  "score_category": "Strong Bullish",
  "recommendation": "Call",
  "confidence_score": 0.75,
  "risk_level": "Medium",
  "explanation": { ... },
  "warnings": [ ... ]
}
```

### Python Library Usage

```python
from core.nse_option_chain import fetch_nifty_option_chain
from core.validator import validate_nifty_option_chain
from core.converter import convert_to_dataframe
from core.features import calculate_features
from rules import evaluate, calculate_score, check_safety, explain

# Fetch and analyze
raw_data = fetch_nifty_option_chain()
validated_data = validate_nifty_option_chain(raw_data)
df = convert_to_dataframe(validated_data)
features = calculate_features(df, raw_data=validated_data)

# Evaluate rules
evaluation = evaluate(features)
score_result = calculate_score(evaluation.rule_results)
safety = check_safety(df, raw_data=validated_data, features=features)
explanation = explain(evaluation, score_result, safety)

# View results
print(f"Bias: {evaluation.market_bias}")
print(f"Recommendation: {evaluation.trade_recommendation}")
print(f"Risk Level: {evaluation.risk_level}")
print(f"Confidence: {evaluation.confidence_score:.1%}")
```

## 📁 Project Structure

```
nifty-options-ai-assistant/
├── core/                    # Core data processing modules
│   ├── nse_option_chain.py  # NSE data fetcher
│   ├── validator.py         # Data validation
│   ├── converter.py         # JSON to DataFrame converter
│   ├── features.py           # Feature engineering
│   └── backtest.py          # Backtesting engine
├── rules/                   # Rule engine and analysis
│   ├── engine.py            # Rule evaluator
│   ├── scoring.py           # Score calculation
│   ├── safety.py            # Safety checks
│   └── explainer.py         # Beginner-friendly explanations
├── app.py                   # FastAPI application
├── streamlit_app.py        # Streamlit web interface
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Rule Weights

Default weights can be customized in `rules/scoring.py`:

```python
DEFAULT_WEIGHTS = {
    "PCR Rule": 0.4,              # 40% weight
    "OI Build-up Rule": 0.2,      # 20% weight
    "Max OI Rule": 0.2,           # 20% weight
    "Support/Resistance Rule": 0.2,  # 20% weight
}
```

### Safety Thresholds

Safety parameters can be adjusted in `rules/safety.py`:

```python
_SAFETY_THRESHOLDS = {
    "weekly_expiry_days": 7,        # Block expiries within 7 days
    "far_otm_percentage": 5.0,     # Warn if >5% away from ATM
    "low_iv_threshold": 15.0,       # Warn if IV < 15%
    "very_low_iv_threshold": 10.0,  # Block if IV < 10%
}
```

## 📊 Backtesting

The backtesting engine allows you to test strategies on historical data:

```python
from core.backtest import run_backtest

result = run_backtest(
    daily_data=historical_data,
    initial_capital=100000.0,
    stop_loss=0.20,  # 20% stop loss
    target=0.50,     # 50% target
    quantity=1,
    max_open_trades=1,  # One trade per day
)

print(f"Win Rate: {result.win_rate:.2%}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Return: {result.total_return:.2%}")
```

## ⚠️ Risk Disclaimer

**IMPORTANT: READ THIS CAREFULLY**

1. **Not Financial Advice**: This software is for educational purposes only. It does not constitute financial, investment, or trading advice.

2. **No Guarantees**: Past performance does not guarantee future results. The AI analysis may be incorrect, and you may lose money.

3. **Options Trading Risk**: Options trading involves substantial risk of loss. You can lose your entire investment or more.

4. **No Liability**: The developers and contributors are not responsible for any financial losses incurred from using this software.

5. **Your Responsibility**: You are solely responsible for your trading decisions, risk management, and capital allocation.

6. **Market Risk**: Markets are unpredictable. Technical analysis has limitations and may not account for all market conditions.

7. **Data Accuracy**: While we strive for accuracy, data from NSE may have delays or errors.

8. **SEBI Compliance**: Ensure your trading activities comply with SEBI regulations. Consult a SEBI-registered investment advisor.

**By using this software, you acknowledge that you understand these risks and agree to use it at your own risk.**

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NSE (National Stock Exchange) for providing option chain data
- The open-source community for various Python libraries used in this project

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Remember**: This tool is designed to help you make more informed decisions, not to guarantee profits. Always trade responsibly, use proper risk management, and never invest more than you can afford to lose.

**Happy Trading! 📈 (But trade responsibly! ⚠️)**
