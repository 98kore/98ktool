from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
import requests
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
from flask import Flask, send_file, request
from datetime import datetime
import socket
import threading
import time
import json

# Changed WEBHOOKS_FILE to a relative path for compatibility in different environments
WEBHOOKS_FILE = "webhooks.json" 
console = Console()
app = Flask(__name__)

logo = """[bold medium_purple3]
 .----------------. .----------------. .----------------. 
| .--------------. | .--------------. | .--------------. |
| |    ______    | | |     ____     | | |  ___  ____   | |
| |  .' ____ '.  | | |   .' __ '.   | | | |_  ||_  _|  | |
| |  | (____) |  | | |   | (__) |   | | |   | |_/ /    | |
| |  '_.____. |  | | |   .`____'.   | | |   |  __'.    | |
| |  | \____| |  | | |  | (____) |  | | |  _| |  \ \_  | |
| |   \______,'  | | |  `.______.'  | | | |____||____| | |
| |              | | |              | | |              | |
| '--------------' | '--------------' | '--------------' |
 '----------------' '----------------' '----------------' 
                                    
[/bold medium_purple3]"""

def ip_lookup():
    ip = Prompt.ask("[bold cyan]Enter IP address or domain[/bold cyan]").strip()
    url = f"http://ip-api.com/json/{ip}?fields=66846719"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data["status"] != "success":
            console.print(f"[bold red]Error:[/bold red] {data.get('message', 'Invalid IP or domain')}")
            return

        table = Table(title=f"[bold magenta]IP Lookup Result for [white]{ip}[/white][/bold magenta]")

        def add(label, value):
            table.add_row(f"[bold violet]{label}[/bold violet]", str(value) if value else "[grey53]-[/grey53]")

        add("IP Address", data.get("query"))
        add("ISP", data.get("isp"))
        add("Organization", data.get("org"))
        add("ASN", data.get("as"))
        add("Country", data.get("country"))
        add("Region", data.get("regionName"))
        add("City", data.get("city"))
        add("ZIP Code", data.get("zip"))
        add("Latitude", data.get("lat"))
        add("Longitude", data.get("lon"))
        add("Time Zone", data.get("timezone"))
        add("Mobile Network", "✅" if data.get("mobile") else "❌")
        add("Proxy/VPN Detected", "✅" if data.get("proxy") else "❌")
        add("Hosting Provider", "✅" if data.get("hosting") else "❌")

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Network error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")

def convert_dms_to_degrees(value):
    d0, d1 = value[0]
    m0, m1 = value[1]
    s0, s1 = value[2]

    degrees = float(d0) / float(d1)
    minutes = float(m0) / float(m1)
    seconds = float(s0) / float(s1)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)

