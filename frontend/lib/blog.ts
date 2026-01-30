import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import readingTime from 'reading-time'

const POSTS_PATH = path.join(process.cwd(), 'content/blog')

export interface PostMeta {
  slug: string
  title: string
  description: string
  date: string
  author: string
  authorTwitter?: string
  readingTime: string
  keywords: string[]
  image?: string
}

export interface Post extends PostMeta {
  content: string
}

/**
 * Get all post slugs for static generation
 */
export function getPostSlugs(): string[] {
  if (!fs.existsSync(POSTS_PATH)) {
    return []
  }
  return fs.readdirSync(POSTS_PATH)
    .filter(file => file.endsWith('.mdx'))
    .map(file => file.replace(/\.mdx$/, ''))
}

/**
 * Get post metadata and content by slug
 */
export function getPostBySlug(slug: string): Post | null {
  const filePath = path.join(POSTS_PATH, `${slug}.mdx`)

  if (!fs.existsSync(filePath)) {
    return null
  }

  const fileContents = fs.readFileSync(filePath, 'utf8')
  const { data, content } = matter(fileContents)
  const stats = readingTime(content)

  return {
    slug,
    title: data.title || 'Untitled',
    description: data.description || '',
    date: data.date || new Date().toISOString(),
    author: data.author || 'ggbots',
    authorTwitter: data.authorTwitter,
    readingTime: stats.text,
    keywords: data.keywords || [],
    image: data.image,
    content,
  }
}

/**
 * Get all posts sorted by date (newest first)
 */
export function getAllPosts(): PostMeta[] {
  const slugs = getPostSlugs()

  return slugs
    .map(slug => {
      const post = getPostBySlug(slug)
      if (!post) return null
      // Return metadata only (no content)
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { content: _, ...meta } = post
      return meta
    })
    .filter((post): post is PostMeta => post !== null)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}

/**
 * Generate BlogPosting JSON-LD schema for SEO
 */
export function generateBlogPostSchema(post: Post, url: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.description,
    image: post.image || 'https://ggbots.ai/opengraph-image.png',
    datePublished: post.date,
    dateModified: post.date,
    author: {
      '@type': 'Person',
      name: post.author,
      url: post.authorTwitter ? `https://x.com/${post.authorTwitter.replace('@', '')}` : undefined,
    },
    publisher: {
      '@type': 'Organization',
      name: 'ggbots',
      logo: {
        '@type': 'ImageObject',
        url: 'https://ggbots.ai/icon-512.png',
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': url,
    },
    keywords: post.keywords.join(', '),
  }
}
