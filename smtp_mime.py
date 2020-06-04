
import argparse
import os
import sys
import glob
import socket
import ssl
import base64
from getpass import getpass


image_exts = ['gif', 'png', 'jpeg', 'jpg']
image_files = []

context = ssl.create_default_context()
verbosel = False


class ServerAnswer:
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


def get_answer(sock):
    data = sock.recv(1024)\
        .decode('utf-8')\
        .splitlines()
    answer = list(map(lambda x: ServerAnswer(x[:3], x[4:]),
                      data))
    return answer


def print_answers(answers, inbase64=False):
    for answer in answers:
        if answer.code[0] in {'4', '5'}:
            print(answer.code, answer.msg, file=sys.stderr)
            raise Exception
        if inbase64:
            if verbosel:
                print(answer.code,
                      base64
                      .b64decode(answer.msg)
                      .decode('utf-8'))
        else:
            if verbosel:
                print(answer.code, answer.msg)

    if verbosel:
        print()


def send_msg(sock, msg):
    msg += '\n'
    sock.send(msg.encode('utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssl', default=False, type=bool,
                        help='разрешить использование ssl, если сервер '
                             'поддерживает (по умолчанию не использовать)')
    parser.add_argument('-s', '--serve',
                        help='адрес (или доменное имя) SMTP-сервера в формате '
                             'адрес[:порт] (порт по умолчанию 25)',
                        required=True)
    parser.add_argument('-t', '--to',
                        help='почтовый адрес получателя письма',
                        required=True)
    parser.add_argument('-f', '--from', default='',
                        help='почтовый адрес отправителя'
                             '(по умолчанию <>)')
    parser.add_argument('--subject', default='Happy Pictures',
                        help='необязательный параметр, задающий тему письма'
                             '(по умолчанию "Happy Pictures")')
    parser.add_argument('-auth', default=False, type=bool,
                        help='Запрос авторизации (по умолчанию нет)')
    parser.add_argument('-v', '--verbosel', default=False, type=bool,
                        help='Отображение протокола работы (по умолчанию нет)')
    parser.add_argument('-d', '--directory', default='',
                        help='Каталог с изображениями (по умолчанию $pwd)')

    args = parser.parse_args().__dict__
    verbosel = args['verbosel']
    message = make_message(args['from'], args['to'], args['subject'], args['directory'])
    smtp_client(message, args['serve'], args['from'],
                args['to'], args['ssl'], args['auth'])


def make_message(msg_from, msg_to, subject, directory):
    message = f'''From: <{msg_from}>
To: <{msg_to}>
Subject: {subject}
Content-Type: multipart/mixed; boundary=bound

'''
    for ext in image_exts:
        image_files.extend(glob.glob(f'{directory}\*.{ext}'))
    for image_file in image_files:
        filename, fileext = os.path.splitext(image_file)
        fileext = fileext[1:]
        filename = os.path.basename(filename)
        with open(image_file, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
            message += f'''--bound
Content-Type: image/{fileext}
Content-Transfer-Encoding: base64
Content-disposition:attachment; filename="{filename}.{fileext}"

{encoded_string}

'''
    message += '''--bound--

\r\n.\r\n'''
    return message


def smtp_client(message, smtp_server, msg_from, msg_to, use_ssl, use_auth):
    old_sock = None
    host_name = smtp_server
    host_port = 25
    if ':' in smtp_server:
        host_name, host_port = host_name.split(':')
        host_port = int(host_port)
    sock = socket.socket()
    sock.connect((host_name, host_port))

    print_answers(get_answer(sock))

    send_msg(sock, 'EHLO x')
    print_answers(get_answer(sock))


    if use_ssl:
        send_msg(sock, 'STARTTLS')
        print_answers(get_answer(sock))
        old_sock = sock
        sock = context.wrap_socket(sock,
                             server_hostname=host_name)
    send_msg(sock, 'EHLO x')
    print_answers(get_answer(sock))
    if use_auth:
        send_msg(sock, 'AUTH LOGIN')

        print_answers(get_answer(sock), True)
        print('Login:', end=' ')
        username = base64.b64encode(input()
                                    .encode('utf-8')).decode('utf-8')
        send_msg(sock, username)

        print_answers(get_answer(sock), True)
        password = getpass()
        password = base64.b64encode(password
                                    .encode('utf-8'))\
            .decode('utf-8')
        send_msg(sock, password)
        print_answers(get_answer(sock))

    send_msg(sock, f'mail from: <{msg_from}>')
    print_answers(get_answer(sock))
    send_msg(sock, f'rcpt to: <{msg_to}>')
    print_answers(get_answer(sock))

    send_msg(sock, 'data')
    print_answers(get_answer(sock))
    send_msg(sock, message)
    print_answers(get_answer(sock))
    send_msg(sock, 'QUIT')
    if old_sock:
        old_sock.close()
    sock.close()


if __name__ == '__main__':
    main()

