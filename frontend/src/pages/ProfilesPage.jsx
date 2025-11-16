import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { 
  Search, 
  Filter, 
  Mail, 
  Phone, 
  MapPin, 
  Briefcase, 
  Building2,
  Linkedin,
  Eye,
  EyeOff,
  Loader2
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';

export const ProfilesPage = () => {
  const { user, updateUser } = useAuth();
  const [filters, setFilters] = useState({
    first_name: '',
    last_name: '',
    job_title: '',
    company_name: '',
    industry: '',
    city: '',
    state: '',
    country: '',
    page: 1,
    page_size: 20
  });
  
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [showFilters, setShowFilters] = useState(true);
  const [revealDialog, setRevealDialog] = useState({ open: false, profile: null, type: null });

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await api.post('/profiles/search', filters);
      setProfiles(response.data.profiles);
      setTotal(response.data.total);
      toast.success(`Found ${response.data.total} profiles`);
    } catch (error) {
      toast.error('Failed to search profiles');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleReveal = async (profile, type) => {
    const cost = type === 'email' ? 1 : 3;
    
    if (user.credits < cost) {
      toast.error(`Insufficient credits. You need ${cost} credits.`);
      return;
    }

    try {
      const response = await api.post(`/profiles/${profile.id}/reveal`, {
        profile_id: profile.id,
        reveal_type: type
      });
      
      // Update profile with revealed data
      const updatedProfiles = profiles.map(p => {
        if (p.id === profile.id) {
          return {
            ...p,
            ...(type === 'email' ? { emails: response.data.emails } : { phones: response.data.phones })
          };
        }
        return p;
      });
      setProfiles(updatedProfiles);
      
      // Update user credits
      updateUser({ ...user, credits: user.credits - cost });
      
      toast.success(`${type === 'email' ? 'Email' : 'Phone'} revealed! ${cost} credits used.`);
      setRevealDialog({ open: false, profile: null, type: null });
    } catch (error) {
      toast.error('Failed to reveal contact information');
      console.error(error);
    }
  };

  const openRevealDialog = (profile, type) => {
    setRevealDialog({ open: true, profile, type });
  };

  const isRevealed = (profile, type) => {
    if (type === 'email') {
      return profile.emails && profile.emails.length > 0 && !profile.emails[0].includes('***');
    }
    return profile.phones && profile.phones.length > 0 && !profile.phones[0].includes('***');
  };

  return (
    <div className="space-y-6 fade-in" data-testid="profiles-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Search Profiles</h1>
          <p className="text-gray-600 mt-1">Find and connect with qualified leads</p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          data-testid="toggle-filters-button"
        >
          <Filter className="w-4 h-4 mr-2" />
          {showFilters ? 'Hide' : 'Show'} Filters
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card className="glass-card" data-testid="filters-card">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Filter className="w-5 h-5 mr-2" />
              Search Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  placeholder="John"
                  value={filters.first_name}
                  onChange={(e) => setFilters({ ...filters, first_name: e.target.value })}
                  data-testid="filter-first-name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  placeholder="Doe"
                  value={filters.last_name}
                  onChange={(e) => setFilters({ ...filters, last_name: e.target.value })}
                  data-testid="filter-last-name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="job_title">Job Title</Label>
                <Input
                  id="job_title"
                  placeholder="CEO, CTO, Manager"
                  value={filters.job_title}
                  onChange={(e) => setFilters({ ...filters, job_title: e.target.value })}
                  data-testid="filter-job-title"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input
                  id="company_name"
                  placeholder="Company"
                  value={filters.company_name}
                  onChange={(e) => setFilters({ ...filters, company_name: e.target.value })}
                  data-testid="filter-company-name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Input
                  id="industry"
                  placeholder="Technology, Finance"
                  value={filters.industry}
                  onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
                  data-testid="filter-industry"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  placeholder="New York"
                  value={filters.city}
                  onChange={(e) => setFilters({ ...filters, city: e.target.value })}
                  data-testid="filter-city"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  placeholder="NY"
                  value={filters.state}
                  onChange={(e) => setFilters({ ...filters, state: e.target.value })}
                  data-testid="filter-state"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  placeholder="USA"
                  value={filters.country}
                  onChange={(e) => setFilters({ ...filters, country: e.target.value })}
                  data-testid="filter-country"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button 
                onClick={handleSearch} 
                className="btn-primary"
                disabled={loading}
                data-testid="search-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => setFilters({
                  first_name: '',
                  last_name: '',
                  job_title: '',
                  company_name: '',
                  industry: '',
                  city: '',
                  state: '',
                  country: '',
                  page: 1,
                  page_size: 20
                })}
                data-testid="clear-filters-button"
              >
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {profiles.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-gray-600" data-testid="results-count">
              Found <span className="font-semibold text-gray-900">{total}</span> profiles
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {profiles.map((profile, index) => (
              <Card key={profile.id} className="glass-card card-hover" data-testid={`profile-card-${index}`}>
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900" data-testid={`profile-name-${index}`}>
                            {profile.first_name} {profile.last_name}
                          </h3>
                          <div className="flex items-center text-gray-600 mt-1">
                            <Briefcase className="w-4 h-4 mr-2" />
                            <span data-testid={`profile-job-${index}`}>{profile.job_title}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="flex items-center text-gray-600">
                          <Building2 className="w-4 h-4 mr-2" />
                          <span data-testid={`profile-company-${index}`}>{profile.company_name}</span>
                        </div>
                        
                        {profile.city && (
                          <div className="flex items-center text-gray-600">
                            <MapPin className="w-4 h-4 mr-2" />
                            <span>{profile.city}, {profile.state}, {profile.country}</span>
                          </div>
                        )}
                        
                        {profile.industry && (
                          <div className="flex items-center text-gray-600">
                            <Badge variant="secondary">{profile.industry}</Badge>
                          </div>
                        )}
                        
                        {profile.profile_linkedin_url && (
                          <a 
                            href={profile.profile_linkedin_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center text-blue-600 hover:text-blue-700"
                          >
                            <Linkedin className="w-4 h-4 mr-2" />
                            LinkedIn Profile
                          </a>
                        )}
                      </div>
                      
                      <div className="flex gap-3 pt-4 border-t border-gray-200">
                        {profile.emails && profile.emails.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4 text-gray-400" />
                            {isRevealed(profile, 'email') ? (
                              <span className="text-sm text-gray-700" data-testid={`profile-email-${index}`}>{profile.emails[0]}</span>
                            ) : (
                              <>
                                <span className="text-sm text-gray-400">{profile.emails[0]}</span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openRevealDialog(profile, 'email')}
                                  data-testid={`reveal-email-button-${index}`}
                                >
                                  <Eye className="w-3 h-3 mr-1" />
                                  Reveal (1 credit)
                                </Button>
                              </>
                            )}
                          </div>
                        )}
                        
                        {profile.phones && profile.phones.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-4 h-4 text-gray-400" />
                            {isRevealed(profile, 'phone') ? (
                              <span className="text-sm text-gray-700" data-testid={`profile-phone-${index}`}>{profile.phones[0]}</span>
                            ) : (
                              <>
                                <span className="text-sm text-gray-400">{profile.phones[0]}</span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openRevealDialog(profile, 'phone')}
                                  data-testid={`reveal-phone-button-${index}`}
                                >
                                  <Eye className="w-3 h-3 mr-1" />
                                  Reveal (3 credits)
                                </Button>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Reveal Confirmation Dialog */}
      <Dialog open={revealDialog.open} onOpenChange={(open) => setRevealDialog({ ...revealDialog, open })}>
        <DialogContent data-testid="reveal-dialog">
          <DialogHeader>
            <DialogTitle>Reveal Contact Information</DialogTitle>
            <DialogDescription>
              Are you sure you want to reveal {revealDialog.type === 'email' ? 'email' : 'phone number'}?
              This will cost you {revealDialog.type === 'email' ? '1' : '3'} credit{revealDialog.type === 'phone' ? 's' : ''}.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-3 mt-4">
            <Button 
              variant="outline" 
              onClick={() => setRevealDialog({ open: false, profile: null, type: null })}
              data-testid="cancel-reveal-button"
            >
              Cancel
            </Button>
            <Button 
              onClick={() => handleReveal(revealDialog.profile, revealDialog.type)}
              className="btn-primary"
              data-testid="confirm-reveal-button"
            >
              Reveal ({revealDialog.type === 'email' ? '1' : '3'} credits)
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
