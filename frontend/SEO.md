# ggbots SEO & Content Strategy

**Last Updated:** 2026-01-30

This document outlines our SEO infrastructure, blog system, and content strategy following 2026 best practices.

---

## Overview

Our SEO strategy is built on three pillars:
1. **Technical SEO** - Sitemap, robots.txt, structured data, meta tags
2. **Content SEO** - Blog with MDX, cornerstone articles, keyword targeting
3. **Social SEO** - Open Graph images, Twitter cards, social sharing optimization

---

## Technical SEO Infrastructure

### Files & Locations

| File | Purpose | Type |
|------|---------|------|
| `app/sitemap.ts` | Auto-generates `/sitemap.xml` with all public pages + blog posts | Dynamic |
| `app/robots.ts` | Crawl rules, blocks protected routes (`/forge`, `/admin`, `/settings`) | Dynamic |
| `app/layout.tsx` | Global metadata, OG tags, Twitter cards, icons | Static |
| `app/opengraph-image.png` | Default social sharing image (1200×630) | Static |
| `app/twitter-image.png` | Twitter card image (1200×630) | Static |
| `public/manifest.json` | PWA manifest for home screen install | Static |
| `public/icon-192.png` | Android home screen icon | Static |
| `public/icon-512.png` | Splash screen / install prompt icon | Static |
| `public/apple-touch-icon.png` | iOS home screen icon (180×180) | Static |

### Metadata Configuration

**Root Layout (`app/layout.tsx`)**:
```typescript
export const metadata: Metadata = {
  metadataBase: new URL('https://ggbots.ai'),
  title: {
    default: "ggbots - Your Edge, Amplified",
    template: "%s | ggbots",  // Pages override with their title
  },
  description: "Build autonomous AI trading agents...",
  openGraph: { ... },
  twitter: { ... },
  icons: { ... },
  manifest: "/manifest.json",
}
```

**Page-Level Overrides**: Each page can export its own `metadata` object to override defaults.

### Protected Routes (noindex)

These routes have `robots: { index: false, follow: false }`:
- `/forge/*` - Main app (requires auth)
- `/settings/*` - User settings
- `/admin/*` - Admin panel
- `/view/*` - Bot view pages

---

## Blog Infrastructure

### Architecture

```
frontend/
├── content/blog/           # MDX content files
│   └── what-is-vibe-trading.mdx
├── lib/blog.ts             # Post loading, parsing, schema generation
└── app/blog/
    ├── page.tsx            # Blog index (lists all posts)
    ├── layout.tsx          # Blog-specific layout
    └── [slug]/page.tsx     # Individual post page (SSG)
```

### Adding New Posts

1. Create a new `.mdx` file in `frontend/content/blog/`:

```mdx
---
title: "Your Post Title"
description: "Meta description (under 160 chars for SEO)"
date: "2026-02-15"
author: "Sev"
authorTwitter: "@SevNightingale"
keywords:
  - primary keyword
  - secondary keyword
  - long tail keyword
image: "/blog/custom-og-image.png"  # Optional, defaults to main OG
---

Your content here in Markdown...

## Use H2 for Main Sections

Include keywords naturally in headings.

### Use H3 for Subsections

Break up content for readability.
```

2. Push to git → Vercel builds → Post is live with full SEO

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Post title (also used in OG/Twitter) |
| `description` | Yes | Meta description, shown in search results |
| `date` | Yes | Publication date (ISO format: YYYY-MM-DD) |
| `author` | Yes | Author name |
| `authorTwitter` | No | Author's Twitter handle (for E-E-A-T) |
| `keywords` | Yes | Array of target keywords |
| `image` | No | Custom OG image path (defaults to main OG) |

### Generated Features

**Per Post**:
- BlogPosting JSON-LD schema (rich results in Google)
- Open Graph tags for social sharing
- Twitter Card metadata
- Canonical URL
- Automatic sitemap entry
- RSS feed entry

**Blog-Wide**:
- `/blog` - Index page with all posts
- `/feed.xml` - RSS feed for syndication
- Reading time calculation
- Author bio section with social links

---

## Structured Data (JSON-LD)

### Landing Page Schema

The landing page (`app/landing/page.tsx`) includes SoftwareApplication schema:

```json
{
  "@type": "SoftwareApplication",
  "name": "ggbots",
  "applicationCategory": "FinanceApplication",
  "offers": { "@type": "Offer", "price": "0" },
  "aggregateRating": { ... },
  "featureList": [ ... ]
}
```

### Blog Post Schema

Each blog post automatically generates BlogPosting schema via `lib/blog.ts`:

```json
{
  "@type": "BlogPosting",
  "headline": "Post Title",
  "author": { "@type": "Person", "name": "Sev" },
  "publisher": { "@type": "Organization", "name": "ggbots" },
  "datePublished": "2026-01-30",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "..." }
}
```

