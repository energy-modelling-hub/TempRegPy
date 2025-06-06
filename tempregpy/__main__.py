import logging
import colorlog
import typer

def get_console_handler():
    class SingleLetterFilter(logging.Filter):
        LEVEL_LETTERS = {
            'DEBUG': 'D',
            'INFO': 'I', 
            'WARNING': 'W',
            'ERROR': 'E',
            'CRITICAL': 'C'
        }
        
        def filter(self, record):
            record.levelname_short = self.LEVEL_LETTERS.get(record.levelname, 'U')
            return True
        
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(light_black)s[%(log_color)s%(levelname_short)s%(light_black)s]%(reset)s %(name)s: %(message_log_color)s%(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'light_green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'DEBUG': 'light_black',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        },
        style='%'
    )
    handler.setFormatter(formatter)
    handler.addFilter(SingleLetterFilter())
    return handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        get_console_handler(),
    ],
)

logger = logging.getLogger(__name__)
app = typer.Typer(
    help="Build and run the TempRegPy model according to a specific config excel file."
)

@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")

def main():
    app()
    
if __name__ == "__main__":
    app()