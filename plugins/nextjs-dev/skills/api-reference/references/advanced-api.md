# Advanced Next.js API Reference

Extended API reference for core components, middleware, image loading, font configuration, and advanced config options.

## Table of Contents

- [Image Component](#image-component)
- [Font Optimization](#font-optimization)
- [Script Component](#script-component)
- [next.config.ts Key Options](#nextconfigts-key-options)
- [Middleware API](#middleware-api)
- [Image Loader Configuration](#image-loader-configuration)
- [Font Configuration](#font-configuration)
- [Advanced next.config.ts Options](#advanced-nextconfigts-options)

## Image Component

```tsx
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero image"
  width={800}
  height={400}
  priority           // Load eagerly (for above-the-fold)
  placeholder="blur" // Show blur while loading (requires blurDataURL for remote)
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

## Font Optimization

```tsx
import { Inter, Roboto_Mono } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], display: 'swap' })
const robotoMono = Roboto_Mono({ subsets: ['latin'], variable: '--font-mono' })

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.className} ${robotoMono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

## Script Component

```tsx
import Script from 'next/script'

<Script src="https://analytics.example.com/script.js" strategy="afterInteractive" />
```

Strategies: `beforeInteractive`, `afterInteractive` (default), `lazyOnload`, `worker`.

## next.config.ts Key Options

```ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.example.com' },
    ],
  },
  async redirects() {
    return [{ source: '/old', destination: '/new', permanent: true }]
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: 'https://backend.example.com/:path*' }]
  },
  async headers() {
    return [{ source: '/:path*', headers: [{ key: 'X-Frame-Options', value: 'DENY' }] }]
  },
  output: 'standalone',
  env: { CUSTOM_KEY: 'value' },
}

export default nextConfig
```

## Cache & Revalidation Functions

### `revalidatePath(path, type?)`

```tsx
import { revalidatePath } from 'next/cache'

revalidatePath('/posts')          // Revalidate specific path
revalidatePath('/posts', 'layout') // Revalidate layout and all child pages
revalidatePath('/', 'layout')      // Revalidate everything
```

### `revalidateTag(tag)`

```tsx
import { revalidateTag } from 'next/cache'

revalidateTag('posts')
```

### `unstable_cache()` (deprecated in 16+, use `use cache`)

```tsx
import { unstable_cache } from 'next/cache'

const getCachedUser = unstable_cache(
  async (id: string) => db.user.findUnique({ where: { id } }),
  ['user'],
  { revalidate: 3600, tags: ['user'] }
)
```

## Middleware API

### `NextRequest`

Extends the standard `Request` with additional properties:

| Property | Type | Description |
|----------|------|-------------|
| `nextUrl` | `NextURL` | Parsed URL with Next.js specific properties |
| `cookies` | `RequestCookies` | Cookie access |
| `geo` | `{ city, country, region, latitude, longitude }` | Geolocation (Vercel only) |
| `ip` | `string` | Client IP address |

### `NextResponse`

| Method | Description |
|--------|-------------|
| `NextResponse.next()` | Continue to the next middleware or route |
| `NextResponse.redirect(url)` | Redirect to a different URL |
| `NextResponse.rewrite(url)` | Rewrite request to a different URL (URL stays the same) |
| `NextResponse.json(data)` | Return a JSON response |

### Middleware Matcher

```ts
export const config = {
  matcher: [
    // Match specific paths
    '/dashboard/:path*',
    '/api/:path*',
    // Match all except static files and _next
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
```

### Setting Cookies in Middleware

```ts
export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  response.cookies.set('visited', 'true', {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24, // 1 day
  })
  return response
}
```

### Setting Headers in Middleware

```ts
export function middleware(request: NextRequest) {
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-request-id', crypto.randomUUID())

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })
  response.headers.set('x-response-time', Date.now().toString())
  return response
}
```

## Image Loader Configuration

### Remote Patterns

```ts
// next.config.ts
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.example.com',  // Wildcard subdomain
        port: '',
        pathname: '/images/**',
      },
    ],
    // Image sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    // Formats
    formats: ['image/avif', 'image/webp'],
    // Custom loader
    loader: 'custom',
    loaderFile: './lib/image-loader.ts',
  },
}
```

### Custom Image Loader

```ts
// lib/image-loader.ts
export default function cloudinaryLoader({
  src,
  width,
  quality,
}: {
  src: string
  width: number
  quality?: number
}) {
  const params = ['f_auto', 'c_limit', `w_${width}`, `q_${quality || 'auto'}`]
  return `https://res.cloudinary.com/demo/image/upload/${params.join(',')}${src}`
}
```

## Font Configuration

### Local Fonts

```tsx
import localFont from 'next/font/local'

const myFont = localFont({
  src: [
    { path: './fonts/MyFont-Regular.woff2', weight: '400', style: 'normal' },
    { path: './fonts/MyFont-Bold.woff2', weight: '700', style: 'normal' },
    { path: './fonts/MyFont-Italic.woff2', weight: '400', style: 'italic' },
  ],
  display: 'swap',
  variable: '--font-my-font',
})
```

### Font Options

| Option | Type | Description |
|--------|------|-------------|
| `subsets` | `string[]` | Character subsets (`'latin'`, `'cyrillic'`, etc.) |
| `weight` | `string \| string[]` | Font weights (`'400'`, `['400', '700']`) |
| `style` | `string \| string[]` | Font styles (`'normal'`, `'italic'`) |
| `display` | `string` | CSS `font-display` (`'swap'`, `'block'`, `'fallback'`, `'optional'`) |
| `variable` | `string` | CSS variable name (`'--font-sans'`) |
| `preload` | `boolean` | Whether to preload (default: `true`) |
| `adjustFontFallback` | `boolean` | Adjust fallback font metrics (default: `true`) |

## Advanced next.config.ts Options

### Turbopack Configuration

```ts
const nextConfig = {
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
    resolveAlias: {
      underscore: 'lodash',
    },
  },
}
```

### Webpack Configuration

```ts
const nextConfig = {
  webpack: (config, { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }) => {
    config.plugins.push(new webpack.DefinePlugin({ 'process.env.BUILD_ID': JSON.stringify(buildId) }))
    return config
  },
}
```

### Instrumentation

```ts
// instrumentation.ts (project root)
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Initialize server-side monitoring (e.g., Sentry, OpenTelemetry)
  }
}
```

### Security Headers

```ts
const securityHeaders = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
]

const nextConfig = {
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }]
  },
}
```

### Content Security Policy

```ts
// middleware.ts
import { NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const csp = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic';
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
  `.replace(/\n/g, '')

  const response = NextResponse.next()
  response.headers.set('Content-Security-Policy', csp)
  response.headers.set('x-nonce', nonce)
  return response
}
```