def imgmeta():
    path = Prompt.ask("[bold cyan]Enter image file path[/bold cyan]").strip()

    if not os.path.isfile(path):
        console.print("[bold red]File not found.[/bold red]")
        return

    try:
        image = Image.open(path)
        exif_data = image._getexif()

        if not exif_data:
            console.print("[bold yellow]No EXIF metadata found.[/bold yellow]")
            return

        console.print(Panel(f"[bold magenta]Metadati EXIF: {os.path.basename(path)}[/bold magenta]", expand=False))

        device_info_table = Table(title="[bold blue]Informazioni Dispositivo/Software[/bold blue]")
        device_info_table.add_column("[bold violet]Campo[/bold violet]")
        device_info_table.add_column("[bold violet]Valore[/bold violet]")

        image_properties_table = Table(title="[bold blue]Proprietà Immagine[/bold blue]")
        image_properties_table.add_column("[bold violet]Campo[/bold violet]")
        image_properties_table.add_column("[bold violet]Valore[/bold violet]")

        gps_info = {}
        
        device_specific_tags = {
            "Make": "Produttore Dispositivo",
            "Model": "Modello Dispositivo",
            "Software": "Software di Elaborazione"
        }

        image_specific_tags = {
            "DateTimeOriginal": "Data/Ora Originale",
            "FNumber": "Numero F",
            "ExposureTime": "Tempo di Esposizione",
            "ISOSpeedRatings": "ISO",
            "Flash": "Flash",
            "FocalLength": "Lunghezza Focale",
            "LensMake": "Produttore Lente",
            "LensModel": "Modello Lente",
            "Orientation": "Orientamento",
            "ImageWidth": "Larghezza Immagine",
            "ImageLength": "Altezza Immagine",
            "ResolutionUnit": "Unità Risoluzione",
            "XResolution": "Risoluzione X",
            "YResolution": "Risoluzione Y",
            "Artist": "Artista",
            "Copyright": "Copyright"
        }

        processed_tags = set()

        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)

            if tag == "GPSInfo":
                for gps_id in value:
                    gps_tag = GPSTAGS.get(gps_id, gps_id)
                    gps_info[gps_tag] = value[gps_id]
                processed_tags.add(tag)
                continue
            
            display_value = str(value)
            if tag == "FNumber" and isinstance(value, tuple) and len(value) == 2:
                display_value = f"f/{value[0]/value[1]:.1f}" if value[1] != 0 else str(value)
            elif tag == "ExposureTime" and isinstance(value, tuple) and len(value) == 2:
                display_value = f"1/{int(value[1]/value[0])}s" if value[0] != 0 else str(value)
            elif tag == "FocalLength" and isinstance(value, tuple) and len(value) == 2:
                display_value = f"{value[0]/value[1]:.1f} mm" if value[1] != 0 else str(value)

            if tag in device_specific_tags:
                device_info_table.add_row(f"[bold violet]{device_specific_tags[tag]}[/bold violet]", display_value)
                processed_tags.add(tag)
            elif tag in image_specific_tags:
                image_properties_table.add_row(f"[bold violet]{image_specific_tags[tag]}[/bold violet]", display_value)
                processed_tags.add(tag)
            
        console.print(device_info_table)
        console.print(image_properties_table)

        # Mostra i tag rimanenti non categorizzati
        other_tags_table = Table(title="[bold blue]Altri Metadati[/bold blue]")
        other_tags_table.add_column("[bold violet]Campo[/bold violet]")
        other_tags_table.add_column("[bold violet]Valore[/bold violet]")
        
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag not in processed_tags:
                other_tags_table.add_row(f"[bold violet]{tag}[/bold violet]", str(value))
        
        if other_tags_table.rows:
            console.print(other_tags_table)

        if gps_info:
            latitude = None
            longitude = None
            
            if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
                latitude = convert_dms_to_degrees(gps_info["GPSLatitude"])
                if gps_info["GPSLatitudeRef"] == "S":
                    latitude *= -1
            
            if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
                longitude = convert_dms_to_degrees(gps_info["GPSLongitude"])
                if gps_info["GPSLongitudeRef"] == "W":
                    longitude *= -1

            gps_table = Table(title="[bold blue]Informazioni GPS[/bold blue]")
            gps_table.add_column("[bold violet]Campo[/bold violet]")
            gps_table.add_column("[bold violet]Valore[/bold violet]")

            gps_table.add_row("[bold violet]GPS Latitudine[/bold violet]", f"{latitude:.6f}" if latitude is not None else "[grey53]-[/grey53]")
            gps_table.add_row("[bold violet]GPS Longitudine[/bold violet]", f"{longitude:.6f}" if longitude is not None else "[grey53]-[/grey53]")
            
            if latitude is not None and longitude is not None:
                google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                gps_table.add_row("[bold violet]Visualizza su Mappa[/bold violet]", f"[link={google_maps_link}]Google Maps[/link]")
            else:
                gps_table.add_row("[bold violet]Visualizza su Mappa[/bold violet]", "[grey53]Coordinate non disponibili[/grey53]")
            
            console.print(gps_table)

        console.print("\n[bold yellow]Attenzione:[/bold yellow] I metadati EXIF possono contenere informazioni sensibili come la posizione GPS, il modello della fotocamera e la data di scatto.")

    except Exception as e:
        console.print(f"[bold red]Errore nell'estrazione dei metadati:[/bold red] {e}")

