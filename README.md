# 21184-ProjetoFinal
Repositório do projeto final da UC 21184 - Projectos de Engenharia Informática

## Preparação de Ambiente
Assume-se que o utilizador tem as seguintes ferramentas instaladas:
* Docker
* Terminal e/ou IDE

### 1. Instanciação Local
1.1) Na pasta desejada, clonar o repositório:
```
git clone https://github.com/andreiaRomao/21184-ProjetoFinal-UniAnalytics.git
```

### 2. Instalação de Moodle Local:
Para a primeira utilização, terá de se instalar localmente o Moodle, seguindo os seguintes passos:
2.1) Navegar para a pasta moodle-docker:
```
cd moodle-docker
```

2.2) Fazer download da versão desejada do Moodle (4.4):
```
git clone -b MOODLE_404_STABLE https://git.moodle.org/git/moodle.git
```
PS: Info de releases pode ser encontrada em : https://moodledev.io/general/releases 

2.3) Criar uma diretoria config com o ficheiro php.ini, e a seguinte configuração:
```
mkdir config
touch config/php.ini
nano php.ini
```

```
max_input_vars = 50000
max_execution_time = 120
post_max_size = 256M
upload_max_filesize = 256M
```

2.4) Subir o container em docker:
```
docker-compose up -d
```

2.5) Seguir os passos de intalação no: http://localhost:8080/

(Opcional) Para utilizar os backup que está de dados que foram previamente criados (db_moodle_backup.sql) e que está presente no repositório, seguir os seguintes passos:
```
cd /backups/moodle_backup/
chmod +x restore.sh
./restore.sh
```

## Execução do Programa
Navegar até á pasta:
```
cd .../moodle-docker
```

Compilar e iniciar o programa com:
```
docker compose up --build
```

Utilizar em: 
```
http://localhost:8050/
```
