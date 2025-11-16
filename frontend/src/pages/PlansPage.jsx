import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Check, Loader2 } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';

export const PlansPage = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/plans');
      setPlans(response.data);
    } catch (error) {
      toast.error('Failed to load plans');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = (plan) => {
    toast.info('Payment integration coming soon!');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in" data-testid="plans-page">
      <div className="text-center max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
        <p className="text-xl text-gray-600">
          Purchase credits to unlock contact information and grow your business
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.length === 0 ? (
          <div className="col-span-3 text-center py-12">
            <p className="text-gray-500">No plans available at the moment</p>
          </div>
        ) : (
          plans.map((plan, index) => (
            <Card 
              key={plan.id} 
              className={`glass-card card-hover ${index === 1 ? 'border-2 border-blue-600 shadow-xl' : ''}`}
              data-testid={`plan-card-${index}`}
            >
              {index === 1 && (
                <div className="bg-blue-600 text-white text-center py-2 rounded-t-lg font-semibold text-sm">
                  Most Popular
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <CardDescription>{plan.duration_days} days validity</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                  <span className="text-gray-500 ml-2">/ {plan.credits} credits</span>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start">
                      <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button 
                  className={`w-full ${index === 1 ? 'btn-primary' : ''}`}
                  variant={index === 1 ? 'default' : 'outline'}
                  onClick={() => handlePurchase(plan)}
                  data-testid={`purchase-button-${index}`}
                >
                  Purchase Plan
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
