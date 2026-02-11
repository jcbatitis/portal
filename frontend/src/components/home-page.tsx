import { useLoaderData } from "react-router"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface UserData {
  userId: number
  username: string
}

export async function homeLoader(): Promise<UserData> {
  const res = await fetch("/api/me", { credentials: "include" })
  if (!res.ok) throw new Response("Unauthorized", { status: 401 })
  return res.json()
}

export function HomePage() {
  const user = useLoaderData() as UserData

  async function handleLogout() {
    await fetch("/api/logout", {
      method: "POST",
      credentials: "include",
    })
    window.location.href = "/"
  }

  const initial = user.username.charAt(0).toUpperCase()

  return (
    <div className="relative flex min-h-svh flex-col overflow-hidden">
      {/* Toolbar */}
      <header className="relative z-10 flex h-14 shrink-0 items-center justify-between border-b border-border px-5">
        {/* Left — Branding */}
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 ring-1 ring-primary/20">
            <svg
              viewBox="0 0 16 16"
              fill="none"
              className="h-3.5 w-3.5 text-primary"
              aria-hidden="true"
            >
              <path
                d="M8 1L14.5 5v6L8 15L1.5 11V5L8 1Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M8 5.5L11 7.5v3L8 12.5L5 10.5v-3L8 5.5Z"
                fill="currentColor"
                opacity="0.4"
              />
            </svg>
          </div>
          <span className="text-sm font-medium tracking-wide text-muted-foreground">
            Portal
          </span>
        </div>

        {/* Right — User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary ring-1 ring-primary/20 transition-colors hover:bg-primary/20 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/40"
              aria-label="User menu"
            >
              {initial}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-0">
            <DropdownMenuItem
              onClick={handleLogout}
              className="cursor-pointer px-3 py-2 text-xs"
            >
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Main content */}
      <main className="relative flex flex-1 items-center justify-center px-4">
        {/* Radial glow — same as login page */}
        <div
          className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
          aria-hidden="true"
        >
          <div className="h-[600px] w-[600px] rounded-full bg-primary/[0.03] blur-[120px]" />
        </div>

        <div className="relative w-full max-w-[340px]">
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
              Dashboard
            </p>
            <h1 className="text-2xl font-semibold tracking-tight">
              Welcome back, {user.username}
            </h1>
            <p className="text-sm text-muted-foreground">
              You're signed in and ready to go.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