def roblox_lookup():
    username = Prompt.ask("[bold cyan]Enter Roblox username[/bold cyan]").strip()

    try:
        r = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
            headers={"Content-Type": "application/json"}
        )
        data = r.json()
        if not data.get("data"):
            console.print("[bold red]User not found.[/bold red]")
            return
        user = data["data"][0]
        user_id = user["id"]

        profile = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=150&height=150&format=png"

        presence = requests.post(
            "https://presence.roblox.com/v1/presence/users",
            json={"userIds": [user_id]},
            headers={"Content-Type": "application/json"}
        ).json()

        p = presence.get("userPresences", [{}])[0]
        presence_type = p.get("userPresenceType", 0)
        last_location = p.get("lastLocation") or "N/A"

        presence_map = {
            0: ("🔴 Offline", "N/A"),
            1: ("🟠 Online sul sito", last_location),
            2: ("🟢 In gioco", last_location),
            3: ("🟣 In studio", last_location)
        }

        online_status, last_location = presence_map.get(presence_type, ("❓ Sconosciuto", "N/A"))

        place_name = join_link = "N/A"
        place_id = p.get("placeId")
        universe_id = p.get("universeId")

        # Debugging output for placeId and universeId
        if presence_type == 2:
            console.print(f"[bold yellow]Debug:[/bold yellow] User is 'In gioco'. Checking for placeId and universeId...")
            console.print(f"[bold yellow]Debug:[/bold yellow] Raw presence data for game: {p}")
            console.print(f"[bold yellow]Debug:[/bold yellow] placeId: {place_id}, universeId: {universe_id}")


        if presence_type == 2 and universe_id: # This condition is key
            try:
                game_data = requests.get(f"https://games.roblox.com/v1/games?universeIds={universe_id}").json()
                place_name = game_data.get("data", [{}])[0].get("name", "Sconosciuto")
                if place_name == "Sconosciuto": # If name is still unknown after API call
                     console.print(f"[bold yellow]Debug:[/bold yellow] Game name still 'Sconosciuto' after API call for universeId: {universe_id}. Raw game_data: {game_data}")

                if place_id:
                    join_link = f"https://www.roblox.com/games/{place_id}"
            except Exception as e:
                console.print(f"[bold red]Errore nel recupero gioco attuale:[/bold red] {e}")
        elif presence_type == 2 and not universe_id:
            console.print("[bold yellow]Attenzione:[/bold yellow] L'utente è 'In gioco', ma universeId non è disponibile dall'API di presenza.")


        badges = []
        if profile.get("hasVerifiedBadge"):
            badges.append("✅ Verificato")
        if profile.get("isBanned"):
            badges.append("⛔ Bannato")

        premium = requests.get(f"https://premiumfeatures.roblox.com/v1/users/{user_id}/ispremium").json()
        if premium.get("isPremium"):
            badges.append("💎 Premium")

        info = Table.grid()
        info.add_column(justify="right", style="bold medium_purple3")
        info.add_column()

        info.add_row("Username:", profile.get("name", "N/A"))
        info.add_row("Display Name:", profile.get("displayName", "N/A"))
        info.add_row("User ID:", str(user_id))
        info.add_row("Created:", profile.get("created", "N/A").replace("T", " ").split(".")[0])
        info.add_row("Description:", profile.get("description", "N/A") or "[italic grey53](Nessuna descrizione)[/italic grey53]")
        info.add_row("Online:", online_status)
        info.add_row("Last Location:", last_location)
        if presence_type == 2:
            info.add_row("Gioco:", place_name)
            info.add_row("Join:", f"[link={join_link}]{join_link}[/link]" if join_link != "N/A" else "N/A")
        info.add_row("Badges:", ", ".join(badges) if badges else "[grey53]Nessuno[/grey53]")

        recent_games = requests.get(f"https://games.roblox.com/v2/users/{user_id}/played-games?sortOrder=Desc&limit=5").json()
        games = recent_games.get("data", [])

        if games:
            game_names = "\n".join(f"• {g.get('name', 'Sconosciuto')}" for g in games)
            info.add_row("Recenti:", game_names)

        console.print(Panel.fit(info, title=f"[bold medium_purple3]Roblox User Lookup[/bold medium_purple3]", subtitle=f"[link={avatar_url}]Avatar[/link]"))

    except Exception as e:
        console.print(f"[bold red]Errore:[/bold red] {e}")

