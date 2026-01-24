import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for multi-tenant routing
 *
 * On Vercel FREE tier: Only path-based routing works (/store/[slug])
 * On Vercel PRO tier: This middleware enables custom domain routing
 *
 * How it works:
 * 1. Path-based (FREE): /store/myshop -> stays as /store/myshop
 * 2. Subdomain (PRO): myshop.yourdomain.com -> rewrites to /store/myshop
 * 3. Custom domain (PRO): customdomain.com -> rewrites to /store/slug (looked up by domain)
 */

const MAIN_DOMAIN = "craftflow.com"; // Replace with your actual domain
const PUBLIC_FILE = /\.(.*)$/;

export async function middleware(request: NextRequest) {
  const url = request.nextUrl;
  const hostname = request.headers.get("host") || "";
  const pathname = url.pathname;

  // Skip middleware for:
  // - Public files (images, fonts, etc.)
  // - Next.js internals (_next, api routes)
  // - Existing /store/ paths (already multi-tenant)
  if (
    PUBLIC_FILE.test(pathname) ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/store/")
  ) {
    return NextResponse.next();
  }

  // Extract subdomain or custom domain
  const hostParts = hostname.replace(`.${MAIN_DOMAIN}`, "").split(".");

  // Case 1: Main domain (www.craftflow.com or craftflow.com)
  if (
    hostname === MAIN_DOMAIN ||
    hostname === `www.${MAIN_DOMAIN}` ||
    hostname.includes("localhost") ||
    hostname.includes("vercel.app")
  ) {
    // Let the request through - it's accessing the main site or already a /store/ path
    return NextResponse.next();
  }

  // Case 2: Subdomain (myshop.craftflow.com) - REQUIRES PRO TIER
  if (hostParts.length === 1 && hostParts[0]) {
    const slug = hostParts[0];
    url.pathname = `/store/${slug}${pathname}`;
    return NextResponse.rewrite(url);
  }

  // Case 3: Custom domain (customershop.com) - REQUIRES PRO TIER + DOMAIN LOOKUP
  // This would require a database lookup to map domain -> store slug
  // For now, return main site
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
