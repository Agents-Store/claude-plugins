# NextAuth v4 and Auth.js v5 for Existing Projects

For codebases that already run NextAuth, and for a credentials login against an existing token API. New projects should start with Better Auth (see `SKILL.md`). The proxy, DAL, Server Action and Route Handler layering in `SKILL.md` is library independent: only the session helper changes.

## NextAuth v4 (`next-auth@latest`, 4.24.x)

A working path with Next.js 16, not a deprecated one: v4 is still what `npm i next-auth` installs (v5 is published only as `next-auth@beta`). The recipe below signs users in against Directus with the Credentials provider and keeps the Directus tokens in the encrypted session cookie; swap the three `fetch` calls for another token-issuing API. The Directus side (payloads, `expires` in milliseconds, single-use refresh tokens) is in the `directus-dev` plugin, skill `sdk-patterns`, `references/ssr-client.md`.

```bash
npm install next-auth
```

```bash
# .env.local: generate the secret with: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<random-string>
DIRECTUS_URL=<address-of-your-directus>
```

```typescript
// lib/auth.ts
import type { NextAuthOptions } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';

type TokenResponse = { access_token: string; refresh_token: string; expires: number };

async function refreshTokens(token: JWT): Promise<JWT> {
  const res = await fetch(`${process.env.DIRECTUS_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: token.refreshToken, mode: 'json' }),
  });
  if (!res.ok) return { ...token, error: 'RefreshTokenError' };
  const { data }: { data: TokenResponse } = await res.json();
  return {
    ...token,
    accessToken: data.access_token,
    refreshToken: data.refresh_token, // the old refresh token is now dead
    expiresAt: Date.now() + data.expires,
    error: undefined,
  };
}

export const authOptions: NextAuthOptions = {
  // Keep the session no longer than the refresh token lives (Directus default: 7 days)
  session: { strategy: 'jwt', maxAge: 7 * 24 * 60 * 60 },
  providers: [
    CredentialsProvider({
      name: 'Directus',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials.password) return null;

        const login = await fetch(`${process.env.DIRECTUS_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: credentials.email, password: credentials.password, mode: 'json' }),
        });
        if (!login.ok) return null;
        const { data }: { data: TokenResponse } = await login.json();

        const meRes = await fetch(`${process.env.DIRECTUS_URL}/users/me?fields=id,email,first_name,last_name`, {
          headers: { Authorization: `Bearer ${data.access_token}` },
        });
        if (!meRes.ok) return null;
        const { data: me } = await meRes.json();

        return {
          id: me.id,
          email: me.email,
          name: `${me.first_name ?? ''} ${me.last_name ?? ''}`.trim(),
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          expiresAt: Date.now() + data.expires,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // First call after sign-in: `user` is what authorize() returned
      if (user) {
        return { ...token, accessToken: user.accessToken, refreshToken: user.refreshToken, expiresAt: user.expiresAt };
      }
      if (Date.now() < token.expiresAt - 10_000) return token;
      return refreshTokens(token);
    },
    async session({ session, token }) {
      session.user.id = token.sub ?? '';
      session.accessToken = token.accessToken; // visible to browser code through useSession(): see below
      session.error = token.error;
      return session;
    },
  },
  pages: { signIn: '/login' },
};
```

```typescript
// types/next-auth.d.ts
import type { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface User {
    accessToken: string;
    refreshToken: string;
    expiresAt: number;
  }
  interface Session {
    user: { id: string } & DefaultSession['user'];
    accessToken: string;
    error?: 'RefreshTokenError';
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken: string;
    refreshToken: string;
    expiresAt: number;
    error?: 'RefreshTokenError';
  }
}
```

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
```

```tsx
// app/providers.tsx
'use client';
import { SessionProvider } from 'next-auth/react';

export default function Providers({ children }: { children: React.ReactNode }) {
  // refetchInterval (seconds) must be shorter than the access token lifetime, see "Limits" below
  return (
    <SessionProvider refetchInterval={4 * 60} refetchOnWindowFocus>
      {children}
    </SessionProvider>
  );
}
```

Wrap `children` in `app/layout.tsx` with `<Providers>`. The session helpers used by the rest of the app:

```typescript
// lib/session.ts
import 'server-only';
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '@/lib/auth';

/** The signed-in session, or a redirect to /login. Call it first in every Server Action and Route Handler. */
export async function requireUser() {
  const session = await getServerSession(authOptions);
  if (!session?.user || session.error) redirect('/login');
  return session;
}
```

### Proxy guard (Next.js 16)

`middleware.ts` is deprecated in Next.js 16; the file is `proxy.ts` and the function is `proxy`. `getToken` decodes the session cookie without a database or network call, so it is safe to use there:

```typescript
// proxy.ts
import { getToken } from 'next-auth/jwt';
import { NextResponse, type NextRequest } from 'next/server';

export async function proxy(request: NextRequest) {
  const token = await getToken({ req: request });
  if (!token || token.error) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = { matcher: ['/dashboard/:path*', '/admin/:path*'] };
```

This is an optimistic check, as everywhere in this skill: pages, Server Actions and Route Handlers still call `requireUser()`.

### Login page

```tsx
// app/login/page.tsx
'use client';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const result = await signIn('credentials', {
      email: formData.get('email'),
      password: formData.get('password'),
      redirect: false,
    });
    if (result?.error) setError('Invalid email or password');
    else router.push(searchParams.get('callbackUrl') || '/dashboard');
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <input name="password" type="password" required />
      {error && <p>{error}</p>}
      <button type="submit">Sign In</button>
    </form>
  );
}
```

`useSearchParams()` in a statically rendered page needs a `<Suspense>` boundary around the component that calls it.

### Limits to know before choosing v4

- **Refreshing is saved only by the client.** `getServerSession()` called from a Server Component or Route Handler cannot write cookies, so a token refreshed there is not saved, and Directus refresh tokens are single use. What saves new tokens is the NextAuth route `/api/auth/session`, which `SessionProvider` calls on mount, on focus and every `refetchInterval`. Keep that interval clearly shorter than the access token lifetime (15 minutes by default). After a gap longer than the lifetime (a closed laptop), the first server render refreshes and spends the refresh token without saving it, the next `/api/auth/session` call finds it spent, and the session ends with `RefreshTokenError`: the user signs in again.
- **The access token is readable in the browser.** `session.accessToken` is returned by `/api/auth/session` and `useSession()`. It is short-lived and belongs to the signed-in user, and the refresh token stays inside the encrypted cookie, but any script running in the page can read it. If that is not acceptable, do not copy it into `session`; call the API only from server code with a server credential.
- **No rate limit.** NextAuth does not throttle credential sign-ins. Put a limit in front of `/api/auth/callback/credentials`.

## Auth.js v5 (`next-auth@beta`)

> Auth.js v5 is still published as `next-auth@beta` and the project is in maintenance mode under Better Auth. Prefer Better Auth for new work; use this section when maintaining an Auth.js codebase.

```bash
npm install next-auth@beta
```

```typescript
// auth.ts
import NextAuth from 'next-auth'
import GitHub from 'next-auth/providers/github'

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [GitHub],
})
```

```typescript
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth'
export const { GET, POST } = handlers
```

```tsx
// Usage in Server Components
import { auth } from '@/auth'

export default async function Page() {
  const session = await auth()
  if (!session?.user) return <p>Not signed in</p>
  return <p>Welcome, {session.user.name}</p>
}
```

v5 uses the `AUTH_` prefix for its settings (`AUTH_SECRET`, `AUTH_URL`); the examples above for v4 use `NEXTAUTH_SECRET` and `NEXTAUTH_URL`.