def rblxceleb():
    username = Prompt.ask("[bold cyan]Enter Roblox username[/bold cyan]").strip()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": False})
        data = r.json()
        if not data.get("data"):
            console.print("[bold red]User not found.[/bold red]")
            return
        user_id = data["data"][0]["id"]

        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends").json().get("data", [])

        celeb_friends = []
        for f in friends:
            fid = f.get("id")
            followers = requests.get(f"https://friends.roblox.com/v1/users/{fid}/followers/count").json().get("count", 0)
            if f.get("hasVerifiedBadge") or followers > 10000:
                celeb_friends.append({
                    "username": f["name"],
                    "displayName": f.get("displayName", f["name"]),
                    "followers": followers,
                    "verified": f.get("hasVerifiedBadge", False)
                })

        celeb_friends.sort(key=lambda x: x["followers"], reverse=True)

        if not celeb_friends:
            console.print("[bold yellow]Nessun amico celebrità trovato.[/bold yellow]")
            return

        table = Table(title="Amici Celebrità", show_lines=True)
        table.add_column("Username", style="bold")
        table.add_column("Display Name")
        table.add_column("Followers", justify="right")
        table.add_column("Verificato")

        for f in celeb_friends:
            table.add_row(f["username"], f["displayName"], str(f["followers"]), "✅" if f["verified"] else "")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Errore:[/bold red] {e}")