---

## Open Graph Images

### Generation System

OG images are generated programmatically using HTML templates + Playwright:

```
frontend/scripts/
├── og-image-template.html      # Main site OG template
├── og-image-arena.html         # Arena-specific template
└── generate_og_image.py        # Playwright screenshot generator
```

### Regenerating Images

```bash
cd frontend/scripts
source /home/sev/ggbot/.venv/bin/activate

# Regenerate main OG image
python generate_og_image.py og-image-template.html ../app/opengraph-image.png

# Regenerate Arena OG image
python generate_og_image.py og-image-arena.html ../app/arena/opengraph-image.png

# Copy to Twitter (can be same image)
cp ../app/opengraph-image.png ../app/twitter-image.png
```

### Brand Colors (from VIBE.md)

Templates use official brand colors:
- Background: `#0b0b0c` (obsidian)
- Accent: `#c1a87d` (brass)
- Text Primary: `#edebe7` (ivory)
- Text Muted: `#8a8781` (warm gray)

---

## Content Strategy

### Cornerstone Content

Our first cornerstone article targets the primary keyword "vibe trading":

**"What is Vibe Trading?"** (`/blog/what-is-vibe-trading`)
- ~3,200 words (long-form authority signal)
- Primary keywords: "what is vibe trading", "vibe trading explained", "ai autonomous trading"
- Secondary keywords: "ai trading bots 2026", "vibe trading vs algo trading"

### Content Pillars (Planned)

1. **Vibe Trading Education** - What it is, how it works, getting started
2. **AI Trading Strategy** - Strategy types, confidence scoring, risk management
3. **Platform Tutorials** - How to use ggbots features
4. **Case Studies** - Real bot performance, lessons learned
5. **Industry Analysis** - Market trends, competition results (ggArena)

### Distribution Checklist

For each new blog post:
- [ ] Publish to `ggbots.ai/blog/[slug]`
- [ ] Syndicate to Medium with canonical URL pointing back
- [ ] Create X thread (10-12 tweets linking to full article)
- [ ] Post to Reddit (r/algotrading, r/CryptoCurrency)
- [ ] Email to user base
- [ ] Link from relevant site pages

---

## RSS Feed

**URL**: `https://ggbots.ai/feed.xml`

The RSS feed is auto-generated from blog posts and includes:
- Title, description, URL for each post
- Publication date
- Author
- Keywords as categories

**Use Cases**:
- Podcast app syndication
- RSS readers
- Automated content aggregators
- Email newsletter automation

---

## Testing & Validation

### After Deployment

1. **Sitemap**: Visit `https://ggbots.ai/sitemap.xml`
2. **Robots**: Visit `https://ggbots.ai/robots.txt`
3. **OG Preview**: [opengraph.xyz](https://www.opengraph.xyz/) or [metatags.io](https://metatags.io/)
4. **Twitter Cards**: [Twitter Card Validator](https://cards-dev.twitter.com/validator)
5. **Rich Results**: [Google Rich Results Test](https://search.google.com/test/rich-results)
6. **Mobile-Friendly**: [Google Mobile-Friendly Test](https://search.google.com/test/mobile-friendly)

### Google Search Console

Once live, submit sitemap to Google Search Console:
1. Go to [Search Console](https://search.google.com/search-console)
2. Add property: `https://ggbots.ai`
3. Submit sitemap: `https://ggbots.ai/sitemap.xml`

---

## Dependencies

```json
{
  "gray-matter": "^4.0.3",      // Frontmatter parsing
  "next-mdx-remote": "^5.0.0",  // MDX rendering
  "reading-time": "^1.5.0",     // Reading time calculation
  "rss": "^1.2.2"               // RSS feed generation
}
```

---

## Quick Reference

### Key URLs

| URL | Purpose |
|-----|---------|
| `ggbots.ai/blog` | Blog index |
| `ggbots.ai/blog/[slug]` | Individual posts |
| `ggbots.ai/feed.xml` | RSS feed |
| `ggbots.ai/sitemap.xml` | Sitemap |
| `ggbots.ai/robots.txt` | Crawl rules |

### File Locations

| What | Where |
|------|-------|
| Blog posts | `frontend/content/blog/*.mdx` |
| Blog logic | `frontend/lib/blog.ts` |
| OG templates | `frontend/scripts/og-image-*.html` |
| OG images | `frontend/app/opengraph-image.png` |
| PWA icons | `frontend/public/icon-*.png` |

---

## Related Documentation

- **[VIBE.md](VIBE.md)** - Design system and brand colors
- **[README.md](README.md)** - Frontend architecture
- **[/CLAUDE.md](/CLAUDE.md)** - Development guidelines
