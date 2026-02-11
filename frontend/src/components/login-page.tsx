import { useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      })

      if (res.ok) {
        window.location.href = "/home"
        return
      }

      if (res.status === 401) {
        setError("Invalid credentials")
      } else if (res.status === 429) {
        setError("Too many attempts, please try again later")
      } else {
        setError("Something went wrong")
      }
    } catch {
      setError("Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-hidden px-4">
      {/* Subtle radial glow behind the form */}
      <div
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
        aria-hidden="true"
      >
        <div className="h-[600px] w-[600px] rounded-full bg-primary/[0.03] blur-[120px]" />
      </div>

      <div className="relative w-full max-w-[340px]">
        {/* Header */}
        <div className="mb-10 space-y-2">
          <div className="mb-6 flex items-center gap-2.5">
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
          <h1 className="text-2xl font-semibold tracking-tight">
            Sign in
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter your credentials to continue
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <Label
              htmlFor="username"
              className="font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground"
            >
              Username
            </Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoComplete="username"
              required
              className="h-10 border-0 bg-secondary/60 font-mono text-sm placeholder:text-muted-foreground/40 focus-visible:ring-1 focus-visible:ring-primary/50"
            />
          </div>
          <div className="space-y-1.5">
            <Label
              htmlFor="password"
              className="font-mono text-[11px] font-medium uppercase tracking-widest text-muted-foreground"
            >
              Password
            </Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
              className="h-10 border-0 bg-secondary/60 font-mono text-sm placeholder:text-muted-foreground/40 focus-visible:ring-1 focus-visible:ring-primary/50"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2">
              <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
              <p className="text-xs text-destructive">{error}</p>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="h-10 w-full font-medium tracking-wide transition-all duration-200"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2" opacity="0.25" />
                  <path d="M14 8a6 6 0 00-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Signing in
              </span>
            ) : (
              "Continue"
            )}
          </Button>
        </form>

        {/* Footer */}
        {false && (
          <div className="mt-8 border-t border-border pt-5">
            <p className="text-center font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground/50">
              Secure authentication
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
