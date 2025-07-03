# volmon - Cryptocurrency Volatility Monitor

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Real-time cryptocurrency price volatility monitoring and alert system

volmon is a powerful tool that monitors real-time cryptocurrency prices on Binance exchange and sends instant Discord notifications when price movements exceed your specified threshold.

## Key Features

- Real-time cryptocurrency price monitoring (Binance WebSocket)
- 60-second volatility monitoring for rapid market movement detection
- Progressive alert thresholds: 0.3% (minimum), 0.5%, 1.0%, 2.0%, 3.0%, 5.0%
- Minute-by-minute alerts when volatility remains above 0.3%
- Instant Discord notifications for each threshold crossed
- Multiple coin monitoring simultaneously
- Intuitive console interface
- Smart auto-reconnect with exponential backoff for network issues

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Binance API key (optional, basic WebSocket works without it)
- Discord webhook URL (for receiving alerts)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Lacri1/volmon.git
   cd volmon
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

Create a `.env` file in the project root with the following variables:

```env
# Binance API Credentials (Required for private endpoints)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Discord Webhook Configuration (Required for notifications)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token
ALLOWED_WEBHOOK_IDS=your_webhook_id  # The numeric ID from your webhook URL

# Application Security (Required)
SECURITY_TOKEN=your_secure_random_token_here  # For API request validation
```

#### Environment Variables Description

| Variable | Required | Description |
|----------|----------|-------------|
| `BINANCE_API_KEY` | Optional* | Your Binance API key (required for private endpoints) |
| `BINANCE_API_SECRET` | Optional* | Your Binance API secret key (required for private endpoints) |
| `DISCORD_WEBHOOK_URL` | **Required** | Full Discord webhook URL for sending alerts |
| `ALLOWED_WEBHOOK_IDS` | **Required** | The webhook ID extracted from your Discord webhook URL |
| `SECURITY_TOKEN` | **Required** | Random token for API request validation |

> *Note: Binance API keys are optional for basic price monitoring but required if you need access to private endpoints.

### Configuration

You can configure the following in `volmon/config.py`:

- `SYMBOLS`: List of cryptocurrency pairs to monitor (default: `['btcusdt', 'ethusdt']`)
- `ALERT_THRESHOLD`: Volatility threshold for alerts in percentage (default: `0.3`)
- `TIME_WINDOW`: Time window in seconds for volatility calculation (default: `60`)
- `UPDATE_INTERVAL`: Console display refresh interval in seconds (default: `5`)

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
Alert threshold: 0.3% change within 60 seconds
==================================================

[VolMon] Starting monitoring: BTCUSDT
[VolMon] Starting monitoring: ETHUSDT

=== Cryptocurrency Price Monitor ===
Symbol      |      Price (USDT) | Last Updated
--------------------------------------------------
BTCUSDT   |      106,650.13 | 10:16:40
ETHUSDT   |        2,404.61 | 10:16:41

[BTCUSDT] Volatility detected! Change: +0.35% (Threshold: 0.3%)
[Notifier] Successfully sent alert to Discord
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
