import React, { useState, useEffect } from 'react';
import { Page, PageHeader, DataTable, Button, Modal, Form, FormField, Label, Input } from '@/components/ui';
import { User, QrCode, CheckCircle, XCircle, Search, AlertCircle, RefreshCw, Clock, Activity } from 'lucide-react';
import { useUI } from '@/context/UIContext';
import QRCode from 'qrcode';

// Helper for relative timestamps
const timeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
};

export const RetailersTab = () => {
  const [retailers, setRetailers] = useState([]);
  const [pendingRetailers, setPendingRetailers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // QR Invite State
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteQRUrl, setInviteQRUrl] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [expiresAt, setExpiresAt] = useState(null);
  const [isExpired, setIsExpired] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Timeline State
  const [showTimelineModal, setShowTimelineModal] = useState(false);
  const [selectedRetailer, setSelectedRetailer] = useState(null);
  
  const { addToast } = useUI();

  const fetchRetailersData = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('gc_user');
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const pendingRes = await fetch(`${API_URL}/retailers/pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (pendingRes.ok) {
        const pendingData = await pendingRes.json();
        setPendingRetailers(pendingData);
      }
    } catch (err) {
      console.error(err);
      addToast({ title: 'Error fetching retailers', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRetailersData();
  }, []);

  // Check Expiration Interval
  useEffect(() => {
    if (!expiresAt || !showInviteModal) return;
    
    const checkExpiry = () => {
      const now = new Date();
      const expDate = new Date(expiresAt);
      if (now > expDate && !isExpired) {
        setIsExpired(true);
      }
    };
    
    // Initial check
    checkExpiry();
    const interval = setInterval(checkExpiry, 1000);
    return () => clearInterval(interval);
  }, [expiresAt, showInviteModal, isExpired]);

  const handleGenerateInvite = async () => {
    setIsGenerating(true);
    setIsExpired(false);
    try {
      const token = localStorage.getItem('gc_user');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${API_URL}/retailers/invite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      
      if (!res.ok) throw new Error('Failed to generate invite');
      
      const data = await res.json();
      
      const qrDataUrl = await QRCode.toDataURL(data.qr_url, {
        width: 300,
        margin: 2,
        color: { dark: '#111111', light: '#FFFFFF' }
      });
      
      setInviteQRUrl(qrDataUrl);
      setInviteCode(data.invite_code);
      setExpiresAt(data.expires_at);
    } catch (err) {
      addToast({ title: 'Error generating invite', type: 'error' });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (retailerId) => {
    try {
      const token = localStorage.getItem('gc_user');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${API_URL}/retailers/${retailerId}/approve`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          credit_limit: 50000,
          zone: "East Zone"
        })
      });
      
      if (!res.ok) throw new Error('Failed to approve');
      
      addToast({ title: 'Retailer Approved Successfully!', type: 'success' });
      fetchRetailersData();
    } catch (err) {
      addToast({ title: 'Error approving retailer', type: 'error' });
    }
  };

  const handleReject = async (retailerId) => {
    try {
      const token = localStorage.getItem('gc_user');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const res = await fetch(`${API_URL}/retailers/${retailerId}/reject`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Failed to reject');
      
      addToast({ title: 'Retailer Rejected', type: 'success' });
      fetchRetailersData();
    } catch (err) {
      addToast({ title: 'Error rejecting retailer', type: 'error' });
    }
  };

  const pendingColumns = [
    {
      key: "name",
      label: "Owner Name",
      align: "left",
      sortable: true,
      render: (val, row) => (
        <div className="flex flex-col">
          <span className="font-bold text-[#111111]">{val}</span>
          <span className="text-[10px] text-gray-500 flex items-center gap-1 mt-0.5">
            <Clock size={10} /> {timeAgo(row.registration_time)}
          </span>
        </div>
      )
    },
    {
      key: "shop_name",
      label: "Shop Name",
      align: "left",
      sortable: true
    },
    {
      key: "phone",
      label: "WhatsApp",
      align: "left",
      render: (val) => <span className="font-mono text-xs">{val}</span>
    },
    {
      key: "timeline",
      label: "Timeline",
      align: "center",
      render: (_, row) => (
        <Button 
          variant="secondary" 
          size="sm" 
          className="bg-transparent border-gray-300 text-gray-600 hover:text-black"
          onClick={() => {
            setSelectedRetailer(row);
            setShowTimelineModal(true);
          }}
        >
          <Activity size={14} className="mr-1" /> View Flow
        </Button>
      )
    },
    {
      key: "actions",
      label: "Action",
      align: "right",
      render: (_, row) => (
        <div className="flex justify-end gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleReject(row.id)}
            className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
          >
            <XCircle size={14} />
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleApprove(row.id)}
            className="bg-green-600 hover:bg-green-700 border-none"
          >
            <CheckCircle size={14} className="mr-1" /> Approve
          </Button>
        </div>
      )
    }
  ];

  return (
    <Page>
      <PageHeader
        title="Retailer Onboarding"
        description="Invite new retailers and manage pending approvals."
      >
        <div className="flex gap-2">
          <Button variant="secondary" onClick={fetchRetailersData}>
            <RefreshCw size={16} />
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              setInviteQRUrl('');
              setInviteCode('');
              setExpiresAt(null);
              setIsExpired(false);
              setShowInviteModal(true);
            }}
          >
            <QrCode size={16} className="mr-2" /> Invite Retailer
          </Button>
        </div>
      </PageHeader>

      <div className="mt-6">
        <h3 className="text-sm font-extrabold text-[#111111] uppercase tracking-wider mb-4 flex items-center gap-2">
          <AlertCircle size={16} className="text-orange-500" /> Pending Approvals ({pendingRetailers.length})
        </h3>
        
        <DataTable
          columns={pendingColumns}
          data={pendingRetailers}
          loading={isLoading}
          emptyIcon={User}
          emptyTitle="No pending approvals"
          emptyDescription="All registrations have been processed."
          searchQuery={searchQuery}
          searchKeys={["name", "shop_name", "phone"]}
          pageSize={10}
        />
      </div>

      {/* Invite QR Modal */}
      <Modal
        open={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title="Invite New Retailer"
        size="md"
      >
        <Modal.Body className="flex flex-col items-center justify-center p-6 space-y-6">
          {!inviteQRUrl ? (
            <div className="text-center w-full">
              <div className="bg-[#FAFAFA] p-6 rounded-xl border border-[#EBEBEB] mb-6">
                <QrCode size={48} className="mx-auto text-[#666666] mb-4" />
                <h4 className="text-[#111111] font-bold mb-2">Generate Unique Invitation</h4>
                <p className="text-xs text-[#666666]">
                  This will generate a one-time use WhatsApp QR code linked to your tenant account. 
                  The retailer will scan this code to begin onboarding.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={handleGenerateInvite}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? "Generating..." : "Generate QR Code"}
              </Button>
            </div>
          ) : (
            <div className="text-center w-full animate-in fade-in zoom-in duration-300">
              <h3 className="font-extrabold text-xl mb-2 text-[#111111]">Scan to Register</h3>
              <p className="text-sm text-[#666666] mb-6">Have the retailer scan this code with their camera.</p>
              
              <div className={`relative bg-white p-4 rounded-2xl border-2 ${isExpired ? 'border-red-500 opacity-50' : 'border-[#111111]'} inline-block mb-6 shadow-xl transition-all`}>
                <img src={inviteQRUrl} alt="WhatsApp Invite QR" className="w-64 h-64 object-contain" />
                {isExpired && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-xl">
                    <span className="bg-red-600 text-white font-bold py-1 px-3 rounded-full text-sm">EXPIRED</span>
                  </div>
                )}
              </div>
              
              <div className="bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg p-3 w-full mb-4">
                <p className="text-[10px] text-[#666666] font-bold uppercase tracking-wider mb-1">Invite Code</p>
                <p className={`font-mono text-sm font-bold ${isExpired ? 'text-red-500 line-through' : 'text-[#111111]'}`}>{inviteCode}</p>
              </div>

              {isExpired && (
                <Button variant="primary" className="w-full" onClick={handleGenerateInvite} disabled={isGenerating}>
                  {isGenerating ? "Generating..." : "Generate New QR"}
                </Button>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowInviteModal(false)} className="w-full">
            {inviteQRUrl && !isExpired ? "Done" : "Close"}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Timeline Modal */}
      <Modal
        open={showTimelineModal}
        onClose={() => setShowTimelineModal(false)}
        title={selectedRetailer ? `${selectedRetailer.shop_name} Timeline` : "Timeline"}
        size="md"
      >
        <Modal.Body className="p-6">
          {selectedRetailer && selectedRetailer.timeline && selectedRetailer.timeline.length > 0 ? (
            <div className="relative border-l border-gray-200 ml-3 space-y-6">
              {selectedRetailer.timeline.map((evt, idx) => (
                <div key={idx} className="relative pl-6">
                  <span className="absolute -left-2.5 top-1 h-5 w-5 rounded-full border-2 border-white bg-blue-500 flex items-center justify-center">
                    <div className="h-1.5 w-1.5 rounded-full bg-white"></div>
                  </span>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-bold text-[#111111]">
                        {evt.event.replace(/_/g, ' ')}
                      </p>
                      {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          {JSON.stringify(evt.metadata)}
                        </p>
                      )}
                    </div>
                    <span className="text-xs font-mono text-gray-400 whitespace-nowrap ml-4">
                      {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Activity size={32} className="mx-auto mb-2 opacity-20" />
              <p>No timeline data available for this retailer.</p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowTimelineModal(false)} className="w-full">
            Close
          </Button>
        </Modal.Footer>
      </Modal>

    </Page>
  );
};
