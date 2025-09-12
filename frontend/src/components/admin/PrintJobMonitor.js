import React, { useState, useEffect } from 'react';

const PrintJobMonitor = () => {
  const [printJobs, setPrintJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadJobs = async () => {
      await new Promise(resolve => setTimeout(resolve, 600));
      setPrintJobs([
        { id: '1', order: '#12345', status: 'printing', progress: 75, printer: 'HP LaserJet Pro', eta: '5 min' },
        { id: '2', order: '#12346', status: 'queued', progress: 0, printer: 'Canon Inkjet', eta: '15 min' },
        { id: '3', order: '#12347', status: 'completed', progress: 100, printer: 'Epson Sublimation', eta: 'Done' },
        { id: '4', order: '#12348', status: 'failed', progress: 45, printer: 'HP LaserJet Pro', eta: 'Error' }
      ]);
      setLoading(false);
    };
    loadJobs();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'printing': return 'bg-blue-100 text-blue-800';
      case 'queued': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div className="animate-pulse h-64 bg-slate-200 rounded-lg"></div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">8</div>
          <div className="text-sm text-slate-600">Active Jobs</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-yellow-600">12</div>
          <div className="text-sm text-slate-600">Queued</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-green-600">245</div>
          <div className="text-sm text-slate-600">Completed Today</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-red-600">3</div>
          <div className="text-sm text-slate-600">Failed</div>
        </div>
      </div>

      <div className="bg-white border rounded-lg">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">Recent Print Jobs</h3>
        </div>
        <div className="divide-y">
          {printJobs.map((job) => (
            <div key={job.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div>
                  <div className="font-medium">{job.order}</div>
                  <div className="text-sm text-slate-500">{job.printer}</div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="w-24">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{job.progress}%</span>
                    <span>{job.eta}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                  {job.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PrintJobMonitor;