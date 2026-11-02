import platform
import psutil
from rich.console import Console
from rich.panel import Panel

console = Console()


def system_info():
    cpu = platform.processor()

    if not cpu:
        with open("/proc/cpuinfo", encoding="utf-8") as file:
            for line in file:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break

    if not cpu:
        cpu = platform.machine()

    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    console.print(Panel(
        f"""
[cyan]Operatsion tizim:[/] {platform.system()}
[cyan]Versiya:[/] {platform.release()}
[cyan]Kompyuter:[/] {platform.node()}
[cyan]Protsessor:[/] {cpu}
[cyan]RAM:[/] {ram.total / (1024**3):.2f} GB
[cyan]RAM ishlatilgan:[/] {ram.percent:.1f}%
[cyan]Disk hajmi:[/] {disk.total / (1024**3):.2f} GB
[cyan]Disk band:[/] {disk.percent:.1f}%
        """,
        title="[bold green]ZYTRIX SYSTEM INFORMATION[/]"
    ))


def cpu_monitor():
    cpu = psutil.cpu_percent(interval=1)

    console.print(Panel(
        f"[bold cyan]CPU yuklanishi: {cpu:.1f}%[/]",
        title="ZYTRIX CPU MONITOR"
    ))


def battery_monitor():
    battery = psutil.sensors_battery()

    if battery is None:
        console.print("[yellow]Batareya ma'lumoti topilmadi![/]")
        return

    status = "Zaryad olmoqda" if battery.power_plugged else "Zaryad olmayapti"

    console.print(Panel(
        f"""
[cyan]Batareya:[/] {battery.percent:.1f}%
[cyan]Holati:[/] {status}
        """,
        title="ZYTRIX BATTERY MONITOR"
    ))


while True:
    console.print(Panel(
        "1. Kompyuter haqida\n"
        "2. RAM haqida\n"
        "3. CPU monitoring\n"
        "4. Batareya monitoring\n"
        "5. Chiqish",
        title="[bold green]ZYTRIX 1.1[/]"
    ))

    choice = input("Tanlang (1-5): ")

    if choice == "1":
        system_info()
    elif choice == "2":
        ram = psutil.virtual_memory()
        console.print(f"[cyan]RAM ishlatilgan:[/] {ram.percent:.1f}%")
    elif choice == "3":
        cpu_monitor()
    elif choice == "4":
        battery_monitor()
    elif choice == "5":
        console.print("[red]ZYTRIX yopildi![/]")
        break
    else:
        console.print("[red]Noto'g'ri tanlov![/]")
