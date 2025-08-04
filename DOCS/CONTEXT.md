# NGINX Configuration Update - CORS Fix for Frontend

## Issue
The Vercel frontend at `https://ggbot-app.vercel.app` cannot access the API at `https://ggbots-api.nightingale.business` due to missing CORS headers in nginx configuration.

## Solution
Replace the entire contents of `/etc/nginx/sites-available/ggbots-api` with the configuration below:

```nginx
server {
    server_name ggbots-api.nightingale.business;

    location / {
        # CORS headers for Vercel frontend
        add_header 'Access-Control-Allow-Origin' 'https://ggbot-app.vercel.app' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-Requested-With' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://ggbot-app.vercel.app' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-Requested-With' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
        
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

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ggbots-api.nightingale.business/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ggbots-api.nightingale.business/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = ggbots-api.nightingale.business) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name ggbots-api.nightingale.business;
    return 404; # managed by Certbot


}
```

## Commands to Execute

After copying the configuration above:

1. **Test the configuration:**
   ```bash
   sudo nginx -t
   ```

2. **If test passes, reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

3. **Verify CORS is working:**
   ```bash
   curl -I -H "Origin: https://ggbot-app.vercel.app" "https://ggbots-api.nightingale.business/health"
   ```
   
   Should return headers including:
   ```
   Access-Control-Allow-Origin: https://ggbot-app.vercel.app
   ```

## What This Fixes

- **CORS Policy**: Allows Vercel frontend to make API requests
- **Preflight Requests**: Handles OPTIONS requests properly  
- **Headers**: Permits necessary headers for API communication
- **Credentials**: Allows cookies/auth headers if needed

After applying this fix, the frontend should be able to load the ggShot flagship configuration and display real data instead of "Loading dashboard..."