import { useLoaderData } from "react-router"
import { Button } from "@/components/ui/button"

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

  return (
    <div className="flex min-h-svh items-center justify-center px-4">
      <div className="w-full max-w-[340px] space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome, {user.username}
          </h1>
          <p className="text-sm text-muted-foreground">
            You are signed in.
          </p>
        </div>
        <Button
          onClick={handleLogout}
          variant="outline"
          className="h-10 w-full font-medium tracking-wide"
        >
          Sign out
        </Button>
      </div>
    </div>
  )
}
