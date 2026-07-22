"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { User } from "@/types";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname)}`);
    } else {
      // Token exists, fetch user details to verify token validity
      api.get<User>("/auth/me")
        .then((userData) => {
          setUser(userData);
          setAuthorized(true);
        })
        .catch(() => {
          // Token expired or invalid
          router.push("/login");
        });
    }
  }, [router]);

  if (!authorized) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center">
        <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
        <p className="text-sm text-muted-foreground font-medium">Securing session...</p>
      </div>
    );
  }

  const isChat = pathname?.startsWith("/chat");

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar Layout component */}
      <Sidebar user={user} />

      {/* Main content pane — overflow-hidden so each page controls its own scroll */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {isChat ? (
          children
        ) : (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 max-w-7xl w-full mx-auto">
            {children}
          </div>
        )}
      </div>
    </div>
  );
}
