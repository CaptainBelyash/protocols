
import socket
import ssl
import base64


host_name = 'smtp.gmail.com'
context = ssl.create_default_context()


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
    throw = False
    for answer in answers:
        if answer.code[0] in {'4', '5'}:
            throw = True
        if inbase64:
            print(answer.code,
                  base64
                  .b64decode(answer.msg)
                  .decode('utf-8'))
        else:
            print(answer.code, answer.msg)
    print()
    if throw:
        raise Exception


def send_msg(sock, msg):
    msg += '\n'
    sock.send(msg.encode('utf-8'))


def main():
    sock = socket.socket()
    sock.connect((host_name, 587))

    print_answers(get_answer(sock))

    send_msg(sock, 'EHLO x')
    print_answers(get_answer(sock))

    send_msg(sock, 'STARTTLS')
    print_answers(get_answer(sock))

    with context.wrap_socket(sock,
                             server_hostname=host_name) as sslsock:
        send_msg(sslsock, 'EHLO x')
        print_answers(get_answer(sslsock))

        send_msg(sslsock, 'AUTH LOGIN')

        print_answers(get_answer(sslsock), True)
        username = base64.b64encode(input()
                                    .encode('utf-8')).decode('utf-8')
        print(username)
        send_msg(sslsock, username)

        print_answers(get_answer(sslsock), True)
        password = base64.b64encode(input()
                                    .encode('utf-8')).decode('utf-8')
        send_msg(sslsock, password)

        print_answers(get_answer(sslsock))

        send_msg(sslsock, f'mail from: <{username}>')
        print_answers(get_answer(sslsock))
        next = input()
        while next != '.':
            print('sasamba')
            send_msg(sslsock, f'rcpt to: <{next}>')
            print_answers(get_answer(sslsock))
            next = input()
        send_msg(sslsock, 'data')
        print_answers(get_answer(sslsock))
        send_msg(sslsock,
                 '''From: <belyaevnp@gmail.com>
To: <example@example.com>
Subject: test

This is test mail
Sent from python script
\r\n.\r\n''')
        print('sas')
        print_answers(get_answer(sslsock))
        send_msg(sslsock, 'QUIT')
        print('sass')
    sock.close()


if __name__ == '__main__':
    main()

