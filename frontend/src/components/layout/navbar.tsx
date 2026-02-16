"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { ThemeToggle } from "./theme-toggle";

export function Navbar() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  const handleSignOut = () => {
    signOut();
    router.push("/auth");
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-border-subtle bg-surface/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <button
          onClick={() => router.push("/dashboard")}
          className="font-[family-name:var(--font-display)] text-xl font-bold tracking-tight transition-opacity hover:opacity-80"
        >
          <span className="gradient-text">Operate</span>
          <span className="text-accent">+</span>
        </button>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {user && (
            <span className="hidden text-sm text-text-secondary sm:block">
              {user.name}
            </span>
          )}
          <ThemeToggle />
          <button
            onClick={handleSignOut}
            className="flex h-9 w-9 items-center justify-center rounded-lg
                       border border-border-subtle text-text-secondary
                       transition-all duration-200
                       hover:border-danger/30 hover:text-danger
                       active:scale-95"
            aria-label="Sign out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </nav>
  );
}
