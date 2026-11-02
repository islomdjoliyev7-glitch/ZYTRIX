from rich.console import Console
from rich.panel import Panel

console = Console()

while True:
    console.print(Panel(
        "1. Salomlashish\n"
        "2. Kompyuter haqida\n"
        "3. Chiqish",
        title="Z Y T R I X"
    ))

    choice = input("Tanlang (1-3): ")

    if choice == "1":
        name = input("Ismingiz: ")
        console.print(f"Salom, {name}!", style="green")

    elif choice == "2":
        console.print("Operatsion tizim: Nobara Linux", style="yellow")

    elif choice == "3":
        print("Dastur tugadi!")
        break

    else:
        print("Noto'g'ri tanlov!")
