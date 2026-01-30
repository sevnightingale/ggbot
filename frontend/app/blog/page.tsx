import Link from 'next/link'
import { getAllPosts } from '@/lib/blog'
import { Calendar, Clock, User } from 'lucide-react'

export default function BlogPage() {
  const posts = getAllPosts()

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl font-display font-semibold text-[var(--text-primary)] mb-4">
          Blog
        </h1>
        <p className="text-lg text-[var(--text-secondary)]">
          Learn about vibe trading, AI-autonomous trading, and building trading bots.
        </p>
      </div>

      {/* Posts List */}
      {posts.length === 0 ? (
        <div className="text-center py-16 text-[var(--text-muted)]">
          <p>No posts yet. Check back soon!</p>
        </div>
      ) : (
        <div className="space-y-8">
          {posts.map((post) => (
            <article
              key={post.slug}
              className="group rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6 hover:border-[var(--border-hover)] transition-colors"
            >
              <Link href={`/blog/${post.slug}`}>
                <h2 className="text-2xl font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors mb-3">
                  {post.title}
                </h2>
                <p className="text-[var(--text-secondary)] mb-4 line-clamp-2">
                  {post.description}
                </p>
                <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--text-muted)]">
                  <span className="flex items-center gap-1.5">
                    <User className="h-4 w-4" />
                    {post.author}
                  </span>
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
              </Link>
            </article>
          ))}
        </div>
      )}

      {/* CTA */}
      <div className="mt-16 rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-8 text-center">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-3">
          Ready to build your first vibe trading bot?
        </h2>
        <p className="text-[var(--text-secondary)] mb-6">
          Start free with 20 AI decisions per day. No credit card required.
        </p>
        <Link
          href="/signup"
          className="inline-block bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] font-medium px-6 py-3 rounded-lg transition-colors"
        >
          Get Started Free
        </Link>
      </div>
    </div>
  )
}
