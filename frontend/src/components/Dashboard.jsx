import { useEffect, useState } from 'react';
import { fetchStatus } from '../services/api';
import ProgressBar from './ProgressBar';

const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const updateStatus = async () => {
    const data = await fetchStatus();
    if (data) {
      setStatus(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    updateStatus();
    const interval = setInterval(updateStatus, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!status) {
    return <div className="text-red-500 text-center mt-10">Error connecting to backend.</div>;
  }

  const { account, progress, connected, mock_mode } = status;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          Trading Bot Dashboard
        </h1>
        <div className="flex gap-2">
           {mock_mode && <span className="px-3 py-1 bg-yellow-600 rounded text-xs font-bold">MOCK MODE</span>}
           <span className={`px-3 py-1 rounded text-xs font-bold ${connected ? 'bg-green-600' : 'bg-red-600'}`}>
             {connected ? 'CONNECTED' : 'DISCONNECTED'}
           </span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-gray-300">Account Info</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Login:</span>
              <span className="font-mono">{account.login}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Balance:</span>
              <span className="font-mono text-xl">${account.balance.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Equity:</span>
              <span className="font-mono text-xl text-blue-400">${account.equity.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
          <h2 className="text-xl font-semibold mb-4 text-gray-300">Daily Goal (10%)</h2>
          <div className="flex flex-col justify-center h-full pb-4">
             <ProgressBar 
               current={progress.daily_profit_pct} 
               target={progress.target_pct} 
               label="Daily Profit" 
             />
             <div className="flex justify-between text-sm mt-2">
               <span className="text-gray-400">Current: ${progress.daily_profit.toFixed(2)}</span>
               <span className="text-gray-400">Target: ${(account.balance * (progress.target_pct/100)).toFixed(2)}</span>
             </div>
             {progress.goal_reached && (
               <div className="mt-4 p-3 bg-green-900/50 border border-green-500 rounded text-center text-green-300 font-bold animate-pulse">
                 🎉 DAILY GOAL REACHED! TRADING STOPPED.
               </div>
             )}
          </div>
        </div>
      </div>

      {/* Placeholder for Trade Log or Chart */}
      <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 opacity-50">
        <h2 className="text-xl font-semibold mb-4 text-gray-300">Active Trades</h2>
        <p className="text-center text-gray-500 py-8">No active trades</p>
      </div>
    </div>
  );
};

export default Dashboard;
