import React, { useState } from 'react';
import { apiCall } from '../hooks/useApi';

const ApiTest = () => {
  const [testResult, setTestResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirm, setRegConfirm] = useState('');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const testApiConnection = async () => {
    setLoading(true);
    setTestResult('Testing...');
    try {
      const result = await apiCall('/ping', { method: 'GET' });
      setTestResult(`✅ Success! Backend responded: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestResult(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTestResult('Registering...');
    try {
      const result = await apiCall('/auth', {
        method: 'POST',
        body: JSON.stringify({ email: regEmail, password: regPassword })
      });
      setTestResult(`✅ Registration successful! Result: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestResult(`❌ Registration failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTestResult('Logging in...');
    try {
      const result = await apiCall('/auth/token', {
        method: 'POST',
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });
      setTestResult(`✅ Login successful! Result: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestResult(`❌ Login failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">API Connection Test</h2>
      <button
        onClick={testApiConnection}
        disabled={loading}
        className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 mb-4"
      >
        Test API Connection
      </button>
      <form onSubmit={handleRegister} className="mb-4">
        <h3 className="font-semibold mb-2">Register</h3>
        <input type="email" placeholder="Email" value={regEmail} onChange={e => setRegEmail(e.target.value)} className="w-full mb-2 p-2 border rounded" required />
        <input type="password" placeholder="Password" value={regPassword} onChange={e => setRegPassword(e.target.value)} className="w-full mb-2 p-2 border rounded" required />
        <input type="password" placeholder="Confirm Password" value={regConfirm} onChange={e => setRegConfirm(e.target.value)} className="w-full mb-2 p-2 border rounded" required />
        <button type="submit" disabled={loading || regPassword !== regConfirm} className="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50">Register</button>
        {regPassword !== regConfirm && <div className="text-red-500 text-xs mt-1">Passwords do not match</div>}
      </form>
      <form onSubmit={handleLogin} className="mb-4">
        <h3 className="font-semibold mb-2">Login</h3>
        <input type="email" placeholder="Email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)} className="w-full mb-2 p-2 border rounded" required />
        <input type="password" placeholder="Password" value={loginPassword} onChange={e => setLoginPassword(e.target.value)} className="w-full mb-2 p-2 border rounded" required />
        <button type="submit" disabled={loading} className="w-full bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50">Login</button>
      </form>
      <div className="mt-4 p-3 bg-gray-100 rounded">
        <h3 className="font-semibold mb-2">Result:</h3>
        <pre className="text-sm whitespace-pre-wrap">{testResult}</pre>
      </div>
      <div className="text-xs text-gray-600 mt-2">
        <p>Check browser console for request logs.</p>
        <p>Expected API URL: http://localhost:3003</p>
      </div>
    </div>
  );
};

export default ApiTest; 