def port_scanner():
    target = Prompt.ask("[bold cyan]Enter target IP address or domain[/bold cyan]").strip()
    port_range_str = Prompt.ask("[bold cyan]Enter port range (e.g., 1-100 or 80,443)[/bold cyan]").strip()

    try:
        target_ip = socket.gethostbyname(target)
        console.print(f"[bold green]Scanning ports on {target} ({target_ip})...[/bold green]")
    except socket.gaierror:
        console.print(f"[bold red]Error:[/bold red] Could not resolve hostname: {target}")
        return

    ports_to_scan = []
    if '-' in port_range_str:
        start_port, end_port = map(int, port_range_str.split('-'))
        ports_to_scan = range(start_port, end_port + 1)
    else:
        ports_to_scan = [int(p.strip()) for p in port_range_str.split(',')]

    open_ports = []
    closed_ports = []
    filtered_ports = []

    def scan_port(ip, port, timeout=1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
            else:
                closed_ports.append(port)
        except socket.timeout:
            filtered_ports.append(port)
        except Exception as e:
            console.print(f"[bold yellow]Warning:[/bold yellow] Error scanning port {port}: {e}")
            filtered_ports.append(port)

    threads = []
    for port in ports_to_scan:
        thread = threading.Thread(target=scan_port, args=(target_ip, port,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    table = Table(title=f"[bold magenta]Port Scan Results for {target}[/bold magenta]")
    table.add_column("[bold violet]Port[/bold violet]")
    table.add_column("[bold violet]Status[/bold violet]")

    open_ports.sort()
    closed_ports.sort()
    filtered_ports.sort()

    for port in open_ports:
        table.add_row(str(port), "[bold green]Open[/bold green]")
    for port in closed_ports:
        table.add_row(str(port), "[red]Closed[/red]")
    for port in filtered_ports:
        table.add_row(str(port), "[yellow]Filtered[/yellow]")

    if not open_ports and not closed_ports and not filtered_ports:
        console.print("[bold yellow]No ports scanned or no results found.[/bold yellow]")
    else:
        console.print(table)
        console.print(f"\n[bold green]Summary:[/bold green] Open: {len(open_ports)}, Closed: {len(closed_ports)}, Filtered: {len(filtered_ports)}")


def dns_lookup():
    domain = Prompt.ask("[bold cyan]Enter domain name[/bold cyan]").strip()

    table = Table(title=f"[bold magenta]DNS Lookup Results for {domain}[/bold magenta]")
    table.add_column("[bold violet]Record Type[/bold violet]")
    table.add_column("[bold violet]Valore[/bold violet]")

    try:
        ip_address = socket.gethostbyname(domain)
        table.add_row("[bold green]A Record (IPv4)[/bold green]", ip_address)
    except socket.gaierror:
        table.add_row("[bold red]A Record (IPv4)[/bold red]", "[grey53]Non Trovato / Errore[/grey53]")
    except Exception as e:
        table.add_row("[bold red]A Record (IPv4)[/bold red]", f"[grey53]Errore: {e}[/grey53]")

    console.print(table)


def main():
    console.clear()
    console.print(logo)
    
    while True:
        try:
            cmd = Prompt.ask("[bold medium_purple3]>>>[/bold medium_purple3]", default="help")

            if cmd.lower() == "exit":
                console.print("\n[bold red]Exiting... Goodbye.[/bold red]")
                break
            elif cmd.lower() == "help":
                console.print("""
[bold violet]Available Commands:[/bold violet]
- help        : display this help message
- exit        : exit the multitool
- iplookup    : perform IP/domain geolocation and VPN/proxy detection
- imgmeta     : extract technical EXIF metadata from image files
- imgtracker  : start image tracking server (port 8080)
- portscan    : scan a target IP/domain for open ports
- dnslookup   : perform DNS lookups for a domain
- creators    : show GitHub & Discord links of the authors
- robloxlookup : mostra informazioni dettagliate su un utente Roblo
- rblxceleb : looks up celeb connection
- rblxtrack : tracks Roblox user status and sends webhooks
""")
            elif cmd.lower() == "iplookup":
                ip_lookup()
            elif cmd.lower() == "rblxtrack":
                rblxtrack()
            elif cmd.lower() == "imgmeta":
                imgmeta()
            elif cmd.lower() == "imgtracker":
                console.print("[bold cyan]Starting Flask tracking server on [bold green]http://localhost:8080/track.png[/bold green][/bold cyan]")
                console.print("[bold yellow]Share this link or embed the image to track access (server must remain running).[/bold yellow]")
                # Note: os.system("start cmd /k python -m flask run --host=0.0.0.0 --port=8080") will not work in this environment.
                # The Flask app needs to be run directly or handled by the environment's specific Flask execution method.
                # For this interactive environment, the Flask app will be run via the __name__ == '__main__' block.
                # You would typically run this in a separate terminal for persistent tracking.
                console.print("[bold yellow]To run the Flask server, execute this script directly and ensure the `if __name__ == '__main__':` block handles Flask.[/bold yellow]")
            elif cmd.lower() == "portscan":
                port_scanner()
            elif cmd.lower() == "dnslookup":
                dns_lookup()
            elif cmd.lower() == "rblxlookup":
                roblox_lookup()
            elif cmd.lower() == "rblxceleb":
                rblxceleb()

            elif cmd.lower() == "creators":
                console.print("""
[bold magenta]👥 Creators:[/bold magenta]

[bold cyan]💻 GitHub:[/bold cyan]
- [link=https://github.com/zeno98k]zeno98k[/link]
- [link=https://github.com/VinoFFR]VinoFFR[/link]

[bold cyan]🎮 Discord:[/bold cyan]
- [link=https://discord.com/users/893215049282359337]zeno.98k[/link]
- [link=https://discord.com/users/767072748945539126]69vin[/link]
""")
                
            else:
                console.print("[bold red]Unknown command. Type 'help' for a list of valid commands.[/bold red]")

        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted by user. Shutting down...[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred in main loop:[/bold red] {e}")
            
def load_webhooks():
    if os.path.exists(WEBHOOKS_FILE):
        try:
            with open(WEBHOOKS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(f"[bold yellow]Warning:[/bold yellow] {WEBHOOKS_FILE} is empty or contains invalid JSON. Starting with empty webhooks.")
            return {}
    return {}

def save_webhooks(data):
    with open(WEBHOOKS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def send_webhook(webhook_url, embed):
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
    except Exception as e:
        console.print(f"[red]Errore nell'invio del webhook:[/red] {e}")

def rblxtrack():
    username = Prompt.ask("[bold cyan]Enter Roblox username to track[/bold cyan]").strip()
    webhooks = load_webhooks()

    console.print("[bold medium_purple3]Webhook disponibili:[/bold medium_purple3]")
    if not webhooks:
        console.print("[grey53]Nessun webhook salvato. Aggiungine uno nuovo.[/grey53]")
    else:
        for i, key in enumerate(webhooks, 1):
            console.print(f"{i}. {key}: {webhooks[key][:60]}...")

    choice = Prompt.ask("[bold cyan]Usa quale webhook? (numero o 'new')[/bold cyan]")
    if choice.lower() == "new":
        name = Prompt.ask("[bold cyan]Nome per questo webhook[/bold cyan]")
        url = Prompt.ask("[bold cyan]Inserisci URL webhook Discord[/bold cyan]")
        webhooks[name] = url
        save_webhooks(webhooks)
        webhook_url = url
    else:
        try:
            index = int(choice) - 1
            webhook_url = list(webhooks.values())[index]
        except (ValueError, IndexError):
            console.print("[red]Scelta non valida.[/red]")
            return

    r = requests.post(
        "https://users.roblox.com/v1/usernames/users",
        json={"usernames": [username], "excludeBannedUsers": False},
        headers={"Content-Type": "application/json"}
    )
    data = r.json()
    if not data.get("data"):
        console.print("[red]Utente non trovato.[/red]")
        return

    user = data["data"][0]
    user_id = user["id"]
    console.print(f"[green]Tracking {username} (ID: {user_id}) ogni 30 secondi... Premi CTRL+C per fermare.[/green]")

    # Inizializza lo stato precedente del gioco (0: Offline, 1: Online sul sito, 2: In gioco, 3: In studio)
    # Vogliamo tracciare i cambiamenti da/verso lo stato "In gioco" (2)
    last_presence_type = -1 # Usa un valore che non corrisponde a nessuno stato iniziale valido
    last_game_id = None # Per tracciare il cambio di gioco

    # Using a separate thread for tracking to not block the main console
    def tracking_thread():
        nonlocal last_presence_type, last_game_id # Allows modification of these variables
        while True:
            try:
                presence = requests.post(
                    "https://presence.roblox.com/v1/presence/users",
                    json={"userIds": [user_id]},
                    headers={"Content-Type": "application/json"}
                ).json().get("userPresences", [{}])[0]

                profile = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()

                current_presence_type = presence.get("userPresenceType", 0)
                location = presence.get("lastLocation", "N/A")

                presence_map = {
                    0: ("🔴 Offline", "N/A"),
                    1: ("🟠 Online sul sito", location),
                    2: ("🟢 In gioco", location),
                    3: ("🟣 In studio", location)
                }

                status_text, location = presence_map.get(current_presence_type, ("❓ Sconosciuto", "N/A"))

                game = "N/A"
                join_link = "N/A"
                universe_id = presence.get("universeId")
                place_id = presence.get("placeId")
                
                # Debugging output for placeId and universeId in tracking thread
                if current_presence_type == 2:
                    console.print(f"[bold yellow]Debug (Tracking):[/bold yellow] User is 'In gioco'. Checking for placeId and universeId...")
                    console.print(f"[bold yellow]Debug (Tracking):[/bold yellow] Raw presence data for game: {presence}")
                    console.print(f"[bold yellow]Debug (Tracking):[/bold yellow] placeId: {place_id}, universeId: {universe_id}")

                current_game_id = None # Initialize current_game_id

                if current_presence_type == 2 and universe_id:
                    try:
                        game_info = requests.get(f"https://games.roblox.com/v1/games?universeIds={universe_id}").json()
                        game = game_info.get("data", [{}])[0].get("name", "Sconosciuto")
                        current_game_id = universe_id # Use universe_id as the game identifier for tracking changes
                        if place_id:
                            join_link = f"https://www.roblox.com/games/{place_id}"
                        if game == "Sconosciuto":
                            console.print(f"[bold yellow]Debug (Tracking):[/bold yellow] Game name still 'Sconosciuto' after API call for universeId: {universe_id}. Raw game_info: {game_info}")
                    except Exception as e:
                        console.print(f"[red]Errore nel recupero gioco attuale durante il tracking:[/red] {e}")
                elif current_presence_type == 2 and not universe_id:
                    console.print("[bold yellow]Attenzione (Tracking):[/bold yellow] L'utente è 'In gioco', ma universeId non è disponibile dall'API di presenza.")


                description = profile.get("description", "")
                if not description:
                    description = "(nessuna descrizione)" # Removed rich text for embed description

                embed = {
                    "title": f"{profile.get('displayName')} ({username})",
                    "description": f"**Online:** {status_text}\n**Luogo:** {location}\n**Gioco:** {game}",
                    "fields": [],
                    "footer": {"text": f"UserID: {user_id}"},
                    "timestamp": datetime.utcnow().isoformat(),
                    "thumbnail": {"url": f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=150&height=150&format=png"},
                    "color": 0x9370DB
                }

                if join_link != "N/A":
                    embed["fields"].append({"name": "Join", "value": join_link, "inline": False})

                # Logica per inviare il webhook solo quando l'utente entra/esce da un gioco o cambia gioco
                should_send_webhook = False
                
                # Caso 1: L'utente era offline/online sul sito e ora è in gioco
                if last_presence_type != 2 and current_presence_type == 2:
                    should_send_webhook = True
                    embed["description"] = f"**{profile.get('displayName')} è entrato in gioco!**\n**Gioco:** {game}\n**Luogo:** {location}"
                    embed["color"] = 0x00FF00 # Verde per "entrato"
                # Caso 2: L'utente era in gioco e ora è offline/online sul sito/in studio
                elif last_presence_type == 2 and current_presence_type != 2:
                    should_send_webhook = True
                    embed["description"] = f"**{profile.get('displayName')} è uscito dal gioco!**\n**Stato attuale:** {status_text}\n**Luogo:** {location}"
                    embed["color"] = 0xFF0000 # Rosso per "uscito"
                # Caso 3: L'utente era in gioco e ha cambiato gioco
                elif last_presence_type == 2 and current_presence_type == 2 and last_game_id != current_game_id:
                    should_send_webhook = True
                    embed["description"] = f"**{profile.get('displayName')} ha cambiato gioco!**\n**Nuovo Gioco:** {game}\n**Luogo:** {location}"
                    embed["color"] = 0xFFA500 # Arancione per "cambio gioco"

                if should_send_webhook:
                    send_webhook(webhook_url, embed)
                    console.print(f"[green]Webhook inviato: Stato gioco cambiato per {profile.get('displayName')} a {status_text}[/green]")
                else:
                    console.print(f"[grey53]Stato invariato per {profile.get('displayName')}: {status_text}. Prossimo controllo in 30 secondi.[/grey53]")

                last_presence_type = current_presence_type # Aggiorna lo stato precedente
                last_game_id = current_game_id # Aggiorna l'ID del gioco precedente

            except Exception as e:
                console.print(f"[red]Errore durante il tracking:[/red] {e}")

            time.sleep(5) # Controlla ogni 30 secondi

    # Start the tracking in a new thread
    tracker_thread = threading.Thread(target=tracking_thread)
    tracker_thread.daemon = True # Allow the main program to exit even if this thread is running
    tracker_thread.start()


@app.route('/track.png')
def track():    
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Renamed variable to avoid conflict with time module

    print(f"[{time_now}] 📥 Image opened!")
    print(f"IP: {ip}")
    print(f"User-Agent: {user_agent}")
    print("-" * 40)

    # Ensure track.png exists or create it
    if not os.path.exists("track.png"):
        try:
            from PIL import Image
            img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            img.save("track.png", "PNG")
        except Exception as e:
            print(f"Error creating track.png: {e}")
            from flask import Response
            return Response("Error: Could not create tracking image.", status=500, mimetype='text/plain')

    return send_file("track.png", mimetype='image/png')

if __name__ == '__main__':
    # This block determines whether to run the Flask app or the main console app.
    # In a typical local environment, you'd run one or the other.
    # For this sandbox, the Flask part might not be directly runnable as a web server
    # unless the environment specifically supports it.
    # The `request` object is only available within a Flask request context.
    # The `FLASK_APP` environment variable is checked to see if Flask is intended to run.
    if os.environ.get("FLASK_APP") == "app.py" or (request and "track.png" in request.path):
        app.run(host='0.0.0.0', port=8080)
    else:
        main()