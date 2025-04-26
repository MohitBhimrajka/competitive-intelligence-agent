import { Bell, User } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-card border-b border-border">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold">Dashboard</h2>
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-2 rounded-full hover:bg-muted">
            <Bell className="w-5 h-5 text-muted-foreground" />
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
            <span className="text-sm font-medium">Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
} 