#!/bin/bash
sudo apt update -y
sudo apt install tmux python3-venv postgresql -y

domain=$1
port=$2

sudo chmod 777 /home/$4/backend/db-setup.sql
mv /home/$4/backend/db-setup.sql /tmp/

# Install caddy
tmux new -ds caddy "
cd ~/;
mkdir caddy;
cd caddy;
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https;
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg;
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list;
sudo apt update;
sudo apt install caddy;
sudo caddy stop;
echo '$domain
{
reverse_proxy 127.0.0.1:$port
log {
output file log.txt

}
}' >> Caddyfile;
sudo caddy start;
exec $SHELL"

# Start flask server
tmux new -ds backend "
export DOMAIN_NAME=$domain;
export FB_CREDENTIALS=$3;
cd ~/backend;
python3 -m venv venv;
source venv/bin/activate;
pip install -r requirements.txt;
python server.py;
exec $SHELL"

# Setup database
tmux new -ds database "
sudo -u postgres psql -f /tmp/db-setup.sql;
exec $SHELL"