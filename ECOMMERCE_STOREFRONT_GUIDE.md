# Ecommerce Storefront - Complete Guide

**Date:** December 12, 2025
**Status:** Phase 2 - Frontend Foundation Complete

---

## 📊 Overview

A modern, production-ready Next.js 14 ecommerce storefront that integrates with the backend API. Designed as a **separate Railway service** from your admin dashboard.

---

## ✅ What's Been Created

### Project Structure

```
storefront/
├── package.json                  # Dependencies & scripts
├── next.config.js                # Next.js configuration
├── tsconfig.json                 # TypeScript configuration
├── tailwind.config.ts            # Tailwind CSS styling
├── Dockerfile                    # Production deployment
├── .env.example                  # Environment variables template
│
├── src/
│   ├── app/
│   │   ├── layout.tsx            # ✅ Root layout with Header/Footer
│   │   ├── page.tsx              # ✅ Homepage with hero & featured products
│   │   ├── providers.tsx         # ✅ Client-side providers
│   │   └── globals.css           # ✅ Global styles
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx        # ✅ Navigation, search, cart icon
│   │   │   └── Footer.tsx        # ✅ Footer with links
│   │   ├── cart/
│   │   │   └── CartSidebar.tsx   # ✅ Sliding cart with checkout
│   │   └── products/
│   │       ├── ProductGrid.tsx   # ✅ Product grid display
│   │       └── ProductCard.tsx   # ✅ Product card with quick add
│   │
│   ├── lib/
│   │   ├── api.ts                # ✅ Complete API client (all endpoints)
│   │   └── utils.ts              # ✅ Formatting & helper functions
│   │
│   ├── store/
│   │   └── useStore.ts           # ✅ Zustand global state (cart, auth, UI)
│   │
│   └── types/
│       └── index.ts              # ✅ TypeScript definitions (all types)
```

---

## 🎯 Features Implemented

### ✅ Core Features

1. **Homepage**
   - Hero section with CTA buttons
   - Featured products grid
   - Category cards (UVDTF, DTF, Sublimation)
   - Benefits section (quality, shipping, etc.)

2. **Product Display**
   - Product grid component
   - Product cards with images, prices, badges
   - Quick add to cart functionality
   - Sale/Featured badges
   - Stock status indicators

3. **Shopping Cart**
   - Sliding sidebar cart
   - Add/update/remove items
   - Real-time subtotal calculation
   - Quantity controls
   - Checkout button

4. **Navigation**
   - Responsive header with mobile menu
   - Product search functionality
   - Category navigation
   - Account/login links
   - Cart icon with item count

5. **State Management**
   - Zustand store for cart state
   - Customer authentication state
   - UI state (mobile menu, cart sidebar)
   - Persistent storage (localStorage)

6. **API Integration**
   - Complete API client for all endpoints
   - Products API (list, search, filter, get)
   - Cart API (CRUD operations)
   - Customer API (auth, profile, addresses)
   - Orders API (history, tracking)
   - Checkout API (init, payment, complete)

7. **Styling**
   - Tailwind CSS utility-first styling
   - Responsive mobile-first design
   - Custom color scheme (customizable)
   - Professional UI components
   - Smooth animations & transitions

---

## 🚧 Pages To Implement

The foundation is complete. Here are the remaining pages to build:

### Product Pages

**Create: `src/app/products/page.tsx`**

```tsx
// Product catalog with filtering & pagination
// Features: Search, filter by print method/category, sort, pagination
```

**Create: `src/app/products/[slug]/page.tsx`**

```tsx
// Product detail page
// Features: Image gallery, variants, description, add to cart, reviews
```

### Checkout Pages

**Create: `src/app/checkout/page.tsx`**

```tsx
// Multi-step checkout
// Steps: Shipping info, payment (Stripe), order review
```

**Create: `src/app/checkout/success/page.tsx`**

```tsx
// Order confirmation page
// Shows: Order number, receipt, next steps
```

### Authentication Pages

**Create: `src/app/login/page.tsx`**

