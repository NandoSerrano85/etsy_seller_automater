# Ecommerce Storefront

Modern, customer-facing ecommerce storefront built with Next.js 14, TypeScript, and Tailwind CSS.

## 🚀 Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Payment:** Stripe
- **HTTP Client:** Axios
- **Icons:** Lucide React
- **Notifications:** React Hot Toast

## 📋 Features

- ✅ Server-side rendering for SEO
- ✅ Product catalog with filtering & search
- ✅ Shopping cart with real-time updates
- ✅ Customer authentication (JWT)
- ✅ Stripe payment integration
- ✅ Customer account dashboard
- ✅ Order tracking
- ✅ Responsive design (mobile-first)
- ✅ Optimized images
- ✅ Fast page loads

## 🏗️ Project Structure

```
storefront/
├── src/
│   ├── app/                    # Next.js 14 app directory
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Homepage
│   │   ├── products/           # Product pages
│   │   ├── checkout/           # Checkout flow
│   │   ├── account/            # Customer dashboard
│   │   └── login/              # Authentication
│   ├── components/             # Reusable components
│   │   ├── layout/             # Header, Footer
│   │   ├── products/           # Product cards, grids
│   │   ├── cart/               # Cart sidebar
│   │   └── checkout/           # Checkout components
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Helper functions
│   ├── store/                  # Zustand state management
│   │   └── useStore.ts         # Global store
│   └── types/                  # TypeScript types
│       └── index.ts            # Type definitions
├── public/                     # Static assets
├── .env.example                # Environment variables template
├── Dockerfile                  # Production Docker build
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
└── package.json                # Dependencies

```

## 🛠️ Setup

### Prerequisites

- Node.js 18+ installed
- Backend API running (see main project README)

### Installation

1. **Navigate to storefront directory:**

   ```bash
   cd storefront
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local`:

   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:3003
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
   NEXT_PUBLIC_SITE_NAME=Your Store Name
   NEXT_PUBLIC_SITE_URL=http://localhost:3001
   ```

4. **Run development server:**

   ```bash
   npm run dev
   ```

   Open [http://localhost:3001](http://localhost:3001)

## 🌐 Pages

### Public Pages

- `/` - Homepage with featured products
- `/products` - Product catalog
- `/products/[slug]` - Product detail page
- `/login` - Customer login
- `/register` - Customer registration
- `/track-order` - Guest order tracking

### Protected Pages (Require Authentication)

- `/account` - Customer dashboard
- `/account/orders` - Order history
- `/account/addresses` - Saved addresses
- `/account/profile` - Profile settings
- `/checkout` - Checkout flow

## 🔧 API Integration

The storefront communicates with the backend API at `NEXT_PUBLIC_API_URL`. All API calls are handled in `src/lib/api.ts`:

- **Products:** Browse, search, filter
- **Cart:** Add, update, remove items
- **Customers:** Register, login, profile management
- **Orders:** View history, track orders
- **Checkout:** Initialize, payment, completion

## 💳 Stripe Integration

### Setup

1. Get Stripe public key from dashboard
2. Add to `.env.local`:
   ```bash
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...
   ```

### Payment Flow

1. Customer adds items to cart
2. Proceeds to checkout
3. Frontend calls backend `/api/storefront/checkout/init`
4. Backend returns checkout session with total
5. Frontend calls backend `/api/storefront/checkout/create-payment-intent`
6. Frontend displays Stripe payment form
7. Customer completes payment with Stripe.js
8. Frontend calls backend `/api/storefront/checkout/complete`
9. Order created, cart cleared

## 🎨 Customization

### Branding

Edit `storefront/src/components/layout/Header.tsx`:

```tsx
<Link href="/" className="text-2xl font-bold text-primary-600">
  YourStore {/* Change this */}
</Link>
```

### Colors

Edit `tailwind.config.ts` to customize colors:

```ts
colors: {
  primary: {
    500: '#0ea5e9',  // Change primary color
    600: '#0284c7',
    // ...
  }
}
```

### Homepage Content

Edit `src/app/page.tsx` to customize:

- Hero section text
- Featured products
- Categories
- Benefits section

## 🚀 Deployment

### Railway Deployment

1. **Create new service in Railway:**
   - Click "New Service"
   - Select "GitHub Repo"
   - Choose your repository
   - Set root directory to `storefront/`

2. **Set environment variables in Railway:**

   ```
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_your_live_key
   NEXT_PUBLIC_SITE_NAME=Your Store Name
   NEXT_PUBLIC_SITE_URL=https://your-storefront.up.railway.app
   ```

3. **Railway will automatically:**
   - Detect the Dockerfile
   - Build the container
   - Deploy on port 3001

### Custom Domain

1. In Railway, go to Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `NEXT_PUBLIC_SITE_URL` to your domain

## 📦 Building for Production

```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Docker Build

```bash
# Build Docker image
docker build -t ecommerce-storefront .

# Run container
docker run -p 3001:3001 \
  -e NEXT_PUBLIC_API_URL=http://localhost:3003 \
  -e NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_... \
  ecommerce-storefront
```

## 🧪 Development

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## 📝 Environment Variables

| Variable                        | Description            | Example                      |
| ------------------------------- | ---------------------- | ---------------------------- |
| `NEXT_PUBLIC_API_URL`           | Backend API URL        | `https://api.yourstore.com`  |
| `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_live_...`                |
| `NEXT_PUBLIC_SITE_NAME`         | Store name             | `Your Store`                 |
| `NEXT_PUBLIC_SITE_URL`          | Storefront URL         | `https://shop.yourstore.com` |

## 🔐 Security

- All sensitive API calls require authentication
- JWT tokens stored in localStorage
- Stripe payment details never touch your server
- HTTPS enforced in production
- Environment variables for sensitive data

## 📱 Responsive Design

The storefront is mobile-first and fully responsive:

- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

## 🎯 Performance

- Server-side rendering for fast initial load
- Image optimization with Next.js Image component
- Code splitting for smaller bundles
- Lazy loading for images and components
- Optimized fonts with next/font

## 🐛 Troubleshooting

### API Connection Issues

- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend is running
- Verify CORS is enabled on backend

### Stripe Issues

- Verify public key starts with `pk_`
- Check browser console for errors
- Ensure backend has matching secret key

### Build Errors

- Clear `.next` folder: `rm -rf .next`
- Delete node_modules: `rm -rf node_modules`
- Reinstall: `npm install`
- Rebuild: `npm run build`

## 📄 License

Same as main project.

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## ✨ Next Steps

After deployment, consider adding:

- [ ] Product reviews
- [ ] Wishlist functionality
- [ ] Related products
- [ ] Recently viewed items
- [ ] Social sharing
- [ ] Email marketing integration
- [ ] Analytics (Google Analytics, etc.)
- [ ] SEO optimization (meta tags, structured data)
- [ ] Progressive Web App (PWA) features
- [ ] Multi-language support

---

**Built with ❤️ using Next.js and TypeScript**
