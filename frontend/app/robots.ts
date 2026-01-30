import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/forge/',      // App - requires auth
          '/settings/',   // User settings
          '/admin/',      // Admin panel
          '/view/',       // Bot view pages
          '/api/',        // API endpoints
          '/test/',       // Test pages
          '/credits/',    // Payment flows
          '/success/',    // Success pages
        ],
      },
    ],
    sitemap: 'https://ggbots.ai/sitemap.xml',
  }
}
