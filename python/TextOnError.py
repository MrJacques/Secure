"""
textOnError cmd, if the cmd exits with an error then send text
textOnError -m message to send on error

www.twilio.com/referral/ft9Jn1

"""
import argparse
import json
import logging
import re
import socket
import subprocess
import sys
import time
from threading import Thread
from typing import IO, AnyStr, TextIO

from twilio.rest import Client


def get_hostname():
    """
    :return: safely return the hostname
    """
    hostname = "<Host Undetermined>"
    try:
        hostname = socket.gethostname()
    except Exception as e:
        logging.error(f"Could not get hostname.\nException: {e}")
    return hostname


def echo_pipe(name: str, pipe: IO[AnyStr], dest_file: TextIO):
    """
    Echo output from pipe to dest_file
    """
    assert pipe
    with pipe:
        for line in iter(pipe.readline, b''):
            if not line:
                break
            logging.debug(name, len(line), line, end="", file=dest_file)
            print(line, end="", file=dest_file)

    logging.info(f"{name} closed")


# Set these after parsing args
twilio_sid = None
twilio_token = None
twilio_from_phone = None


default_message = r"There was a failure on {host}.\nExit Code: {code}\nCommand: {cmd}"

parser = argparse.ArgumentParser(usage='%(prog)s -options shell command to run',
                                 description="Run a non-interactive command and send a text if there is an error")

parser.add_argument('-n', '--pretend',
                    action='store_true',
                    help='Do not actually send text')

parser.add_argument('-m', '--message',
                    default=default_message,
                    help=f'Message to send.  Defaults text message is "{default_message.strip()}"\n'
                         r'The {tags} and are \n replaced at runtime.')

parser.add_argument('-a', '--always',
                    action='store_true',
                    help='Always send text even if there is no error.')

parser.add_argument('-t', '--test',
                    action='store_true',
                    help='Use test credentials to send text.')

parser.add_argument('--loglevel',
                    choices=['critical', 'error', 'warning', 'info', 'debug'],
                    type=str.lower,
                    help='Set logging level. Example --loglevel debug')

parser.add_argument('cmd', nargs=argparse.REMAINDER,
                    help='Command to run with parameters'
                    )

parser.usage = parser.format_help()
args = parser.parse_args()

if args.loglevel:
    logging.basicConfig(level=args.loglevel.upper())
    logging.info(f"Logging set to {args.loglevel.upper()}")

# TODO make path settable from command line or environment
with open(r'twilio.json') as f:
    data = json.load(f)

if args.test:
    # test credentials
    assert data['twilio']['test']['account_sid']
    assert data['twilio']['test']['auth_token']
    assert data['twilio']['test']['from_phone']

    twilio_sid = data['twilio']['test']['account_sid']
    twilio_token = data['twilio']['test']['auth_token']
    twilio_from_phone = data['twilio']['test']['test_from']
else:
    # live credentials
    assert data['twilio']['account_sid']
    assert data['twilio']['auth_token']
    assert data['twilio']['from_phone']

    twilio_sid = data['twilio']['account_sid']
    twilio_token = data['twilio']['auth_token']
    twilio_from_phone = data['twilio']['from_phone']

assert data['twilio']['to_phones']
twilio_to_phones = data['twilio']['to_phones']

twilio_client = Client(twilio_sid, twilio_token)

cmd = args.cmd
pretend_mode = args.pretend
always_send_mode = args.always
message = args.message if args.message else default_message

if not (cmd or always_send_mode):
    parser.error("There must be a command to run (unless --always)")

error_code = 0
if cmd:
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               bufsize=1)

    st_out = Thread(target=echo_pipe, args=[
                    "stdout", process.stdout, sys.stdout], daemon=False)
    st_out.start()
    st_err = Thread(target=echo_pipe, args=[
                    "stderr", process.stderr, sys.stderr], daemon=False)
    st_err.start()

    while process.poll() is None or st_out.is_alive() or st_err.is_alive():
        logging.debug(
            f"Not dead yet, poll {process.poll()}, is alive out {st_out.is_alive()}, err {st_err.is_alive()}")
        time.sleep(0.2)

    logging.info(f"Exit code {process.poll()}")
    if process.poll() is not None and process.poll() > 0:
        error_code = process.poll()
        message = message.replace("{cmd}", " ".join(cmd))
        message = message.replace("{code}", str(error_code))

if always_send_mode or error_code > 0:
    message = message.replace("{host}", get_hostname())
    # replace \n but not \\n with newline
    message = re.sub(r"(^|[^\\])(\\n)", "\\1\n", message)

    if pretend_mode:
        print(f"\n\nTEXT that would be sent:\n{message}")
    else:
        logging.info(f"\n\nTEXT that will be sent:\n{message}")
        for to_phone in twilio_to_phones:
            logging.info(f"Text to {to_phone}")
            twilio_client.messages.create(
                to=to_phone,
                from_=twilio_from_phone,
                body=message)
else:
    logging.debug("No text was sent.")

if error_code > 0:
    sys.exit(error_code)
