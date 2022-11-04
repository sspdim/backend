sudo apt update -y
sudo apt install tmux python3-venv postgresql -y

# Install caddy
tmux new -ds caddy '
cd ~/;
mkdir caddy;
cd caddy;
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https;
curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/gpg.key" | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg;
curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt" | sudo tee /etc/apt/sources.list.d/caddy-stable.list;
sudo apt update;
sudo apt install caddy;
sudo caddy stop;
echo "$1
{
reverse_proxy 127.0.0.1:$2
log {
output file log.txt

}
}" >> Caddyfile;
sudo caddy start;
exec $SHELL'

# Start flask server
tmux new -ds backend '
cd ~/backend;
python3 -m venv venv;
source venv/bin/activate;
pip install -r requirements.txt;
python server.py;
exec $SHELL'

# Setup database
tmux new -ds database '
sudo -i -u postgresql;
psql -f /home/$3/backend/db-setup.sql;
exec $SHELL'