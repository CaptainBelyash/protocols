Скрипт для отправки сообщений с помощью протокола SMTP
Отправляет все картинки из данного каталога по указанному адресу

usage: smtp_mime.py [-h] [--ssl SSL] -s SERVER -t TO [-f FROM]
                    [--subject SUBJECT] [-auth AUTH] [-v VERBOSEL]
                    [-d DIRECTORY]

optional arguments:
  -h, --help            show this help message and exit
  --ssl SSL             разрешить использование ssl, если сервер поддерживает
                        (по умолчанию не использовать)
  -s SERVER, --server SERVER
                        адрес (или доменное имя) SMTP-сервера в формате
                        адрес[:порт] (порт по умолчанию 25)
  -t TO, --to TO        почтовый адрес получателя письма
  -f FROM, --from FROM  почтовый адрес отправителя(по умолчанию <>)
  --subject SUBJECT     необязательный параметр, задающий тему письма(по
                        умолчанию "Happy Pictures")
  -auth AUTH            Запрос авторизации (по умолчанию нет)
  -v VERBOSEL, --verbosel VERBOSEL
                        Отображение протокола работы (по умолчанию нет)
  -d DIRECTORY, --directory DIRECTORY
                        Каталог с изображениями (по умолчанию $pwd)
