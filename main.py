import platform
import time
from datetime import timedelta

import psutil
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
VERSION = "2.0"
GB = 1024**3


# ---------- Yordamchi funksiyalar ----------

def color_for(percent, reverse=False):
    """Foizga qarab rang tanlaydi. reverse=True: kam foiz yomon (batareya)."""
    if reverse:
        percent = 100 - percent
    if percent < 60:
        return "green"
    if percent < 85:
        return "yellow"
    return "red"


def bar(percent, width=30, reverse=False):
    """Rangli progress bar yasaydi."""
    filled = int(percent / 100 * width)
    color = color_for(percent, reverse)
    return (
        f"[{color}]{'█' * filled}[/]"
        f"[dim]{'░' * (width - filled)}[/] "
        f"[{color}]{percent:.1f}%[/]"
    )


def format_bytes(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(seconds):
    delta = timedelta(seconds=int(seconds))
    hours, rest = divmod(delta.seconds, 3600)
    minutes = rest // 60
    parts = []
    if delta.days:
        parts.append(f"{delta.days} kun")
    parts.append(f"{hours} soat")
    parts.append(f"{minutes} daqiqa")
    return " ".join(parts)


def get_cpu_name():
    cpu = platform.processor()

    if not cpu:
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as file:
                for line in file:
                    if line.startswith("model name"):
                        cpu = line.split(":", 1)[1].strip()
                        break
        except OSError:
            pass

    return cpu or platform.machine()


def get_temperature():
    """CPU haroratini qaytaradi, topilmasa None."""
    try:
        temps = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None

    for name in ("k10temp", "coretemp", "acpitz"):
        if temps.get(name):
            return temps[name][0].current

    for entries in temps.values():
        if entries:
            return entries[0].current
    return None


# ---------- Panellar (qayta ishlatiladi) ----------

def info_panel():
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = time.time() - psutil.boot_time()
    temp = get_temperature()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()

    table.add_row("Operatsion tizim:", f"{platform.system()} {platform.release()}")
    table.add_row("Kompyuter:", platform.node())
    table.add_row("Protsessor:", get_cpu_name())
    table.add_row(
        "Yadrolar:",
        f"{psutil.cpu_count(logical=False)} fizik / {psutil.cpu_count()} mantiqiy",
    )
    if temp is not None:
        table.add_row("Harorat:", f"[{color_for(temp)}]{temp:.0f} °C[/]")
    table.add_row("Ishlash vaqti:", format_duration(uptime))
    table.add_row("", "")
    table.add_row("RAM:", f"{ram.total / GB:.2f} GB")
    table.add_row("", bar(ram.percent))
    table.add_row("Disk:", f"{disk.total / GB:.2f} GB")
    table.add_row("", bar(disk.percent))

    return Panel(table, title="[bold green]ZYTRIX SYSTEM INFORMATION[/]")


def ram_panel():
    ram = psutil.virtual_memory()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()
    table.add_row("Ishlatilgan:", f"{ram.used / GB:.2f} GB / {ram.total / GB:.2f} GB")
    table.add_row("Mavjud:", f"{ram.available / GB:.2f} GB")
    table.add_row("", bar(ram.percent))

    return Panel(table, title="[bold green]ZYTRIX RAM MONITOR[/]")


def cpu_panel(cores):
    total = sum(cores) / len(cores)

    lines = [f"[cyan]Umumiy:[/]\n{bar(total)}\n"]
    for i, value in enumerate(cores, start=1):
        lines.append(f"[cyan]Yadro {i:>2}:[/] {bar(value, 20)}")

    return Panel("\n".join(lines), title="[bold green]ZYTRIX CPU MONITOR[/]")


def battery_panel():
    battery = psutil.sensors_battery()

    if battery is None:
        return Panel("[yellow]Batareya ma'lumoti topilmadi![/]",
                     title="[bold green]ZYTRIX BATTERY MONITOR[/]")

    status = "Zaryad olmoqda ⚡" if battery.power_plugged else "Zaryad olmayapti"

    lines = [
        f"[cyan]Batareya:[/]\n{bar(battery.percent, reverse=True)}",
        f"[cyan]Holati:[/] {status}",
    ]

    if not battery.power_plugged and battery.secsleft > 0:
        lines.append(f"[cyan]Qolgan vaqt:[/] {format_duration(battery.secsleft)}")

    return Panel("\n".join(lines), title="[bold green]ZYTRIX BATTERY MONITOR[/]")


def network_panel(down, up):
    counters = psutil.net_io_counters()

    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()
    table.add_row("Yuklab olish:", f"[green]↓ {format_bytes(down)}/s[/]")
    table.add_row("Yuborish:", f"[yellow]↑ {format_bytes(up)}/s[/]")
    table.add_row("Jami olingan:", format_bytes(counters.bytes_recv))
    table.add_row("Jami yuborilgan:", format_bytes(counters.bytes_sent))

    return Panel(table, title="[bold green]ZYTRIX NETWORK MONITOR[/]")


def process_panel(limit=8):
    procs = []
    for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
        info = proc.info
        info["memory_percent"] = info["memory_percent"] or 0
        info["name"] = info["name"] or "?"
        procs.append(info)

    procs.sort(key=lambda p: p["memory_percent"], reverse=True)

    table = Table(header_style="bold cyan")
    table.add_column("PID", justify="right")
    table.add_column("Nomi")
    table.add_column("RAM", justify="right")

    for p in procs[:limit]:
        percent = p["memory_percent"]
        table.add_row(
            str(p["pid"]),
            p["name"],
            f"[{color_for(percent * 5)}]{percent:.1f}%[/]",
        )

    return Panel(table, title="[bold green]ZYTRIX TOP PROCESSES (RAM)[/]")


# ---------- Menyu amallari ----------

def system_info():
    console.print(info_panel())


def ram_monitor():
    console.print(ram_panel())


def cpu_monitor():
    console.print(cpu_panel(psutil.cpu_percent(interval=1, percpu=True)))


def battery_monitor():
    console.print(battery_panel())


def network_monitor():
    before = psutil.net_io_counters()
    time.sleep(1)
    after = psutil.net_io_counters()
    console.print(network_panel(
        after.bytes_recv - before.bytes_recv,
        after.bytes_sent - before.bytes_sent,
    ))


def process_monitor():
    console.print(process_panel())


def dashboard():
    """Jonli panel. Ctrl+C bilan menyuga qaytadi."""
    psutil.cpu_percent(percpu=True)  # birinchi o'lchovni "isitish"
    last = psutil.net_io_counters()
    last_time = time.time()

    try:
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)

                now = psutil.net_io_counters()
                now_time = time.time()
                dt = now_time - last_time
                down = (now.bytes_recv - last.bytes_recv) / dt
                up = (now.bytes_sent - last.bytes_sent) / dt
                last, last_time = now, now_time

                live.update(Group(
                    cpu_panel(psutil.cpu_percent(percpu=True)),
                    ram_panel(),
                    battery_panel(),
                    network_panel(down, up),
                    Text("Chiqish uchun Ctrl + C", style="dim"),
                ))
    except KeyboardInterrupt:
        pass


MENU = {
    "1": ("Kompyuter haqida", system_info),
    "2": ("RAM monitoring", ram_monitor),
    "3": ("CPU monitoring", cpu_monitor),
    "4": ("Batareya monitoring", battery_monitor),
    "5": ("Internet monitoring", network_monitor),
    "6": ("Top jarayonlar", process_monitor),
    "7": ("Live dashboard", dashboard),
}
EXIT_KEY = str(len(MENU) + 1)


def show_menu():
    items = [f"{key}. {name}" for key, (name, _) in MENU.items()]
    items.append(f"{EXIT_KEY}. Chiqish")

    console.print(Panel(
        "\n".join(items),
        title=f"[bold green]ZYTRIX {VERSION}[/]"
    ))


def main():
    while True:
        show_menu()

        try:
            choice = input(f"Tanlang (1-{EXIT_KEY}): ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]ZYTRIX yopildi![/]")
            break

        if choice == EXIT_KEY:
            console.print("[red]ZYTRIX yopildi![/]")
            break

        if choice in MENU:
            MENU[choice][1]()
        else:
            console.print("[red]Noto'g'ri tanlov![/]")


if __name__ == "__main__":
    main()
