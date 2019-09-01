class c:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BLACK = '\033]90m'
    WHITE = '\033[97m'

    END = '\033[0m'

def red(msg):
    print(c.RED + msg + c.END)

def yellow(msg):
    print(c.YELLOW + msg + c.END)

def green(msg):
    print(c.GREEN + msg + c.END)

def cyan(msg):
    print(c.CYAN + msg + c.END)

def blue(msg):
    print(c.BLUE + msg + c.END)

def magenta(msg):
    print(c.MAGENTA + msg + c.END)

def black(msg):
    print(c.BLACK + msg + c.END)

def white(msg):
    print(c.WHITE + msg + c.END)

def test():
    red(   ".------. | RED")
    yellow("|C.--. | | YELLOW")
    green( "| :/\\: | | GREEN")
    cyan(  "| :\\/: | | CYAN")
    blue(  "| '--'C| | BLUE")
    magenta( "`------' | WHITE")