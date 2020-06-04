
import argparse
import socket
import ssl
from getpass import getpass

context = ssl.create_default_context()


def send_msg(sock, msg):
    msg += '\n'
    sock.send(msg.encode('utf-8'))


def required_length(nmin, nmax):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values) <= nmax:
                msg=f'argument "{self.dest}" requires between {nmin} and {nmax} arguments'
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength


class ServerAnswer:
    def __init__(self, msg_id, msg):
        self.msg_id = msg_id
        self.msg = msg


def print_answers(answers):
    for answer in answers:
        print(answer.msg_id, answer.msg)


def get_answer(sock):
    data = sock.recv(1024)\
        .decode('utf-8')\
        .splitlines()
    print(len(data))
    msg_id = data[0].split()[0]
    answer = list(map(lambda x:
                      ServerAnswer(msg_id,
                                   x[len(msg_id) + 1:]),
                      data))
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssl', default=False, type=bool,
                        help='разрешить использование ssl, если сервер '
                             'поддерживает (по умолчанию не использовать)')
    parser.add_argument('-s', '--server',
                        help='адрес (или доменное имя) IMAP-сервера в формате '
                             'адрес[:порт] (порт по умолчанию 143)',
                        required=True)
    parser.add_argument('-n', nargs='+', action=required_length(1, 2),
                        help='диапазон писем, по умолчанию все')
    parser.add_argument('-u', '--user', default='',
                        help='имя пользователя', required=True)
    args = parser.parse_args()
    imap_client(args.server, args.user, args.n, args.ssl)


def imap_client(imap_server, user, diapasone, use_ssl):
    old_sock = None
    host_name = imap_server
    host_port = 143
    if ':' in imap_server:
        host_name, host_port = host_name.split(':')
        host_port = int(host_port)
    sock = socket.socket()
    sock.connect((host_name, host_port))
    if use_ssl:
        old_sock = sock
        sock = context.wrap_socket(sock,
                                   server_hostname=host_name)
    print("here1")
    print_answers(get_answer(sock))
    print("here2")
    send_msg(sock, 'a0002 STARTTTS')

    password = getpass()
    send_msg(sock, f'a0001 AUTHENTICATE PLAIN\n-{user} {password}')

    send_msg(sock, f'a0002 CREATE belyaev_biba')

    if old_sock:
        old_sock.close()
    sock.close()


if __name__ == '__main__':
    main()
