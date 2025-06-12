# API Server Setup Guide

Setting up ggbots-api.nightingale.business to serve main_api.py over HTTPS

## Step 1: Create nginx config for API

```bash
sudo nano /etc/nginx/sites-available/ggbots-api
```

Add this content (copy exactly):

```nginx
server {
    listen 80;
    server_name ggbots-api.nightingale.business;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 2: Enable the site

```bash
sudo ln -s /etc/nginx/sites-available/ggbots-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 3: Install and setup PM2

```bash
npm install -g pm2
cd /home/sev/ggbot
pm2 start main_api.py --name ggbots-api --interpreter python3
pm2 save
pm2 startup
```

Follow the command PM2 gives you for startup.

## Step 4: Install certbot and get SSL

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ggbots-api.nightingale.business
```

## Step 5: Test

```bash
curl -I https://ggbots-api.nightingale.business
```

Should return 200 OK with your API response.


https://ggbots-api.nightingale.business