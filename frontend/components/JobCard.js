import { useState } from 'react';

export default function JobCard({ job }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const truncateDescription = (text, maxLength = 150) => {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
  };

  const getDomainColor = (domain) => {
    const colors = {
      'DevOps': 'bg-purple-100 text-purple-800',
      'Cloud/AWS': 'bg-orange-100 text-orange-800',
      'Java': 'bg-red-100 text-red-800',
      'Backend': 'bg-green-100 text-green-800',
      'Frontend': 'bg-blue-100 text-blue-800',
      'Data/ML': 'bg-indigo-100 text-indigo-800',
      'QA': 'bg-yellow-100 text-yellow-800',
      'PM': 'bg-pink-100 text-pink-800',
      'Other': 'bg-gray-100 text-gray-800'
    };
    return colors[domain] || colors['Other'];
  };

  const formatSalary = (min, max) => {
    if (!min && !max) return null;
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    if (max) return `Up to $${max.toLocaleString()}`;
  };

  const handleApply = () => {
    // Open in new tab to original job posting
    window.open(job.apply_url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 mb-1">
            {job.title}
          </h3>
          <p className="text-lg text-gray-600 mb-2">{job.company}</p>
        </div>
        
        <div className="flex flex-col items-end space-y-2">
          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getDomainColor(job.domain)}`}>
            {job.domain}
          </span>
          
          {job.remote && (
            <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Remote
            </span>
          )}
        </div>
      </div>

      {job.location && (
        <p className="text-sm text-gray-500 mb-2">📍 {job.location}</p>
      )}

      {formatSalary(job.salary_min, job.salary_max) && (
        <p className="text-sm text-gray-600 mb-3">💰 {formatSalary(job.salary_min, job.salary_max)}</p>
      )}

      <div className="mb-4">
        <p className="text-gray-700">
          {isExpanded ? job.description : truncateDescription(job.description)}
        </p>
        
        {job.description.length > 150 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm mt-1"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-500">
          <span>Source: {job.source}</span>
          <span className="mx-2">•</span>
          <span>{new Date(job.created_at).toLocaleDateString()}</span>
        </div>
        
        <button
          onClick={handleApply}
          className="btn-primary"
        >
          Apply Now
        </button>
      </div>
    </div>
  );
}