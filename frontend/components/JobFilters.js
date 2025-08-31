import { useState } from 'react';

export default function JobFilters({ onFiltersChange, totalJobs }) {
  const [filters, setFilters] = useState({
    domain: '',
    remote: '',
    search: ''
  });

  const domains = [
    'DevOps', 'Cloud/AWS', 'Java', 'Backend', 'Frontend', 
    'Data/ML', 'QA', 'PM', 'Other'
  ];

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters = { domain: '', remote: '', search: '' };
    setFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Filter Jobs ({totalJobs} found)
        </h2>
        <button
          onClick={clearFilters}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          Clear all
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search
          </label>
          <input
            type="text"
            placeholder="Job title or company..."
            className="input w-full"
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
          />
        </div>

        {/* Domain Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Domain
          </label>
          <select
            className="input w-full"
            value={filters.domain}
            onChange={(e) => handleFilterChange('domain', e.target.value)}
          >
            <option value="">All domains</option>
            {domains.map(domain => (
              <option key={domain} value={domain}>{domain}</option>
            ))}
          </select>
        </div>

        {/* Remote Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Work Type
          </label>
          <select
            className="input w-full"
            value={filters.remote}
            onChange={(e) => handleFilterChange('remote', e.target.value)}
          >
            <option value="">All jobs</option>
            <option value="true">Remote only</option>
            <option value="false">On-site only</option>
          </select>
        </div>

        {/* Quick Actions */}
        <div className="flex items-end">
          <button
            onClick={() => handleFilterChange('remote', 'true')}
            className="btn-secondary w-full"
          >
            Remote Jobs
          </button>
        </div>
      </div>
    </div>
  );
}