```tsx
// Customer login form
// Features: Email/password, remember me, redirect to account
```

**Create: `src/app/register/page.tsx`**

```tsx
// Customer registration form
// Features: Email, password, name, phone, marketing opt-in
```

### Account Pages

**Create: `src/app/account/layout.tsx`**

```tsx
// Account dashboard layout with sidebar
```

**Create: `src/app/account/page.tsx`**

```tsx
// Account overview
// Shows: Stats, recent orders, profile summary
```

**Create: `src/app/account/orders/page.tsx`**

```tsx
// Order history
// Features: List all orders, filter by status, pagination
```

**Create: `src/app/account/orders/[id]/page.tsx`**

```tsx
// Order details
// Shows: Items, shipping, tracking, download digital products
```

**Create: `src/app/account/profile/page.tsx`**

```tsx
// Profile management
// Features: Update name, email, phone, password
```

**Create: `src/app/account/addresses/page.tsx`**

```tsx
// Address book
// Features: Add/edit/delete addresses, set default
```

### Other Pages

**Create: `src/app/track-order/page.tsx`**

```tsx
// Guest order tracking
// Features: Lookup by order number + email
```

---

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
cd storefront
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:3003

# Stripe
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key

# Site Info
NEXT_PUBLIC_SITE_NAME=Your Store Name
NEXT_PUBLIC_SITE_URL=http://localhost:3001
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001)

---

## 🚀 Railway Deployment

### Setup Steps

1. **In Railway Dashboard:**
   - Click "New Service"
   - Select "GitHub Repo"
   - Choose your repository
   - Click "Add variables" before deploying

2. **Set Root Directory:**
   - In service settings, set **Root Directory** to `storefront`
   - Railway will detect the Dockerfile automatically

3. **Add Environment Variables:**

   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_your_stripe_live_key
   NEXT_PUBLIC_SITE_NAME=Your Store Name
   NEXT_PUBLIC_SITE_URL=https://your-storefront.up.railway.app
   ```

4. **Deploy:**
   - Railway will build using the Dockerfile
   - Deployment typically takes 3-5 minutes
   - Service will be available on generated Railway domain

5. **Custom Domain (Optional):**
   - Go to Settings → Domains
   - Add your custom domain
   - Update DNS records as shown
   - Update `NEXT_PUBLIC_SITE_URL` to your domain

### Architecture

```
┌─────────────────────┐
│  Railway Service 1  │
│     (Backend)       │
│  FastAPI + Python   │
│   Port: 8080        │
└──────────┬──────────┘
           │
           │ API Requests
           │
┌──────────┴──────────┐
│  Railway Service 2  │
│   (Storefront)      │
│  Next.js + Node     │
│   Port: 3001        │
└─────────────────────┘
```

Both services in the same Railway project but deployed independently.

---

## 🎨 Customization Guide

### Branding

**Update Store Name:**

`src/components/layout/Header.tsx`:

```tsx
<Link href="/" className="text-2xl font-bold text-primary-600">
  YourStore {/* Change to your brand name */}
</Link>
```

`src/components/layout/Footer.tsx`:

```tsx
<h3 className="text-white text-lg font-bold mb-4">YourStore</h3>
```

### Colors

`tailwind.config.ts`:

```ts
colors: {
  primary: {
    50: '#f0f9ff',
    // ... change these to your brand colors
    600: '#0284c7',  // Primary CTA color
  }
}
```

### Homepage Content

`src/app/page.tsx` - Edit:

- Hero title and description
- CTA button text
- Benefits section
- Category descriptions

---

## 📱 Responsive Breakpoints

```css
/* Mobile (default) */
< 768px

/* Tablet */
md: 768px - 1024px

