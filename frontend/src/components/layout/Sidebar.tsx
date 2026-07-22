"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  GraduationCap,
  LayoutDashboard,
  FileText,
  Brain,
  MessageSquare,
  Network,
  Briefcase,
  LogOut,
  User as UserIcon,
} from "lucide-react";
import { removeToken } from "@/lib/auth";
import { User } from "@/types";
import { cn } from "@/lib/utils";
import ThemeToggle from "@/components/layout/ThemeToggle";

interface SidebarProps {
  user: User | null;
}

export default function Sidebar({ user }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const menuItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "My Notes", href: "/documents", icon: FileText },
    { name: "Flashcards", href: "/flashcards", icon: Brain },
    { name: "Quizzes", href: "/quizzes", icon: MessageSquare },
    { name: "Doubt Solver", href: "/chat", icon: MessageSquare },
    { name: "Knowledge Graph", href: "/graph", icon: Network },
    { name: "Placement Prep", href: "/resume", icon: Briefcase },
  ];

  const handleLogout = () => {
    removeToken();
    router.push("/");
    router.refresh();
  };

  return (
    <aside className="w-64 bg-card border-r border-border/50 flex flex-col h-full shrink-0">
      {/* Branding */}
      <div className="h-16 flex items-center px-6 border-b border-border/40 gap-2.5">
        <GraduationCap className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg bg-gradient-to-r from-primary to-indigo-500 bg-clip-text text-transparent">
          StudyMate AI
        </span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-6 px-4 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/10"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User profile & controls */}
      <div className="p-4 border-t border-border/40 space-y-2 bg-accent/10">
        <div className="flex items-center gap-3 px-3 mb-2">
          <div className="h-9 w-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold text-sm shrink-0">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="h-4 w-4" />}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate text-foreground leading-tight">
              {user?.full_name || "User Account"}
            </p>
            <p className="text-xs text-muted-foreground truncate font-light mt-0.5">
              {user?.email || "student@university.edu"}
            </p>
          </div>
        </div>

        {/* Theme toggle — compact pill variant */}
        <ThemeToggle compact />

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/5 rounded-xl transition-all duration-200"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}

