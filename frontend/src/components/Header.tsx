import { Moon, Sun } from "lucide-react"
import { useTheme } from "./ThemeProvider"

export default function Header() {
  const { setTheme } = useTheme()

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains("dark")
    setTheme(isDark ? "light" : "dark")
  }

  const isDark = typeof document !== "undefined" && document.documentElement.classList.contains("dark")

  return (
    <header className="border-b bg-background sticky top-0 z-10">
      <div className="container max-w-6xl mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex flex-col">
          <h1 className="text-xl font-bold tracking-tight">AEO Diagnostic</h1>
          <p className="text-xs text-muted-foreground hidden sm:block">
            See how your product ranks across AI engines vs real Google results
          </p>
        </div>
        
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Toggle theme"
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
      </div>
    </header>
  )
}
