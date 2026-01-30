# Highbit CNY Transfer Bot - Manual Test Checklist

## Pre-Deployment Setup

- [ ] `.env` file configured with all required variables
- [ ] `BOT_TOKEN` set correctly
- [ ] `ADMIN_IDS` includes admin user ID (5109426501)
- [ ] `ADMIN_CHAT_ID` set for transfer notifications
- [ ] `P2P_ARMY_API_KEY` set (optional, but recommended for P2P rates)
- [ ] `DATABASE_PATH` directory exists and is writable

## Bot Startup

- [ ] Bot starts without errors: `python main.py`
- [ ] Database initialized message appears in logs
- [ ] Bot commands are registered (check in Telegram)
- [ ] Scheduler starts (daily post at 10:00)

## User Commands

### /start and /help
- [ ] `/start` shows welcome message with bot description
- [ ] `/help` shows usage instructions
- [ ] Both commands work for non-admin users

### /rates
- [ ] `/rates` displays current exchange rates
- [ ] Rates include USDT/CNY from HTX P2P
- [ ] Rates include CBA official rates (AMD/USD/RUB)
- [ ] Rate caching works (subsequent calls are fast)

### /convert
- [ ] `/convert 1000 USD` converts correctly
- [ ] `/convert 5000 CNY` shows CNY conversion
- [ ] Invalid amounts show error message
- [ ] Invalid currency codes show error message

### /transfer (Main Flow)
- [ ] `/transfer` starts the transfer form
- [ ] **Step 1**: Enter CNY amount
  - [ ] Amounts < 5000 show minimum order error
  - [ ] Valid amounts (e.g., 10000) proceed to next step
  - [ ] Non-numeric input shows error
- [ ] **Step 2**: Select payment method
  - [ ] Alipay/WeChat/Bank Transfer options displayed
  - [ ] Selection proceeds to next step
- [ ] **Step 3**: Select payment currency
  - [ ] AMD/USD/RUB/USDT options displayed
  - [ ] Pricing calculated and shown with discount
  - [ ] Selection proceeds to next step
- [ ] **Step 4**: Add recipient details
  - [ ] Photo/QR upload accepted
  - [ ] Text message accepted
  - [ ] Can skip this step
- [ ] **Step 5**: Confirmation
  - [ ] Summary shows all details correctly
  - [ ] Discount tier shown correctly
  - [ ] Confirm creates request
  - [ ] Cancel aborts the process
- [ ] Admin notification sent to ADMIN_CHAT_ID

### /my_requests
- [ ] Shows user's transfer requests
- [ ] Status displayed correctly
- [ ] Empty state shown if no requests

## Admin Commands (Admin only)

### /requests
- [ ] Lists active transfer requests
- [ ] Shows request status and details
- [ ] Non-admin users get "Not authorized"

### /request <id>
- [ ] Shows detailed request info
- [ ] Shows attached files (QR codes)
- [ ] Status change buttons displayed
- [ ] Status flow:
  - [ ] NEW → ASSIGNED (Assign to me)
  - [ ] ASSIGNED → CONTACTED
  - [ ] CONTACTED → PAYMENT_RECEIVED
  - [ ] PAYMENT_RECEIVED → SENT
  - [ ] SENT → COMPLETED
- [ ] Cancel button works from any non-final state
- [ ] User notifications sent on status changes

### /stats
- [ ] Shows transfer statistics
- [ ] Total requests count
- [ ] Completed requests count
- [ ] Total CNY volume

### /kb (Knowledge Base)
- [ ] `/kb` shows KB menu (admin only)
- [ ] User texts accessible
- [ ] Operator texts accessible
- [ ] "Copy to forward" button works
- [ ] Quick commands: `/kb_intro`, `/kb_how`, `/kb_faq`

### /margin (Legacy)
- [ ] Margin adjustment works (if implemented)

## Pricing Logic

### Discount Tiers
- [ ] Orders < $4000 USD equivalent:
  - [ ] FIAT (AMD/USD/RUB): -1.5% discount
  - [ ] USDT: -1.0% discount
- [ ] Orders >= $4000 USD equivalent:
  - [ ] FIAT (AMD/USD/RUB): -1.0% discount
  - [ ] USDT: -0.5% discount

### Rate Sources
- [ ] P2P.Army API used when API key configured
- [ ] HTX P2P direct fallback works
- [ ] Binance fallback works
- [ ] Cached rate fallback works
- [ ] CBA rates fetched correctly

## Inline Query
- [ ] Inline query for conversions works
- [ ] Results display correctly

## Error Handling

- [ ] Network errors handled gracefully
- [ ] Invalid user input shows helpful errors
- [ ] Rate fetch failures use cached values
- [ ] Database errors logged appropriately

## Performance

- [ ] Rate caching reduces API calls
- [ ] Antiflood middleware prevents spam
- [ ] Memory usage stable over time

## Scheduled Tasks

- [ ] Daily rates post at 10:00 (configured timezone)
- [ ] Post appears in configured CHANNEL_ID

## Database

- [ ] Requests saved correctly
- [ ] Request files (QR codes) saved
- [ ] Status history tracked
- [ ] Stats queries work

## Cleanup

- [ ] Remove test data after testing
- [ ] Verify logs for any errors
- [ ] Check disk space for database growth

---

## Quick Test Sequence

1. Start bot: `systemctl restart currencybot`
2. Send `/start` - verify welcome
3. Send `/rates` - verify rates display
4. Send `/transfer` - test full flow with 5000 CNY
5. As admin: `/requests` - verify request appears
6. Update status through workflow
7. Verify user receives notifications
8. Send `/stats` - verify statistics

## Environment Variables Reference

```bash
# Required
BOT_TOKEN=your_bot_token
ADMIN_IDS=5109426501
ADMIN_CHAT_ID=your_admin_chat_id

# Optional but recommended
P2P_ARMY_API_KEY=your_api_key
CHANNEL_ID=your_channel_id

# Pricing (defaults shown)
MIN_ORDER_CNY=5000
DISCOUNT_THRESHOLD_USD=4000
DISCOUNT_FIAT_HIGH=-0.010
DISCOUNT_FIAT_LOW=-0.015
DISCOUNT_USDT_HIGH=-0.005
DISCOUNT_USDT_LOW=-0.010

# Caching (defaults shown)
HTX_P2P_TTL_SECONDS=45
CBA_RATES_TTL_SECONDS=900
RATE_TTL_SECONDS=600

# Network (defaults shown)
HTTP_TIMEOUT=8
HTTP_RETRIES=3

# Database
DATABASE_PATH=/opt/highbitbot/data/highbit.db
```