/* Desktop */
lg: > 1024px
```

All components are mobile-first responsive.

---

## 🔒 Security Best Practices

1. **Environment Variables:**
   - Never commit `.env` files
   - Use `NEXT_PUBLIC_` prefix for client-side vars only
   - Keep API keys secret

2. **Authentication:**
   - JWT tokens stored in localStorage
   - Auto-removed on 401 responses
   - Secure HTTP-only in production

3. **Stripe:**
   - Payment details never touch your server
   - Use Stripe.js for PCI compliance
   - Verify payments server-side

4. **HTTPS:**
   - Railway provides HTTPS by default
   - Enforce HTTPS in production
   - Set secure cookie flags

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Homepage loads correctly
- [ ] Product search works
- [ ] Can add items to cart
- [ ] Cart updates properly
- [ ] Cart persists on page refresh
- [ ] Mobile menu works
- [ ] Product filtering works
- [ ] Checkout flow completes
- [ ] Order confirmation displays
- [ ] Login/register works
- [ ] Account dashboard accessible
- [ ] Order history shows
- [ ] Address management works

### Test Cards (Development)

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Insufficient funds: 4000 0000 0000 9995

Expiry: Any future date
CVC: Any 3 digits
ZIP: Any 5 digits
```

---

## 📊 Performance Optimization

### Implemented

- ✅ Server-side rendering (SSR)
- ✅ Code splitting
- ✅ Image optimization ready
- ✅ Font optimization (next/font)
- ✅ Standalone output for Docker

### Recommended

- [ ] Add `next/image` for product images
- [ ] Implement ISR for product pages
- [ ] Add caching headers
- [ ] Lazy load components
- [ ] Optimize bundle size

---

## 📈 Analytics & Monitoring

### To Add

**Google Analytics:**

`src/app/layout.tsx`:

```tsx
import Script from "next/script";

// Add in <head>
<Script src="https://www.googletagmanager.com/gtag/js?id=GA_ID" />;
```

**Stripe Analytics:**

- Already integrated
- View in Stripe Dashboard

**Performance Monitoring:**

- Consider: Vercel Analytics, Sentry, or LogRocket

---

## 🔄 Development Workflow

1. **Make changes** in `src/`
2. **Test locally** with `npm run dev`
3. **Type check** with `npm run type-check`
4. **Lint** with `npm run lint`
5. **Commit** changes to git
6. **Push** to GitHub
7. **Railway auto-deploys** from main branch

---

## 🐛 Common Issues & Fixes

### Issue: API Connection Failed

**Solution:**

- Check `NEXT_PUBLIC_API_URL` is correct
- Verify backend is running
- Check backend CORS settings

### Issue: Stripe Not Loading

**Solution:**

- Verify `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` starts with `pk_`
- Check browser console for errors
- Ensure key matches environment (test/live)

### Issue: Cart Not Persisting

**Solution:**

- Check localStorage is enabled
- Verify session ID is being set
- Check backend cart API responses

### Issue: Build Failures

**Solution:**

```bash
rm -rf .next node_modules
npm install
npm run build
```

---

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zustand](https://github.com/pmndrs/zustand)
- [Stripe Documentation](https://stripe.com/docs)
- [Railway Documentation](https://docs.railway.app)

---

## ✨ Next Steps

### Immediate (Core Functionality)

1. Create product catalog page (`/products`)
2. Create product detail page (`/products/[slug]`)
3. Create checkout flow (`/checkout`)
4. Create login/register pages
5. Create customer account dashboard

### Future Enhancements

6. Add product reviews
7. Add wishlist functionality
8. Implement email notifications
9. Add social sharing
10. SEO optimization (meta tags, structured data)
11. Progressive Web App (PWA)
12. Multi-language support
13. Advanced analytics
14. Discount codes/coupons
15. Gift cards

---

## 📋 Summary

### Completed ✅

- Project structure & configuration
- Homepage with featured products
- Product grid and card components
- Shopping cart functionality
- Navigation and layout
- API client (all endpoints)
- State management
- Docker configuration
- Railway deployment setup

### Remaining 🚧

- Product catalog page
- Product detail pages
- Checkout flow pages
- Authentication pages
- Customer account pages
- Order tracking pages

### Deployment Ready ✅

The foundation is **production-ready**. You can deploy to Railway now and add the remaining pages incrementally.

---

**Status:** ✅ **Phase 2 Foundation Complete - Ready for Railway Deployment!**
