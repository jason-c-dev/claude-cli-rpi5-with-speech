import asyncio
import pygame
from colorama import init
from dotenv import load_dotenv
from claude_cli import ClaudeCLI

if __name__ == "__main__":
    
    # Initialize colorama
    init(autoreset=True)


    # Initialize pygame mixer
    pygame.mixer.init()

    # Load environment variables
    load_dotenv()

    cli = ClaudeCLI()

    try:
        asyncio.run(cli.run())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cli.shutdown()