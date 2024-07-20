
=================================== Конфигурация сервера ===============================================


1. Создание пользователя
    Входим под root: root@5.35.89.111
    Вводим пароль из эл. письма: J4rqM8h*URnV
    Соглашаемся с сообщением:
        The authenticity of host '5.35.89.111 (5.35.89.111)' can't be established.
        ED25519 key fingerprint is SHA256:BXyr+8GiGyPSsiGtzFSXmtf+NevDRISJpnP80hhFUNE.
        This key is not known by any other names
        Are you sure you want to continue connecting (yes/no/[fingerprint])? 
    
        yes

    Создаем пользователя командами:
    ---------------------
    adduser username / создали пользователя
    apt update / обновили систему
    apt list --upgradable / поолучили список возможных обновления
    apt update / обновили систему еще раз
    apt install sudo / проверили наличие библиотеки sudo
    usermod -aG sudo username / добавили пользователя в группу sudo
    groups username / проверили группы пользователя (должно быть users, sudo)
    su username / переключиться на пользователя - username

    Создан пользователь - vladis@5.35.89.111


2. Устанавливаем ПО (NGINX, GIT, supervisor, PostgresQL, gunicorn)
    Команды:
        sudo apt install nginx
        sudo apt install git
        sudo apt install supervisor
        sudo apt install postgresql
        sudo apt install gunicorn


3. Создаем БД PostgresQL
    cd ~postgres/ / переходим в папку postgres/
    sudo -u postgres psql / запускаем в консоли возможность управлять PostgresQL

    Команды от имени "postgres=#": (точка с запятой в конце обязательны)
        CREATE DATABASE mikado; / создаем бд
        CREATE USER user_db WITH PASSWORD 'PASSWORD'; / создаем пользователя с именем и паролем
        ALTER ROLE user_db SET client_encoding TO 'utf8'; / кодировка
        ALTER ROLE user_db SET default_transaction_isolation TO 'read committed'; / хз
        ALTER ROLE user_db SET timezone TO 'UTC'; / время в офрмате utc
        GRANT ALL PRIVILEGES ON DATABASE mikado TO user_db; / все привелении для бд mikado пользователю user_db
        ALTER DATABASE mikado OWNER TO user_db; / передаем владение бд пользователю 
        \q / выйти из пользователя "postgres=#"


4. Проверяем версию Python и создаем venv
    python -V / версия питона 2+
    python3 -V / версия питона 3+

    Если версия питона 3 устраивает, то создаем venv из корневой папки:
        sudo apt install python3.11-venv / устанавливем библиотеку venv
        python3 -m venv venv / создаем виртульное окружение
        source venv/bin/activate / запускаем venv


5. Клонируем проект с GIT

    git init / указываем git, что данная директория является репозиторием Git

    если репа приватная то используем токен - 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
    git pull https://token@github.com/gromovvladis/mikado.git

    git pull https://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@github.com/gromovvladis/mikado.git

    отменить все локальные изменения 
        git reset --hard
    переместить изменения в папку stash
        git stash 
    

6. Устанавливаем зависимости
    Устанавливем библиотеки для норм работы:
        sudo apt-get install -y make build-essential libssl-dev zlib1g-dev 
        sudo apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm
        sudo apt-get install -y libncurses5-dev  libncursesw5-dev xz-utils tk-dev

    Устанавливаем зависимости:
        pip install -U pip / обновляем pip
        pip install -r requirements.txt / устанавливем зависимости


7. Делаем миграции и создаем суперпользователя
    перед миграциями смотрим в файил настроек и убеждаемся, что в файле .env база данных подключена корректно
    переходим в директорию с файлом manage.py
    миграции
        python manage.py makemigrations
    
    суперпользователь
        python manage.py createsuperuser

    если были сделаны изменения непосредственно в базе данных, то запускаем Команду
        python manage.py update_index


8. Конфигурация NGINX
    открываем фаил конфигурации NGING:
    sudo nano /etc/nginx/sites-available/default 

    очистить фаил команда: ALT + T

    Конфигурация:
        server {
            listen 80;
            server_name mikado-sushi.ru www.mikado-sushi.ru 5.35.89.111;
            access_log  /var/log/nginx/logger.log;
            client_max_body_size 20M;
            location /media/ {
                root /home/vladis/mikado/public/;
                expires 30d;
            }

            location /static/ {
                root /home/vladis/mikado/public/;
                expires 30d;
            }

            location / {
                proxy_pass http://127.0.0.1:8000; 
                proxy_set_header Host $server_name;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            }
        }

    Перезапускаем NGING:
        sudo service nginx restart


9. Установка SSL серфтификата через
    Устанавливаем утилиту Certbot:
        sudo apt install certbot python3-certbot-nginx

    Запускаем Certbot:
        sudo certbot --nginx


10. Запускаем Supervisor для сайта и для Celery
    переходим в папку супервизора
        cd /etc/supervisor/conf.d/

    в этой папке создаем ссылки на файлы конфигураций mikado.conf, celery.conf
    создаем ссылку:
        sudo ln /home/vladis/mikado/config/mikado.conf
        sudo ln /home/vladis/mikado/config/celery.conf

    активируем супервизора:
        sudo update-rc.d supervisor enable

    запускаем супервизор:
        sudo service supervisor start

    проверка доспутности:
        sudo supervisorctl reread
    
    обновляем список процессов supervisor:
        sudo supervisorctl update

    команды для проверки статуса и перезагрузки:
        sudo supervisorctl status project
        sudo supervisorctl restart project
        sudo supervisorctl restart all


