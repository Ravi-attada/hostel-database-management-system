import { useEffect, useState } from 'react';
import axios from 'axios';
import { Wallet, Search, CheckCircle2, QrCode, X } from 'lucide-react';

export default function MonthlyRent() {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Modal state
  const [payModal, setPayModal] = useState({ isOpen: false, record: null, amount: 0, date: new Date().toISOString().split('T')[0] });

  const fetchData = () => {
    setLoading(true);
    axios.get(`http://localhost:5000/api/rent-collection?month=${month}`)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching rent collection:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, [month]);

  const handlePay = (e) => {
    e.preventDefault();
    axios.post('http://localhost:5000/api/pay-rent', {
      tenant_id: payModal.record.tenant.id,
      rent_month: month,
      amount: payModal.amount,
      payment_date: payModal.date
    }).then(() => {
      setPayModal({ isOpen: false, record: null, amount: 0, date: '' });
      fetchData(); // Refresh data
    }).catch(err => console.error(err));
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const collection = data?.collection || [];
  const filteredCollection = collection.filter(c => 
    c.tenant.name.toLowerCase().includes(search.toLowerCase()) || 
    c.tenant.room_label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-4 rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-100 p-2 rounded-lg">
            <Wallet className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">Monthly Rent Collection</h2>
        </div>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search student or room..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-white/20 dark:border-slate-700/50 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <input 
            type="month" 
            value={month} 
            onChange={(e) => setMonth(e.target.value)}
            className="border border-white/20 dark:border-slate-700/50 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Summary Cards */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-5 border-l-4 border-l-slate-400">
            <div className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Total Expected</div>
            <div className="text-3xl font-black text-slate-800 dark:text-white">&#8377;{data.summary.expected.toLocaleString('en-IN')}</div>
          </div>
          <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-5 border-l-4 border-l-emerald-500">
            <div className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Total Collected</div>
            <div className="text-3xl font-black text-emerald-600">&#8377;{data.summary.collected.toLocaleString('en-IN')}</div>
          </div>
          <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 p-5 border-l-4 border-l-rose-500">
            <div className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-1">Total Pending</div>
            <div className="text-3xl font-black text-rose-600">&#8377;{data.summary.pending.toLocaleString('en-IN')}</div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="glass-card rounded-xl shadow-sm border border-white/20 dark:border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-500/10 border-b border-white/20 dark:border-slate-700/50 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold">
                <th className="p-4">Student</th>
                <th className="p-4">Room</th>
                <th className="p-4">Amount Due</th>
                <th className="p-4">Amount Paid</th>
                <th className="p-4">Balance</th>
                <th className="p-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/50 dark:divide-slate-700/50">
              {filteredCollection.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-slate-500 dark:text-slate-400">No rent records found for {month}.</td>
                </tr>
              ) : (
                filteredCollection.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-500/10 transition-colors">
                    <td className="p-4">
                      <div className="font-bold text-slate-800 dark:text-white">{c.tenant.name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">{c.tenant.phone}</div>
                    </td>
                    <td className="p-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:text-white">
                        {c.tenant.room_label}
                      </span>
                    </td>
                    <td className="p-4 font-semibold text-slate-700 dark:text-slate-200">&#8377;{c.due.toLocaleString('en-IN')}</td>
                    <td className="p-4 font-semibold text-emerald-600">&#8377;{c.paid.toLocaleString('en-IN')}</td>
                    <td className="p-4">
                      <span className={`font-bold ${c.balance > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                        &#8377;{c.balance.toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      {c.balance > 0 ? (
                        <button 
                          onClick={() => setPayModal({ isOpen: true, record: c, amount: c.balance, date: new Date().toISOString().split('T')[0] })}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors shadow-sm"
                        >
                          Pay
                        </button>
                      ) : (
                        <span className="inline-flex items-center text-emerald-600 text-sm font-medium">
                          <CheckCircle2 className="w-4 h-4 mr-1" /> Paid
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Modal */}
      {payModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-card rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col md:flex-row">
            
            {/* Left side Form */}
            <div className="p-6 md:w-3/5">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xl font-bold text-slate-800 dark:text-white">Record Payment</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{payModal.record.tenant.name} &bull; {payModal.record.tenant.room_label}</p>
                </div>
                <button onClick={() => setPayModal({ ...payModal, isOpen: false })} className="text-slate-400 hover:text-slate-600 dark:text-slate-300 md:hidden">
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handlePay} className="space-y-4">
                <div className="bg-rose-50 p-3 rounded-lg border border-rose-100 mb-4">
                  <div className="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-1">Pending Balance</div>
                  <div className="text-2xl font-black text-rose-700">&#8377;{payModal.record.balance.toLocaleString('en-IN')}</div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">Amount Paying (&#8377;)</label>
                  <input 
                    type="number" 
                    max={payModal.record.balance}
                    value={payModal.amount}
                    onChange={(e) => setPayModal({...payModal, amount: e.target.value})}
                    required
                    className="w-full border border-white/20 dark:border-slate-700/50 rounded-lg px-3 py-2 text-lg font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">Date</label>
                  <input 
                    type="date" 
                    value={payModal.date}
                    onChange={(e) => setPayModal({...payModal, date: e.target.value})}
                    required
                    className="w-full border border-white/20 dark:border-slate-700/50 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="pt-2 flex justify-end space-x-3">
                  <button 
                    type="button" 
                    onClick={() => setPayModal({ ...payModal, isOpen: false })}
                    className="px-4 py-2 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-sm"
                  >
                    Confirm Payment
                  </button>
                </div>
              </form>
            </div>

            {/* Right side QR */}
            <div className="bg-slate-500/10 p-6 md:w-2/5 border-t md:border-t-0 md:border-l border-white/20 dark:border-slate-700/50 flex flex-col items-center justify-center text-center">
               <button onClick={() => setPayModal({ ...payModal, isOpen: false })} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:text-slate-300 hidden md:block">
                  <X className="w-6 h-6" />
               </button>
               <div className="glass-card p-3 rounded-xl shadow-sm mb-4 border border-white/20 dark:border-slate-700/50">
                 <img 
                   src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi%3A%2F%2Fpay%3Fpa%3D8074177332%40ybl%26pn%3DBhavani%20Residency%26am%3D${payModal.amount}%26cu%3DINR`}
                   alt="UPI QR Code" 
                   className="w-40 h-40"
                 />
               </div>
               <div className="flex items-center text-slate-700 dark:text-slate-200 font-bold mb-1">
                 <QrCode className="w-4 h-4 mr-1.5 text-blue-600" />
                 Scan to Pay Exact Amount
               </div>
               <div className="text-sm text-slate-500 dark:text-slate-400">PhonePe: <span className="font-semibold text-slate-700 dark:text-slate-200">8074177332</span></div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
