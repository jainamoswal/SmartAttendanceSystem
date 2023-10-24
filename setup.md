## Database 

- Redis database should be running on port `6379`
---

## Configuration Files : 

- /etc/systemd/system/show_pass.service
```
[Unit]
Description=Show WiFi Passphrase on LED Display

[Service]
User=root
ExecStart=/usr/bin/python3 /root/display.py
Restart=always

[Install]
WantedBy=multi-user.target
```

- /etc/systemd/system/web_service.service
```
[Unit]
Description=Web Server
After=network.target

[Service]
User=root
ExecStart=/usr/bin/python3 /root/WebApp/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

- /etc/hostapd/hostapd.conf
```
country_code=IN
interface=wlan0
ssid=Attendence System
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=12345678
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

- /etc/dnsmasq.conf
```
interface=wlan0 # Listening interface
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h

domain=local
address=/pi.local/192.168.4.1
address=/admin.pi.local/192.168.4.1
```

- /etc/nginx/conf.d/local-proxy.conf
```
server {
    listen 443 ssl;
#    server_name _;

    ssl_certificate /etc/nginx/ssl/local.crt;
    ssl_certificate_key /etc/nginx/ssl/local.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    if ($host ~* ^www\.(.*)) {
        set $redirect_host $1;
        rewrite ^(.*)$ http://$redirect_host$1 permanent;
    }
}

server {
    listen 80;
    server_name 192.168.4.1; 

    if ($host ~* ^www\.(.*)) {
        set $redirect_host $1;
        rewrite ^(.*)$ http://$redirect_host$1 permanent;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
