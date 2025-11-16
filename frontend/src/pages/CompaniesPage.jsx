import React from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Building2 } from 'lucide-react';

export const CompaniesPage = () => {
  return (
    <div className="space-y-6 fade-in" data-testid="companies-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Companies</h1>
        <p className="text-gray-600 mt-1">Browse and search for companies</p>
      </div>

      <Card className="glass-card p-12 text-center">
        <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">Companies Search</h3>
        <p className="text-gray-500">Company search functionality will be available soon</p>
      </Card>
    </div>
  );
};
