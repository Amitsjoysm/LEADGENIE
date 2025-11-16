import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Users, Building2, CreditCard, TrendingUp, Search, DollarSign } from 'lucide-react';
import api from '../utils/api';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalProfiles: 0,
    totalCompanies: 0,
    creditsUsed: 0,
    recentSearches: 0
  });

  useEffect(() => {
    // In a real app, fetch these stats from API
    setStats({
      totalProfiles: 0,
      totalCompanies: 0,
      creditsUsed: 0,
      recentSearches: 0
    });
  }, []);

  const statCards = [
    {
      title: 'Available Credits',
      value: user?.credits || 0,
      icon: CreditCard,
      description: 'Use credits to reveal contact info',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Profiles Found',
      value: stats.totalProfiles,
      icon: Users,
      description: 'Total profiles in database',
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50'
    },
    {
      title: 'Companies',
      value: stats.totalCompanies,
      icon: Building2,
      description: 'Unique companies tracked',
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50'
    },
    {
      title: 'Recent Searches',
      value: stats.recentSearches,
      icon: TrendingUp,
      description: 'Searches this week',
      color: 'text-violet-600',
      bgColor: 'bg-violet-50'
    }
  ];

  return (
    <div className="space-y-8 fade-in" data-testid="dashboard-page">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl p-8 text-white shadow-lg">
        <h1 className="text-3xl font-bold mb-2" data-testid="dashboard-welcome">
          Welcome back, {user?.full_name}!
        </h1>
        <p className="text-blue-100 mb-6">
          Find high-quality leads and grow your business with precision targeting
        </p>
        <div className="flex gap-4">
          <Link to="/profiles">
            <Button 
              size="lg" 
              className="bg-white text-blue-600 hover:bg-blue-50"
              data-testid="search-profiles-cta"
            >
              <Search className="w-5 h-5 mr-2" />
              Search Profiles
            </Button>
          </Link>
          <Link to="/plans">
            <Button 
              size="lg" 
              variant="outline" 
              className="border-white text-white hover:bg-white/10"
              data-testid="buy-credits-cta"
            >
              <DollarSign className="w-5 h-5 mr-2" />
              Buy Credits
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card 
              key={index} 
              className="card-hover glass-card" 
              data-testid={`stat-card-${stat.title.toLowerCase().replace(' ', '-')}`}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 ${stat.bgColor} rounded-lg`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" data-testid={`stat-value-${index}`}>
                  {stat.value.toLocaleString()}
                </div>
                <p className="text-sm text-gray-500 mt-1">{stat.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with these common tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/profiles">
              <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl hover:shadow-md cursor-pointer" data-testid="quick-action-search">
                <Search className="w-8 h-8 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-1">Search Leads</h3>
                <p className="text-sm text-gray-600">Find profiles by job title, industry, location</p>
              </div>
            </Link>
            
            <Link to="/companies">
              <div className="p-6 bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl hover:shadow-md cursor-pointer" data-testid="quick-action-companies">
                <Building2 className="w-8 h-8 text-cyan-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-1">Browse Companies</h3>
                <p className="text-sm text-gray-600">Explore companies by size and industry</p>
              </div>
            </Link>
            
            <Link to="/plans">
              <div className="p-6 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl hover:shadow-md cursor-pointer" data-testid="quick-action-plans">
                <CreditCard className="w-8 h-8 text-emerald-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-1">Buy Credits</h3>
                <p className="text-sm text-gray-600">Purchase credits to unlock contact details</p>
              </div>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
          <CardDescription>Start finding your ideal customers in 3 simple steps</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">1</div>
              <h3 className="font-semibold text-gray-900 mb-2">Search & Filter</h3>
              <p className="text-sm text-gray-600">Use advanced filters to find your target audience by industry, job title, location, and more</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-cyan-500 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">2</div>
              <h3 className="font-semibold text-gray-900 mb-2">Review Matches</h3>
              <p className="text-sm text-gray-600">Browse through qualified leads that match your criteria with detailed profiles</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">3</div>
              <h3 className="font-semibold text-gray-900 mb-2">Unlock & Connect</h3>
              <p className="text-sm text-gray-600">Use credits to reveal email and phone numbers, then reach out directly</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
