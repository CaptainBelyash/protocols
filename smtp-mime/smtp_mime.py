
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

verbosel = False


class ServerAnswer:
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssl', default=False, type=bool,
                        help='разрешить использование ssl, если сервер '
                             'поддерживает (по умолчанию не использовать)')
    parser.add_argument('-s', '--server',
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
    parser.add_argument('-d', '--directory', default='.',
                        help='Каталог с изображениями (по умолчанию $pwd)')

    args = parser.parse_args().__dict__
    message = make_message(args['from'], args['to'], args['subject'], args['directory'])
    smtp_client = SMTPClient(message, args['server'], args['from'],
                             args['to'], args['ssl'], args['auth'], args['verbosel'])


def make_message(msg_from, msg_to, subject, directory):
    message = f'''From: <{msg_from}>
To: <{msg_to}>
Subject: {subject}
Content-Type: multipart/mixed; boundary=bound

'''
    for ext in image_exts:
        image_files.extend(glob.glob(f'{directory}/*.{ext}'))
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


class SMTPClient:
    def __init__(self, message,
                 smtp_server_name, sender,
                 recipient, use_ssl,
                 use_auth, verbosel):
        self.message = message
        self.host_name = smtp_server_name
        self.host_port = 25
        self.parse_server_name(smtp_server_name)

        self.verbosel = verbosel
        self.use_ssl = use_ssl
        self.use_auth = use_auth

        self.sock = None
        self.ssl_sock = None
        self.main_sock = None
        self.context = ssl.create_default_context()

        self.sender = sender
        self.recipient = recipient

        self.start()

    def start(self):
        self.sock = socket.socket()
        self.sock.connect((self.host_name, self.host_port))
        self.main_sock = self.sock

        self.print_answers(self.get_answer())

        self.send_msg('EHLO x')
        self.print_answers(self.get_answer())

        if self.use_ssl:
            self.start_ssl()

        if self.use_auth:
            self.authorization()

        self.send_msg(f'mail from: <{self.sender}>')
        self.print_answers(self.get_answer())
        self.send_msg(f'rcpt to: <{self.recipient}>')
        self.print_answers(self.get_answer())

        self.send_msg('data')
        self.print_answers(self.get_answer())
        self.send_msg(self.message)
        self.print_answers(self.get_answer())
        self.send_msg('QUIT')
        if self.ssl_sock:
            self.ssl_sock.close()
        self.sock.close()

    def start_ssl(self):
        self.send_msg('STARTTLS')
        self.print_answers(self.get_answer())

        self.ssl_sock = self.context.wrap_socket(self.sock,
                                                 server_hostname=self.host_name)
        self.main_sock = self.ssl_sock
        self.send_msg('EHLO x')
        self.print_answers(self.get_answer())

    def authorization(self):
        self.send_msg('AUTH LOGIN')

        self.print_answers(self.get_answer(), True)
        print('Login:', end=' ')
        username = base64.b64encode(input()
                                    .encode('utf-8')).decode('utf-8')
        self.send_msg(username)

        self.print_answers(self.get_answer(), True)
        password = getpass()
        password = base64.b64encode(password
                                    .encode('utf-8'))\
            .decode('utf-8')
        self.send_msg(password)
        self.print_answers(self.get_answer())

    def parse_server_name(self, server_name):
        if ':' in server_name:
            self.host_name, self.host_port = server_name.split(':')
            self.host_port = int(self.host_port)

    def get_answer(self):
        data = self.main_sock.recv(1024) \
            .decode('utf-8') \
            .splitlines()
        answer = list(map(lambda x: ServerAnswer(x[:3], x[4:]),
                          data))
        return answer

    def print_answers(self, answers, inbase64=False):
        for answer in answers:
            if answer.code[0] in {'4', '5'}:
                print(answer.code, answer.msg, file=sys.stderr)
                raise Exception
            if inbase64:
                if self.verbosel:
                    print(answer.code,
                          base64
                          .b64decode(answer.msg)
                          .decode('utf-8'))
            else:
                if verbosel:
                    print(answer.code, answer.msg)

        if verbosel:
            print()

    def send_msg(self, msg):
        msg += '\n'
        self.main_sock.send(msg.encode('utf-8'))


if __name__ == '__main__':
    main()

