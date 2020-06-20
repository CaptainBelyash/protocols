
import sys
import argparse


class Server:
    def __init__(self, port, delay):
        self.port = port
        self.delay = delay



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delay', type=int, default=0)
    parser.add_argument('-p', '--port', type=int, default=123)
    args = parser.parse_args()

    if args.port not in range(1, 65536):
        print('Invalid port', file=sys.stderr)
        exit(1)

    server = Server(args.port, args.delay)
    try:
        server.start()
    except KeyboardInterrupt:
        server.server.close()
        print('Server has stopped.')


if __name__ == "__main__":
    main()
