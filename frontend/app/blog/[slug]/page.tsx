import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { MDXRemote } from 'next-mdx-remote/rsc'
import { getPostBySlug, getPostSlugs, generateBlogPostSchema } from '@/lib/blog'
import { Calendar, Clock, User, Twitter, ArrowLeft } from 'lucide-react'

interface PageProps {
  params: Promise<{ slug: string }>
}

// Generate static paths for all posts
export async function generateStaticParams() {
  const slugs = getPostSlugs()
  return slugs.map((slug) => ({ slug }))
}

// Generate metadata for SEO
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  const post = getPostBySlug(slug)

  if (!post) {
    return {
      title: 'Post Not Found',
    }
  }

  return {
    title: post.title,
    description: post.description,
    keywords: post.keywords,
    authors: [{ name: post.author }],
    openGraph: {
      title: post.title,
      description: post.description,
      type: 'article',
      publishedTime: post.date,
      authors: [post.author],
      url: `https://ggbots.ai/blog/${slug}`,
      images: [
        {
          url: post.image || '/opengraph-image.png',
          width: 1200,
          height: 630,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.description,
      images: [post.image || '/twitter-image.png'],
    },
    alternates: {
      canonical: `https://ggbots.ai/blog/${slug}`,
    },
  }
}

// MDX components for custom styling
const mdxComponents = {
  h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h1 className="text-3xl font-display font-semibold text-[var(--text-primary)] mt-10 mb-4" {...props} />
  ),
  h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="text-2xl font-display font-semibold text-[var(--text-primary)] mt-10 mb-4 pb-2 border-b border-[var(--border)]" {...props} />
  ),
  h3: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="text-xl font-semibold text-[var(--text-primary)] mt-8 mb-3" {...props} />
  ),
  h4: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h4 className="text-lg font-semibold text-[var(--text-primary)] mt-6 mb-2" {...props} />
  ),
  p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="text-[var(--text-secondary)] leading-relaxed mb-4" {...props} />
  ),
  ul: (props: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc pl-6 space-y-2 text-[var(--text-secondary)] mb-4" {...props} />
  ),
  ol: (props: React.HTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal pl-6 space-y-2 text-[var(--text-secondary)] mb-4" {...props} />
  ),
  li: (props: React.HTMLAttributes<HTMLLIElement>) => (
    <li className="leading-relaxed" {...props} />
  ),
  a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a className="text-[var(--accent)] hover:text-[var(--accent-hover)] underline underline-offset-2 transition-colors" {...props} />
  ),
  blockquote: (props: React.HTMLAttributes<HTMLQuoteElement>) => (
    <blockquote className="border-l-4 border-[var(--accent)] pl-4 my-6 text-[var(--text-muted)] italic" {...props} />
  ),
  code: (props: React.HTMLAttributes<HTMLElement>) => (
    <code className="bg-[var(--bg-tertiary)] text-[var(--accent)] px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
  ),
  pre: (props: React.HTMLAttributes<HTMLPreElement>) => (
    <pre className="bg-[var(--bg-tertiary)] border border-[var(--border)] rounded-lg p-4 overflow-x-auto mb-4 text-sm" {...props} />
  ),
  hr: () => (
    <hr className="my-8 border-[var(--border)]" />
  ),
  strong: (props: React.HTMLAttributes<HTMLElement>) => (
    <strong className="text-[var(--text-primary)] font-semibold" {...props} />
  ),
  em: (props: React.HTMLAttributes<HTMLElement>) => (
    <em className="text-[var(--text-primary)]" {...props} />
  ),
  table: (props: React.HTMLAttributes<HTMLTableElement>) => (
    <div className="overflow-x-auto mb-6 rounded-lg border border-[var(--border)]">
      <table className="w-full text-sm" {...props} />
    </div>
  ),
  thead: (props: React.HTMLAttributes<HTMLTableSectionElement>) => (
    <thead className="bg-[var(--bg-tertiary)] text-[var(--text-primary)]" {...props} />
  ),
  th: (props: React.HTMLAttributes<HTMLTableCellElement>) => (
    <th className="px-4 py-2.5 text-left font-semibold border-b border-[var(--border)] whitespace-nowrap" {...props} />
  ),
  td: (props: React.HTMLAttributes<HTMLTableCellElement>) => (
    <td className="px-4 py-2.5 text-[var(--text-secondary)] border-b border-[var(--border)]" {...props} />
  ),
  tr: (props: React.HTMLAttributes<HTMLTableRowElement>) => (
    <tr className="hover:bg-[var(--bg-secondary)] transition-colors" {...props} />
  ),
}

export default async function BlogPostPage({ params }: PageProps) {
  const { slug } = await params
  const post = getPostBySlug(slug)

  if (!post) {
    notFound()
  }

  const url = `https://ggbots.ai/blog/${slug}`
  const schema = generateBlogPostSchema(post, url)

  return (
    <>
      {/* JSON-LD Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />

      <article className="max-w-3xl mx-auto px-6 py-12">
        {/* Back Link */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors mb-8"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Blog
        </Link>

        {/* Header */}
        <header className="mb-10">
          <h1 className="text-4xl md:text-5xl font-display font-semibold text-[var(--text-primary)] leading-tight mb-6">
            {post.title}
          </h1>

          <p className="text-xl text-[var(--text-secondary)] mb-6">
            {post.description}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--text-muted)] pb-6 border-b border-[var(--border)]">
            <span className="flex items-center gap-1.5">
              <User className="h-4 w-4" />
              {post.author}
            </span>
            {post.authorTwitter && (
              <a
                href={`https://x.com/${post.authorTwitter.replace('@', '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
              >
                <Twitter className="h-4 w-4" />
                {post.authorTwitter}
              </a>
            )}
            <span className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4" />
              {new Date(post.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-4 w-4" />
              {post.readingTime}
            </span>
          </div>
        </header>

        {/* Content */}
        <div className="prose-custom">
          <MDXRemote source={post.content} components={mdxComponents} />
        </div>

        {/* Author Bio */}
        <div className="mt-12 p-6 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)]">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] font-semibold">
              {post.author.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)]">{post.author}</h3>
              {post.authorTwitter && (
                <a
                  href={`https://x.com/${post.authorTwitter.replace('@', '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  {post.authorTwitter}
                </a>
              )}
              <p className="text-sm text-[var(--text-muted)] mt-2">
                Building ggbots.ai — AI-autonomous trading agents that think, adapt, and execute 24/7.
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-8 text-center">
          <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-3">
            Ready to try vibe trading?
          </h2>
          <p className="text-[var(--text-secondary)] mb-6">
            Build your first AI trading bot in 2 minutes. Start free with 20 AI decisions per day.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/signup"
              className="inline-block bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Get Started Free
            </Link>
            <Link
              href="/arena"
              className="inline-block border border-[var(--border)] hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Watch Live Bots
            </Link>
          </div>
        </div>
      </article>
    </>
  )
}
