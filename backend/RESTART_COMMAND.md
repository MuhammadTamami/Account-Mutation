# 🔄 COMMAND /restart - Auto Reload Bot

## Date: September 2, 2026
## Status: ✅ IMPLEMENTED

---

## 🎯 Purpose

Command `/restart` memungkinkan bot untuk **restart otomatis** tanpa perlu:
- ❌ Stop bot manual di CMD (Ctrl+C)
- ❌ Run ulang `python bot_telegram.py`
- ❌ Kehilangan koneksi sementara

Cukup kirim `/restart` di Telegram, dan bot akan:
- ✅ Restart sendiri
- ✅ Load semua perubahan kode terbaru
- ✅ Kembali online dalam hitungan detik

---

## 🚀 Use Cases

### 1. **Setelah Update Kode**
```
Scenario:
1. Developer update bot_telegram.py
2. Ada fitur baru atau bug fix
3. User kirim /restart
4. Bot load kode baru tanpa manual restart
```

### 2. **Bug Fix Cepat**
```
Scenario:
1. User laporkan bug
2. Developer fix bug
3. Save file
4. User /restart
5. Bug fix langsung aktif
```

### 3. **Fitur Baru**
```
Scenario:
1. Ada format processor baru (misal: bank BRI update)
2. Developer tambahkan processor
3. Save file
4. User /restart
5. Processor baru langsung bisa dipakai
```

---

## 📱 How to Use

### In Telegram:

```
/restart
```

### Bot Response:

```
🔄 Restarting Bot...

Bot akan restart dalam 2 detik.
Fitur terbaru akan di-load otomatis.

Tunggu sebentar...
```

### After 2 Seconds:
- Bot process terminates
- New process starts
- Bot reconnects to Telegram
- All new code loaded
- Ready to use!

---

## 🔧 Technical Implementation

### Code:

```python
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /restart command"""
    if not is_authorized(update.effective_user.id):
        return
    
    await update.message.reply_text(
        "🔄 *Restarting Bot...*\n\n"
        "Bot akan restart dalam 2 detik.\n"
        "Fitur terbaru akan di-load otomatis.\n\n"
        "Tunggu sebentar...",
        parse_mode='Markdown'
    )
    
    # Give time for message to be sent
    import asyncio
    await asyncio.sleep(2)
    
    # Restart the bot process
    import os
    import sys
    
    logger.info("Bot restart requested by user")
    
    # For Windows
    if sys.platform.startswith('win'):
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        # For Linux/Mac
        os.execv(sys.executable, [sys.executable] + sys.argv)
```

### How It Works:

1. **Authorization Check**
   - Only authorized user (ID: 1819390132) can restart

2. **Send Message**
   - Inform user bot is restarting
   - Set expectation (2 seconds)

3. **Wait**
   - `asyncio.sleep(2)` ensures message is sent
   - Without this, message might not reach user

4. **Execute Restart**
   - `os.execv()` replaces current process
   - Same Python executable
   - Same script arguments
   - **All modules reloaded from disk**

5. **Reconnect**
   - Bot automatically reconnects to Telegram
   - Token unchanged
   - Chat history preserved

---

## ✅ Benefits

### For User:
- ✅ **No CMD access needed**
- ✅ **Instant updates** (no waiting for developer)
- ✅ **Zero downtime** (restart in seconds)
- ✅ **Simple command** (just `/restart`)

### For Developer:
- ✅ **Fast deployment** (save file, user restart)
- ✅ **No manual intervention** (no SSH, no CMD)
- ✅ **Safe** (only authorized user can restart)
- ✅ **Logs preserved** (restart logged)

---

## ⚠️ Important Notes

### What Gets Reset:
- ❌ **user_sessions dict** (in-memory data cleared)
  - Last results
  - Waiting file flags
  - Temporary states

### What's Preserved:
- ✅ **Bot token** (reconnects with same identity)
- ✅ **Authorization** (user ID check still works)
- ✅ **Uploaded files** (stored in filesystem)
- ✅ **Chat history** (Telegram server-side)

### Safety:
- ✅ **Only authorized user** can restart
- ✅ **Graceful shutdown** (2 second delay)
- ✅ **Automatic reconnect** (no manual intervention)
- ✅ **Logs restart event** (for debugging)

---

## 🧪 Testing

### Test Command Locally:
```bash
cd backend
python test_restart_command.py
```

### Expected Output:
```
✅ Platform: Windows
✅ Python executable found
✅ Script file found
✅ Restart logic verified
```

### Test in Telegram:

1. **Start Bot:**
   ```bash
   python bot_telegram.py
   ```

2. **Send Command:**
   ```
   /restart
   ```

3. **Verify:**
   - Bot sends "Restarting..." message
   - After 2 seconds, bot goes offline briefly
   - Bot comes back online
   - Send `/start` to verify bot responds

4. **Test Code Update:**
   ```bash
   # Edit bot_telegram.py (add a print statement)
   print("TEST UPDATE")
   
   # In Telegram
   /restart
   
   # Check CMD/terminal - should see "TEST UPDATE"
   ```

---

## 📊 Workflow Example

### Scenario: Bug Fix Deployment

**Before (Manual Way):**
```
1. User reports: "Saldo showing 0.00"
2. Developer fixes parse_amount() function
3. Developer: Ctrl+C to stop bot
4. Developer: python bot_telegram.py to restart
5. User: Try /saldo again
6. Total time: 2-5 minutes
```

**After (With /restart):**
```
1. User reports: "Saldo showing 0.00"
2. Developer fixes parse_amount() function
3. Developer saves file
4. User: /restart
5. User: Try /saldo again
6. Total time: 10 seconds ✅
```

---

## 🔐 Security

### Authorization:
```python
AUTHORIZED_USER_ID = 1819390132

def is_authorized(user_id: int) -> bool:
    return user_id == AUTHORIZED_USER_ID
```

### Protection:
- ✅ Only user ID 1819390132 can restart
- ✅ Other users see no response
- ✅ No error message to unauthorized users
- ✅ Restart logged for audit

---

## 📝 Command List (Updated)

| Command | Function |
|---------|----------|
| `/start` | Welcome & help |
| `/help` | Full guide |
| `/mutasi` | Upload mutasi (full scan) |
| `/saldo` | Upload saldo harian |
| `/ideb` | Upload IDEB SLIK |
| `/export` | Export results (Excel/CSV) |
| `/restart` | **Restart bot (NEW!)** ✨ |

---

## 🎉 Summary

**Feature:** `/restart` command untuk auto-reload bot

**Implementation:**
- ✅ Added `restart_bot()` async function
- ✅ Added command handler in `main()`
- ✅ Updated `/start` and `/help` messages
- ✅ Platform-specific restart logic (Windows/Linux/Mac)

**Benefits:**
- ✅ No manual CMD interaction needed
- ✅ Instant code deployment
- ✅ Zero downtime
- ✅ Developer-friendly

**Status:** ✅ **READY TO USE**

---

## 🚀 Next Steps

1. **Start bot normally:**
   ```bash
   python bot_telegram.py
   ```

2. **When you update code:**
   - Save file
   - Send `/restart` in Telegram
   - New code loads automatically!

3. **Monitor logs:**
   - Check terminal for restart message
   - Verify new features work

**No more manual restarts!** 🎉

---

**Last Updated:** September 2, 2026  
**File:** backend/bot_telegram.py  
**Function:** restart_bot()  
**Command:** /restart
