# 🛠️ 98kTools.py - Python Multitool for OSINT & Network Analysis
---
## ✨ Features

### 🌍 IP Lookup (`iplookup`)
Get detailed information about an IP address or domain:
- ISP
- Organization
- Country, city
- Geographic coordinates
- Proxy/VPN detection

### 📷 Image Metadata (`imgmeta`)
Extract EXIF metadata from an image:
- Camera model
- Shooting settings
- GPS coordinates (if present)

### 🕵️‍♂️ Image Tracker (`imgtracker`)
Starts a local Flask server that serves a transparent 1x1 pixel image. When viewed, it logs:
- Viewer’s IP address
- User-Agent

Useful for basic tracking via email or websites.

### 🔍 Port Scanner (`portscan`)
Scan an IP address or domain to identify ports that are:
- Open
- Closed
- Filtered

### 🌐 DNS Lookup (`dnslookup`)
Performs a DNS lookup for a domain name, showing the associated IP address (A record).

### 🎮 Roblox Lookup (`rblxlookup`)
Retrieve detailed information about a Roblox user:
- Username and ID
- Online status
- Last known location
- Recent games and badges

### 🌟 Roblox Celebrity Friends (`rblxceleb`)
Find a Roblox user's friends who are "celebrities" (verified badge or high follower count).

---

### 🔔 Roblox Tracker (`rblxtrack`)

Track a Roblox user's online status and send notifications to a **Discord webhook** when their status changes.

> ⚠️ **Note:** If the user's **"Join Game" setting is not public**, you will not be able to see which game they're playing. Roblox limits visibility of game data based on the user's privacy settings.

---

## ⚙️ Installation

Make sure you have **Python 3.8+** installed. Then install the required dependencies with:

```bash
pip install rich requests Pillow Flask
````

---

## ▶️ Usage

Run the tool with:

```bash
python 98kTools.py
```

Once started, you can interact with the command-line interface. Type `help` to see all available commands.

---

## 📝 Available Commands

| Command      | Description                                          |
| ------------ | ---------------------------------------------------- |
| `iplookup`   | Lookup IP address or domain                          |
| `imgmeta`    | Extract EXIF metadata from an image                  |
| `imgtracker` | Start tracking server with transparent image         |
| `portscan`   | Scan ports on a host                                 |
| `dnslookup`  | DNS query (A record)                                 |
| `rblxlookup` | Lookup a Roblox user                                 |
| `rblxceleb`  | Show celebrity friends of a Roblox user              |
| `rblxtrack`  | Monitor a Roblox user and send Discord notifications |
| `exit`       | Exit the program                                     |

---

## ⚠️ Notes on `imgtracker`

* The Flask server listens on **port 8080**
* The image is a **transparent 1x1 pixel**
* The script must **remain running** to log access events
* In production, consider using **Gunicorn** or similar WSGI server

---

## 👨‍💻 Credits

Developed by:

### 💻 GitHub

* [zeno98k](https://github.com/zeno98k)
* [VinoFFR](https://github.com/VinoFFR)

### 🎮 Discord

* [zeno.98k](https://discord.com/users/893215049282359337)
* [69vin](https://discord.com/users/767072748945539126)

---
