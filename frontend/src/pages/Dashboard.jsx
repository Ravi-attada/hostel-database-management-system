import { useEffect, useState } from 'react';
import axios from 'axios';
import { Users, AlertCircle, TrendingUp, IndianRupee, Activity } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:5000/api/dashboard-stats')
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching stats:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!data) return <div className="text-rose-500 bg-rose-50 p-4 rounded-lg font-medium border border-rose-200">Failed to load data. Ensure Flask server is running.</div>;

  const { stats, rent, collection } = data;
  const occupancyPercentage = Math.round((stats.total_occupied / stats.total_capacity) * 100) || 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
      {collection.pending_count > 0 && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm flex items-start">
          <AlertCircle className="w-6 h-6 text-amber-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-amber-800 font-bold mb-1">Rent Collection Reminder</h3>
            <p className="text-amber-700">
              <strong className="font-semibold">{collection.pending_count} students</strong> have pending rent balances for {collection.month}.
            </p>
          </div>
          <a href="http://localhost:5000/rent" className="ml-auto bg-amber-500 hover:bg-amber-600 text-white px-4 py-1.5 rounded text-sm font-medium transition-colors shadow-sm">
            Collect Now
          </a>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Total Students" 
          value={stats.total_occupied} 
          subtitle={`${stats.total_capacity - stats.total_occupied} beds available`}
          icon={<Users className="w-6 h-6 text-blue-600" />}
          color="bg-blue-100"
        />
        <MetricCard 
          title="Occupancy Rate" 
          value={`${occupancyPercentage}%`} 
          subtitle={`${stats.total_capacity} total capacity`}
          icon={<Activity className="w-6 h-6 text-emerald-600" />}
          progress={occupancyPercentage}
          color="bg-emerald-100"
        />
        <MetricCard 
          title="Total Advance Held" 
          value={`₹${stats.advance_paid.toLocaleString('en-IN')}`} 
          subtitle="Security deposits"
          icon={<IndianRupee className="w-6 h-6 text-violet-600" />}
          color="bg-violet-100"
        />
        <MetricCard 
          title="Pending Rents" 
          value={`₹${collection.total_balance.toLocaleString('en-IN')}`} 
          subtitle={`From ${collection.pending_count} students`}
          icon={<TrendingUp className="w-6 h-6 text-rose-600" />}
          color="bg-rose-100"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2 glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-6 hover:shadow-md transition-shadow">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-6 border-b pb-4">Collection Progress ({collection.month})</h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-300 font-medium">Collected (₹{collection.total_paid.toLocaleString('en-IN')})</span>
                <span className="text-slate-900 font-bold">₹{collection.total_due.toLocaleString('en-IN')} Total</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden shadow-inner">
                <div 
                  className="bg-emerald-500 h-3.5 rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${Math.min(100, (collection.total_paid / (collection.total_due || 1)) * 100)}%` }}>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="bg-slate-500/10 p-4 rounded-xl border border-white/10 dark:border-slate-700/30 flex flex-col justify-center">
                <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1 uppercase tracking-wider">Received</div>
                <div className="text-3xl font-black text-emerald-600">₹{collection.total_paid.toLocaleString('en-IN')}</div>
              </div>
              <div className="bg-slate-500/10 p-4 rounded-xl border border-white/10 dark:border-slate-700/30 flex flex-col justify-center">
                <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1 uppercase tracking-wider">Outstanding</div>
                <div className="text-3xl font-black text-rose-600">₹{collection.total_balance.toLocaleString('en-IN')}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-6 hover:shadow-md transition-shadow">
          <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 border-b pb-4">Current Rates</h3>
          <div className="mb-5">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
              Active: {rent.period}
            </span>
          </div>
          
          <ul className="space-y-4">
            <li className="flex justify-between items-center py-2 border-b border-slate-50">
              <span className="text-slate-600 dark:text-slate-300 flex items-center font-medium"><span className="w-2.5 h-2.5 rounded-full bg-blue-400 mr-2.5"></span>Room Rent</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">₹{rent.room.toLocaleString('en-IN')}</span>
            </li>
            <li className="flex justify-between items-center py-2 border-b border-slate-50">
              <span className="text-slate-600 dark:text-slate-300 flex items-center font-medium"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400 mr-2.5"></span>Food Rent</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">₹{rent.food.toLocaleString('en-IN')}</span>
            </li>
            <li className="flex justify-between items-center mt-4 bg-slate-500/10 p-4 rounded-lg border border-white/10 dark:border-slate-700/30">
              <span className="font-bold text-slate-800 dark:text-white uppercase tracking-wide text-sm">Total Monthly</span>
              <span className="font-black text-blue-700 text-xl">₹{rent.total.toLocaleString('en-IN')}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle, icon, color, progress }) {
  return (
    <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-5 hover:shadow-md transition-all duration-300 transform hover:-translate-y-1">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
      </div>
      <h4 className="text-slate-500 dark:text-slate-400 text-sm font-semibold mb-1 tracking-wide">{title}</h4>
      <div className="text-3xl font-black text-slate-800 dark:text-white mb-1 tracking-tight">{value}</div>
      
      {progress !== undefined ? (
        <div className="mt-4">
          <div className="w-full bg-slate-100 rounded-full h-1.5 mb-2 overflow-hidden">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="text-xs text-slate-400 font-medium">{subtitle}</div>
        </div>
      ) : (
        <div className="text-xs text-slate-400 font-medium mt-3">{subtitle}</div>
      )}
    </div>
  );
}
