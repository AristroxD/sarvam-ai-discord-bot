# Sarvam AI Discord Bot

> **An intelligent, fun‑first Discord assistant powered by Sarvam AI and built with ❤️ by Team Thinkron**

---

## ✨ Features

| Category         | Highlights                                                                 |
| ---------------- | -------------------------------------------------------------------------- |
| **General**      | `!info`, `!help`, dynamic status updates, per‑guild AI chat channel memory |
| **Fun**          | `!flip`, `!roll`, `!joke`, mini games & auto‑reactions                     |
| **Study**        | `!quiz`, `!explain`, `!convert`, `!formula`, `!math`                       |
| **Dev Tools**    | `!codehelper`, `!notes`, `!compare`                                        |
| **Admin**        | `!setchannel`, `!unsetchannel`, `!setstatus`                               |

> ⚡  **Powered by Sarvam-M** – GPT‑style text generation with contextual memory.

---

## 🛠️  Quick Start

### 1. Clone & Install

```bash
# clone
git clone https://github.com/teamthinkron/sarvam-ai-discord-bot.git
cd sarvam-ai-discord-bot

# install deps (Python 3.11+)
pip install -r requirements.txt
```

### 2. Create `.env`

```env
DISCORD_TOKEN="your‑bot‑token"
SARVAM_API_KEY="your‑sarvam‑key"
COMMAND_PREFIX="!"           # optional, default "!"
ADMIN_USER_ID=123456789012345
```

### 3. Run it

```bash
python main.py
```

Bot will log to **bot.log** and announce itself in console.

---

## 🔑  Environment Variables

| Variable         | Description                                      |
| ---------------- | ------------------------------------------------ |
| `DISCORD_TOKEN`  | Your Discord bot token from the developer portal |
| `SARVAM_API_KEY` | API key for Sarvam AI                            |
| `COMMAND_PREFIX` | (optional) Command prefix, default `!`           |
| `ADMIN_USER_ID`  | (optional) Owner ID for privileged commands      |

---

## 📖 Command Reference

### General & Admin

| Command                         | Description                               |
| ------------------------------- | ----------------------------------------- |
| `!info`                         | Show bot, team & model info               |
| `!help`                         | Display categorized command list          |
| `!setchannel` / `!unsetchannel` | Enable/disable AI chat in current channel |
| `!setstatus <type> <text>`      | Change bot activity (admin only)          |

### Study & Learning

| Command                  | Action                            |
| ------------------------ | --------------------------------- |
| `!explain <concept>`     | Plain‑English explanation         |
| `!convert 5 km to miles` | Unit converter                    |
| `!formula <topic>`       | Key formulas list                 |
| `!math <expr>`           | Step‑by‑step solution             |
| `!notes <subject>`       | AI‑generated study notes          |

### Dev / Code

| Command              | Action                     |
| -------------------- | -------------------------- |
| `!codehelper <code>` | Explains code line by line |

---

## 🖥️  Folder Structure (simplified)

```
.
├── bot/
│   ├── discord_client.py   # core bot class
│   ├── chat_commands.py    # fun / misc
│   ├── study_commands.py   # study helpers
│   ├── study_productivity_commands.py
│   ├── memory.py           # per‑guild channel memory
│   └── ...
├── main.py                 # entry‐point
└── README.md
```

---

## 🚀  Deploying to Render / Railway

1. Add the repo.
2. Set env vars (`DISCORD_TOKEN`, `SARVAM_API_KEY` …).
3. Start command: `python main.py`.

> 💡 **Tip:** use `worker` type with auto‑restart for reliability.

---

## 🤝 Contributing

1. Fork ➜ Create branch ➜ Commit ➜ PR.
2. Run `ruff`, `black`, and `pytest` before pushing.
3. Be kind in code reviews 💜

---
host it on https://wispbyte.com/

## 📜 License

[MIT](LICENSE) © 2025 Team Thinkron
