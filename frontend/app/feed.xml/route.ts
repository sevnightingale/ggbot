import RSS from 'rss'
import { getAllPosts } from '@/lib/blog'

export async function GET() {
  const posts = getAllPosts()

  const feed = new RSS({
    title: 'ggbots Blog',
    description: 'Learn about vibe trading, AI-autonomous trading, and building trading bots.',
    site_url: 'https://ggbots.ai',
    feed_url: 'https://ggbots.ai/feed.xml',
    language: 'en',
    pubDate: new Date(),
    copyright: `© ${new Date().getFullYear()} ggbots`,
    image_url: 'https://ggbots.ai/icon-512.png',
  })

  posts.forEach((post) => {
    feed.item({
      title: post.title,
      description: post.description,
      url: `https://ggbots.ai/blog/${post.slug}`,
      date: new Date(post.date),
      author: post.author,
      categories: post.keywords,
    })
  })

  return new Response(feed.xml({ indent: true }), {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate',
    },
  })
}
