# Highbit Exchange Rates Bot

A Telegram bot for currency exchange rates.

## Installation

### 1. Set up the bot directory

```bash
mkdir -p /opt/highbitbot
cd /opt/highbitbot
python3 -m venv .venv
```

### 2. Create environment file

```bash
cp .env.example /opt/highbitbot/.env
# Edit .env with your configuration
```

### 3. Install the systemd service

```bash
sudo cp currencybot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable currencybot.service
sudo systemctl start currencybot.service
```

### 4. Check service status

```bash
sudo systemctl status currencybot.service
journalctl -u currencybot.service -f
```

## Service Management

- Start: `sudo systemctl start currencybot.service`
- Stop: `sudo systemctl stop currencybot.service`
- Restart: `sudo systemctl restart currencybot.service`
- Status: `sudo systemctl status currencybot.service`
- Logs: `journalctl -u currencybot.service -f`
