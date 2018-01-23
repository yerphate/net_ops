import socket
import getpass
import sys
import time
import colorama
import signal
import os


from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

os.system("cls")

print(Fore.WHITE + Style.BRIGHT + "       __            _                ")
print(Fore.WHITE + Style.BRIGHT + "      / /_  ______  (_)___  ___  _____")
print(Fore.WHITE + Style.BRIGHT + " __  / / / / / __ \/ / __ \/ _ \/ ___/")
print(Fore.WHITE + Style.BRIGHT + "/ /_/ / /_/ / / / / / /_/ /  __/ /    ")
print(Fore.WHITE + Style.BRIGHT + "\____/\__._/_/ /_/_/ ,___/\___/_/     ")
print(Fore.WHITE + Style.BRIGHT + "                  /_/                 ")
print(Fore.CYAN + Style.BRIGHT +  "            #humblebrag\n")

def check_ssh(address, port):
    s = socket.socket()
    try:
        s.connect((address, port))
        return True
    except socket.error:
        return False

def query_yes_no(question, default=None):
    """Ask a yes/no question via raw_input() and return their answer.
    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def interrupted(signum, frame):
    print("TIME IS UP!")
signal.signal(signal.SIGALRM)


device_list = open("device.list").read().splitlines()

port = 22

user = raw_input("Enter username: ")

password = getpass.getpass(prompt='Enter the password:')

os.system("cls")

for device in device_list:
    current_host = "%s" % device
    ssh_open = check_ssh(current_host, port)
    if ssh_open is True:
        print(Fore.CYAN + Style.BRIGHT + "SSH is reachable at " + current_host)

        JUNOS_device = Device(host=current_host, user=user, password=password)
        JUNOS_device.open()
        cfg = Config(JUNOS_device)

        cfg.lock()
        print ("\nRemote device config has been locked for editing.")

        cfg.load(path="load.set", format="set", merge=True)
        print("\n" + "Sending set commands...\n")


        print(Fore.CYAN + Style.BRIGHT + "CONFIG CHANGES")
        print(Fore.CYAN + Style.BRIGHT + "****************")
        print(cfg.diff() + Style.BRIGHT)
        print(Fore.CYAN + Style.BRIGHT + "****************\n")

        show_compare = (cfg.diff())

        if show_compare != None:
            response = query_yes_no("Do you wish to commit these changes?")
            if response is True:
                cfg.commit(confirm=1)
                print(Fore.CYAN + Style.BRIGHT + "Changes have been committed!")
                print("Changes will automatically rollback after 2 minutes!")
                signal.alarm(120)
                try:
                    while response is True:
                        confirm = query_yes_no("Are you sure you want save these changes?")
                        if confirm is True:
                            cfg.commit()
                            print("Changes have been saved.")
                            break
                        else:
                            cfg.rollback(1)
                            cfg.commit()
                            print("Changes were not saved.")
                            print(Fore.CYAN + Style.BRIGHT + "The configuration has been rolled back!")
                            break
                except:
                    print(Fore.CYAN + Style.BRIGHT + "\nYou took to long to respond!")
                    print("Changes are being rolled back automatically.")
                    print("\nPausing for 30 seconds to await rollback completion...")
                    time.sleep(30)
            else:
                cfg.rollback(0)
                print(Fore.CYAN + Style.BRIGHT + "Changes have been aborted!")
        else:
            print("\nTHERE ARE NO CHANGES TO BE MADE")

        cfg.unlock()
        print("Remote device config has been unlocked.")
        JUNOS_device.close()

    else:
        print(Fore.RED + Style.BRIGHT + "SSH is NOT reachable at " + current_host)
