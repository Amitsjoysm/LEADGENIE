import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { CollapsibleSidebar } from '../components/CollapsibleSidebar';
import { 
  Search, 
  SlidersHorizontal,
  Mail, 
  Phone, 
  MapPin, 
  Briefcase, 
  Building2,
  Linkedin,
  Eye,
  Loader2,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';

export const ProfilesPage = () => {
  const { user, updateUser } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filters, setFilters] = useState({
    first_name: '',
    last_name: '',
    job_title: '',
    company_name: '',
    industry: '',
    city: '',
    state: '',
    country: '',
    experience_years_min: '',
    experience_years_max: '',
    company_size: '',
    revenue_range: '',
    skills: '',
    page: 1,
    page_size: 20
  });
  
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [revealDialog, setRevealDialog] = useState({ open: false, profile: null, type: null });

  const handleSearch = async () => {
    setLoading(true);
    try {
      const cleanFilters = { ...filters };
      // Convert experience years to numbers
      if (cleanFilters.experience_years_min) {
        cleanFilters.experience_years_min = parseInt(cleanFilters.experience_years_min);
      } else {
        delete cleanFilters.experience_years_min;
      }
      if (cleanFilters.experience_years_max) {
        cleanFilters.experience_years_max = parseInt(cleanFilters.experience_years_max);
      } else {
        delete cleanFilters.experience_years_max;
      }
      
      const response = await api.post('/profiles/search', cleanFilters);
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
      updateUser({ ...user, credits: user.credits - response.data.credits_used });
      
      if (response.data.already_revealed) {
        toast.info(`${type === 'email' ? 'Email' : 'Phone'} already revealed - no credits charged`);
      } else {
        toast.success(`${type === 'email' ? 'Email' : 'Phone'} revealed! ${cost} credits used.`);
      }
      setRevealDialog({ open: false, profile: null, type: null });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reveal contact information');
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

  const clearFilters = () => {
    setFilters({
      first_name: '',
      last_name: '',
      job_title: '',
      company_name: '',
      industry: '',
      city: '',
      state: '',
      country: '',
      experience_years_min: '',
      experience_years_max: '',
      company_size: '',
      revenue_range: '',
      skills: '',
      page: 1,
      page_size: 20
    });
  };

  return (
    <div className="space-y-6 fade-in" data-testid="profiles-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Search Profiles</h1>
          <p className="text-gray-600 mt-1">Find and connect with qualified leads</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setSidebarOpen(true)}
            className="btn-primary"
            data-testid="open-filters-button"
          >
            <SlidersHorizontal className="w-4 h-4 mr-2" />
            Advanced Filters
          </Button>
          <Button
            onClick={handleSearch}
            className="btn-primary"
            disabled={loading}
            data-testid="quick-search-button"
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
        </div>
      </div>

      {/* Collapsible Sidebar */}
      <CollapsibleSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        title="Advanced Filters"
      >
        <div className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 border-b pb-2">Basic Information</h3>
            
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
          </div>

          {/* Company Information */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 border-b pb-2">Company Information</h3>
            
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
              <Label htmlFor="company_size">Company Size</Label>
              <select
                id="company_size"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.company_size}
                onChange={(e) => setFilters({ ...filters, company_size: e.target.value })}
                data-testid="filter-company-size"
              >
                <option value="">All Sizes</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="501-1000">501-1000 employees</option>
                <option value="1000+">1000+ employees</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="revenue_range">Revenue Range</Label>
              <select
                id="revenue_range"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.revenue_range}
                onChange={(e) => setFilters({ ...filters, revenue_range: e.target.value })}
                data-testid="filter-revenue-range"
              >
                <option value="">All Ranges</option>
                <option value="<1M">Less than $1M</option>
                <option value="1M-10M">$1M - $10M</option>
                <option value="10M-50M">$10M - $50M</option>
                <option value="50M-100M">$50M - $100M</option>
                <option value="100M+">$100M+</option>
              </select>
            </div>
          </div>

          {/* Location */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 border-b pb-2">Location</h3>
            
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

          {/* Experience & Skills */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 border-b pb-2">Experience & Skills</h3>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="experience_years_min">Min Years</Label>
                <Input
                  id="experience_years_min"
                  type="number"
                  placeholder="0"
                  value={filters.experience_years_min}
                  onChange={(e) => setFilters({ ...filters, experience_years_min: e.target.value })}
                  data-testid="filter-experience-min"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="experience_years_max">Max Years</Label>
                <Input
                  id="experience_years_max"
                  type="number"
                  placeholder="50"
                  value={filters.experience_years_max}
                  onChange={(e) => setFilters({ ...filters, experience_years_max: e.target.value })}
                  data-testid="filter-experience-max"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="skills">Skills/Keywords</Label>
              <Input
                id="skills"
                placeholder="Python, Leadership, Sales"
                value={filters.skills}
                onChange={(e) => setFilters({ ...filters, skills: e.target.value })}
                data-testid="filter-skills"
              />
              <p className="text-xs text-gray-500">Separate with commas</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3 pt-4 border-t">
            <Button
              onClick={() => {
                handleSearch();
                setSidebarOpen(false);
              }}
              className="btn-primary w-full"
              disabled={loading}
              data-testid="sidebar-search-button"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Apply Filters
                </>
              )}
            </Button>
            
            <Button
              variant="outline"
              onClick={clearFilters}
              className="w-full"
              data-testid="sidebar-clear-filters-button"
            >
              Clear All Filters
            </Button>
          </div>
        </div>
      </CollapsibleSidebar>

      {/* Active Filters Display */}
      {(filters.first_name || filters.last_name || filters.job_title || filters.company_name || filters.industry || filters.city) && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-2">
                <span className="text-sm font-medium text-gray-700">Active Filters:</span>
                {filters.first_name && <Badge variant="secondary">First Name: {filters.first_name}</Badge>}
                {filters.last_name && <Badge variant="secondary">Last Name: {filters.last_name}</Badge>}
                {filters.job_title && <Badge variant="secondary">Job: {filters.job_title}</Badge>}
                {filters.company_name && <Badge variant="secondary">Company: {filters.company_name}</Badge>}
                {filters.industry && <Badge variant="secondary">Industry: {filters.industry}</Badge>}
                {filters.city && <Badge variant="secondary">City: {filters.city}</Badge>}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
              >
                Clear All
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
                        
                        {profile.industry && (
                          <div className="flex items-center text-gray-600">
                            <Badge variant="outline" className="text-xs">{profile.industry}</Badge>
                          </div>
                        )}
                        
                        {profile.city && profile.country && (
                          <div className="flex items-center text-gray-600">
                            <MapPin className="w-4 h-4 mr-2" />
                            <span>{profile.city}, {profile.state && `${profile.state}, `}{profile.country}</span>
                          </div>
                        )}
                        
                        {profile.experience_years && (
                          <div className="flex items-center text-gray-600">
                            <Briefcase className="w-4 h-4 mr-2" />
                            <span>{profile.experience_years} years experience</span>
                          </div>
                        )}
                      </div>

                      {/* Contact Information */}
                      <div className="flex flex-wrap gap-3">
                        {profile.emails && profile.emails.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4 text-gray-500" />
                            <span className="text-sm text-gray-600" data-testid={`profile-email-${index}`}>
                              {profile.emails[0]}
                            </span>
                            {!isRevealed(profile, 'email') && user.role !== 'super_admin' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openRevealDialog(profile, 'email')}
                                data-testid={`reveal-email-${index}`}
                              >
                                <Eye className="w-3 h-3 mr-1" />
                                Reveal (1 credit)
                              </Button>
                            )}
                          </div>
                        )}
                        
                        {profile.phones && profile.phones.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-4 h-4 text-gray-500" />
                            <span className="text-sm text-gray-600" data-testid={`profile-phone-${index}`}>
                              {profile.phones[0]}
                            </span>
                            {!isRevealed(profile, 'phone') && user.role !== 'super_admin' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openRevealDialog(profile, 'phone')}
                                data-testid={`reveal-phone-${index}`}
                              >
                                <Eye className="w-3 h-3 mr-1" />
                                Reveal (3 credits)
                              </Button>
                            )}
                          </div>
                        )}
                        
                        {profile.linkedin_url && (
                          <a
                            href={profile.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                          >
                            <Linkedin className="w-4 h-4" />
                            LinkedIn
                          </a>
                        )}
                      </div>
                      
                      {profile.skills && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {profile.skills.split(',').slice(0, 5).map((skill, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {skill.trim()}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center gap-2">
            <Button
              variant="outline"
              disabled={filters.page === 1}
              onClick={() => {
                setFilters({ ...filters, page: filters.page - 1 });
                handleSearch();
              }}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <span className="flex items-center px-4 text-sm text-gray-600">
              Page {filters.page}
            </span>
            <Button
              variant="outline"
              disabled={profiles.length < filters.page_size}
              onClick={() => {
                setFilters({ ...filters, page: filters.page + 1 });
                handleSearch();
              }}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* No Results */}
      {profiles.length === 0 && !loading && (
        <Card className="glass-card">
          <CardContent className="p-12 text-center">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No profiles found</h3>
            <p className="text-gray-600 mb-4">Try adjusting your search filters or search all profiles</p>
            <Button onClick={handleSearch} className="btn-primary">
              <Search className="w-4 h-4 mr-2" />
              Search All
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Reveal Confirmation Dialog */}
      <Dialog open={revealDialog.open} onOpenChange={(open) => !open && setRevealDialog({ open: false, profile: null, type: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reveal Contact Information</DialogTitle>
            <DialogDescription>
              {revealDialog.type === 'email' 
                ? `This will reveal the email address and cost 1 credit. You have ${user.credits} credits available.`
                : `This will reveal the phone number and cost 3 credits. You have ${user.credits} credits available.`
              }
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRevealDialog({ open: false, profile: null, type: null })}
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleReveal(revealDialog.profile, revealDialog.type)}
              className="btn-primary"
            >
              Confirm Reveal
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
