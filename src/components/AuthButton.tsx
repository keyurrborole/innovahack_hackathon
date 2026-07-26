import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { LogIn, User, LogOut, Loader2 } from 'lucide-react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';

const GOOGLE_CLIENT_ID = '341547498123-g9l1ichk7itcceh6g2ab6app7fb3s2t1.apps.googleusercontent.com';

const AuthButtonContent = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [user, setUser] = useState<{ name: string; email: string; picture?: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Check for stored user on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('user');
      }
    }
  }, []);

  const handleGoogleSuccess = (credentialResponse: any) => {
    setIsLoading(true);
    try {
      if (credentialResponse.credential) {
        // Decode the JWT to get user info
        const decoded: any = jwtDecode(credentialResponse.credential);
        const userData = {
          name: decoded.name,
          email: decoded.email,
          picture: decoded.picture,
        };
        
        // Store in state and localStorage
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', credentialResponse.credential);
        
        setIsOpen(false);
        // Redirect to dashboard
        window.location.href = '/cryptoflow/dashboard';
      }
    } catch (error) {
      console.error('Google login processing error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    console.error('Google Login Failed');
  };

  const handleLogout = async () => {
    setIsLoading(true);
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('authToken');
    setIsLoading(false);
    window.location.href = '/cryptoflow';
  };

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full px-4 py-2">
          {user.picture ? (
            <img src={user.picture} alt={user.name} className="h-6 w-6 rounded-full" />
          ) : (
            <User className="h-4 w-4 text-crypto-purple" />
          )}
          <span className="text-sm text-white">{user.name}</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          disabled={isLoading}
          className="text-gray-300 hover:text-white"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <LogOut className="h-4 w-4 mr-2" />
          )}
          Logout
        </Button>
      </div>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" className="text-gray-300 hover:text-white">
          <LogIn className="h-4 w-4 mr-2" />
          Login
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-crypto-blue border-white/10">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-white">
            Welcome to FundFlow Trace
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Sign in with Google to access advanced features
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex justify-center mt-6 py-4">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            theme="filled_black"
            shape="pill"
            size="large"
          />
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-400">
            By signing in, you agree to our{' '}
            <a href="#!" className="text-crypto-purple hover:underline">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="#!" className="text-crypto-purple hover:underline">
              Privacy Policy
            </a>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const AuthButton = () => {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthButtonContent />
    </GoogleOAuthProvider>
  );
};

export default AuthButton;