11. Настраиваем REDIS
    устанавливем редис сервер 
        sudo apt install redis-server

    запускаем сервер:
        sudo systemctl start redis-server

    делаем:
        sudo systemctl enable redis-server

    sudo nano /etc/redis/redis.conf

    Проверка
        redis-cli

    очистить кэш
        redis-cli Flushall


12. Собираем статику
    переходим в директорию с файлом manage.py
    python manage.py collectstatic


vladis@5.35.89.111

============================================= Доп возможности =================================================

1. Бэкап БД из файла


=============================================== ИСХОДНИКИ =====================================================


Создание пользователя
---------------------
adduser username
usermod -aG sudo username
group username
su username
---------------------------------------
Компиляции python 3.6
----------------------
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev
sudo apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm
sudo apt-get install -y libncurses5-dev  libncursesw5-dev xz-utils tk-dev

wget https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tgz
tar xvf Python-3.6.4.tgz
cd Python-3.6.4
./configure --enable-optimizations
make -j8
sudo make altinstall
python3.6

-----------------------------------------
Создание базы данных
--------------------
sudo -u postgres psql
CREATE DATABASE banket;
CREATE USER b_user WITH PASSWORD 'She3348Jdfurfghs';
ALTER ROLE userdb SET client_encoding TO 'utf8';
ALTER ROLE userdb SET default_transaction_isolation TO 'read committed';
ALTER ROLE userdb SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE movie TO userdb;
\q

----------------------------------------
Установка Gunicorn
------------------
gunicorn project.wsgi:application --bind 111.222.333.44:8000
----------------------------------------
Настрока nginx
--------------
server {
    listen 80;
    server_name 111.222.333.44; # здесь прописать или IP-адрес или доменное имя сервера
    access_log  /var/log/nginx/example.log;
 
    location /static/ {
        root /home/user/myprojectenv/myproject/myproject/;
        expires 30d;
    }
 
    location / {
        proxy_pass http://127.0.0.1:8000; 
        proxy_set_header Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

sudo service nginx restart

------------------------------------------
For SSL
-------
map $sent_http_content_type $expires {
    "text/html"                 epoch;
    "text/html; charset=utf-8"  epoch;
    default                     off;
}
server {
    listen 80;
    server_name www.django.com;
    return 301 https://django.com$request_uri;
}
server{
    listen 443 ssl;
    ssl on;                                      
    ssl_certificate /etc/ssl/django.crt;     
    ssl_certificate_key /etc/ssl/django.key; 
    server_name django.com;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/x-javascript text/xml application/xml application/xml+rss text/javascript application/javascript;

    location /static/ {
        root /home/user/pj;
        expires 1d;
    }

    location /media/ {
        root /home/user/pj;
        expires 1d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

---------------------------------------
Настройка supervisor
cd /etc/supervisor/conf.d/
sudo update-rc.d supervisor enable
sudo service supervisor start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status project
sudo supervisorctl restart project
--------------------



======== Изменяем индексы после изменения товаров в бд =================
python manage.py update_index


======== Создаем БД =================
CREATE DATABASE mikado
CREATE USER user_db WITH PASSWORD 'mikadosushi';

ALTER ROLE user_db SET client_encoding TO 'utf8';
ALTER ROLE user_db SET default_transaction_isolation TO 'read committed';
ALTER ROLE user_db SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE mikado TO vladis;

ALTER DATABASE mikado OWNER TO vladis;
ALTER DATABASE mikado OWNER TO user_db;



======== Настраиваем gunicorn =================
gunicorn mikado.config.wsgi:application --bind 5.35.89.111:8000
gunicorn config.wsgi:application --bind 5.35.89.111:8000


======== Настраиваем NGINX без SSL =================
server {
    listen 80;
    server_name mikado-sushi.ru www.mikado-sushi.ru 5.35.89.111;
    access_log  /var/log/nginx/logger.log;
    client_max_body_size 20M;
     location /media/ {
        root /home/vladis/mikado/public/;
        expires 30d;
    }

    location /static/ {
        root /home/vladis/mikado/public/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000; 
        proxy_set_header Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

======== Настраиваем NGINX пример с SSL =================


server {
    server_name mikado-sushi.ru www.mikado-sushi.ru 5.35.89.111;
    access_log  /var/log/nginx/logger.log;
    client_max_body_size 20M;

    location /media/ {
        root /home/vladis/mikado/public/;
        expires 30d;
    }

    location /static/ {
        root /home/vladis/mikado/public/;
        expires 30d;
    }
 
    location / {
        proxy_pass http://127.0.0.1:8000; 
        proxy_set_header Host $server_name;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    listen 443 ssl http2; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/mikado-sushi.ru/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/mikado-sushi.ru/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot


}

server {
     if ($host = www.mikado-sushi.ru) {
         return 301 https://$host$request_uri;
     } # managed by Certbot


     if ($host = mikado-sushi.ru) {
         return 301 https://$host$request_uri;
     } # managed by Certbot


     listen 80;
     server_name mikado-sushi.ru www.mikado-sushi.ru 5.35.89.111;
     return 404; # managed by Certbot

}


======== Настраиваем REDIS =================
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo nano /etc/redis/redis.conf




======== Копирум с репы GIT =================
git pull https://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@github.com/gromovvladis/mikado.git



======== Создание venv =================
python3 -m venv venv


======== Установка зависимостей =================
pip install -r requirements.txt 


======== Бэкап БД =================
sudo -u postgres pg_dump -Fc mikado > /home/vladis/mikado-backup.sql

