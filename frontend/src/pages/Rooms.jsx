import { useEffect, useState } from 'react';
import axios from 'axios';
import { Home, Users, UserPlus, Phone, Bed } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Rooms() {
  const [floors, setFloors] = useState([]);
  const [activeFloorId, setActiveFloorId] = useState(null);
  const [floorData, setFloorData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all floors for tabs
    axios.get('http://localhost:5000/api/floors')
      .then(res => {
        setFloors(res.data);
        if (res.data.length > 0) {
          setActiveFloorId(res.data[0].id);
        } else {
          setLoading(false);
        }
      })
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    if (!activeFloorId) return;
    setLoading(true);
    axios.get(`http://localhost:5000/api/floor/${activeFloorId}`)
      .then(res => {
        setFloorData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [activeFloorId]);

  if (loading && !floorData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-4 rounded-xl">
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-tr from-emerald-500 to-teal-400 p-2 rounded-lg shadow-lg shadow-emerald-500/30">
            <Home className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">Rooms & Availability</h2>
        </div>
        <Link to="/add-student" className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all shadow-lg shadow-blue-500/30 flex items-center">
          <UserPlus className="w-4 h-4 mr-2" /> Add Student
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-2">
        {floors.map(floor => (
          <button
            key={floor.id}
            onClick={() => setActiveFloorId(floor.id)}
            className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 whitespace-nowrap ${
              activeFloorId === floor.id 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 transform -translate-y-1' 
                : 'glass-card text-slate-600 dark:text-slate-300 hover:bg-white/80 dark:hover:bg-slate-800/80'
            }`}
          >
            {floor.name}
          </button>
        ))}
      </div>

      {/* Rooms Grid */}
      {floorData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {floorData.rooms.map(room => {
            const occupied = room.tenants.length;
            const isFull = occupied >= room.capacity;
            const occupancyPercent = (occupied / room.capacity) * 100;

            return (
              <div key={room.id} className="glass-panel p-6 rounded-2xl flex flex-col h-full hover:shadow-xl transition-all duration-300">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-2xl font-black text-slate-800 dark:text-white flex items-center">
                      Room {room.room_number}
                      {room.is_ac ? (
                        <span className="ml-3 text-xs bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">AC</span>
                      ) : (
                        <span className="ml-3 text-xs bg-slate-100 text-slate-600 dark:bg-slate-700/50 dark:text-slate-300 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">Non-AC</span>
                      )}
                    </h3>
                    <div className="text-slate-500 dark:text-slate-400 text-sm mt-1 flex items-center">
                      <Bed className="w-4 h-4 mr-1.5" /> {room.capacity} bed capacity
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-3xl font-black ${isFull ? 'text-rose-500' : 'text-emerald-500'}`}>
                      {occupied}<span className="text-lg text-slate-400 dark:text-slate-500 font-semibold">/{room.capacity}</span>
                    </div>
                  </div>
                </div>

                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 mb-6 overflow-hidden">
                  <div 
                    className={`h-2 rounded-full transition-all duration-1000 ${isFull ? 'bg-rose-500' : 'bg-emerald-500'}`} 
                    style={{ width: `${occupancyPercent}%` }}>
                  </div>
                </div>

                <div className="flex-1 bg-slate-50/50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700/50">
                  <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">Current Students</h4>
                  
                  {room.tenants.length === 0 ? (
                    <div className="text-slate-400 dark:text-slate-500 text-sm py-4 text-center italic">Room is entirely vacant.</div>
                  ) : (
                    <ul className="space-y-3">
                      {room.tenants.map(t => (
                        <li key={t.id} className="flex justify-between items-center group">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-sm">
                              {t.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-slate-800 dark:text-slate-200 text-sm">{t.name}</div>
                              <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center mt-0.5">
                                <Phone className="w-3 h-3 mr-1" /> {t.phone}
                              </div>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
