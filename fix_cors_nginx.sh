#!/bin/bash
# Fix CORS nginx configuration for new domain

echo "🔧 Fixing CORS configuration for app.ggbots.ai domain..."

# Backup current config
echo "📋 Creating backup..."
sudo cp /etc/nginx/sites-available/ggbots-api /etc/nginx/sites-available/ggbots-api.backup

# Update the CORS headers to the new domain
echo "🔄 Updating CORS headers from ggbot-app.vercel.app to app.ggbots.ai..."
sudo sed -i 's/https:\/\/ggbot-app\.vercel\.app/https:\/\/app\.ggbots\.ai/g' /etc/nginx/sites-available/ggbots-api

# Test nginx configuration
echo "✅ Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx config test passed!"
    
    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo "🎉 CORS fix completed successfully!"
    echo "📝 Frontend should now be able to connect without CORS errors"
    
else
    echo "❌ Nginx config test failed! Rolling back..."
    sudo cp /etc/nginx/sites-available/ggbots-api.backup /etc/nginx/sites-available/ggbots-api
    echo "⚠️  Restored backup configuration"
fi