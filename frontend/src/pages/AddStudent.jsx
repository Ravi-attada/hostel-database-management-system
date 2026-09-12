import { useEffect, useState } from 'react';
import axios from 'axios';
import { UserPlus, Calendar, Phone, User, BedDouble, FileText, Info, Save } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AddStudent() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  
  const today = new Date().toISOString().split('T')[0];
  const [form, setForm] = useState({
    name: '',
    phone: '',
    room_id: '',
    join_date: today,
    food_start_date: today,
    advance_paid: 0,
    notes: ''
  });

  useEffect(() => {
    axios.get('http://localhost:5000/api/rooms/available')
      .then(res => {
        setRooms(res.data);
        if (res.data.length > 0) {
          setForm(prev => ({...prev, room_id: res.data[0].id}));
        }
      })
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    if (form.food_start_date && form.room_id) {
      axios.get(`http://localhost:5000/api/rent-preview?food_date=${form.food_start_date}&room_id=${form.room_id}`)
        .then(res => {
          if (!res.data.error) {
            setPreview(res.data);
          }
        })
        .catch(err => console.error(err));
    }
  }, [form.food_start_date, form.room_id]);

  const handleChange = (e) => {
    setForm({...form, [e.target.name]: e.target.value});
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    axios.post('http://localhost:5000/api/tenant/add', {
      ...form,
      rent_start_date: form.food_start_date, // Sync rent start with food start as default
    })
      .then(res => {
        setLoading(false);
        if (res.data.success) {
          navigate('/rooms');
        } else {
          alert('Error: ' + res.data.error);
        }
      })
      .catch(err => {
        setLoading(false);
        console.error(err);
      });
  };

  const advanceTotal = preview ? preview.advance_amount : 10000;
  const advanceRemaining = advanceTotal - form.advance_paid;

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-700">
      <div className="glass-card p-6 rounded-2xl flex items-center shadow-lg border-b-4 border-b-blue-500">
        <div className="bg-gradient-to-tr from-blue-500 to-indigo-500 p-3 rounded-xl shadow-lg shadow-blue-500/30 mr-4 group-hover:scale-110 transition-transform">
          <UserPlus className="w-8 h-8 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-slate-800 dark:text-white tracking-tight">Onboard New Student</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Register tenant, calculate prorated rent, and collect advance.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col lg:flex-row gap-6">
        {/* Left Side: Form Fields */}
        <div className="flex-1 space-y-6">
          <div className="glass-panel p-8 rounded-2xl shadow-xl border border-white/20 dark:border-slate-700/50">
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-6 border-b border-slate-100 dark:border-slate-700/50 pb-3">Personal & Room Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="space-y-2 group">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                  <User className="w-4 h-4 mr-2 text-blue-500" /> Full Name <span className="text-rose-500 ml-1">*</span>
                </label>
                <input 
                  required type="text" name="name" value={form.name} onChange={handleChange}
                  placeholder="e.g. Rahul Kumar"
                  className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-800 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="space-y-2 group">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                  <Phone className="w-4 h-4 mr-2 text-emerald-500" /> Phone Number <span className="text-rose-500 ml-1">*</span>
                </label>
                <input 
                  required type="text" name="phone" value={form.phone} onChange={handleChange}
                  placeholder="10-digit number"
                  className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-800 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div className="space-y-2 group mb-6">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                <BedDouble className="w-4 h-4 mr-2 text-violet-500" /> Assign Room <span className="text-rose-500 ml-1">*</span>
              </label>
              <select 
                required name="room_id" value={form.room_id} onChange={handleChange}
                className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              >
                <option value="">-- Select an Available Room --</option>
                {rooms.map(r => (
                  <option key={r.id} value={r.id}>
                    Floor {r.floor_name} - Room {r.room_number} ({r.is_ac ? 'AC' : 'Non-AC'}) - {r.available_beds} beds left
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2 group">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-slate-500" /> Joining Date <span className="text-rose-500 ml-1">*</span>
                </label>
                <input 
                  required type="date" name="join_date" value={form.join_date} onChange={handleChange}
                  className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-2.5 text-slate-800 dark:text-white focus:ring-2 focus:ring-blue-500 transition-all"
                />
              </div>

              <div className="space-y-2 group">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-orange-500" /> Food/Rent Start Date <span className="text-rose-500 ml-1">*</span>
                </label>
                <input 
                  required type="date" name="food_start_date" value={form.food_start_date} onChange={handleChange}
                  className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-2.5 text-slate-800 dark:text-white focus:ring-2 focus:ring-orange-500 transition-all"
                />
              </div>
            </div>
            
            <div className="space-y-2 group mt-6">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center">
                <FileText className="w-4 h-4 mr-2 text-amber-500" /> Additional Notes
              </label>
              <textarea 
                name="notes" value={form.notes} onChange={handleChange} rows="2"
                placeholder="Any other info."
                className="w-full bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-800 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
          
          <div className="glass-panel p-8 rounded-2xl shadow-xl border border-white/20 dark:border-slate-700/50">
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-6 border-b border-slate-100 dark:border-slate-700/50 pb-3">Advance Payment</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="text-sm font-bold text-slate-500 dark:text-slate-400 block mb-2">Total Required</label>
                <div className="bg-slate-100 dark:bg-slate-800 px-4 py-3 rounded-xl font-black text-xl text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600">
                  &#8377;{advanceTotal.toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <label className="text-sm font-bold text-emerald-600 dark:text-emerald-400 block mb-2">Advance Paid Now</label>
                <div className="relative">
                  <span className="absolute left-4 top-3 font-black text-slate-400">&#8377;</span>
                  <input 
                    type="number" name="advance_paid" value={form.advance_paid} onChange={handleChange} min="0" step="1"
                    className="w-full pl-8 pr-4 py-3 bg-white dark:bg-slate-900 border-2 border-emerald-500 rounded-xl font-black text-xl text-slate-800 dark:text-white focus:outline-none focus:ring-4 focus:ring-emerald-500/20"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-bold text-rose-500 dark:text-rose-400 block mb-2">Remaining</label>
                <div className={`px-4 py-3 rounded-xl font-black text-xl border ${advanceRemaining > 0 ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-600 border-rose-200 dark:border-rose-800' : 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 border-emerald-200 dark:border-emerald-800'}`}>
                  &#8377;{advanceRemaining.toLocaleString('en-IN')}
                </div>
              </div>
            </div>
          </div>

          <button 
            disabled={loading}
            type="submit" 
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-500/30 flex items-center justify-center transition-all hover:scale-[1.02] active:scale-[0.98] text-lg"
          >
            {loading ? 'Processing...' : <><Save className="w-6 h-6 mr-2" /> Add Student to Hostel</>}
          </button>
        </div>

        {/* Right Side: Prorated Rent Preview */}
        <div className="w-full lg:w-[400px] space-y-6">
          <div className="glass-card p-6 rounded-2xl shadow-lg border border-white/20 dark:border-slate-700/50">
            <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center mb-4">
              <Info className="w-5 h-5 mr-2 text-sky-500" /> Monthly Rent Calculation
            </h3>
            
            {!preview ? (
              <div className="text-center text-slate-500 py-8">Select Food Start Date to calculate rent</div>
            ) : (
              <div className="space-y-6 animate-in slide-in-from-right-4">
                <div className="bg-sky-50 dark:bg-sky-900/20 p-4 rounded-xl border border-sky-100 dark:border-sky-800">
                  <div className="font-bold text-sky-800 dark:text-sky-300 mb-1">{preview.month_label} - First Month Bill</div>
                  <div className="text-sm text-sky-600 dark:text-sky-400">
                    Charged for <strong>{preview.days_charged}</strong> out of <strong>{preview.days_in_month}</strong> days.
                  </div>
                  <div className="text-4xl font-black text-sky-600 dark:text-sky-400 mt-4">
                    &#8377;{preview.total_prorated.toLocaleString('en-IN')}
                  </div>
                  <div className="text-xs text-sky-500 mt-2 font-medium">From next month: &#8377;{preview.total_full.toLocaleString('en-IN')}/month</div>
                </div>

                <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700/50">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Component</th>
                        <th className="px-4 py-3 font-semibold">Full</th>
                        <th className="px-4 py-3 font-semibold">Prorated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50 bg-white/50 dark:bg-slate-900/50">
                      <tr>
                        <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">Room</td>
                        <td className="px-4 py-3 text-slate-600 dark:text-slate-400">&#8377;{preview.room_rent_full.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 font-bold text-slate-800 dark:text-slate-200">&#8377;{preview.room_prorated.toLocaleString('en-IN')}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">Food</td>
                        <td className="px-4 py-3 text-slate-600 dark:text-slate-400">&#8377;{preview.food_rent_full.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 font-bold text-slate-800 dark:text-slate-200">&#8377;{preview.food_prorated.toLocaleString('en-IN')}</td>
                      </tr>
                      <tr className="bg-slate-50/80 dark:bg-slate-800/80">
                        <td className="px-4 py-3 font-bold text-slate-800 dark:text-white">Total</td>
                        <td className="px-4 py-3 font-bold text-slate-800 dark:text-white">&#8377;{preview.total_full.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 font-black text-blue-600 dark:text-blue-400">&#8377;{preview.total_prorated.toLocaleString('en-IN')}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
