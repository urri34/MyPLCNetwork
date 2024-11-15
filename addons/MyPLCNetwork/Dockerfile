FROM debian:latest

# Instal·lar plc-utils
RUN apt-get update && apt-get install -y plc-utils

# Copiar el teu codi
COPY . /app
WORKDIR /app

# Instal·lar dependències Python
RUN apt-get install -y python3 python3-pip
RUN pip3 install -r requirements.txt

CMD ["python3", "MyPLCNetwork.py"]