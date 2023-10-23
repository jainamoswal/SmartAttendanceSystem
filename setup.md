# Configuration Files : 

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

    # Redirect www.example.com to example.com
    if ($host ~* ^www\.(.*)) {
        set $redirect_host $1;
        rewrite ^(.*)$ http://$redirect_host$1 permanent;
    }
}



server {
    listen 80;
    server_name 192.168.4.1;  # Replace with your domain or server IP address

    # Redirect www.example.com to example.com
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
