This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

# TutorMax Frontend (Next.js 15)

Modern frontend for the TutorMax Tutor Performance Evaluation Platform built with:
- **Next.js 15** with App Router
- **Tailwind CSS v4** for styling
- **shadcn/ui** component library
- **TypeScript** for type safety

## Prerequisites

- Node.js 18+ and pnpm
- Backend API running on `http://localhost:8000` (see main project README)
- PostgreSQL database with users created

## Setup

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```

   See [ENV_SETUP.md](./ENV_SETUP.md) for detailed environment variable documentation.

3. **Run the development server:**
   ```bash
   pnpm dev
   ```

4. **Open the app:**
   - Open [http://localhost:3000](http://localhost:3000) in your browser
   - Login page: [http://localhost:3000/login](http://localhost:3000/login)
   - User management (admin only): [http://localhost:3000/users](http://localhost:3000/users)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with AuthProvider
│   ├── page.tsx           # Home page
│   ├── login/
│   │   └── page.tsx       # Login page
│   ├── users/
│   │   └── page.tsx       # User management (admin)
│   └── dashboard/
│       └── page.tsx       # Dashboard (in progress)
├── components/
│   └── ui/                # shadcn/ui components
├── contexts/
│   ├── AuthContext.tsx    # Authentication context
│   └── index.tsx
├── hooks/
│   ├── useWebSocket.ts    # WebSocket hook for real-time data
│   └── index.ts
├── lib/
│   ├── api.ts             # API client with JWT auth
│   ├── websocket.ts       # WebSocket service
│   ├── types.ts           # TypeScript types
│   └── utils.ts
└── public/
```

## Features

- ✅ **Authentication**: JWT-based login/logout with role-based access control
- ✅ **User Management**: Admin dashboard for managing users and roles
- ✅ **Real-time Updates**: WebSocket integration for live dashboard data
- ✅ **Role-Based UI**: Components adapt based on user roles (Admin, Ops Manager, Tutor, Student)
- ✅ **Modern UI**: shadcn/ui components with Tailwind CSS
- ⏳ **Dashboard**: Real-time tutor performance metrics (in progress)
- ⏳ **Tutor Portal**: Performance tracking for tutors (planned)

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint
- `pnpm type-check` - Run TypeScript compiler check

## Environment Variables

See [ENV_SETUP.md](./ENV_SETUP.md) for complete environment variable documentation.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
