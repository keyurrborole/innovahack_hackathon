import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../lib/api';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`OAuth Error: ${errorParam}`);
      setTimeout(() => navigate('/cryptoflow'), 3000);
      return;
    }

    if (!code) {
      setError('No authorization code received');
      setTimeout(() => navigate('/cryptoflow'), 3000);
      return;
    }

    // Exchange the code for tokens
    const handleCallback = async () => {
      try {
        const response = await authApi.handleCallback(code, 'google');
        
        // Store auth data - backend returns user object with name, email, avatar
        const userData = {
          id: response.user.id,
          name: response.user.name,
          email: response.user.email,
        };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.access_token);
        
        // Use window.location for full page navigation to ensure state is fresh
        window.location.href = '/cryptoflow/dashboard';
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'Authentication failed');
        setTimeout(() => navigate('/cryptoflow'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="text-center">
        {error ? (
          <div className="text-red-400">
            <p className="text-xl font-semibold">{error}</p>
            <p className="text-sm text-gray-400 mt-2">Redirecting...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 animate-spin text-crypto-purple" />
            <p className="mt-4 text-white text-lg">Completing sign in...</p>
          </div>
        )}
      </div>
    </div>
  );
}
