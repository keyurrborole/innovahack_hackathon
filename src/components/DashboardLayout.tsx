import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { 
  LayoutDashboard, 
  Upload, 
  BarChart3, 
  Network, 
  FileText, 
  Settings, 
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  Zap
} from "lucide-react";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { useTheme } from "../contexts/ThemeContext";
import { GitBranch, Target, Grid3X3 } from "lucide-react";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Dashboard", href: "/cryptoflow/dashboard", icon: LayoutDashboard },
  { name: "Upload Transactions", href: "/cryptoflow/upload", icon: Upload },
  { name: "Subscription Leaks", href: "/cryptoflow/subscriptions", icon: Zap },
  { name: "Analysis", href: "/cryptoflow/analysis", icon: BarChart3 },
  { name: "Fund flow graph", href: "/cryptoflow/graph", icon: Network },
  { name: "Branch heatmap", href: "/cryptoflow/heatmap", icon: Grid3X3 },
  { name: "Fraud patterns", href: "/cryptoflow/patterns", icon: GitBranch },
  { name: "ML benchmarks", href: "/cryptoflow/benchmarks", icon: Target },
  { name: "FIU reports", href: "/cryptoflow/reports", icon: FileText },
  { name: "Settings", href: "/cryptoflow/settings", icon: Settings },
];

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  
  const userStr = localStorage.getItem("user");
  const user = userStr ? JSON.parse(userStr) : null;

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");
    navigate("/cryptoflow");
  };

  return (
    <div className="min-h-screen transition-colors duration-300 bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-[#0a0118] dark:via-[#1a0b2e] dark:to-[#0a0118]">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/80 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 border-r transition-all duration-300 ease-in-out lg:translate-x-0
        bg-white dark:bg-gradient-to-b dark:from-[#1a0b2e] dark:to-[#0a0118]
        border-gray-200 dark:border-crypto-purple/20
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-crypto-purple/20">
          <Link to="/cryptoflow/dashboard" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-crypto-purple to-pink-600 rounded-lg flex items-center justify-center shadow-lg shadow-crypto-purple/50">
              <span className="text-white font-bold text-sm">FF</span>
            </div>
            <span className="font-bold text-xl bg-gradient-to-r from-crypto-purple via-pink-500 to-purple-400 bg-clip-text text-transparent">
              FundFlow Trace
            </span>
          </Link>
          <button 
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
            title="Close sidebar"
          >
            <X className="h-6 w-6 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center px-4 py-3 text-sm font-medium rounded-lg
                  transition-all duration-200
                  ${isActive 
                    ? 'bg-gradient-to-r from-crypto-purple to-pink-600 text-white shadow-lg shadow-crypto-purple/50' 
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white'
                  }
                `}
              >
                <item.icon className="h-5 w-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-gray-200 dark:border-crypto-purple/20 p-4">
          <div className="flex items-center space-x-3 mb-3 p-3 rounded-lg bg-gray-100 dark:bg-white/5">
            <Avatar>
              <AvatarImage src={user?.avatar} alt={user?.name} />
              <AvatarFallback className="bg-gradient-to-br from-crypto-purple to-pink-600 text-white">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-gray-900 dark:text-white">
                {user?.name || 'Guest'}
              </p>
              <p className="text-xs truncate text-gray-600 dark:text-gray-400">
                {user?.email || 'Not signed in'}
              </p>
            </div>
          </div>
          <Button 
            variant="outline" 
            className="w-full justify-start border-gray-300 text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:border-crypto-purple/30 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white dark:hover:border-crypto-purple"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 backdrop-blur-xl border-b h-16 flex items-center justify-between px-4 lg:px-8 bg-white/80 dark:bg-[#0a0118]/80 border-gray-200 dark:border-crypto-purple/20">
          <div className="flex items-center">
            <button
              className="lg:hidden mr-4"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
              title="Open sidebar"
            >
              <Menu className="h-6 w-6 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:bg-gradient-to-r dark:from-white dark:to-gray-300 dark:bg-clip-text dark:text-transparent">
              {navigation.find(item => item.href === location.pathname)?.name || 'FundFlow Trace'}
            </h1>
          </div>
          
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            className="rounded-full hover:bg-gray-100 dark:hover:bg-white/10"
          >
            {theme === 'dark' ? (
              <Sun className="h-5 w-5 text-yellow-400" />
            ) : (
              <Moon className="h-5 w-5 text-gray-700" />
            )}
          </Button>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8 min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
};
