# VolMon - Cryptocurrency Volatility Monitor

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Real-time cryptocurrency price volatility monitoring and alert system

VolMon is a powerful tool that monitors real-time cryptocurrency prices on Binance exchange and sends instant Discord notifications when price movements exceed your specified threshold.

## Key Features

- Real-time cryptocurrency price monitoring (Binance WebSocket)
- Customizable volatility threshold (default: 1%)
- Instant Discord notifications
- Multiple coin monitoring simultaneously
- Intuitive console interface

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Binance API key (optional, basic WebSocket works without it)
- Discord webhook URL (for receiving alerts)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Lacri1/VolMon.git
   cd VolMon
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
BINANCE_API_KEY=your_api_key_optional
BINANCE_API_SECRET=your_api_secret_optional
```

### Configuration

You can configure the following in `volmon/config.py`:

- `SYMBOLS`: List of cryptocurrency pairs to monitor (default: `['btcusdt', 'ethusdt']`)
- `ALERT_THRESHOLD`: Volatility threshold for alerts in percentage (default: `1.0`)
- `TIME_WINDOW`: Time window in seconds for volatility calculation (default: `60`)

### Running the Application

```bash
python main.py
```

## Usage Examples

```bash
# Run with default settings (monitors BTCUSDT, ETHUSDT)
python main.py

# Monitor specific coins (modify SYMBOLS in config.py)
# Or pass as command-line arguments (future implementation)
```

## Example Output

```
=== VolMon - Cryptocurrency Volatility Monitor ===
Monitoring 2 coins - BTCUSDT, ETHUSDT
Alert threshold: 1.0% change within 60 seconds
==================================================

[VolMon] Starting monitoring: BTCUSDT
[VolMon] Starting monitoring: ETHUSDT

=== Cryptocurrency Price Monitor ===
Symbol      |      Price (USDT) | Last Updated
--------------------------------------------------
BTCUSDT   |      106,650.13 | 10:16:40
ETHUSDT   |        2,404.61 | 10:16:41

[BTCUSDT] Volatility detected! Change: +1.23% (Threshold: 1.0%)
[Notifier] Successfully sent alert to Discord
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
